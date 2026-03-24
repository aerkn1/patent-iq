from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import replace
import logging
import os
import shutil
from threading import Lock
from time import perf_counter, sleep
from pathlib import Path
from typing import Any

from patentiq_etl.bronze.ingest_uspto_fulltext import extract_publication_numbers, filter_bulk_xml_to_publications
from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REGISTER_TABLES
from patentiq_etl.common.io import append_jsonl, ensure_dir, parquet_row_count, write_text_json
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.types import BuildSettings, StageResult, utc_now_iso
from patentiq_etl.prebronze.extract import (
    EPAB_GROUP_NAME_MAP,
    _copy_reference_inputs,
    _extract_epab_tip_groups,
    _seed_patstat_scope_tip,
)
from patentiq_etl.prebronze.plan import plan_tip_chunked_export, plan_tip_heritage_chunked_export
from patentiq_etl.prebronze.tip_clients import (
    close_tip_client,
    get_patstat_client,
    get_patstat_database_module,
    query_to_dataframe,
    resolve_patstat_model,
    resolve_register_model,
    slugify_value,
    write_dataframe_parquet,
)


LOGGER = logging.getLogger(__name__)

ALL_TIP_SEED_KEYS = (
    "seed_appln_ids",
    "seed_family_ids",
    "seed_publn_ids",
    "seed_person_ids",
    "seed_ep_appln_ids",
    "seed_us_publication_numbers",
    "seed_ep_publication_numbers",
    "seed_family_field_counts",
)

CHUNK_MINIMAL_SEED_KEYS = {
    "seed_appln_ids",
    "seed_family_ids",
    "seed_ep_appln_ids",
    "seed_family_field_counts",
}

CHUNK_DERIVED_SEED_KEYS = {
    "seed_publn_ids",
    "seed_person_ids",
    "seed_us_publication_numbers",
    "seed_ep_publication_numbers",
}


PATSTAT_FAMILY_TABLES = {
    "core": [
        "bronze_patstat_appln",
        "bronze_patstat_appln_title",
        "bronze_patstat_appln_abstr",
        "bronze_patstat_appln_prior",
        "bronze_patstat_person",
        "bronze_patstat_pers_appln",
        "bronze_patstat_appln_ipc",
        "bronze_patstat_appln_contn",
        "bronze_patstat_appln_cpc",
        "bronze_patstat_appln_techn_field",
    ],
    "publications": [
        "bronze_patstat_pat_publn",
    ],
    "legal": [
        "bronze_patstat_inpadoc_legal_event",
        "bronze_ref_legal_event_code",
    ],
    "citations": [
        "bronze_patstat_citation",
        "bronze_patstat_npl_publn",
        "bronze_patstat_docdb_fam_citn",
    ],
}


def _citation_npl_column(path: Path) -> str | None:
    """Return the citation parquet column that carries NPL publication ids."""
    import duckdb

    con = duckdb.connect()
    columns = [row[0] for row in con.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()]
    for candidate in ("cited_npl_publn_id", "npl_publn_id"):
        if candidate in columns:
            return candidate
    return None


def _chunk_manifest_path(settings: BuildSettings, chunk_id: str) -> Path:
    """Return the per-chunk manifest path."""
    return settings.manifests_dir / "chunks" / f"{chunk_id}.json"


def _chunk_temp_dir(settings: BuildSettings, chunk_id: str) -> Path:
    """Return the local temporary directory for one chunk."""
    return settings.repo_root / "etl" / "data" / "temp" / "chunks" / chunk_id


def _seed_dir_for_horizon(settings: BuildSettings, horizon_label: str) -> Path:
    """Return the bounded seed directory for one extraction horizon."""
    if horizon_label == "heritage":
        return settings.repo_root / "etl" / "data" / "raw-bounded-heritage" / "_seeds"
    return settings.bounded_seed_dir


def _chunk_seed_sidecar_dir(settings: BuildSettings, horizon_label: str, seed_key: str) -> Path:
    """Return the per-seed sidecar directory used by chunk-derived seed consolidation."""
    return _seed_dir_for_horizon(settings, horizon_label) / "_chunk_derived" / seed_key


def _quote_duckdb_path(path: Path) -> str:
    """Return a single-quoted DuckDB-safe filesystem path literal."""
    return str(path).replace("'", "''")


def _copy_duckdb_query_to_parquet(query: str, out_path: Path) -> int:
    """Materialize one DuckDB query to parquet and return its row count."""
    import duckdb

    ensure_dir(out_path.parent)
    con = duckdb.connect()
    con.execute(f"copy ({query}) to '{_quote_duckdb_path(out_path)}' (format parquet, compression zstd)")
    return parquet_row_count(out_path)


def _successfully_finished(path: Path) -> bool:
    """Return whether a chunk manifest indicates a completed successful chunk."""
    if not path.exists():
        return False
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return payload.get("status") == "success"


def _get_container_client(settings: BuildSettings):
    """Return an Azure Blob container client when intermediate upload is enabled."""
    execution = settings.execution or {}
    if not execution.get("blob_intermediate_enabled", False):
        return None
    connection_env = settings.azure.get("connection_string_env")
    if not connection_env:
        raise RuntimeError("Azure blob intermediate upload is enabled but no connection_string_env is configured.")
    connection_string = os.environ.get(connection_env)
    if not connection_string:
        raise RuntimeError(
            f"Azure blob intermediate upload is enabled but environment variable `{connection_env}` is not set."
        )
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(
        connection_string,
        connection_timeout=max(1, int(execution.get("upload_connection_timeout_seconds", 60))),
        read_timeout=max(1, int(execution.get("upload_read_timeout_seconds", 1200))),
    )
    return service.get_container_client(settings.azure["container"])


def _stage_event_log_path(settings: BuildSettings, stage_name: str) -> Path:
    """Return the JSONL path for rich real-time stage events."""
    return settings.manifests_dir / "stages" / f"{stage_name}.events.jsonl"


def _scheduler_limits(settings: BuildSettings, horizon_label: str) -> tuple[int, dict[str, int]]:
    """Return the global and family-level concurrency limits for one horizon."""
    execution = settings.execution or {}
    if horizon_label == "heritage":
        global_limit = int(execution.get("heritage_max_parallel_chunks", 1))
        raw_family_limits = execution.get("heritage_max_workers", {})
    else:
        global_limit = int(execution.get("tip_max_parallel_chunks", 2))
        raw_family_limits = execution.get("max_workers", {})
    family_limits = {str(key): max(1, int(value)) for key, value in raw_family_limits.items()}
    return max(1, global_limit), family_limits


def _upload_options(settings: BuildSettings) -> dict[str, int]:
    """Return Azure upload tuning options sized for constrained TIP runtimes."""
    execution = settings.execution or {}
    return {
        "max_concurrency": max(1, int(execution.get("upload_max_concurrency", 3))),
        "max_block_size": max(1, int(execution.get("upload_max_block_size_mb", 8))) * 1024 * 1024,
        "max_single_put_size": max(1, int(execution.get("upload_max_single_put_size_mb", 16))) * 1024 * 1024,
        "retry_max_attempts": max(1, int(execution.get("upload_retry_max_attempts", 3))),
        "retry_backoff_seconds": max(1, int(execution.get("upload_retry_backoff_seconds", 5))),
    }


def _is_retryable_blob_error(exc: Exception) -> bool:
    """Return whether one Blob upload exception looks transient and worth retrying."""
    text = f"{exc.__class__.__name__}: {exc}".lower()
    markers = (
        "serviceresponseerror",
        "timeout",
        "timed out",
        "connection aborted",
        "connect timeout",
        "read timeout",
        "write operation timed out",
        "temporarily unavailable",
        "connection reset",
        "remote end closed connection",
    )
    return any(marker in text for marker in markers)


def _upload_paths(
    container,
    files: list[Path],
    blob_prefix: str,
    upload_options: dict[str, int],
    *,
    logger: logging.Logger | None = None,
    emit_event=None,
    chunk_id: str | None = None,
) -> list[str]:
    """Upload files to one blob prefix and return blob names."""
    uploaded: list[str] = []
    if container is None:
        return uploaded
    prefix = blob_prefix.rstrip("/")
    for path in files:
        if not path.is_file():
            continue
        blob_name = f"{prefix}/{path.name}"
        size_bytes = path.stat().st_size
        try:
            blob_client = container.get_blob_client(
                blob_name,
                max_block_size=upload_options["max_block_size"],
                max_single_put_size=upload_options["max_single_put_size"],
            )
            tuning_mode = "client_and_upload"
        except TypeError:
            blob_client = container.get_blob_client(blob_name)
            tuning_mode = "upload_only"
        if logger is not None:
            logger.info(
                "Uploading blob chunk_id=%s blob=%s size_bytes=%s max_concurrency=%s tuning_mode=%s",
                chunk_id or "-",
                blob_name,
                size_bytes,
                upload_options["max_concurrency"],
                tuning_mode,
            )
        if emit_event is not None:
            emit_event(
                "blob_upload_started",
                chunk_id=chunk_id,
                blob_name=blob_name,
                size_bytes=size_bytes,
                max_concurrency=upload_options["max_concurrency"],
                tuning_mode=tuning_mode,
            )

        def _upload_once() -> None:
            with path.open("rb") as handle:
                try:
                    blob_client.upload_blob(
                        handle,
                        overwrite=True,
                        length=size_bytes,
                        max_concurrency=upload_options["max_concurrency"],
                        max_block_size=upload_options["max_block_size"],
                        max_single_put_size=upload_options["max_single_put_size"],
                    )
                except TypeError:
                    handle.seek(0)
                    try:
                        blob_client.upload_blob(
                            handle,
                            overwrite=True,
                            length=size_bytes,
                            max_block_size=upload_options["max_block_size"],
                            max_single_put_size=upload_options["max_single_put_size"],
                        )
                    except TypeError:
                        handle.seek(0)
                        blob_client.upload_blob(handle, overwrite=True)

        attempt_count = upload_options.get("retry_max_attempts", 3)
        for attempt in range(1, attempt_count + 1):
            try:
                _upload_once()
                break
            except Exception as exc:
                retryable = _is_retryable_blob_error(exc)
                if logger is not None:
                    logger.warning(
                        "Blob upload attempt failed chunk_id=%s blob=%s attempt=%s/%s retryable=%s error=%s",
                        chunk_id or "-",
                        blob_name,
                        attempt,
                        attempt_count,
                        retryable,
                        exc,
                    )
                if emit_event is not None:
                    emit_event(
                        "blob_upload_attempt_failed",
                        chunk_id=chunk_id,
                        blob_name=blob_name,
                        attempt=attempt,
                        max_attempts=attempt_count,
                        retryable=retryable,
                        error=str(exc),
                    )
                if not retryable or attempt >= attempt_count:
                    raise
                delay_seconds = upload_options.get("retry_backoff_seconds", 5) * attempt
                if logger is not None:
                    logger.info(
                        "Retrying blob upload chunk_id=%s blob=%s in %s seconds",
                        chunk_id or "-",
                        blob_name,
                        delay_seconds,
                    )
                if emit_event is not None:
                    emit_event(
                        "blob_upload_retry_scheduled",
                        chunk_id=chunk_id,
                        blob_name=blob_name,
                        attempt=attempt,
                        delay_seconds=delay_seconds,
                    )
                sleep(delay_seconds)
        uploaded.append(blob_name)
        if logger is not None:
            logger.info("Uploaded blob chunk_id=%s blob=%s size_bytes=%s", chunk_id or "-", blob_name, size_bytes)
        if emit_event is not None:
            emit_event("blob_upload_finished", chunk_id=chunk_id, blob_name=blob_name, size_bytes=size_bytes)
    return uploaded


def _download_blob_to_path(
    container,
    blob_name: str,
    out_path: Path,
    transfer_options: dict[str, int],
    *,
    logger: logging.Logger | None = None,
    emit_event=None,
    chunk_id: str | None = None,
) -> Path:
    """Download one blob to a local path with retry/backoff support."""
    ensure_dir(out_path.parent)
    attempt_count = transfer_options.get("retry_max_attempts", 3)
    for attempt in range(1, attempt_count + 1):
        try:
            blob_client = container.get_blob_client(blob_name)
            if logger is not None:
                logger.info("Downloading blob chunk_id=%s blob=%s attempt=%s/%s", chunk_id or "-", blob_name, attempt, attempt_count)
            if emit_event is not None:
                emit_event("blob_download_started", chunk_id=chunk_id, blob_name=blob_name, attempt=attempt, max_attempts=attempt_count)
            downloader = blob_client.download_blob(max_concurrency=transfer_options.get("max_concurrency", 1))
            with out_path.open("wb") as handle:
                try:
                    downloader.readinto(handle)
                except Exception:
                    handle.seek(0)
                    handle.truncate(0)
                    handle.write(downloader.readall())
            if emit_event is not None:
                emit_event("blob_download_finished", chunk_id=chunk_id, blob_name=blob_name, output=str(out_path))
            return out_path
        except Exception as exc:
            retryable = _is_retryable_blob_error(exc)
            if logger is not None:
                logger.warning(
                    "Blob download attempt failed chunk_id=%s blob=%s attempt=%s/%s retryable=%s error=%s",
                    chunk_id or "-",
                    blob_name,
                    attempt,
                    attempt_count,
                    retryable,
                    exc,
                )
            if emit_event is not None:
                emit_event(
                    "blob_download_attempt_failed",
                    chunk_id=chunk_id,
                    blob_name=blob_name,
                    attempt=attempt,
                    max_attempts=attempt_count,
                    retryable=retryable,
                    error=str(exc),
                )
            if out_path.exists():
                out_path.unlink(missing_ok=True)
            if attempt >= attempt_count or not retryable:
                raise
            sleep(transfer_options.get("retry_backoff_seconds", 5) * attempt)
    return out_path


def _chunk_scope_tip(settings: BuildSettings, field: str, year_start: int, year_end: int) -> dict[str, Any]:
    """Build one chunk-specific TIP scope bundle with subqueries and small DataFrames."""
    from sqlalchemy import func

    patstat = None
    try:
        patstat, db = get_patstat_client(settings.tip_env)
        database_module = get_patstat_database_module()
        TLS201 = resolve_patstat_model(database_module, "bronze_patstat_appln")
        TLS207 = resolve_patstat_model(database_module, "bronze_patstat_pers_appln")
        TLS211 = resolve_patstat_model(database_module, "bronze_patstat_pat_publn")
        TLS230 = resolve_patstat_model(database_module, "bronze_patstat_appln_techn_field")
        TLS901 = resolve_patstat_model(database_module, "bronze_ref_techn_field_ipc")

        if None in {TLS201, TLS211, TLS230, TLS901}:
            raise RuntimeError("TIP chunk scope requires TLS201, TLS211, TLS230, and TLS901.")

        seed_appln_q = (
            db.query(
                TLS230.appln_id.label("appln_id"),
                TLS901.techn_field.label("wipo_field"),
            )
            .join(TLS201, TLS230.appln_id == TLS201.appln_id)
            .join(TLS901, TLS230.techn_field_nr == TLS901.techn_field_nr)
            .filter(TLS901.techn_field == field)
            .distinct()
        )
        from patentiq_etl.prebronze.tip_clients import apply_year_window_filter

        seed_appln_q = apply_year_window_filter(seed_appln_q, TLS201, year_start, year_end)
        appln_sq = seed_appln_q.subquery()
        family_q = (
            db.query(TLS201.docdb_family_id.label("docdb_family_id"))
            .join(appln_sq, TLS201.appln_id == appln_sq.c.appln_id)
            .filter(TLS201.docdb_family_id.isnot(None))
            .distinct()
        )
        family_sq = family_q.subquery()
        publn_q = (
            db.query(
                TLS211.pat_publn_id.label("pat_publn_id"),
                TLS211.appln_id.label("appln_id"),
                TLS211.publn_auth.label("publn_auth"),
                TLS211.publn_nr.label("publication_number"),
                TLS211.publn_kind.label("publication_kind"),
                TLS211.publn_date.label("publication_date"),
                func.concat(
                    func.coalesce(TLS211.publn_auth, ""),
                    func.coalesce(TLS211.publn_nr, ""),
                    func.coalesce(TLS211.publn_kind, ""),
                ).label("publication_number_full"),
            )
            .join(appln_sq, TLS211.appln_id == appln_sq.c.appln_id)
            .filter(TLS211.pat_publn_id.isnot(None))
            .distinct()
        )
        publn_sq = (
            db.query(TLS211.pat_publn_id.label("pat_publn_id"))
            .join(appln_sq, TLS211.appln_id == appln_sq.c.appln_id)
            .filter(TLS211.pat_publn_id.isnot(None))
            .distinct()
            .subquery()
        )

        person_sq = None
        if TLS207 is not None:
            person_sq = (
                db.query(TLS207.person_id.label("person_id"))
                .join(appln_sq, TLS207.appln_id == appln_sq.c.appln_id)
                .filter(TLS207.person_id.isnot(None))
                .distinct()
                .subquery()
            )

        ep_appln_q = (
            db.query(TLS201.appln_id.label("appln_id"))
            .join(appln_sq, TLS201.appln_id == appln_sq.c.appln_id)
            .filter(TLS201.appln_auth == "EP")
            .distinct()
        )
        ep_publn_df = query_to_dataframe(patstat, publn_q).query("publn_auth == 'EP'").copy()
        us_publn_df = query_to_dataframe(patstat, publn_q).query("publn_auth == 'US'").copy()
        counts = {
            "appln_count": int(query_to_dataframe(patstat, seed_appln_q).shape[0]),
            "family_count": int(query_to_dataframe(patstat, family_q).shape[0]),
            "publn_count": int(query_to_dataframe(patstat, publn_q).shape[0]),
            "ep_appln_count": int(query_to_dataframe(patstat, ep_appln_q).shape[0]),
            "ep_publication_count": int(ep_publn_df.shape[0]),
            "us_publication_count": int(us_publn_df.shape[0]),
        }
        return {
            "database_module": database_module,
            "db": db,
            "patstat": patstat,
            "appln_sq": appln_sq,
            "family_sq": family_sq,
            "publn_sq": publn_sq,
            "person_sq": person_sq,
            "ep_appln_q": ep_appln_q,
            "ep_publn_df": ep_publn_df,
            "us_publn_df": us_publn_df,
            "counts": counts,
        }
    except Exception:
        close_tip_client(patstat)
        raise


def _extract_patstat_family(
    scope: dict[str, Any],
    family_name: str,
    out_dir: Path,
) -> list[Path]:
    """Extract one PATSTAT table family for a chunk into local parquet files."""
    db = scope["db"]
    database_module = scope["database_module"]
    appln_sq = scope["appln_sq"]
    family_sq = scope["family_sq"]
    publn_sq = scope["publn_sq"]
    person_sq = scope["person_sq"]
    outputs: list[Path] = []

    filter_map = {
        "bronze_patstat_appln": ("family", "docdb_family_id"),
        "bronze_patstat_appln_title": ("appln", "appln_id"),
        "bronze_patstat_appln_abstr": ("appln", "appln_id"),
        "bronze_patstat_appln_prior": ("appln", "appln_id"),
        "bronze_patstat_person": ("person", "person_id"),
        "bronze_patstat_pers_appln": ("appln", "appln_id"),
        "bronze_patstat_appln_ipc": ("appln", "appln_id"),
        "bronze_patstat_appln_contn": ("appln", "appln_id"),
        "bronze_patstat_appln_cpc": ("appln", "appln_id"),
        "bronze_patstat_appln_techn_field": ("appln", "appln_id"),
        "bronze_patstat_pat_publn": ("appln", "appln_id"),
        "bronze_patstat_inpadoc_legal_event": ("appln", "appln_id"),
        "bronze_patstat_citation": ("publn", "pat_publn_id"),
        "bronze_patstat_docdb_fam_citn": ("family", "docdb_family_id"),
    }
    seed_map = {
        "appln": appln_sq,
        "family": family_sq,
        "publn": publn_sq,
        "person": person_sq,
    }

    for logical_name in PATSTAT_FAMILY_TABLES.get(family_name, []):
        if logical_name == "bronze_patstat_npl_publn":
            continue
        if logical_name == "bronze_ref_legal_event_code":
            model = resolve_patstat_model(database_module, logical_name)
            if model is None:
                continue
            df = query_to_dataframe(scope["patstat"], db.query(model))
        else:
            model = resolve_patstat_model(database_module, logical_name)
            if model is None:
                continue
            seed_type, column_name = filter_map[logical_name]
            seed_sq = seed_map.get(seed_type)
            if seed_sq is None:
                continue
            query = db.query(model).join(seed_sq, getattr(model, column_name) == getattr(seed_sq.c, column_name))
            df = query_to_dataframe(scope["patstat"], query)
        out_path = ensure_dir(out_dir) / f"{PATSTAT_TABLES[logical_name][0]}.parquet"
        write_dataframe_parquet(df, out_path)
        outputs.append(out_path)

    if family_name == "citations":
        citation_path = out_dir / f"{PATSTAT_TABLES['bronze_patstat_citation'][0]}.parquet"
        if citation_path.exists():
            import duckdb

            con = duckdb.connect()
            npl_col = _citation_npl_column(citation_path)
            if npl_col is not None:
                npl_ids = con.execute(
                    f"select distinct {npl_col} as npl_publn_id from read_parquet(?) where {npl_col} is not null",
                    [str(citation_path)],
                ).df()
            else:
                npl_ids = con.execute("select null::bigint as npl_publn_id where false").df()
            if not npl_ids.empty:
                model = resolve_patstat_model(database_module, "bronze_patstat_npl_publn")
                if model is not None:
                    query = db.query(model).filter(getattr(model, "npl_publn_id").in_(npl_ids["npl_publn_id"].tolist()))
                    df = query_to_dataframe(scope["patstat"], query)
                    out_path = ensure_dir(out_dir) / f"{PATSTAT_TABLES['bronze_patstat_npl_publn'][0]}.parquet"
                    write_dataframe_parquet(df, out_path)
                    outputs.append(out_path)
    return outputs


def _extract_register_family(scope: dict[str, Any], out_dir: Path) -> list[Path]:
    """Extract bounded Register tables for one chunk."""
    db = scope["db"]
    database_module = scope["database_module"]
    outputs: list[Path] = []
    ep_appln_df = query_to_dataframe(scope["patstat"], scope["ep_appln_q"])
    if ep_appln_df.empty:
        return outputs

    reg101_model = resolve_register_model(database_module, "bronze_reg101_appln")
    if reg101_model is None:
        return outputs
    reg101_df = query_to_dataframe(
        scope["patstat"],
        db.query(reg101_model).filter(getattr(reg101_model, "appln_id").in_(ep_appln_df["appln_id"].tolist())),
    )
    reg101_path = ensure_dir(out_dir) / f"{REGISTER_TABLES['bronze_reg101_appln'][0]}.parquet"
    write_dataframe_parquet(reg101_df, reg101_path)
    outputs.append(reg101_path)
    if reg101_df.empty:
        return outputs

    reg_ids = reg101_df["id"].dropna().tolist() if "id" in reg101_df.columns else []
    step_ids: list[Any] = []
    event_codes: list[Any] = []
    reg701_ids: list[Any] = []
    reg731_event_codes: list[Any] = []
    for logical_name in REGISTER_TABLES:
        if logical_name == "bronze_reg101_appln":
            continue
        model = resolve_register_model(database_module, logical_name)
        if model is None:
            continue
        query = None
        if hasattr(model, "appln_id"):
            query = db.query(model).filter(getattr(model, "appln_id").in_(ep_appln_df["appln_id"].tolist()))
        elif hasattr(model, "id") and reg_ids:
            ids = reg701_ids if logical_name == "bronze_reg731_event_data" and reg701_ids else reg_ids
            query = db.query(model).filter(getattr(model, "id").in_(ids))
        elif hasattr(model, "step_id") and step_ids:
            query = db.query(model).filter(getattr(model, "step_id").in_(step_ids))
        elif hasattr(model, "event_code"):
            codes = reg731_event_codes if logical_name == "bronze_reg742_event_text" and reg731_event_codes else event_codes
            if codes:
                query = db.query(model).filter(getattr(model, "event_code").in_(codes))
        if query is None:
            continue
        df = query_to_dataframe(scope["patstat"], query)
        out_path = ensure_dir(out_dir) / f"{REGISTER_TABLES[logical_name][0]}.parquet"
        write_dataframe_parquet(df, out_path)
        outputs.append(out_path)
        if logical_name == "bronze_reg201_proc_step" and "step_id" in df.columns:
            step_ids = df["step_id"].dropna().tolist()
        elif logical_name == "bronze_reg301_event_data" and "event_code" in df.columns:
            event_codes = df["event_code"].dropna().tolist()
        elif logical_name == "bronze_reg701_appln" and "id" in df.columns:
            reg701_ids = df["id"].dropna().tolist()
        elif logical_name == "bronze_reg731_event_data" and "event_code" in df.columns:
            reg731_event_codes = df["event_code"].dropna().tolist()
    return outputs


def _extract_epab_family(settings: BuildSettings, scope: dict[str, Any], out_dir: Path) -> list[Path]:
    """Extract bounded EPAB groups for one chunk."""
    outputs: list[Path] = []
    seed_df = scope["ep_publn_df"]
    if seed_df.empty:
        return outputs
    epab_result = StageResult(stage="epab-chunk-extract", status="success", summary="Materialized bounded EPAB chunk groups.")
    for group, df in _extract_epab_tip_groups(settings, seed_df, epab_result).items():
        out_path = ensure_dir(out_dir) / f"epab_{EPAB_GROUP_NAME_MAP[group]}.parquet"
        write_dataframe_parquet(df, out_path)
        outputs.append(out_path)
    return outputs


def _extract_uspto_family(settings: BuildSettings, scope: dict[str, Any], out_dir: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    """Filter staged USPTO bulk XML files down to the chunk-local U.S. publication slice."""
    outputs: list[Path] = []
    metrics: dict[str, Any] = {}
    warnings: list[str] = []

    seed_df = scope["us_publn_df"]
    publication_values = seed_df["publication_number_full"].tolist() if "publication_number_full" in seed_df.columns else []
    publication_numbers = {
        str(value)
        for value in publication_values
        if value is not None and str(value).strip()
    }
    metrics["uspto_chunk_publication_seed_count"] = len(publication_numbers)
    if not publication_numbers:
        return outputs, metrics, warnings

    xml_files = list(settings.raw_uspto_dir.glob("*.XML")) + list(settings.raw_uspto_dir.glob("*.xml"))
    metrics["uspto_chunk_source_xml_count"] = len(xml_files)
    if not xml_files:
        warnings.append("Chunk requires USPTO full-text support but no staged USPTO bulk XML files were found.")
        metrics["uspto_chunk_output_xml_count"] = 0
        metrics["uspto_chunk_matched_document_count"] = 0
        metrics["uspto_chunk_matched_publication_count"] = 0
        metrics["uspto_chunk_unmatched_publication_count"] = len(publication_numbers)
        return outputs, metrics, warnings

    matched_publications: set[str] = set()
    matched_document_count = 0
    for xml_path in xml_files:
        out_path = ensure_dir(out_dir) / xml_path.name
        matched_in_file = filter_bulk_xml_to_publications(xml_path, publication_numbers, out_path)
        if not matched_in_file:
            continue
        outputs.append(out_path)
        matched_document_count += matched_in_file
        matched_publications.update(extract_publication_numbers(out_path))

    metrics["uspto_chunk_output_xml_count"] = len(outputs)
    metrics["uspto_chunk_matched_document_count"] = matched_document_count
    metrics["uspto_chunk_matched_publication_count"] = len(matched_publications)
    metrics["uspto_chunk_unmatched_publication_count"] = max(len(publication_numbers) - len(matched_publications), 0)
    if not outputs:
        warnings.append("Chunk contains in-scope U.S. publications but no staged USPTO bulk XML records matched them.")
    return outputs, metrics, warnings


def _write_chunk_manifest(
    settings: BuildSettings,
    chunk: dict[str, Any],
    *,
    status: str,
    local_outputs: list[Path],
    uploaded_blobs: list[str],
    metrics: dict[str, Any],
    warnings: list[str],
    started_at: str | None = None,
    finished_at: str | None = None,
    duration_seconds: float | None = None,
) -> Path:
    """Persist one chunk manifest."""
    manifest_path = _chunk_manifest_path(settings, chunk["chunk_id"])
    write_text_json(
        manifest_path,
        {
            "chunk_id": chunk["chunk_id"],
            "field": chunk["field"],
            "year_start": chunk["year_start"],
            "year_end": chunk["year_end"],
            "table_family": chunk["table_family"],
            "status": status,
            "local_outputs": [str(path) for path in local_outputs],
            "uploaded_blobs": uploaded_blobs,
            "metrics": metrics,
            "warnings": warnings,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
        },
    )
    return manifest_path


def _chunk_blob_prefix(chunk: dict[str, Any], *, horizon_label: str) -> str:
    """Return the standard Blob prefix for one chunk payload."""
    blob_root = "raw-bounded-heritage" if horizon_label == "heritage" else "raw-bounded"
    table_family = str(chunk["table_family"])
    family_root = "patstat" if table_family in {"core", "publications", "legal", "citations"} else table_family
    return (
        f"{blob_root}/{family_root}/field={chunk['field_slug']}/"
        f"year={chunk['year_start']}-{chunk['year_end']}/family={table_family}"
    )


def _seed_blob_prefix(horizon_label: str) -> str:
    """Return the Blob prefix used for global seed artifacts."""
    return "raw-bounded-heritage/seeds" if horizon_label == "heritage" else "raw-bounded/seeds"


def _manifest_horizon_label(payload: dict[str, Any]) -> str:
    """Infer the horizon label from one chunk manifest payload."""
    chunk_id = str(payload.get("chunk_id", ""))
    return "heritage" if chunk_id.startswith("heritage__") else "main"


def _recovery_candidate(
    *,
    status: str,
    local_outputs: list[Path],
    uploaded_blobs: list[str],
    warnings: list[str],
) -> bool:
    """Return whether a chunk manifest should be considered eligible for Blob recovery."""
    if not local_outputs:
        return False
    if len(uploaded_blobs) >= len(local_outputs):
        return False
    if status == "success":
        return True
    if status != "failed":
        return False
    warning_text = " ".join(str(item).lower() for item in warnings)
    upload_markers = (
        "upload",
        "blob",
        "azure",
        "timeout",
        "timed out",
        "connection timeout",
        "connect timeout",
        "read timeout",
    )
    return bool(uploaded_blobs) or any(marker in warning_text for marker in upload_markers)


def _required_seed_paths(
    settings: BuildSettings,
    horizon_label: str,
    *,
    seed_keys: set[str] | None = None,
) -> dict[str, Path]:
    """Return the expected seed parquet paths for one horizon."""
    seed_dir = _seed_dir_for_horizon(settings, horizon_label)
    seed_paths = {
        "seed_appln_ids": seed_dir / "seed_appln_ids.parquet",
        "seed_family_ids": seed_dir / "seed_family_ids.parquet",
        "seed_publn_ids": seed_dir / "seed_publn_ids.parquet",
        "seed_person_ids": seed_dir / "seed_person_ids.parquet",
        "seed_ep_appln_ids": seed_dir / "seed_ep_appln_ids.parquet",
        "seed_us_publication_numbers": seed_dir / "seed_us_publication_numbers.parquet",
        "seed_ep_publication_numbers": seed_dir / "seed_ep_publication_numbers.parquet",
        "seed_family_field_counts": seed_dir / "seed_family_field_counts.parquet",
    }
    if seed_keys is None:
        return seed_paths
    return {key: path for key, path in seed_paths.items() if key in seed_keys}


def _global_seed_keys_for_chunk_plan(chunks: list[dict[str, Any]]) -> set[str]:
    """Return the seed keys that must be materialized before chunk execution starts."""
    planned_families = {str(chunk["table_family"]) for chunk in chunks}
    required = set(CHUNK_MINIMAL_SEED_KEYS)
    if "publications" not in planned_families:
        required.update({"seed_publn_ids", "seed_us_publication_numbers", "seed_ep_publication_numbers"})
    if "core" not in planned_families:
        required.add("seed_person_ids")
    return required


def _chunk_seed_sidecar_queries(chunk_path: Path, family_name: str) -> dict[str, str]:
    """Return canonical chunk-derived seed queries keyed by target seed name."""
    quoted_path = _quote_duckdb_path(chunk_path)
    if family_name == "publications":
        base_query = (
            "select distinct "
            "pat_publn_id, "
            "appln_id, "
            "publn_auth, "
            "publn_nr as publication_number, "
            "publn_kind as publication_kind, "
            "publn_date as publication_date, "
            "coalesce(cast(publn_auth as varchar), '') || "
            "coalesce(cast(publn_nr as varchar), '') || "
            "coalesce(cast(publn_kind as varchar), '') as publication_number_full "
            f"from read_parquet('{quoted_path}') "
            "where pat_publn_id is not null"
        )
        return {
            "seed_publn_ids": base_query,
            "seed_ep_publication_numbers": f"{base_query} and publn_auth = 'EP'",
            "seed_us_publication_numbers": f"{base_query} and publn_auth = 'US'",
        }
    if family_name == "core":
        return {
            "seed_person_ids": (
                "select distinct person_id "
                f"from read_parquet('{quoted_path}') "
                "where person_id is not null"
            )
        }
    return {}


def _family_seed_keys(family_name: str) -> set[str]:
    """Return the chunk-derived seed keys produced by one chunk family."""
    if family_name == "publications":
        return {
            "seed_publn_ids",
            "seed_us_publication_numbers",
            "seed_ep_publication_numbers",
        }
    if family_name == "core":
        return {"seed_person_ids"}
    return set()


def _chunk_seed_sidecars_exist(settings: BuildSettings, horizon_label: str, chunk_id: str, family_name: str) -> bool:
    """Return whether all expected chunk-derived sidecars already exist for one chunk."""
    seed_keys = _family_seed_keys(family_name)
    if not seed_keys:
        return False
    return all((_chunk_seed_sidecar_dir(settings, horizon_label, seed_key) / f"{chunk_id}.parquet").exists() for seed_key in seed_keys)


def _expected_chunk_source_name(family_name: str) -> str | None:
    """Return the expected primary parquet file name for one family's seed derivation."""
    if family_name == "publications":
        return f"{PATSTAT_TABLES['bronze_patstat_pat_publn'][0]}.parquet"
    if family_name == "core":
        return f"{PATSTAT_TABLES['bronze_patstat_pers_appln'][0]}.parquet"
    return None


def _derive_chunk_seed_sidecars_from_outputs(
    settings: BuildSettings,
    horizon_label: str,
    chunk_id: str,
    family_name: str,
    local_outputs: list[Path],
    *,
    overwrite: bool,
) -> dict[str, Path]:
    """Materialize any chunk-derived seed sidecars for one successful chunk."""
    target_files = {
        "publications": f"{PATSTAT_TABLES['bronze_patstat_pat_publn'][0]}.parquet",
        "core": f"{PATSTAT_TABLES['bronze_patstat_pers_appln'][0]}.parquet",
    }
    target_name = target_files.get(family_name)
    if target_name is None:
        return {}
    source_path = next((path for path in local_outputs if path.name == target_name and path.exists()), None)
    if source_path is None:
        return {}

    created: dict[str, Path] = {}
    for seed_key, query in _chunk_seed_sidecar_queries(source_path, family_name).items():
        sidecar_path = _chunk_seed_sidecar_dir(settings, horizon_label, seed_key) / f"{chunk_id}.parquet"
        if sidecar_path.exists() and not overwrite:
            created[seed_key] = sidecar_path
            continue
        _copy_duckdb_query_to_parquet(query, sidecar_path)
        created[seed_key] = sidecar_path
    return created


def _bootstrap_chunk_seed_sidecars(
    settings: BuildSettings,
    horizon_label: str,
    *,
    logger: logging.Logger,
    emit_event,
) -> dict[str, Path]:
    """Backfill missing chunk-derived seed sidecars from successful manifests whose local outputs still exist."""
    import json

    created: dict[str, Path] = {}
    for manifest_path in sorted((settings.manifests_dir / "chunks").glob("*.json")):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if payload.get("status") != "success":
            continue
        chunk_id = str(payload.get("chunk_id", ""))
        family_name = str(payload.get("table_family", ""))
        if not chunk_id or family_name not in {"publications", "core"}:
            continue
        local_outputs = [Path(path) for path in payload.get("local_outputs", [])]
        sidecars = _derive_chunk_seed_sidecars_from_outputs(
            settings,
            horizon_label,
            chunk_id,
            family_name,
            local_outputs,
            overwrite=False,
        )
        if not sidecars:
            continue
        logger.info(
            "Bootstrapped chunk-derived seeds chunk_id=%s family=%s seed_count=%s",
            chunk_id,
            family_name,
            len(sidecars),
        )
        emit_event(
            "chunk_seed_sidecars_bootstrapped",
            chunk_id=chunk_id,
            table_family=family_name,
            seed_keys=sorted(sidecars.keys()),
        )
        created.update(sidecars)
    return created


def _consolidate_chunk_derived_seeds(
    settings: BuildSettings,
    *,
    horizon_label: str,
    canonical_seed_paths: dict[str, Path],
    required_seed_keys: set[str] | None = None,
    overwrite_existing: bool = False,
    container,
    upload_options: dict[str, int],
    logger: logging.Logger,
    emit_event,
) -> dict[str, Path]:
    """Build canonical derived seed parquet files from chunk sidecars without loading the full universe into pandas."""
    effective_keys = set(required_seed_keys or CHUNK_DERIVED_SEED_KEYS)
    derived_seed_paths = {key: canonical_seed_paths[key] for key in effective_keys if key in canonical_seed_paths}
    existing = {key: path for key, path in derived_seed_paths.items() if path.exists()}
    if len(existing) == len(derived_seed_paths):
        if not overwrite_existing:
            emit_event("derived_seeds_reused", horizon_label=horizon_label, seed_dir=str(_seed_dir_for_horizon(settings, horizon_label)))
            if container is not None:
                _upload_paths(
                    container,
                    list(existing.values()),
                    _seed_blob_prefix(horizon_label),
                    upload_options,
                    logger=logger,
                    emit_event=emit_event,
                    chunk_id=f"{horizon_label}-derived-seeds",
                )
            return derived_seed_paths
        emit_event(
            "derived_seeds_rebuild_requested",
            horizon_label=horizon_label,
            seed_dir=str(_seed_dir_for_horizon(settings, horizon_label)),
        )

    _bootstrap_chunk_seed_sidecars(settings, horizon_label, logger=logger, emit_event=emit_event)

    consolidated: dict[str, Path] = {}
    for seed_key, out_path in derived_seed_paths.items():
        if out_path.exists() and not overwrite_existing:
            consolidated[seed_key] = out_path
            continue
        sidecar_dir = _chunk_seed_sidecar_dir(settings, horizon_label, seed_key)
        sidecar_paths = sorted(sidecar_dir.glob("*.parquet"))
        if not sidecar_paths:
            raise RuntimeError(
                f"Chunk-derived seed consolidation could not build `{seed_key}` because no sidecars were available in `{sidecar_dir}`."
            )
        out_path.unlink(missing_ok=True)
        quoted_inputs = ", ".join(f"'{_quote_duckdb_path(path)}'" for path in sidecar_paths)
        _copy_duckdb_query_to_parquet(f"select distinct * from read_parquet([{quoted_inputs}])", out_path)
        consolidated[seed_key] = out_path
        logger.info(
            "Consolidated derived seed seed_key=%s sidecar_count=%s output=%s",
            seed_key,
            len(sidecar_paths),
            out_path,
        )
        emit_event(
            "derived_seed_consolidated",
            horizon_label=horizon_label,
            seed_key=seed_key,
            sidecar_count=len(sidecar_paths),
            output=str(out_path),
        )

    if container is not None and consolidated:
        _upload_paths(
            container,
            list(consolidated.values()),
            _seed_blob_prefix(horizon_label),
            upload_options,
            logger=logger,
            emit_event=emit_event,
            chunk_id=f"{horizon_label}-derived-seeds",
        )
    return derived_seed_paths


def _materialize_global_tip_seeds(
    settings: BuildSettings,
    working_settings: BuildSettings,
    *,
    horizon_label: str,
    required_seed_keys: set[str],
    container,
    upload_options: dict[str, int],
    logger: logging.Logger,
    emit_event,
) -> dict[str, Path]:
    """Ensure the global TIP seed parquet set exists for the active horizon and upload it when Blob is enabled."""
    seed_paths = _required_seed_paths(settings, horizon_label, seed_keys=required_seed_keys)
    existing = {key: path for key, path in seed_paths.items() if path.exists()}
    if len(existing) == len(seed_paths):
        logger.info("Reusing existing global seeds horizon=%s seed_dir=%s", horizon_label, _seed_dir_for_horizon(settings, horizon_label))
        emit_event("global_seeds_reused", horizon_label=horizon_label, seed_dir=str(_seed_dir_for_horizon(settings, horizon_label)))
        if container is not None:
            _upload_paths(
                container,
                list(seed_paths.values()),
                _seed_blob_prefix(horizon_label),
                upload_options,
                logger=logger,
                emit_event=emit_event,
                chunk_id=f"{horizon_label}-seeds",
            )
        return seed_paths

    seed_result = StageResult(
        stage=f"{'heritage-' if horizon_label == 'heritage' else ''}tip-global-seed-materialization",
        status="success",
        summary="Materialized the global TIP seed parquet set required by chunked pre-Bronze execution.",
    )
    logger.info("Materializing global seeds horizon=%s seed_dir=%s", horizon_label, _seed_dir_for_horizon(settings, horizon_label))
    emit_event(
        "global_seeds_started",
        horizon_label=horizon_label,
        seed_dir=str(_seed_dir_for_horizon(settings, horizon_label)),
        seed_keys=sorted(required_seed_keys),
    )
    seeds = _seed_patstat_scope_tip(
        working_settings,
        seed_result,
        seed_dir=_seed_dir_for_horizon(settings, horizon_label),
        requested_seed_keys=required_seed_keys,
    )
    if seed_result.status == "failed" or not seeds:
        raise RuntimeError("Global TIP seed materialization failed before chunk execution could start.")
    if container is not None:
        _upload_paths(
            container,
            [Path(path) for path in seed_result.outputs],
            _seed_blob_prefix(horizon_label),
            upload_options,
            logger=logger,
            emit_event=emit_event,
            chunk_id=f"{horizon_label}-seeds",
        )
    emit_event(
        "global_seeds_finished",
        horizon_label=horizon_label,
        seed_output_count=len(seed_result.outputs),
        seed_metrics=seed_result.metrics,
    )
    return {key: Path(value) for key, value in seeds.items()}


def _execute_chunk_export(
    settings: BuildSettings,
    working_settings: BuildSettings,
    chunk: dict[str, Any],
    *,
    horizon_label: str,
    container,
    upload_options: dict[str, int],
    uspto_enabled: bool,
    logger: logging.Logger,
    emit_event,
) -> dict[str, Any]:
    """Execute one chunk, emit live logs, and return manifest payload fields."""
    chunk_id = str(chunk["chunk_id"])
    family = str(chunk["table_family"])
    temp_dir = _chunk_temp_dir(settings, chunk_id)
    ensure_dir(temp_dir)
    local_outputs: list[Path] = []
    uploaded_blobs: list[str] = []
    chunk_metrics: dict[str, Any] = {}
    chunk_warnings: list[str] = []
    derived_seed_sidecars: list[Path] = []
    status = "success"
    scope = None
    started_at = utc_now_iso()
    started_clock = perf_counter()
    logger.info(
        "Chunk started chunk_id=%s field=%s year_start=%s year_end=%s family=%s",
        chunk_id,
        chunk["field_slug"],
        chunk["year_start"],
        chunk["year_end"],
        family,
    )
    emit_event(
        "chunk_started",
        chunk_id=chunk_id,
        field=str(chunk["field"]),
        field_slug=str(chunk["field_slug"]),
        year_start=int(chunk["year_start"]),
        year_end=int(chunk["year_end"]),
        table_family=family,
    )
    try:
        scope = _chunk_scope_tip(working_settings, str(chunk["field"]), int(chunk["year_start"]), int(chunk["year_end"]))
        chunk_metrics.update(scope["counts"])
        logger.info(
            "Chunk scope ready chunk_id=%s appln_count=%s family_count=%s publn_count=%s",
            chunk_id,
            chunk_metrics.get("appln_count", 0),
            chunk_metrics.get("family_count", 0),
            chunk_metrics.get("publn_count", 0),
        )
        emit_event("chunk_scope_ready", chunk_id=chunk_id, counts=scope["counts"])

        if family in PATSTAT_FAMILY_TABLES:
            logger.info("Extracting PATSTAT family chunk_id=%s family=%s", chunk_id, family)
            emit_event("chunk_extraction_started", chunk_id=chunk_id, source_family="patstat", table_family=family)
            local_outputs.extend(_extract_patstat_family(scope, family, temp_dir / "patstat"))
            if family == "publications" and uspto_enabled:
                uspto_outputs, uspto_metrics, uspto_warnings = _extract_uspto_family(working_settings, scope, temp_dir / "uspto")
                local_outputs.extend(uspto_outputs)
                chunk_metrics.update(uspto_metrics)
                chunk_warnings.extend(uspto_warnings)
                if uspto_warnings:
                    status = "degraded"
            emit_event(
                "chunk_extraction_finished",
                chunk_id=chunk_id,
                source_family="patstat",
                table_family=family,
                output_file_count=len(local_outputs),
            )
        elif family == "register":
            logger.info("Extracting Register family chunk_id=%s", chunk_id)
            emit_event("chunk_extraction_started", chunk_id=chunk_id, source_family="register", table_family=family)
            local_outputs.extend(_extract_register_family(scope, temp_dir / "register"))
            emit_event("chunk_extraction_finished", chunk_id=chunk_id, source_family="register", table_family=family, output_file_count=len(local_outputs))
        elif family == "epab":
            logger.info("Extracting EPAB family chunk_id=%s", chunk_id)
            emit_event("chunk_extraction_started", chunk_id=chunk_id, source_family="epab", table_family=family)
            local_outputs.extend(_extract_epab_family(working_settings, scope, temp_dir / "epab"))
            emit_event("chunk_extraction_finished", chunk_id=chunk_id, source_family="epab", table_family=family, output_file_count=len(local_outputs))
        else:
            chunk_warnings.append(f"Unsupported chunk family `{family}` was skipped.")
            status = "degraded"

        local_output_bytes = sum(path.stat().st_size for path in local_outputs if path.exists())
        chunk_metrics["local_output_file_count"] = len(local_outputs)
        chunk_metrics["local_output_bytes"] = local_output_bytes
        logger.info(
            "Chunk local outputs ready chunk_id=%s files=%s bytes=%s",
            chunk_id,
            len(local_outputs),
            local_output_bytes,
        )
        emit_event(
            "chunk_local_outputs_ready",
            chunk_id=chunk_id,
            file_count=len(local_outputs),
            size_bytes=local_output_bytes,
        )

        sidecars = _derive_chunk_seed_sidecars_from_outputs(
            settings,
            horizon_label,
            chunk_id,
            family,
            local_outputs,
            overwrite=True,
        )
        if sidecars:
            derived_seed_sidecars.extend(sidecars.values())
            chunk_metrics["derived_seed_sidecar_count"] = len(sidecars)
            logger.info(
                "Chunk-derived seeds ready chunk_id=%s seed_keys=%s",
                chunk_id,
                sorted(sidecars.keys()),
            )
            emit_event(
                "chunk_seed_sidecars_ready",
                chunk_id=chunk_id,
                table_family=family,
                seed_keys=sorted(sidecars.keys()),
            )

        if container is not None and local_outputs and (settings.execution or {}).get("upload_after_chunk", True):
            standard_outputs = [path for path in local_outputs if path.parent.name != "uspto"]
            uspto_outputs = [path for path in local_outputs if path.parent.name == "uspto"]
            logger.info(
                "Uploading chunk outputs chunk_id=%s file_count=%s prefix=%s",
                chunk_id,
                len(local_outputs),
                chunk["blob_prefix"],
            )
            emit_event(
                "chunk_upload_started",
                chunk_id=chunk_id,
                file_count=len(local_outputs),
                blob_prefix=str(chunk["blob_prefix"]),
            )
            if standard_outputs:
                uploaded_blobs.extend(
                    _upload_paths(
                        container,
                        standard_outputs,
                        str(chunk["blob_prefix"]),
                        upload_options,
                        logger=logger,
                        emit_event=emit_event,
                        chunk_id=chunk_id,
                    )
                )
            if uspto_outputs:
                root_prefix = "raw-bounded-heritage" if horizon_label == "heritage" else "raw-bounded"
                uspto_blob_prefix = (
                    f"{root_prefix}/uspto/field={chunk['field_slug']}/"
                    f"year={chunk['year_start']}-{chunk['year_end']}/family={chunk['table_family']}"
                )
                uploaded_blobs.extend(
                    _upload_paths(
                        container,
                        uspto_outputs,
                        uspto_blob_prefix,
                        upload_options,
                        logger=logger,
                        emit_event=emit_event,
                        chunk_id=chunk_id,
                    )
                )
            emit_event(
                "chunk_upload_finished",
                chunk_id=chunk_id,
                uploaded_blob_count=len(uploaded_blobs),
            )

        if (settings.execution or {}).get("cleanup_after_upload", False) and (
            container is not None or not (settings.execution or {}).get("blob_intermediate_enabled", False)
        ):
            logger.info("Cleaning local chunk temp dir chunk_id=%s path=%s", chunk_id, temp_dir)
            emit_event("chunk_cleanup_started", chunk_id=chunk_id, temp_dir=str(temp_dir))
            shutil.rmtree(temp_dir, ignore_errors=True)
            emit_event("chunk_cleanup_finished", chunk_id=chunk_id, temp_dir=str(temp_dir))
    except Exception as exc:
        status = "failed"
        chunk_warnings.append(str(exc))
        logger.exception("Chunk failed chunk_id=%s", chunk_id)
        emit_event("chunk_failed", chunk_id=chunk_id, error=str(exc))
    finally:
        if scope is not None:
            close_tip_client(scope.get("patstat"))

    finished_at = utc_now_iso()
    duration_seconds = round(perf_counter() - started_clock, 3)
    logger.info(
        "Chunk finished chunk_id=%s status=%s duration_seconds=%s uploaded_blob_count=%s",
        chunk_id,
        status,
        duration_seconds,
        len(uploaded_blobs),
    )
    emit_event(
        "chunk_finished",
        chunk_id=chunk_id,
        status=status,
        duration_seconds=duration_seconds,
        uploaded_blob_count=len(uploaded_blobs),
        warning_count=len(chunk_warnings),
    )
    return {
        "chunk": chunk,
        "status": status,
        "local_outputs": local_outputs,
        "uploaded_blobs": uploaded_blobs,
        "derived_seed_sidecars": derived_seed_sidecars,
        "metrics": chunk_metrics,
        "warnings": chunk_warnings,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
    }


def recover_tip_blob_uploads(settings: BuildSettings) -> StageResult:
    """Upload preserved local chunk outputs for manifests that failed or completed before Blob offload finished."""
    stage_name = "tip-blob-recovery"
    result = StageResult(
        stage=stage_name,
        status="success",
        summary="Recovered Blob uploads for TIP chunk manifests whose local outputs remained on disk after missing or failed Blob offload.",
        methods=[
            "Scanned chunk manifests for successful or upload-failed chunks with missing or incomplete Blob upload metadata.",
            "Uploaded any still-present local outputs to the deterministic chunk Blob prefixes.",
            "Updated manifests with recovered uploaded_blobs entries, restored upload-failed chunks to success when appropriate, and cleaned local temp directories when configured.",
        ],
        calculations=[
            "Recovery eligibility requires still-present local outputs plus either a successful manifest with incomplete uploaded_blobs or a failed manifest whose warnings indicate Blob/upload timeout behavior.",
            "Recovered Blob prefixes reuse the same deterministic field/year/table-family layout as the normal chunk executor.",
        ],
        downstream_impacts=[
            "This stage repairs interrupted or misconfigured Blob offload without rerunning expensive TIP extraction work.",
            "Recovered chunk manifests become consistent with later non-TIP consolidation expectations.",
        ],
        doc_refs=[
            "docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )
    execution = settings.execution or {}
    stage_logger = configure_logger(stage_name, settings.manifests_dir / "stages" / f"{stage_name}.log")
    event_log_path = _stage_event_log_path(settings, stage_name)
    event_log_path.unlink(missing_ok=True)
    result.artifacts["live_event_log"] = str(event_log_path)
    event_lock = Lock()

    def emit_event(event_name: str, **payload: Any) -> None:
        if not execution.get("realtime_chunk_logging", True):
            return
        record = {"at": utc_now_iso(), "stage": stage_name, "event": event_name}
        record.update(payload)
        with event_lock:
            append_jsonl(event_log_path, record)

    emit_event("stage_started")
    upload_options = _upload_options(settings)
    result.metrics["recovery_upload_max_concurrency"] = upload_options["max_concurrency"]
    result.metrics["recovery_upload_max_block_size_mb"] = upload_options["max_block_size"] // (1024 * 1024)
    result.metrics["recovery_upload_max_single_put_size_mb"] = upload_options["max_single_put_size"] // (1024 * 1024)

    try:
        container = _get_container_client(settings)
    except Exception as exc:
        result.status = "failed"
        result.warnings.append(str(exc))
        stage_logger.warning("Blob recovery unavailable: %s", exc)
        emit_event("blob_container_unavailable", error=str(exc))
        emit_event("stage_finished", status=result.status)
        return result

    emit_event("blob_container_ready", container=str(settings.azure["container"]))
    chunk_manifest_dir = settings.manifests_dir / "chunks"
    manifest_paths = sorted(chunk_manifest_dir.glob("*.json"))
    result.metrics["recovery_manifest_count"] = len(manifest_paths)

    recoverable_count = 0
    recovered_count = 0
    skipped_uploaded_count = 0
    missing_output_count = 0
    ineligible_failed_count = 0
    uploaded_blob_count = 0

    import json

    for manifest_path in manifest_paths:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        status = str(payload.get("status", ""))
        uploaded_blobs = list(payload.get("uploaded_blobs", []) or [])
        local_outputs = [Path(path) for path in payload.get("local_outputs", [])]
        warnings = list(payload.get("warnings", []) or [])
        if uploaded_blobs and len(uploaded_blobs) >= len(local_outputs):
            skipped_uploaded_count += 1
            continue
        if not _recovery_candidate(
            status=status,
            local_outputs=local_outputs,
            uploaded_blobs=uploaded_blobs,
            warnings=warnings,
        ):
            if status == "failed" and local_outputs:
                ineligible_failed_count += 1
            continue
        recoverable_count += 1
        existing_outputs = [path for path in local_outputs if path.exists() and path.is_file()]
        if not existing_outputs:
            missing_output_count += 1
            result.warnings.append(f"Skipped Blob recovery for `{payload.get('chunk_id')}` because no local outputs remain.")
            emit_event("chunk_recovery_skipped", chunk_id=str(payload.get("chunk_id")), reason="missing_local_outputs")
            continue

        chunk = {
            "chunk_id": payload["chunk_id"],
            "field": payload["field"],
            "field_slug": slugify_value(str(payload["field"])),
            "year_start": payload["year_start"],
            "year_end": payload["year_end"],
            "table_family": payload["table_family"],
        }
        horizon_label = _manifest_horizon_label(payload)
        blob_prefix = _chunk_blob_prefix(chunk, horizon_label=horizon_label)
        standard_outputs = [path for path in existing_outputs if path.parent.name != "uspto"]
        uspto_outputs = [path for path in existing_outputs if path.parent.name == "uspto"]
        recovered_blobs: list[str] = []

        stage_logger.info(
            "Recovering chunk upload chunk_id=%s file_count=%s horizon=%s",
            chunk["chunk_id"],
            len(existing_outputs),
            horizon_label,
        )
        emit_event(
            "chunk_recovery_started",
            chunk_id=chunk["chunk_id"],
            file_count=len(existing_outputs),
            horizon_label=horizon_label,
        )
        if standard_outputs:
            recovered_blobs.extend(
                _upload_paths(
                    container,
                    standard_outputs,
                    blob_prefix,
                    upload_options,
                    logger=stage_logger,
                    emit_event=emit_event,
                    chunk_id=str(chunk["chunk_id"]),
                )
            )
        if uspto_outputs:
            root_prefix = "raw-bounded-heritage" if horizon_label == "heritage" else "raw-bounded"
            uspto_blob_prefix = (
                f"{root_prefix}/uspto/field={chunk['field_slug']}/"
                f"year={chunk['year_start']}-{chunk['year_end']}/family={chunk['table_family']}"
            )
            recovered_blobs.extend(
                _upload_paths(
                    container,
                    uspto_outputs,
                    uspto_blob_prefix,
                    upload_options,
                    logger=stage_logger,
                    emit_event=emit_event,
                    chunk_id=str(chunk["chunk_id"]),
                )
            )

        payload["uploaded_blobs"] = recovered_blobs
        payload["recovered_at"] = utc_now_iso()
        if status != "success":
            payload["recovered_from_status"] = status
            payload["status"] = "success"
        write_text_json(manifest_path, payload)
        result.outputs.append(str(manifest_path))
        recovered_count += 1
        uploaded_blob_count += len(recovered_blobs)
        emit_event(
            "chunk_recovery_finished",
            chunk_id=chunk["chunk_id"],
            uploaded_blob_count=len(recovered_blobs),
        )

        if execution.get("cleanup_after_upload", False):
            temp_dir = _chunk_temp_dir(settings, str(chunk["chunk_id"]))
            shutil.rmtree(temp_dir, ignore_errors=True)
            emit_event("chunk_cleanup_finished", chunk_id=chunk["chunk_id"], temp_dir=str(temp_dir))

    result.metrics["recovery_recoverable_chunk_count"] = recoverable_count
    result.metrics["recovery_recovered_chunk_count"] = recovered_count
    result.metrics["recovery_skipped_uploaded_chunk_count"] = skipped_uploaded_count
    result.metrics["recovery_missing_output_chunk_count"] = missing_output_count
    result.metrics["recovery_ineligible_failed_chunk_count"] = ineligible_failed_count
    result.metrics["recovery_uploaded_blob_count"] = uploaded_blob_count
    emit_event(
        "stage_finished",
        status=result.status,
        recoverable_chunk_count=recoverable_count,
        recovered_chunk_count=recovered_count,
        uploaded_blob_count=uploaded_blob_count,
    )
    return result


def backfill_tip_derived_seeds(settings: BuildSettings) -> StageResult:
    """Rebuild derived seed parquet files from successful chunk outputs available locally or in Blob."""
    stage_name = "tip-derived-seed-backfill"
    result = StageResult(
        stage=stage_name,
        status="success",
        summary="Backfilled canonical derived TIP seed parquet files from successful chunk outputs already present locally, already uploaded to Blob, or previously materialized as chunk-derived sidecars.",
        methods=[
            "Scanned successful chunk manifests for `core` and `publications` families.",
            "Reused existing chunk-derived seed sidecars when present, otherwise derived them from local chunk parquet or downloaded Blob chunk parquet.",
            "Consolidated all reachable chunk-derived sidecars into canonical seed parquet outputs for publication and person seeds.",
        ],
        calculations=[
            "Local successful chunk outputs take precedence over Blob fallback because they avoid redundant transfer and preserve the exact local extraction result.",
            "Canonical derived seed outputs are rebuilt via DuckDB `select distinct *` across per-chunk sidecars to avoid full-universe pandas materialization on TIP.",
        ],
        downstream_impacts=[
            "This stage repairs mixed historical TIP states where some successful chunks were already cleaned after Blob upload while others remain only locally.",
            "Rebuilt canonical seed files support later USPTO/local follow-on stages without forcing expensive chunk reruns.",
        ],
        doc_refs=[
            "docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )
    execution = settings.execution or {}
    stage_logger = configure_logger(stage_name, settings.manifests_dir / "stages" / f"{stage_name}.log")
    event_log_path = _stage_event_log_path(settings, stage_name)
    event_log_path.unlink(missing_ok=True)
    result.artifacts["live_event_log"] = str(event_log_path)
    event_lock = Lock()

    def emit_event(event_name: str, **payload: Any) -> None:
        if not execution.get("realtime_chunk_logging", True):
            return
        record = {"at": utc_now_iso(), "stage": stage_name, "event": event_name}
        record.update(payload)
        with event_lock:
            append_jsonl(event_log_path, record)

    emit_event("stage_started")
    transfer_options = _upload_options(settings)
    result.metrics["seed_backfill_transfer_max_concurrency"] = transfer_options["max_concurrency"]
    result.metrics["seed_backfill_transfer_max_block_size_mb"] = transfer_options["max_block_size"] // (1024 * 1024)
    result.metrics["seed_backfill_transfer_max_single_put_size_mb"] = transfer_options["max_single_put_size"] // (1024 * 1024)

    import json

    manifest_paths = sorted((settings.manifests_dir / "chunks").glob("*.json"))
    result.metrics["seed_backfill_manifest_count"] = len(manifest_paths)

    needs_blob_fallback = False
    candidates: list[dict[str, Any]] = []
    for manifest_path in manifest_paths:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if payload.get("status") != "success":
            continue
        family_name = str(payload.get("table_family", ""))
        if family_name not in {"publications", "core"}:
            continue
        chunk_id = str(payload.get("chunk_id", ""))
        if not chunk_id:
            continue
        horizon_label = _manifest_horizon_label(payload)
        local_outputs = [Path(path) for path in payload.get("local_outputs", [])]
        expected_name = _expected_chunk_source_name(family_name)
        has_local = expected_name is not None and any(path.exists() and path.name == expected_name for path in local_outputs)
        if not has_local and payload.get("uploaded_blobs"):
            needs_blob_fallback = True
        candidates.append(
            {
                "payload": payload,
                "family_name": family_name,
                "chunk_id": chunk_id,
                "horizon_label": horizon_label,
                "local_outputs": local_outputs,
            }
        )

    container = None
    if needs_blob_fallback:
        try:
            container = _get_container_client(settings)
        except Exception as exc:
            result.status = "failed"
            result.warnings.append(str(exc))
            stage_logger.warning("Derived seed backfill could not access Blob fallback: %s", exc)
            emit_event("blob_container_unavailable", error=str(exc))
            emit_event("stage_finished", status=result.status)
            return result
        emit_event("blob_container_ready", container=str(settings.azure["container"]))

    local_source_count = 0
    blob_source_count = 0
    existing_sidecar_chunk_count = 0
    missing_source_count = 0
    staged_download_count = 0
    sidecar_write_count = 0
    affected_horizons: set[str] = set()
    required_seed_keys_by_horizon: dict[str, set[str]] = {}
    download_root = settings.repo_root / "etl" / "data" / "temp" / "seed-backfill"
    shutil.rmtree(download_root, ignore_errors=True)

    for item in candidates:
        payload = item["payload"]
        family_name = item["family_name"]
        chunk_id = item["chunk_id"]
        horizon_label = item["horizon_label"]
        local_outputs = item["local_outputs"]
        affected_horizons.add(horizon_label)
        required_seed_keys_by_horizon.setdefault(horizon_label, set()).update(_family_seed_keys(family_name))

        if _chunk_seed_sidecars_exist(settings, horizon_label, chunk_id, family_name):
            existing_sidecar_chunk_count += 1
            emit_event("chunk_seed_sidecars_reused", chunk_id=chunk_id, table_family=family_name)
            continue

        expected_name = _expected_chunk_source_name(family_name)
        source_path = next((path for path in local_outputs if path.exists() and path.name == expected_name), None)
        cleanup_download = False
        source_mode = None
        if source_path is not None:
            local_source_count += 1
            source_mode = "local"
        else:
            uploaded_blobs = list(payload.get("uploaded_blobs", []) or [])
            target_blob = next((blob for blob in uploaded_blobs if Path(blob).name == expected_name), None)
            if target_blob and container is not None:
                download_path = download_root / horizon_label / chunk_id / expected_name
                source_path = _download_blob_to_path(
                    container,
                    target_blob,
                    download_path,
                    transfer_options,
                    logger=stage_logger,
                    emit_event=emit_event,
                    chunk_id=chunk_id,
                )
                cleanup_download = True
                blob_source_count += 1
                staged_download_count += 1
                source_mode = "blob"

        if source_path is None:
            missing_source_count += 1
            result.warnings.append(
                f"Could not backfill derived seeds for `{chunk_id}` because neither local outputs nor an uploaded blob source were available."
            )
            emit_event("chunk_seed_backfill_missing_source", chunk_id=chunk_id, table_family=family_name)
            continue

        sidecars = _derive_chunk_seed_sidecars_from_outputs(
            settings,
            horizon_label,
            chunk_id,
            family_name,
            [source_path],
            overwrite=True,
        )
        sidecar_write_count += len(sidecars)
        result.outputs.extend(str(path) for path in sidecars.values())
        emit_event(
            "chunk_seed_backfilled",
            chunk_id=chunk_id,
            table_family=family_name,
            source_mode=source_mode,
            seed_keys=sorted(sidecars.keys()),
        )
        if cleanup_download and source_path.exists():
            source_path.unlink(missing_ok=True)

    consolidated_seed_count = 0
    for horizon_label in sorted(affected_horizons or {"main"}):
        canonical_seed_paths = _required_seed_paths(settings, horizon_label)
        derived_seed_paths = _consolidate_chunk_derived_seeds(
            settings,
            horizon_label=horizon_label,
            canonical_seed_paths=canonical_seed_paths,
            required_seed_keys=required_seed_keys_by_horizon.get(horizon_label, set()),
            overwrite_existing=True,
            container=container,
            upload_options=transfer_options,
            logger=stage_logger,
            emit_event=emit_event,
        )
        consolidated_seed_count += len(derived_seed_paths)
        result.outputs.extend(str(path) for path in derived_seed_paths.values())

    shutil.rmtree(download_root, ignore_errors=True)
    result.metrics["seed_backfill_candidate_chunk_count"] = len(candidates)
    result.metrics["seed_backfill_local_source_chunk_count"] = local_source_count
    result.metrics["seed_backfill_blob_source_chunk_count"] = blob_source_count
    result.metrics["seed_backfill_existing_sidecar_chunk_count"] = existing_sidecar_chunk_count
    result.metrics["seed_backfill_missing_source_chunk_count"] = missing_source_count
    result.metrics["seed_backfill_downloaded_blob_count"] = staged_download_count
    result.metrics["seed_backfill_sidecar_file_count"] = sidecar_write_count
    result.metrics["seed_backfill_consolidated_seed_file_count"] = consolidated_seed_count
    if missing_source_count:
        result.status = "failed"
    emit_event(
        "stage_finished",
        status=result.status,
        candidate_chunk_count=len(candidates),
        missing_source_chunk_count=missing_source_count,
        consolidated_seed_file_count=consolidated_seed_count,
    )
    return result


def _run_tip_chunked_export(settings: BuildSettings, *, horizon_label: str) -> StageResult:
    """Execute one named TIP chunked pre-Bronze export flow and optionally upload each chunk to Blob."""
    if horizon_label == "heritage":
        working_settings = replace(
            settings,
            year_window_start=settings.heritage_backfill_start,
            year_window_end=settings.heritage_backfill_end,
        )
        stage_name = "pre-bronze-heritage-chunked-export"
        summary = "Executed chunked TIP heritage-backfill extraction with Blob-first chunk manifests and local cleanup support."
        doc_refs = [
            "docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md",
            "docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
            "docs/data/epo-tip-client-usage.md",
        ]
        plan_result = plan_tip_heritage_chunked_export(settings).finish()
        plan_path = settings.manifests_dir / "chunks" / "tip_heritage_chunk_plan.json"
        refs_blob_prefix = "raw-bounded-heritage/refs"
        uspto_enabled = False
    else:
        working_settings = settings
        stage_name = "pre-bronze-chunked-export"
        summary = "Executed chunked TIP pre-Bronze extraction with Blob-first chunk manifests and local cleanup support."
        doc_refs = [
            "docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
            "docs/data/epo-tip-client-usage.md",
        ]
        plan_result = plan_tip_chunked_export(settings).finish()
        plan_path = settings.manifests_dir / "chunks" / "tip_chunk_plan.json"
        refs_blob_prefix = "raw-bounded/refs"
        uspto_enabled = settings.uspto_source_mode == "local_files"

    result = StageResult(
        stage=stage_name,
        status="success",
        summary=summary,
        methods=[
            "Planned field/year/table-family chunks before extraction.",
            "Built chunk-local bounded scope directly from TIP instead of materializing one monolithic bounded raw layer.",
            "Uploaded chunk artifacts to Azure Blob when configured, then optionally cleaned local chunk temp directories.",
        ],
        calculations=[
            "Chunk ids are deterministic field/year/table-family keys.",
            "Per-chunk scope is bounded by both selected WIPO field and configured year bucket.",
        ],
        downstream_impacts=[
            "Successful chunk manifests allow resumable pre-Bronze extraction across constrained TIP sessions.",
            "Chunk-local Blob prefixes become the authoritative bounded raw intermediate store for later non-TIP Bronze/Silver/Gold consolidation.",
        ],
        doc_refs=doc_refs,
    )

    execution = settings.execution or {}
    stage_logger = configure_logger(stage_name, settings.manifests_dir / "stages" / f"{stage_name}.log")
    event_log_path = _stage_event_log_path(settings, stage_name)
    event_log_path.unlink(missing_ok=True)
    result.artifacts["live_event_log"] = str(event_log_path)
    event_lock = Lock()

    def emit_event(event_name: str, **payload: Any) -> None:
        if not execution.get("realtime_chunk_logging", True):
            return
        record = {"at": utc_now_iso(), "stage": stage_name, "event": event_name}
        record.update(payload)
        with event_lock:
            append_jsonl(event_log_path, record)

    result.outputs.extend(plan_result.outputs)
    import json

    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    chunks: list[dict[str, Any]] = plan_payload["chunks"]
    parallel_limit, family_limits = _scheduler_limits(settings, horizon_label)
    upload_options = _upload_options(settings)
    result.metrics["chunk_scheduler_parallel_limit"] = parallel_limit
    result.metrics["chunk_upload_max_concurrency"] = upload_options["max_concurrency"]
    result.metrics["chunk_upload_max_block_size_mb"] = upload_options["max_block_size"] // (1024 * 1024)
    result.metrics["chunk_upload_max_single_put_size_mb"] = upload_options["max_single_put_size"] // (1024 * 1024)
    stage_logger.info(
        "Starting chunked export stage=%s total_chunks=%s parallel_limit=%s family_limits=%s upload_options=%s",
        stage_name,
        len(chunks),
        parallel_limit,
        family_limits,
        upload_options,
    )
    emit_event(
        "stage_started",
        total_chunks=len(chunks),
        parallel_limit=parallel_limit,
        family_limits=family_limits,
        upload_options=upload_options,
    )
    required_global_seed_keys = _global_seed_keys_for_chunk_plan(chunks)
    container = None
    try:
        container = _get_container_client(settings)
    except Exception as exc:
        if execution.get("blob_intermediate_enabled", False):
            result.status = "degraded"
            result.warnings.append(str(exc))
            stage_logger.warning("Azure intermediate upload unavailable: %s", exc)
            emit_event("blob_container_unavailable", error=str(exc))
    else:
        if container is not None:
            stage_logger.info("Azure Blob intermediate upload enabled container=%s", settings.azure["container"])
            emit_event("blob_container_ready", container=str(settings.azure["container"]))

    seed_paths = _materialize_global_tip_seeds(
        settings,
        working_settings,
        horizon_label=horizon_label,
        required_seed_keys=required_global_seed_keys,
        container=container,
        upload_options=upload_options,
        logger=stage_logger,
        emit_event=emit_event,
    )
    result.outputs.extend(str(path) for path in seed_paths.values())
    result.metrics["global_seed_initial_file_count"] = len(seed_paths)
    result.metrics["global_seed_dir"] = str(_seed_dir_for_horizon(settings, horizon_label))

    # Seed refs once if available.
    if settings.refs_source_mode == "local_files":
        ref_stage = StageResult(stage="refs-copy", status="success", summary="Copied reference inputs for chunked pre-Bronze export.")
        _copy_reference_inputs(working_settings, ref_stage)
        result.inputs.extend(ref_stage.inputs)
        result.outputs.extend(ref_stage.outputs)
        for key, value in ref_stage.metrics.items():
            result.metrics[key] = value
        result.warnings.extend(ref_stage.warnings)
        if container is not None:
            ref_files = [Path(path) for path in ref_stage.outputs if path.endswith(".parquet")]
            stage_logger.info("Uploading reference inputs count=%s prefix=%s", len(ref_files), refs_blob_prefix)
            emit_event("refs_upload_started", file_count=len(ref_files), blob_prefix=refs_blob_prefix)
            uploaded = _upload_paths(
                container,
                ref_files,
                refs_blob_prefix,
                upload_options,
                logger=stage_logger,
                emit_event=emit_event,
                chunk_id="refs",
            )
            result.metrics["refs_uploaded_blob_count"] = len(uploaded)
            emit_event("refs_upload_finished", uploaded_blob_count=len(uploaded))

    total_chunks = 0
    skipped_chunks = 0
    uploaded_files = 0
    failed_chunks = 0
    degraded_chunks = 0
    pending_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        total_chunks += 1
        manifest_path = _chunk_manifest_path(settings, str(chunk["chunk_id"]))
        if _successfully_finished(manifest_path):
            skipped_chunks += 1
            stage_logger.info("Skipping completed chunk chunk_id=%s", chunk["chunk_id"])
            emit_event("chunk_skipped", chunk_id=str(chunk["chunk_id"]), reason="existing_success_manifest")
            continue
        pending_chunks.append(chunk)

    family_active_counts: dict[str, int] = {}
    active_futures: dict[Any, dict[str, Any]] = {}

    def next_schedulable_index() -> int | None:
        for index, pending in enumerate(pending_chunks):
            family = str(pending["table_family"])
            family_limit = family_limits.get(family, 1)
            if family_active_counts.get(family, 0) < family_limit:
                return index
        return None

    with ThreadPoolExecutor(max_workers=parallel_limit, thread_name_prefix="tip-chunk") as executor:
        while pending_chunks or active_futures:
            while pending_chunks and len(active_futures) < parallel_limit:
                next_index = next_schedulable_index()
                if next_index is None:
                    break
                chunk = pending_chunks.pop(next_index)
                family = str(chunk["table_family"])
                family_active_counts[family] = family_active_counts.get(family, 0) + 1
                future = executor.submit(
                    _execute_chunk_export,
                    settings,
                    working_settings,
                    chunk,
                    horizon_label=horizon_label,
                    container=container,
                    upload_options=upload_options,
                    uspto_enabled=uspto_enabled,
                    logger=stage_logger,
                    emit_event=emit_event,
                )
                active_futures[future] = chunk
                stage_logger.info(
                    "Submitted chunk chunk_id=%s family=%s active_total=%s active_family=%s",
                    chunk["chunk_id"],
                    family,
                    len(active_futures),
                    family_active_counts[family],
                )
                emit_event(
                    "chunk_submitted",
                    chunk_id=str(chunk["chunk_id"]),
                    table_family=family,
                    active_total=len(active_futures),
                    active_family=family_active_counts[family],
                )

            if not active_futures:
                break

            done, _ = wait(set(active_futures.keys()), return_when=FIRST_COMPLETED)
            for future in done:
                chunk = active_futures.pop(future)
                family = str(chunk["table_family"])
                family_active_counts[family] = max(family_active_counts.get(family, 1) - 1, 0)
                payload = future.result()
                uploaded_files += len(payload["uploaded_blobs"])
                if payload["status"] == "failed":
                    failed_chunks += 1
                if payload["status"] == "degraded":
                    degraded_chunks += 1
                manifest_path = _write_chunk_manifest(
                    settings,
                    payload["chunk"],
                    status=payload["status"],
                    local_outputs=payload["local_outputs"],
                    uploaded_blobs=payload["uploaded_blobs"],
                    metrics=payload["metrics"],
                    warnings=payload["warnings"],
                    started_at=payload["started_at"],
                    finished_at=payload["finished_at"],
                    duration_seconds=payload["duration_seconds"],
                )
                result.outputs.append(str(manifest_path))
                result.outputs.extend(str(path) for path in payload.get("derived_seed_sidecars", []))

    canonical_seed_paths = _required_seed_paths(settings, horizon_label)
    required_derived_seed_keys = CHUNK_DERIVED_SEED_KEYS.intersection(set(ALL_TIP_SEED_KEYS).difference(required_global_seed_keys))
    try:
        derived_seed_paths = _consolidate_chunk_derived_seeds(
            settings,
            horizon_label=horizon_label,
            canonical_seed_paths=canonical_seed_paths,
            required_seed_keys=required_derived_seed_keys,
            container=container,
            upload_options=upload_options,
            logger=stage_logger,
            emit_event=emit_event,
        )
    except Exception as exc:
        result.status = "failed"
        result.warnings.append(str(exc))
        derived_seed_paths = {}
        stage_logger.exception("Derived seed consolidation failed stage=%s", stage_name)
        emit_event("derived_seed_consolidation_failed", horizon_label=horizon_label, error=str(exc))
    else:
        result.outputs.extend(str(path) for path in derived_seed_paths.values())
    result.metrics["global_seed_file_count"] = len(canonical_seed_paths)
    result.metrics["global_seed_derived_file_count"] = len(derived_seed_paths)

    result.metrics["chunk_total_count"] = total_chunks
    result.metrics["chunk_skipped_count"] = skipped_chunks
    result.metrics["chunk_failed_count"] = failed_chunks
    result.metrics["chunk_degraded_count"] = degraded_chunks
    result.metrics["chunk_uploaded_file_count"] = uploaded_files
    emit_event(
        "stage_finished",
        chunk_total_count=total_chunks,
        chunk_skipped_count=skipped_chunks,
        chunk_failed_count=failed_chunks,
        chunk_degraded_count=degraded_chunks,
        chunk_uploaded_file_count=uploaded_files,
    )
    if failed_chunks:
        result.status = "failed"
    elif degraded_chunks or result.status == "degraded":
        result.status = "degraded"
    return result


def run_tip_chunked_export(settings: BuildSettings) -> StageResult:
    """Execute the main TIP chunked pre-Bronze export flow."""
    return _run_tip_chunked_export(settings, horizon_label="main")


def run_tip_heritage_chunked_export(settings: BuildSettings) -> StageResult:
    """Execute the heritage-backfill TIP chunked pre-Bronze export flow."""
    return _run_tip_chunked_export(settings, horizon_label="heritage")
