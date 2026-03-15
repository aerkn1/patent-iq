from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb

from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REFERENCE_TABLES, REGISTER_TABLES
from patentiq_etl.common.io import candidate_files, parquet_row_count
from patentiq_etl.common.types import BuildSettings, StageResult


LOGGER = logging.getLogger(__name__)


PATSTAT_TYPE_OVERRIDES: dict[str, dict[str, str]] = {
    "bronze_patstat_appln": {
        "appln_id": "bigint",
        "internat_appln_id": "bigint",
        "earliest_filing_id": "bigint",
        "earliest_pat_publn_id": "bigint",
        "docdb_family_id": "bigint",
        "inpadoc_family_id": "bigint",
        "docdb_family_size": "bigint",
        "nb_citing_docdb_fam": "bigint",
        "nb_applicants": "bigint",
        "nb_inventors": "bigint",
        "appln_filing_date": "date",
        "earliest_filing_date": "date",
        "earliest_publn_date": "date",
    },
    "bronze_patstat_appln_title": {
        "appln_id": "bigint",
    },
    "bronze_patstat_appln_abstr": {
        "appln_id": "bigint",
    },
    "bronze_patstat_appln_prior": {
        "appln_id": "bigint",
        "prior_appln_id": "bigint",
        "prior_appln_date": "date",
    },
    "bronze_patstat_person": {
        "person_id": "bigint",
        "doc_std_name_id": "bigint",
        "psn_id": "bigint",
        "psn_level": "bigint",
        "han_id": "bigint",
        "han_harmonized": "bigint",
    },
    "bronze_patstat_pers_appln": {
        "person_id": "bigint",
        "appln_id": "bigint",
        "applt_seq_nr": "bigint",
        "invt_seq_nr": "bigint",
    },
    "bronze_patstat_appln_ipc": {
        "appln_id": "bigint",
        "ipc_version": "date",
    },
    "bronze_patstat_pat_publn": {
        "pat_publn_id": "bigint",
        "appln_id": "bigint",
        "publn_date": "date",
        "publn_first_grant_date": "date",
    },
    "bronze_patstat_citation": {
        "pat_publn_id": "bigint",
        "cited_pat_publn_id": "bigint",
        "cited_appln_id": "bigint",
        "npl_publn_id": "bigint",
    },
    "bronze_patstat_npl_publn": {
        "npl_publn_id": "bigint",
    },
    "bronze_patstat_appln_contn": {
        "appln_id": "bigint",
        "parent_appln_id": "bigint",
    },
    "bronze_patstat_appln_cpc": {
        "appln_id": "bigint",
    },
    "bronze_patstat_appln_techn_field": {
        "appln_id": "bigint",
        "techn_field_nr": "bigint",
        "weight": "double",
    },
    "bronze_patstat_docdb_fam_citn": {
        "docdb_family_id": "bigint",
        "cited_docdb_family_id": "bigint",
    },
    "bronze_patstat_inpadoc_legal_event": {
        "appln_id": "bigint",
        "lec_id": "bigint",
        "event_date": "date",
        "published_date": "date",
    },
    "bronze_ref_legal_event_code": {},
}

REGISTER_TYPE_OVERRIDES: dict[str, dict[str, str]] = {
    "bronze_reg101_appln": {
        "id": "bigint",
        "appln_id": "bigint",
        "appln_filing_date": "date",
        "internat_appln_id": "bigint",
    },
    "bronze_reg403_appln_status": {},
    "bronze_reg107_parties": {
        "id": "bigint",
        "customer_id": "bigint",
        "sequence_nr": "bigint",
    },
    "bronze_reg111_licensee": {
        "id": "bigint",
    },
    "bronze_reg125_appeal": {
        "id": "bigint",
        "date_appeal": "date",
        "date_decision": "date",
    },
    "bronze_reg130_opponent": {
        "id": "bigint",
        "oppt_nr": "bigint",
        "date_opp_filed": "date",
        "oppt_status_date": "date",
    },
    "bronze_reg201_proc_step": {
        "id": "bigint",
        "step_id": "bigint",
        "time_limit": "bigint",
    },
    "bronze_reg202_proc_step_text": {
        "step_id": "bigint",
    },
    "bronze_reg203_proc_step_date": {
        "step_id": "bigint",
        "step_date": "date",
    },
    "bronze_reg301_event_data": {
        "id": "bigint",
        "event_date": "date",
    },
    "bronze_reg402_event_text": {},
    "bronze_reg701_appln": {
        "id": "bigint",
        "appln_id": "bigint",
    },
    "bronze_reg731_event_data": {
        "id": "bigint",
        "event_date": "date",
    },
    "bronze_reg741_appln_status": {},
    "bronze_reg742_event_text": {},
}

REFERENCE_NORMALIZATION_SPECS: dict[str, dict[str, Any]] = {
    "bronze_ref_techn_field_ipc": {
        "columns": {
            "ipc_subclass": ["ipc_subclass", "ipc_maingroup_symbol", "ipc_code"],
            "ipc_maingroup_symbol": ["ipc_maingroup_symbol", "ipc_subclass", "ipc_code"],
            "techn_field_nr": ["techn_field_nr", "wipo_field_nr"],
            "techn_sector": ["techn_sector"],
            "techn_field": ["techn_field", "wipo_field_name", "wipo_industry_code"],
            "wipo_industry_code": ["wipo_industry_code", "techn_field", "wipo_field_name"],
        },
        "casts": {"techn_field_nr": "bigint"},
    },
    "bronze_ext_iso_country_map": {
        "columns": {
            "iso2": ["iso2", "country_code", "iso_2"],
            "iso3": ["iso3", "country_code_3", "iso_3"],
            "country_name": ["country_name", "country", "name"],
        },
        "casts": {},
    },
    "bronze_ext_world_bank_gdp_ppp": {
        "columns": {
            "iso3": ["iso3", "country_code", "code"],
            "snapshot_year": ["snapshot_year", "year"],
            "gdp_value": ["gdp_value", "value", "gdp_ppp"],
        },
        "casts": {"snapshot_year": "bigint", "gdp_value": "double"},
    },
    "bronze_ext_us_chamber_ip_index": {
        "columns": {
            "iso2": ["iso2", "country_code", "Country Code"],
            "snapshot_year": ["snapshot_year", "year"],
            "ip_score": ["ip_score", "Overall Score", "overall_score"],
        },
        "casts": {"snapshot_year": "bigint", "ip_score": "double"},
    },
    "bronze_ext_up_member_states": {
        "columns": {
            "jurisdiction_code": ["jurisdiction_code", "country_code", "state_code", "country"],
        },
        "casts": {},
    },
    "bronze_ext_kind_code_normalization_seed": {
        "columns": {
            "jurisdiction_code": ["jurisdiction_code"],
            "kind_code": ["kind_code"],
            "universal_stage": ["universal_stage"],
            "stage_multiplier": ["stage_multiplier"],
            "is_enforceable": ["is_enforceable"],
            "legal_status_proxy": ["legal_status_proxy"],
        },
        "casts": {"stage_multiplier": "double", "is_enforceable": "boolean"},
    },
    "bronze_ext_oecd_indicator_seed": {
        "columns": {
            "appln_id": ["appln_id"],
            "docdb_family_id": ["docdb_family_id"],
            "indicator_name": ["indicator_name", "metric_name"],
            "indicator_value": ["indicator_value", "metric_value", "value"],
            "snapshot_year": ["snapshot_year", "year"],
        },
        "casts": {
            "appln_id": "bigint",
            "docdb_family_id": "bigint",
            "indicator_value": "double",
            "snapshot_year": "bigint",
        },
    },
    "bronze_ext_cpc_coverage": {
        "columns": {},
        "casts": {},
    },
    "bronze_ext_cpc_ipc_weights": {
        "columns": {},
        "casts": {},
    },
}


def _relation_sql(source_path: Path) -> str:
    """Return a DuckDB relation SQL string for a supported raw source file."""
    suffix = source_path.suffix.lower()
    source = str(source_path)
    if suffix == ".parquet":
        return f"read_parquet('{source}')"
    if suffix in {".csv", ".gz"} or source_path.name.endswith(".csv.gz"):
        return f"read_csv_auto('{source}', header=true)"
    if suffix in {".json", ".jsonl"}:
        return f"read_json_auto('{source}')"
    raise ValueError(f"Unsupported source format for structured Bronze ingestion: {source_path}")


def _source_columns(source_path: Path) -> list[str]:
    """Return raw-source columns for a supported source file."""
    con = duckdb.connect()
    relation = _relation_sql(source_path)
    rows = con.execute(f"describe select * from {relation}").fetchall()
    return [row[0] for row in rows]


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    """Find the first source column matching the candidate list case-insensitively."""
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _typed_copy(source_path: Path, out_path: Path, overrides: dict[str, str]) -> int:
    """Land one raw table into Bronze parquet while preserving all columns and typing key fields."""
    columns = _source_columns(source_path)
    replacements: list[str] = []
    for column, cast_type in overrides.items():
        if column in columns:
            expr = f"try_cast({column} as {cast_type})" if cast_type in {"date", "timestamp"} else f"cast({column} as {cast_type})"
            replacements.append(f"{expr} as {column}")
    relation = _relation_sql(source_path)
    query = f"select * from {relation}"
    if replacements:
        query = f"select * replace ({', '.join(replacements)}) from {relation}"
    con = duckdb.connect()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"copy ({query}) to '{out_path}' (format parquet, compression zstd)")
    return parquet_row_count(out_path)


def _normalized_reference_copy(source_path: Path, out_path: Path, spec: dict[str, Any]) -> int:
    """Normalize a reference source into the canonical Bronze reference schema."""
    columns = _source_columns(source_path)
    selected_exprs: list[str] = []
    casts: dict[str, str] = spec.get("casts", {})
    for target, candidates in spec.get("columns", {}).items():
        source_column = _find_column(columns, candidates)
        if source_column is None:
            null_type = casts.get(target, "varchar")
            selected_exprs.append(f"null::{null_type} as {target}")
            continue
        cast_type = casts.get(target)
        if cast_type is None:
            selected_exprs.append(f"cast({source_column} as varchar) as {target}")
        elif cast_type == "date":
            selected_exprs.append(f"try_cast({source_column} as date) as {target}")
        else:
            selected_exprs.append(f"cast({source_column} as {cast_type}) as {target}")
    relation = _relation_sql(source_path)
    query = f"select {', '.join(selected_exprs)} from {relation}" if selected_exprs else f"select * from {relation}"
    con = duckdb.connect()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"copy ({query}) to '{out_path}' (format parquet, compression zstd)")
    return parquet_row_count(out_path)


def _ingest_structured_group(
    directory: Path,
    out_dir: Path,
    table_map: dict[str, list[str]],
    *,
    type_overrides: dict[str, dict[str, str]] | None = None,
    reference_specs: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[str], list[str], dict[str, int], list[str]]:
    """Land one structured source group into Bronze with typed or normalized table-specific logic."""
    inputs: list[str] = []
    outputs: list[str] = []
    metrics: dict[str, int] = {}
    warnings: list[str] = []
    type_overrides = type_overrides or {}
    reference_specs = reference_specs or {}

    for logical_name, stems in table_map.items():
        matches = candidate_files(directory, stems)
        if not matches:
            warnings.append(f"Skipped `{logical_name}` because no matching raw file was found.")
            continue
        source_path = matches[0]
        out_path = out_dir / f"{logical_name}.parquet"
        LOGGER.info("Landing structured Bronze table `%s` from `%s`", logical_name, source_path.name)
        if logical_name in reference_specs:
            row_count = _normalized_reference_copy(source_path, out_path, reference_specs[logical_name])
        else:
            row_count = _typed_copy(source_path, out_path, type_overrides.get(logical_name, {}))
        inputs.append(str(source_path))
        outputs.append(str(out_path))
        metrics[f"{logical_name}_rows"] = row_count
    return inputs, outputs, metrics, warnings


def ingest_structured_bronze(settings: BuildSettings) -> StageResult:
    """Generate typed Bronze parquet for PATSTAT, Register, and reference input families."""
    result = StageResult(
        stage="bronze",
        status="success",
        summary="Generated typed and source-aware Bronze parquet for PATSTAT, Register, and reference inputs.",
        methods=[
            "Applied table-specific typing for PATSTAT and Register key/date columns while preserving source columns.",
            "Normalized reference inputs to the canonical Bronze schemas required by Silver legal, market, and scope logic.",
        ],
        calculations=[
            "Bronze row counts reflect the landed bounded raw slice, not downstream family-first aggregates.",
        ],
        downstream_impacts=[
            "These Bronze parquet tables feed scope seeding, legal ledger reconstruction, market weighting, EP Register overlays, citation metrics, and OECD support layers.",
            "Typing errors or missing normalized reference columns here will propagate directly into Silver joins and point-in-time analytics.",
        ],
        doc_refs=[
            "docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md",
            "docs/data/patstat-schema.md",
            "docs/data/patstat-register-schema.md",
        ],
    )

    for directory, table_map, overrides, ref_specs in [
        (settings.bounded_patstat_dir, PATSTAT_TABLES, PATSTAT_TYPE_OVERRIDES, {}),
        (settings.bounded_register_dir, REGISTER_TABLES, REGISTER_TYPE_OVERRIDES, {}),
        (settings.bounded_refs_dir, REFERENCE_TABLES, {}, REFERENCE_NORMALIZATION_SPECS),
    ]:
        inputs, outputs, metrics, warnings = _ingest_structured_group(
            directory,
            settings.bronze_dir,
            table_map,
            type_overrides=overrides,
            reference_specs=ref_specs,
        )
        result.inputs.extend(inputs)
        result.outputs.extend(outputs)
        result.metrics.update(metrics)
        result.warnings.extend(warnings)

    result.metrics["bronze_total_row_count"] = sum(
        value for key, value in result.metrics.items() if key.endswith("_rows") and isinstance(value, int)
    )
    return result
