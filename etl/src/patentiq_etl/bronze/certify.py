from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REFERENCE_TABLES, REGISTER_TABLES, REQUIRED_SOURCE_COLUMNS
from patentiq_etl.common.io import candidate_files
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.tip_clients import (
    close_tip_client,
    get_epab_client,
    get_patstat_client,
    get_patstat_database_module,
    resolve_patstat_model,
    resolve_register_model,
)


DOC_REFS = [
    "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
    "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
    "docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md",
]


LOGGER = logging.getLogger(__name__)


def _certify_tip_patstat(settings: BuildSettings, result: StageResult) -> dict[str, Path]:
    """Verify TIP PATSTAT and Register availability instead of local raw files."""
    resolved: dict[str, Path] = {}
    patstat = None
    db = None
    try:
        patstat, db = get_patstat_client(settings.tip_env)
        database_module = get_patstat_database_module()
    except Exception as exc:  # pragma: no cover - requires TIP runtime
        result.status = "failed"
        result.warnings.append(f"TIP PATSTAT client could not be initialized: {exc}")
        return resolved

    result.inputs.append(f"tip://patstat/{settings.tip_env}")
    result.metrics["tip_patstat_client_available"] = 1
    result.metrics["tip_patstat_orm_available"] = int(db is not None)

    for logical_name in PATSTAT_TABLES:
        model = resolve_patstat_model(database_module, logical_name)
        result.metrics[f"{logical_name}_tip_model_available"] = int(model is not None)
        if model is None and logical_name not in {"bronze_patstat_appln_prior", "bronze_patstat_appln_contn"}:
            result.warnings.append(f"TIP PATSTAT model for `{logical_name}` was not resolved.")

    for logical_name in REGISTER_TABLES:
        model = resolve_register_model(database_module, logical_name)
        result.metrics[f"{logical_name}_tip_model_available"] = int(model is not None)

    try:
        TLS230 = resolve_patstat_model(database_module, "bronze_patstat_appln_techn_field")
        TLS901 = resolve_patstat_model(database_module, "bronze_ref_techn_field_ipc")
        if TLS230 is not None and TLS901 is not None:
            from sqlalchemy import func

            rows = (
                db.query(
                    TLS901.techn_field,
                    func.count(func.distinct(TLS230.appln_id)),
                )
                .join(TLS901, TLS230.techn_field_nr == TLS901.techn_field_nr)
                .filter(TLS901.techn_field.in_(settings.selected_wipo_fields))
                .group_by(TLS901.techn_field)
                .all()
            )
            coverage = {row[0]: int(row[1]) for row in rows}
            for field in settings.selected_wipo_fields:
                result.metrics[f"scope_field_appln_count__{field}"] = coverage.get(field, 0)
            missing_fields = [field for field in settings.selected_wipo_fields if coverage.get(field, 0) == 0]
            if missing_fields:
                result.status = "failed"
                result.warnings.append(f"Selected WIPO fields are not represented in TIP PATSTAT technology fields: {missing_fields}.")
    except Exception as exc:  # pragma: no cover - requires TIP runtime
        result.status = "degraded" if result.status == "success" else result.status
        result.warnings.append(f"TIP PATSTAT field coverage check degraded due to query failure: {exc}")
    finally:
        close_tip_client(patstat)

    return resolved


def _certify_tip_epab(settings: BuildSettings, result: StageResult) -> None:
    """Verify TIP EPAB client availability and query construction."""
    epab = None
    try:
        epab = get_epab_client(settings.tip_env)
    except Exception as exc:  # pragma: no cover - requires TIP runtime
        if settings.thresholds.get("degrade_on_missing_epab", True):
            result.status = "degraded" if result.status == "success" else result.status
        result.warnings.append(f"TIP EPAB client could not be initialized: {exc}")
        return
    result.inputs.append(f"tip://epab/{settings.tip_env}")
    result.metrics["tip_epab_client_available"] = 1
    try:
        _ = epab.query_publication(number="1234567", kind_code="A1")
        result.metrics["tip_epab_publication_query_available"] = 1
    except Exception as exc:  # pragma: no cover - requires TIP runtime
        result.status = "degraded" if result.status == "success" else result.status
        result.warnings.append(f"TIP EPAB publication query construction failed: {exc}")
    finally:
        close_tip_client(epab)


def _read_source_columns(path: Path) -> list[str]:
    """Inspect a raw source file and return its column names without materializing a Bronze table."""
    con = duckdb.connect()
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        rows = con.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()
    elif suffix in {".csv", ".gz"} or path.name.endswith(".csv.gz"):
        rows = con.execute("describe select * from read_csv_auto(?, header=true)", [str(path)]).fetchall()
    elif suffix in {".json", ".jsonl"}:
        rows = con.execute("describe select * from read_json_auto(?)", [str(path)]).fetchall()
    else:
        return []
    return [row[0] for row in rows]


def _scan_group(directory: Path, tables: dict[str, list[str]]) -> tuple[list[str], list[str], dict[str, int], dict[str, Path]]:
    """Scan one raw-source directory for required logical tables and validate required columns."""
    inputs: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, int] = {}
    resolved_paths: dict[str, Path] = {}
    for logical_name, stems in tables.items():
        matches = candidate_files(directory, stems)
        if not matches:
            warnings.append(f"Missing source for `{logical_name}` in `{directory}`.")
            continue
        source_path = matches[0]
        resolved_paths[logical_name] = source_path
        inputs.append(str(source_path))
        metrics[f"{logical_name}_file_count"] = len(matches)
        required_columns = REQUIRED_SOURCE_COLUMNS.get(logical_name, [])
        if required_columns:
            present_columns = {column.lower() for column in _read_source_columns(source_path)}
            missing_columns = [column for column in required_columns if column.lower() not in present_columns]
            if missing_columns:
                warnings.append(
                    f"Source `{logical_name}` is missing expected columns {missing_columns} in `{source_path.name}`."
                )
            metrics[f"{logical_name}_column_count"] = len(present_columns)
    return inputs, warnings, metrics, resolved_paths


def _certify_scope_field_coverage(settings: BuildSettings, source_paths: dict[str, Path], result: StageResult) -> None:
    """Check that the configured 10-field mega-cluster is representable in the raw PATSTAT inputs."""
    tech_path = source_paths.get("bronze_patstat_appln_techn_field")
    ipc_path = source_paths.get("bronze_patstat_appln_ipc")
    ref_path = source_paths.get("bronze_ref_techn_field_ipc")
    if tech_path is None and (ipc_path is None or ref_path is None):
        result.status = "failed"
        result.warnings.append(
            "Neither PATSTAT technology fields nor the IPC-to-WIPO concordance are available for 10-field scope sufficiency checks."
        )
        return

    con = duckdb.connect()
    selected_fields_sql = ", ".join([f"'{field}'" for field in settings.selected_wipo_fields])
    if tech_path is not None:
        tech_columns = _read_source_columns(tech_path)
        appln_column = next((column for column in tech_columns if column.lower() == "appln_id"), None)
        field_column = next(
            (
                column
                for column in tech_columns
                if column.lower() in {"techn_field", "techn_field_nr", "wipo_industry_code"}
            ),
            None,
        )
        if appln_column and field_column:
            rows = con.execute(
                f"""
                select
                    cast({field_column} as varchar) as wipo_industry_code,
                    count(distinct cast({appln_column} as bigint)) as appln_count
                from read_parquet(?)
                where cast({field_column} as varchar) in ({selected_fields_sql})
                group by 1
                """,
                [str(tech_path)],
            ).fetchall()
            coverage = {row[0]: int(row[1]) for row in rows}
            for field in settings.selected_wipo_fields:
                result.metrics[f"scope_field_appln_count__{field}"] = coverage.get(field, 0)
            missing_fields = [field for field in settings.selected_wipo_fields if coverage.get(field, 0) == 0]
            if missing_fields:
                result.status = "failed"
                result.warnings.append(
                    f"Selected WIPO fields are not represented in PATSTAT technology-field input: {missing_fields}."
                )
            return

    ipc_columns = _read_source_columns(ipc_path) if ipc_path else []
    ref_columns = _read_source_columns(ref_path) if ref_path else []
    ipc_symbol = next((column for column in ipc_columns if column.lower() == "ipc_class_symbol"), None)
    ipc_appln = next((column for column in ipc_columns if column.lower() == "appln_id"), None)
    ref_ipc = next((column for column in ref_columns if column.lower() in {"ipc_subclass", "ipc_maingroup_symbol"}), None)
    ref_field = next((column for column in ref_columns if column.lower() in {"techn_field", "wipo_industry_code"}), None)
    if ipc_path and ref_path and ipc_symbol and ipc_appln and ref_ipc and ref_field:
        rows = con.execute(
            f"""
            select
                cast(r.{ref_field} as varchar) as wipo_industry_code,
                count(distinct cast(i.{ipc_appln} as bigint)) as appln_count
            from read_parquet(?) i
            join read_parquet(?) r
              on regexp_replace(substr(cast(i.{ipc_symbol} as varchar), 1, length(cast(r.{ref_ipc} as varchar))), '[^A-Za-z0-9]', '', 'g')
                 = regexp_replace(cast(r.{ref_ipc} as varchar), '[^A-Za-z0-9]', '', 'g')
            where cast(r.{ref_field} as varchar) in ({selected_fields_sql})
            group by 1
            """,
            [str(ipc_path), str(ref_path)],
        ).fetchall()
        coverage = {row[0]: int(row[1]) for row in rows}
        for field in settings.selected_wipo_fields:
            result.metrics[f"scope_field_appln_count__{field}"] = coverage.get(field, 0)
        missing_fields = [field for field in settings.selected_wipo_fields if coverage.get(field, 0) == 0]
        if missing_fields:
            result.status = "failed"
            result.warnings.append(f"Selected WIPO fields are not representable through IPC fallback mapping: {missing_fields}.")


def certify_sources(settings: BuildSettings) -> StageResult:
    """Run pre-Bronze source certification across PATSTAT, Register, USPTO, EPAB, and refs."""
    result = StageResult(
        stage="source-certification",
        status="success",
        summary="Certified raw source availability, bridge viability, and mega-cluster sufficiency preconditions.",
        methods=[
            "Scanned local raw-source directories or TIP clients depending on the configured source mode.",
            "Applied release severity classification using configured thresholds and source-family-specific rules.",
            "Recorded source availability and missing-resource warnings before Bronze generation.",
            "Validated required raw-source columns against the schema contracts captured in docs/data and V2 warehouse docs.",
        ],
        calculations=[
            "Source sufficiency is evaluated as presence plus bridge-readiness of family/application/publication identifiers.",
            "Selected field sufficiency requires every configured WIPO field to remain representable downstream.",
        ],
        downstream_impacts=[
            "Failure here blocks Bronze ingestion and prevents the bounded mega-cluster seed from being generated safely.",
            "Missing PATSTAT or weak field coverage will invalidate all downstream family, portfolio, Market Intelligence, and semantic marts.",
            "Missing USPTO or EPAB will specifically degrade semantic claim-space selection while leaving abstract fallback available.",
        ],
        doc_refs=DOC_REFS,
    )

    LOGGER.info("Starting source certification for release `%s`", settings.release_id)
    patstat_inputs: list[str] = []
    patstat_warnings: list[str] = []
    patstat_metrics: dict[str, int] = {}
    patstat_paths: dict[str, Path] = {}
    register_inputs: list[str] = []
    register_warnings: list[str] = []
    register_metrics: dict[str, int] = {}
    register_paths: dict[str, Path] = {}

    if settings.patstat_source_mode == "tip" or settings.register_source_mode == "tip":
        _certify_tip_patstat(settings, result)
    if settings.patstat_source_mode == "local_files":
        patstat_inputs, patstat_warnings, patstat_metrics, patstat_paths = _scan_group(settings.raw_patstat_dir, PATSTAT_TABLES)
    if settings.register_source_mode == "local_files":
        register_inputs, register_warnings, register_metrics, register_paths = _scan_group(settings.raw_register_dir, REGISTER_TABLES)
    ref_inputs, ref_warnings, ref_metrics, ref_paths = _scan_group(settings.raw_refs_dir, REFERENCE_TABLES)

    result.inputs.extend(patstat_inputs + register_inputs + ref_inputs)
    result.warnings.extend(patstat_warnings + register_warnings + ref_warnings)
    result.metrics.update(patstat_metrics | register_metrics | ref_metrics)

    uspto_files = list(settings.raw_uspto_dir.glob("*.XML")) + list(settings.raw_uspto_dir.glob("*.xml"))
    epab_files: list[Path] = []
    if settings.epab_source_mode == "local_files":
        epab_files = list(settings.raw_epab_dir.glob("*.jsonl")) + list(settings.raw_epab_dir.glob("*.json")) + list(settings.raw_epab_dir.glob("*.parquet"))
    else:
        _certify_tip_epab(settings, result)
    result.inputs.extend([str(path) for path in uspto_files[:20]])
    result.inputs.extend([str(path) for path in epab_files[:20]])
    result.metrics["total_input_file_count"] = len(patstat_inputs) + len(register_inputs) + len(ref_inputs) + len(uspto_files) + len(epab_files)
    result.metrics["uspto_xml_file_count"] = len(uspto_files)
    result.metrics["epab_payload_file_count"] = len(epab_files)

    if settings.patstat_source_mode == "local_files" and not patstat_inputs:
        result.status = "failed"
        result.warnings.append("PATSTAT core source family is unavailable. This is a fail-release condition.")
    elif settings.uspto_source_mode == "local_files" and not uspto_files and settings.thresholds.get("degrade_on_missing_uspto", True):
        result.status = "degraded"
        result.warnings.append("USPTO full-text source family is unavailable. Semantic claim-space workflows must degrade.")
    elif settings.epab_source_mode == "local_files" and not epab_files and settings.thresholds.get("degrade_on_missing_epab", True):
        result.status = "degraded"
        result.warnings.append("EPAB full-text source family is unavailable. EP claim-space workflows must degrade.")

    if not settings.ref_techn_field_ipc.exists():
        result.status = "failed"
        result.warnings.append("WIPO field concordance file is missing. Scope seeding cannot proceed safely.")
    else:
        result.inputs.append(str(settings.ref_techn_field_ipc))

    selected = settings.selected_wipo_fields
    result.metrics["selected_wipo_field_count"] = len(selected)
    if len(selected) != 10:
        result.status = "failed"
        result.warnings.append("The configured mega-cluster must contain exactly 10 WIPO fields.")

    if settings.patstat_source_mode == "local_files":
        _certify_scope_field_coverage(settings, patstat_paths | ref_paths, result)

    if settings.register_source_mode == "local_files" and "bronze_reg101_appln" not in register_paths and settings.thresholds.get("degrade_on_missing_register", True):
        if result.status == "success":
            result.status = "degraded"
        result.warnings.append("PATSTAT Register core EP anchors are unavailable. EP prosecution and publication-detail overlays will degrade.")

    LOGGER.info(
        "Source certification complete status=%s patstat=%s register=%s refs=%s uspto=%s epab=%s",
        result.status,
        len(patstat_paths),
        len(register_paths),
        len(ref_paths),
        len(uspto_files),
        len(epab_files),
    )
    return result


def certify_release(settings: BuildSettings) -> StageResult:
    """Verify that the built artifact set is complete enough to publish as one release."""
    result = StageResult(
        stage="release-certification",
        status="success",
        summary="Verified that certified stage outputs exist and are promotable to Azure.",
        methods=[
            "Checked required artifact groups for Bronze, Silver, Gold, ML, and vectors.",
            "Verified that Data Room-facing manifests can be published from one authoritative store.",
        ],
        calculations=[
            "Release validity is based on artifact existence and stage certification, not on cloud deployment status alone.",
        ],
        downstream_impacts=[
            "Failed release certification blocks Blob publish and Data Room release pointer updates.",
            "Empty Bronze, Silver, or Gold directories indicate a non-promotable warehouse build.",
        ],
        doc_refs=DOC_REFS,
    )

    required_paths = [
        settings.bronze_dir,
        settings.silver_dir,
        settings.gold_dir,
        settings.manifests_dir / "stages",
    ]
    for path in required_paths:
        result.inputs.append(str(path))
        if not path.exists():
            result.status = "failed"
            result.warnings.append(f"Required release path is missing: `{path}`.")

    for parquet_dir, metric_prefix in [
        (settings.bronze_dir, "bronze"),
        (settings.silver_dir, "silver"),
        (settings.gold_dir, "gold"),
        (settings.ml_dir, "ml"),
        (settings.vectors_dir, "vectors"),
    ]:
        parquet_count = len(list(parquet_dir.glob("*.parquet")))
        result.metrics[f"{metric_prefix}_parquet_count"] = parquet_count
        if metric_prefix in {"bronze", "silver", "gold"} and parquet_count == 0:
            result.status = "failed"
            result.warnings.append(f"No `{metric_prefix}` Parquet artifacts were found.")

    return result
