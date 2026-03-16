from __future__ import annotations

from dataclasses import replace
import os
import shutil
from pathlib import Path
from typing import Any

from patentiq_etl.bronze.ingest_uspto_fulltext import extract_publication_numbers, filter_bulk_xml_to_publications
from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REGISTER_TABLES
from patentiq_etl.common.io import ensure_dir, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.extract import _copy_reference_inputs
from patentiq_etl.prebronze.plan import plan_tip_chunked_export, plan_tip_heritage_chunked_export
from patentiq_etl.prebronze.tip_clients import (
    close_tip_client,
    get_patstat_client,
    get_patstat_database_module,
    query_to_dataframe,
    resolve_patstat_model,
    resolve_register_model,
    result_to_dataframe,
    get_epab_client,
    slugify_value,
    write_dataframe_parquet,
)


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


def _chunk_manifest_path(settings: BuildSettings, chunk_id: str) -> Path:
    """Return the per-chunk manifest path."""
    return settings.manifests_dir / "chunks" / f"{chunk_id}.json"


def _chunk_temp_dir(settings: BuildSettings, chunk_id: str) -> Path:
    """Return the local temporary directory for one chunk."""
    return settings.repo_root / "etl" / "data" / "temp" / "chunks" / chunk_id


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

    service = BlobServiceClient.from_connection_string(connection_string)
    return service.get_container_client(settings.azure["container"])


def _upload_paths(container, files: list[Path], blob_prefix: str) -> list[str]:
    """Upload files to one blob prefix and return blob names."""
    uploaded: list[str] = []
    if container is None:
        return uploaded
    prefix = blob_prefix.rstrip("/")
    for path in files:
        if not path.is_file():
            continue
        blob_name = f"{prefix}/{path.name}"
        with path.open("rb") as handle:
            container.upload_blob(blob_name, handle, overwrite=True)
        uploaded.append(blob_name)
    return uploaded


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
            npl_ids = con.execute(
                "select distinct npl_publn_id from read_parquet(?) where npl_publn_id is not null",
                [str(citation_path)],
            ).df()
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
    import pandas as pd

    outputs: list[Path] = []
    seed_df = scope["ep_publn_df"]
    if seed_df.empty:
        return outputs
    epab = None
    try:
        epab = get_epab_client(settings.tip_env)
        group_frames: dict[str, list[Any]] = {
            "publication": [],
            "application": [],
            "abstract": [],
            "claims": [],
            "pct": [],
            "designated_states": [],
            "priority": [],
            "parent": [],
            "divisional": [],
            "applicant": [],
            "inventor": [],
            "representative": [],
        }
        allowed_pairs = {
            (str(row["publication_number"]), str(row["publication_kind"]))
            for _, row in seed_df.iterrows()
            if row["publication_number"] is not None and row["publication_kind"] is not None
        }
        batch_size = 100
        for start in range(0, len(seed_df.index), batch_size):
            batch = seed_df.iloc[start : start + batch_size]
            numbers = [str(value) for value in batch["publication_number"].dropna().tolist()]
            kinds = sorted({str(value) for value in batch["publication_kind"].dropna().tolist()})
            if not numbers:
                continue
            q = epab.query_publication(number=numbers, kind_code=kinds or None)
            for group in list(group_frames.keys()):
                try:
                    payload = q.get_results(group)
                    group_frames[group].append(result_to_dataframe(payload))
                except Exception:
                    continue
        group_name_map = {
            "publication": "publication",
            "application": "application",
            "abstract": "abstract",
            "claims": "claims",
            "pct": "pct",
            "designated_states": "designated_states",
            "priority": "priority_links",
            "parent": "parent_links",
            "divisional": "divisional_links",
            "applicant": "applicants",
            "inventor": "inventors",
            "representative": "representative",
        }
        for group, frames in group_frames.items():
            if not frames:
                continue
            df = pd.concat(frames, ignore_index=True)
            if group == "publication":
                possible_number = next((col for col in df.columns if col.lower().endswith("publication.number") or col.lower().endswith("number")), None)
                possible_kind = next((col for col in df.columns if col.lower().endswith("publication.kind") or col.lower().endswith("kind")), None)
                if possible_number and possible_kind:
                    df = df[df.apply(lambda row: (str(row[possible_number]), str(row[possible_kind])) in allowed_pairs, axis=1)]
            out_path = ensure_dir(out_dir) / f"epab_{group_name_map[group]}.parquet"
            write_dataframe_parquet(df, out_path)
            outputs.append(out_path)
        return outputs
    finally:
        close_tip_client(epab)


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
        },
    )
    return manifest_path


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
    result.outputs.extend(plan_result.outputs)
    import json

    plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
    chunks: list[dict[str, Any]] = plan_payload["chunks"]
    container = None
    try:
        container = _get_container_client(settings)
    except Exception as exc:
        if execution.get("blob_intermediate_enabled", False):
            result.status = "degraded"
            result.warnings.append(str(exc))

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
            uploaded = _upload_paths(container, ref_files, refs_blob_prefix)
            result.metrics["refs_uploaded_blob_count"] = len(uploaded)

    total_chunks = 0
    skipped_chunks = 0
    uploaded_files = 0
    failed_chunks = 0
    degraded_chunks = 0

    for chunk in chunks:
        total_chunks += 1
        manifest_path = _chunk_manifest_path(settings, chunk["chunk_id"])
        if _successfully_finished(manifest_path):
            skipped_chunks += 1
            continue

        temp_dir = _chunk_temp_dir(settings, chunk["chunk_id"])
        ensure_dir(temp_dir)
        local_outputs: list[Path] = []
        uploaded_blobs: list[str] = []
        chunk_metrics: dict[str, Any] = {}
        chunk_warnings: list[str] = []
        status = "success"
        scope = None
        try:
            scope = _chunk_scope_tip(working_settings, chunk["field"], int(chunk["year_start"]), int(chunk["year_end"]))
            chunk_metrics.update(scope["counts"])
            family = chunk["table_family"]
            if family in PATSTAT_FAMILY_TABLES:
                local_outputs.extend(_extract_patstat_family(scope, family, temp_dir / "patstat"))
                if family == "publications" and uspto_enabled:
                    uspto_outputs, uspto_metrics, uspto_warnings = _extract_uspto_family(working_settings, scope, temp_dir / "uspto")
                    local_outputs.extend(uspto_outputs)
                    chunk_metrics.update(uspto_metrics)
                    chunk_warnings.extend(uspto_warnings)
                    if uspto_warnings:
                        status = "degraded"
            elif family == "register":
                local_outputs.extend(_extract_register_family(scope, temp_dir / "register"))
            elif family == "epab":
                local_outputs.extend(_extract_epab_family(working_settings, scope, temp_dir / "epab"))
            else:
                chunk_warnings.append(f"Unsupported chunk family `{family}` was skipped.")
                status = "degraded"

            if container is not None and local_outputs and execution.get("upload_after_chunk", True):
                standard_outputs = [path for path in local_outputs if path.parent.name != "uspto"]
                uspto_outputs = [path for path in local_outputs if path.parent.name == "uspto"]
                if standard_outputs:
                    uploaded_blobs.extend(_upload_paths(container, standard_outputs, chunk["blob_prefix"]))
                if uspto_outputs:
                    root_prefix = "raw-bounded-heritage" if horizon_label == "heritage" else "raw-bounded"
                    uspto_blob_prefix = f"{root_prefix}/uspto/field={chunk['field_slug']}/year={chunk['year_start']}-{chunk['year_end']}/family={chunk['table_family']}"
                    uploaded_blobs.extend(_upload_paths(container, uspto_outputs, uspto_blob_prefix))
                uploaded_files += len(uploaded_blobs)

            if execution.get("cleanup_after_upload", False) and (container is not None or not execution.get("blob_intermediate_enabled", False)):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as exc:
            status = "failed"
            failed_chunks += 1
            chunk_warnings.append(str(exc))
        finally:
            if scope is not None:
                close_tip_client(scope.get("patstat"))

        if status == "degraded":
            degraded_chunks += 1
        manifest_path = _write_chunk_manifest(
            settings,
            chunk,
            status=status,
            local_outputs=local_outputs,
            uploaded_blobs=uploaded_blobs,
            metrics=chunk_metrics,
            warnings=chunk_warnings,
        )
        result.outputs.append(str(manifest_path))

    result.metrics["chunk_total_count"] = total_chunks
    result.metrics["chunk_skipped_count"] = skipped_chunks
    result.metrics["chunk_failed_count"] = failed_chunks
    result.metrics["chunk_degraded_count"] = degraded_chunks
    result.metrics["chunk_uploaded_file_count"] = uploaded_files
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
