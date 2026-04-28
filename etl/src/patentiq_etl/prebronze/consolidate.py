from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import duckdb

from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REFERENCE_TABLES, REGISTER_TABLES
from patentiq_etl.common.io import duckdb_connect, ensure_dir, parquet_row_count
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.chunked import _download_blob_to_path, _upload_options


EPAB_CANONICAL_FILES = (
    "epab_publication.parquet",
    "epab_abstract.parquet",
    "epab_claims.parquet",
)
PARTITION_METADATA_COLUMNS = {"filename", "file_row_number", "field", "year", "family"}


def _blob_container_client(settings: BuildSettings):
    """Return an Azure Blob container client for local consolidation downloads."""
    connection_env = settings.azure.get("connection_string_env")
    if not connection_env:
        raise RuntimeError("Azure Blob download requires `azure.connection_string_env` in `etl/conf/azure.yaml`.")
    connection_string = os.environ.get(connection_env)
    if not connection_string:
        raise RuntimeError(f"Azure Blob download requires environment variable `{connection_env}` to be set.")
    try:
        from azure.storage.blob import BlobServiceClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("Azure Blob download requires `azure-storage-blob` in the local ETL environment.") from exc

    transfer_options = _upload_options(settings)
    service = BlobServiceClient.from_connection_string(
        connection_string,
        connection_timeout=max(1, int((settings.execution or {}).get("upload_connection_timeout_seconds", 60))),
        read_timeout=max(1, int((settings.execution or {}).get("upload_read_timeout_seconds", 1200))),
    )
    return service.get_container_client(settings.azure["container"]), transfer_options


def _staging_root(settings: BuildSettings) -> Path:
    """Return the import staging root for downloaded Blob data."""
    execution = settings.execution or {}
    configured = execution.get("consolidate_import_root")
    if configured:
        return ensure_dir((settings.repo_root / str(configured)).resolve())
    return ensure_dir(settings.repo_root / "etl" / "data" / "imports")


def _canonical_staging_path(staging_root: Path, blob_name: str) -> Path:
    """Map one blob name to its local staging path."""
    parts = Path(blob_name).parts
    if len(parts) >= 3 and parts[0] in {"raw-bounded", "raw-bounded-heritage"} and parts[1] == "seeds":
        return staging_root / parts[0] / "_seeds" / parts[-1]
    return staging_root / Path(blob_name)


def _list_blob_names(container, prefix: str) -> list[str]:
    """List parquet blob names for one prefix."""
    names: list[str] = []
    for blob in container.list_blobs(name_starts_with=prefix.rstrip("/") + "/"):
        name = getattr(blob, "name", None)
        if isinstance(name, str) and name.endswith(".parquet"):
            names.append(name)
    return sorted(names)


def _download_prefix(
    *,
    container,
    prefix: str,
    staging_root: Path,
    transfer_options: dict[str, int],
    logger: logging.Logger,
    result: StageResult,
    redownload_existing: bool,
) -> list[Path]:
    """Download all parquet blobs for one prefix into the staging tree."""
    blob_names = _list_blob_names(container, prefix)
    downloaded: list[Path] = []
    reused = 0
    for blob_name in blob_names:
        out_path = _canonical_staging_path(staging_root, blob_name)
        if out_path.exists() and not redownload_existing:
            reused += 1
            downloaded.append(out_path)
            continue
        downloaded.append(
            _download_blob_to_path(
                container,
                blob_name,
                out_path,
                transfer_options,
                logger=logger,
                chunk_id="consolidate-before-bronze",
            )
        )
    result.metrics[f"{prefix.replace('/', '_')}_blob_count"] = len(blob_names)
    result.metrics[f"{prefix.replace('/', '_')}_reused_count"] = reused
    return downloaded


def _target_cleanup(paths: list[Path]) -> int:
    """Delete pre-existing canonical parquet outputs that will be regenerated."""
    removed = 0
    for path in paths:
        if path.exists():
            path.unlink()
            removed += 1
    return removed


def _sql_path_list(paths: list[Path]) -> str:
    """Return one SQL list literal for DuckDB parquet readers."""
    return "[" + ", ".join("'" + str(path).replace("'", "''") + "'" for path in paths) + "]"


def _merge_parquet_group(
    paths: list[Path],
    out_path: Path,
    logger: logging.Logger,
    *,
    deduplicate: bool = True,
) -> int:
    """Union one logical parquet group into its canonical output."""
    ensure_dir(out_path.parent)
    con = duckdb_connect()
    source_sql = f"read_parquet({_sql_path_list(paths)}, union_by_name=true)"
    try:
        describe_rows = con.execute(f"describe select * from {source_sql}").fetchall()
    except duckdb.InvalidInputException as exc:
        if "Need at least one non-root column in the file" not in str(exc):
            raise
        valid_paths: list[Path] = []
        for path in paths:
            try:
                con.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()
                valid_paths.append(path)
            except duckdb.InvalidInputException as path_exc:
                if "Need at least one non-root column in the file" in str(path_exc):
                    logger.warning("Skipping empty-schema parquet during consolidation path=%s", path)
                    continue
                raise
        if not valid_paths:
            raise
        source_sql = f"read_parquet({_sql_path_list(valid_paths)}, union_by_name=true)"
        describe_rows = con.execute(f"describe select * from {source_sql}").fetchall()
    projected_columns = [row[0] for row in describe_rows if row[0] not in PARTITION_METADATA_COLUMNS]
    projection_sql = ", ".join(f'"{column}"' for column in projected_columns) or "*"
    select_sql = f"select {projection_sql} from {source_sql}"
    if deduplicate:
        select_sql = f"select distinct {projection_sql} from {source_sql}"
    con.execute(f"copy ({select_sql}) to ? (format parquet, compression zstd)", [str(out_path)])
    return parquet_row_count(out_path)


def _staged_matches(root: Path, stems: list[str]) -> list[Path]:
    """Find staged parquet files recursively for any of the given stems."""
    matches: list[Path] = []
    for stem in stems:
        matches.extend(sorted(root.rglob(f"{stem}.parquet")))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in matches:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return deduped


def _consolidate_mapped_tables(
    *,
    table_map: dict[str, list[str]],
    roots: list[Path],
    target_dir: Path,
    logger: logging.Logger,
    result: StageResult,
    metric_prefix: str,
) -> tuple[int, int]:
    """Consolidate one logical table map into canonical local bounded files."""
    consolidated = 0
    total_rows = 0
    cleanup_count = 0
    for logical_name, stems in table_map.items():
        source_paths: list[Path] = []
        for root in roots:
            if root.exists():
                source_paths.extend(_staged_matches(root, stems))
        out_path = target_dir / f"{stems[0]}.parquet"
        if not source_paths:
            result.warnings.append(f"Skipped `{logical_name}` because no staged parquet was found for stems {stems}.")
            continue
        cleanup_count += _target_cleanup([out_path])
        row_count = _merge_parquet_group(source_paths, out_path, logger, deduplicate=True)
        consolidated += 1
        total_rows += row_count
        result.outputs.append(str(out_path))
        result.metrics[f"{stems[0]}_source_file_count"] = len(source_paths)
        result.metrics[f"{stems[0]}_bounded_count"] = row_count
        logger.info(
            "Consolidated logical_name=%s output=%s source_file_count=%s row_count=%s",
            logical_name,
            out_path,
            len(source_paths),
            row_count,
        )
    result.metrics[f"{metric_prefix}_target_cleanup_count"] = cleanup_count
    return consolidated, total_rows


def _consolidate_epab(
    *,
    staged_root: Path,
    target_dir: Path,
    logger: logging.Logger,
    result: StageResult,
) -> tuple[int, int]:
    """Consolidate the active EPAB parquet set into canonical local bounded files."""
    cleanup_targets = list(target_dir.glob("epab_*.parquet"))
    result.metrics["epab_target_cleanup_count"] = _target_cleanup(cleanup_targets)
    consolidated = 0
    total_rows = 0
    for filename in EPAB_CANONICAL_FILES:
        source_paths = sorted(staged_root.rglob(filename)) if staged_root.exists() else []
        out_path = target_dir / filename
        if not source_paths:
            result.warnings.append(f"Skipped `{filename}` because no staged EPAB parquet was found.")
            continue
        # EPAB text payloads are wide and expensive to deduplicate in-memory.
        # Bronze only needs one canonical local file per EPAB payload family, so we
        # concatenate the staged chunk outputs here and leave row-level uniqueness to
        # the downstream semantic/text-provider logic where needed.
        row_count = _merge_parquet_group(source_paths, out_path, logger, deduplicate=False)
        consolidated += 1
        total_rows += row_count
        result.outputs.append(str(out_path))
        result.metrics[f"{Path(filename).stem}_source_file_count"] = len(source_paths)
        result.metrics[f"{Path(filename).stem}_bounded_count"] = row_count
        logger.info(
            "Consolidated epab_file=%s output=%s source_file_count=%s row_count=%s",
            filename,
            out_path,
            len(source_paths),
            row_count,
        )
    return consolidated, total_rows


def consolidate_before_bronze(settings: BuildSettings) -> StageResult:
    """Download Blob-backed bounded raw chunks into staging and flatten them for Bronze."""
    result = StageResult(
        stage="consolidate-before-bronze",
        status="success",
        summary="Downloaded Blob-backed bounded raw chunks into local staging, consolidated them into canonical bounded parquet files, and kept heritage seeds isolated from the active main seed root.",
        methods=[
            "Downloaded the Blob-backed bounded raw prefixes needed for local Bronze/Silver/Gold preparation into a separate staging tree.",
            "Merged partitioned field/year chunk parquet into one canonical local bounded parquet per logical table using DuckDB `select distinct *` deduplication.",
            "Folded heritage PATSTAT parquet into the same canonical PATSTAT outputs while keeping heritage seeds in staging only.",
        ],
        calculations=[
            "Main PATSTAT, Register, EPAB, and refs are sourced from `raw-bounded/*` Blob prefixes.",
            "Heritage PATSTAT and heritage seeds are sourced from `raw-bounded-heritage/*` Blob prefixes.",
            "Canonical Bronze inputs remain the existing local bounded directories that downstream stages already read.",
        ],
        downstream_impacts=[
            "The local bounded raw layer becomes compatible with the non-recursive Bronze ingestors that expect one top-level parquet per logical source table.",
            "Heritage history is incorporated into downstream Bronze/Silver/Gold by merging heritage PATSTAT into canonical PATSTAT outputs before Bronze runs.",
        ],
        doc_refs=[
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
            "docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md",
            "docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md",
        ],
    )
    logger = configure_logger(result.stage, settings.manifests_dir / "stages" / f"{result.stage}.log")
    staging_root = _staging_root(settings)
    result.artifacts["staging_root"] = str(staging_root)
    result.inputs.extend(
        [
            f"azure-blob://{settings.azure['container']}/raw-bounded/patstat",
            f"azure-blob://{settings.azure['container']}/raw-bounded/register",
            f"azure-blob://{settings.azure['container']}/raw-bounded/epab",
            f"azure-blob://{settings.azure['container']}/raw-bounded/refs",
            f"azure-blob://{settings.azure['container']}/raw-bounded-heritage/patstat",
            f"azure-blob://{settings.azure['container']}/raw-bounded-heritage/seeds",
        ]
    )

    container, transfer_options = _blob_container_client(settings)
    execution = settings.execution or {}
    redownload_existing = bool(execution.get("consolidate_redownload_existing", False))
    download_main_seeds = bool(execution.get("consolidate_download_main_seeds", False))
    download_heritage_seeds = bool(execution.get("consolidate_download_heritage_seeds", True))

    main_prefixes = [
        "raw-bounded/patstat",
        "raw-bounded/register",
        "raw-bounded/epab",
        "raw-bounded/refs",
    ]
    if download_main_seeds:
        main_prefixes.append("raw-bounded/seeds")
    heritage_prefixes = ["raw-bounded-heritage/patstat"]
    if download_heritage_seeds:
        heritage_prefixes.append("raw-bounded-heritage/seeds")

    downloaded_paths: list[Path] = []
    for prefix in [*main_prefixes, *heritage_prefixes]:
        logger.info("Staging blob prefix=%s", prefix)
        downloaded_paths.extend(
            _download_prefix(
                container=container,
                prefix=prefix,
                staging_root=staging_root,
                transfer_options=transfer_options,
                logger=logger,
                result=result,
                redownload_existing=redownload_existing,
            )
        )

    result.metrics["staged_blob_file_count"] = len(downloaded_paths)
    result.metrics["staged_blob_total_bytes"] = sum(path.stat().st_size for path in downloaded_paths if path.exists())

    staged_main_patstat = staging_root / "raw-bounded" / "patstat"
    staged_main_register = staging_root / "raw-bounded" / "register"
    staged_main_epab = staging_root / "raw-bounded" / "epab"
    staged_main_refs = staging_root / "raw-bounded" / "refs"
    staged_heritage_patstat = staging_root / "raw-bounded-heritage" / "patstat"
    staged_heritage_seed_dir = staging_root / "raw-bounded-heritage" / "_seeds"

    patstat_tables, patstat_rows = _consolidate_mapped_tables(
        table_map=PATSTAT_TABLES,
        roots=[staged_main_patstat, staged_heritage_patstat],
        target_dir=ensure_dir(settings.bounded_patstat_dir),
        logger=logger,
        result=result,
        metric_prefix="patstat",
    )
    register_tables, register_rows = _consolidate_mapped_tables(
        table_map=REGISTER_TABLES,
        roots=[staged_main_register],
        target_dir=ensure_dir(settings.bounded_register_dir),
        logger=logger,
        result=result,
        metric_prefix="register",
    )
    reference_tables, reference_rows = _consolidate_mapped_tables(
        table_map=REFERENCE_TABLES,
        roots=[staged_main_refs],
        target_dir=ensure_dir(settings.bounded_refs_dir),
        logger=logger,
        result=result,
        metric_prefix="refs",
    )
    epab_tables, epab_rows = _consolidate_epab(
        staged_root=staged_main_epab,
        target_dir=ensure_dir(settings.bounded_epab_dir),
        logger=logger,
        result=result,
    )

    result.metrics["patstat_consolidated_table_count"] = patstat_tables
    result.metrics["register_consolidated_table_count"] = register_tables
    result.metrics["refs_consolidated_table_count"] = reference_tables
    result.metrics["epab_consolidated_table_count"] = epab_tables
    result.metrics["consolidated_total_row_count"] = patstat_rows + register_rows + reference_rows + epab_rows
    result.metrics["heritage_seed_staging_count"] = len(list(staged_heritage_seed_dir.glob("*.parquet"))) if staged_heritage_seed_dir.exists() else 0
    result.metrics["main_seed_dir_untouched"] = str(settings.bounded_seed_dir)
    result.artifacts["heritage_seed_staging_dir"] = str(staged_heritage_seed_dir)
    result.artifacts["main_patstat_staging_dir"] = str(staged_main_patstat)
    result.artifacts["heritage_patstat_staging_dir"] = str(staged_heritage_patstat)

    if not settings.bounded_seed_dir.exists():
        result.warnings.append(
            "The active main seed directory does not exist locally. This stage does not populate it unless `consolidate_download_main_seeds` is enabled."
        )
    result.outputs.extend(
        [
            str(settings.bounded_patstat_dir),
            str(settings.bounded_register_dir),
            str(settings.bounded_epab_dir),
            str(settings.bounded_refs_dir),
        ]
    )
    return result
