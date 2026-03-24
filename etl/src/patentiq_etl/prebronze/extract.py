from __future__ import annotations

from collections.abc import Iterable
import json
import logging
from pathlib import Path
import shutil
from typing import Any

import duckdb

from patentiq_etl.bronze.ingest_epab_fulltext import _iter_records
from patentiq_etl.bronze.ingest_uspto_fulltext import extract_publication_numbers, iter_publication_payloads
from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REFERENCE_TABLES, REGISTER_TABLES
from patentiq_etl.common.io import candidate_files, ensure_dir, parquet_row_count, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.tip_clients import (
    apply_year_window_filter,
    close_tip_client,
    get_epab_client,
    get_patstat_client,
    get_patstat_database_module,
    parquet_row_count as tip_parquet_row_count,
    query_to_dataframe,
    resolve_patstat_model,
    resolve_register_model,
    result_to_dataframe,
    write_dataframe_parquet,
)
from patentiq_etl.prebronze.uspto_odp import extract_uspto_odp_to_bronze


LOGGER = logging.getLogger(__name__)


DOC_REFS = [
    "docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md",
    "docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md",
    "docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md",
    "docs/data/patstat-schema.md",
    "docs/data/patstat-register-schema.md",
    "docs/data/uspto-full-text-schema.md",
    "docs/data/ep-full-text-publication-database-schema.md",
]


EPAB_DEFAULT_GROUPS = ("publication", "abstract", "claims")
EPAB_GROUP_NAME_MAP = {
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


def _relation_sql(source_path: Path) -> str:
    """Return the DuckDB relation SQL for a supported raw source file."""
    suffix = source_path.suffix.lower()
    source = str(source_path)
    if suffix == ".parquet":
        return f"read_parquet('{source}')"
    if suffix in {".csv", ".gz"} or source_path.name.endswith(".csv.gz"):
        return f"read_csv_auto('{source}', header=true)"
    if suffix in {".json", ".jsonl"}:
        return f"read_json_auto('{source}')"
    raise ValueError(f"Unsupported source format for pre-Bronze extraction: {source_path}")


def _source_columns(source_path: Path) -> list[str]:
    """Return the source columns of a supported raw source file."""
    con = duckdb.connect()
    rows = con.execute(f"describe select * from {_relation_sql(source_path)}").fetchall()
    return [row[0] for row in rows]


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    """Return the first case-insensitive column match from a candidate set."""
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        match = lowered.get(candidate.lower())
        if match:
            return match
    return None


def _citation_npl_column_from_parquet(path: Path) -> str | None:
    """Return the citation parquet column that carries NPL publication ids."""
    con = duckdb.connect()
    rows = con.execute("describe select * from read_parquet(?)", [str(path)]).fetchall()
    return _find_column([row[0] for row in rows], ["cited_npl_publn_id", "npl_publn_id"])


def _resolve_source(directory: Path, logical_name: str, table_map: dict[str, list[str]]) -> Path | None:
    """Resolve the first matching source file for one logical table."""
    matches = candidate_files(directory, table_map[logical_name])
    return matches[0] if matches else None


def _copy_query_to_parquet(query: str, out_path: Path) -> int:
    """Materialize one DuckDB query to parquet and return the written row count."""
    con = duckdb.connect()
    ensure_dir(out_path.parent)
    con.execute(f"copy ({query}) to '{out_path}' (format parquet, compression zstd)")
    return parquet_row_count(out_path)


def _write_seed(query: str, out_path: Path) -> int:
    """Write one seed parquet artifact and return the row count."""
    return _copy_query_to_parquet(query, out_path)


def _epab_selected_groups(settings: BuildSettings) -> list[str]:
    """Return the configured EPAB groups to materialize."""
    configured = (settings.execution or {}).get("epab_result_groups", list(EPAB_DEFAULT_GROUPS))
    if isinstance(configured, str):
        values = [value.strip() for value in configured.split(",") if value.strip()]
    else:
        values = [str(value).strip() for value in configured if str(value).strip()]
    selected = [value for value in values if value in EPAB_GROUP_NAME_MAP]
    return selected or list(EPAB_DEFAULT_GROUPS)


def _epab_query_batch_size(settings: BuildSettings) -> int:
    """Return the publication-number batch size used to build EPAB queries."""
    return max(1, int((settings.execution or {}).get("epab_query_batch_size", 1000)))


def _epab_iterator_batch_size(settings: BuildSettings) -> int:
    """Return the EPAB iterator batch size used per query."""
    return max(1, int((settings.execution or {}).get("epab_iterator_batch_size", 5000)))


def _epab_batch_date_range(batch_df) -> str | None:
    """Return a compact EPAB date-range filter for one batch when dates are available."""
    import pandas as pd

    if "publication_date" not in batch_df.columns:
        return None
    values = pd.to_datetime(batch_df["publication_date"], errors="coerce").dropna()
    if values.empty:
        return None
    start = values.min().strftime("%Y%m%d")
    end = values.max().strftime("%Y%m%d")
    return start if start == end else f"{start}-{end}"


def _filter_epab_publication_df(df, allowed_pairs: set[tuple[str, str]]):
    """Return only EPAB publication rows matching the bounded publication number/kind pairs."""
    import pandas as pd

    if df.empty or not allowed_pairs:
        return df
    possible_number = next((col for col in df.columns if col.lower().endswith("publication.number") or col.lower().endswith("number")), None)
    possible_kind = next((col for col in df.columns if col.lower().endswith("publication.kind") or col.lower().endswith("kind")), None)
    if not possible_number or not possible_kind:
        return df
    allowed_keys = pd.Index([f"{number}|{kind}" for number, kind in sorted(allowed_pairs)])
    keys = df[possible_number].astype(str) + "|" + df[possible_kind].astype(str)
    return df.loc[keys.isin(allowed_keys)].reset_index(drop=True)


def _extract_epab_tip_groups(settings: BuildSettings, seed_df, result: StageResult) -> dict[str, Any]:
    """Materialize selected EPAB groups for the bounded publication seed using iterator-based batching."""
    import pandas as pd

    selected_groups = _epab_selected_groups(settings)
    query_batch_size = _epab_query_batch_size(settings)
    iterator_batch_size = _epab_iterator_batch_size(settings)
    group_frames: dict[str, list[Any]] = {group: [] for group in selected_groups}
    allowed_pairs = {
        (str(row["publication_number"]), str(row["publication_kind"]))
        for _, row in seed_df.iterrows()
        if row["publication_number"] is not None and row["publication_kind"] is not None
    }
    result.metrics["epab_selected_group_count"] = len(selected_groups)
    result.metrics["epab_query_batch_size"] = query_batch_size
    result.metrics["epab_iterator_batch_size"] = iterator_batch_size

    epab = None
    try:
        epab = get_epab_client(settings.tip_env)
        for start in range(0, len(seed_df.index), query_batch_size):
            batch = seed_df.iloc[start : start + query_batch_size]
            numbers = [str(value) for value in batch["publication_number"].dropna().tolist()]
            kinds = sorted({str(value) for value in batch["publication_kind"].dropna().tolist()})
            if not numbers:
                continue
            q = epab.query_publication(
                number=numbers,
                kind_code=kinds or None,
                date=_epab_batch_date_range(batch),
            )
            for group in selected_groups:
                try:
                    for payload in q.iterator(fields=[group], output_type="dataframe", batch_size=iterator_batch_size):
                        frame = result_to_dataframe(payload)
                        if not frame.empty:
                            group_frames[group].append(frame)
                except Exception as exc:  # pragma: no cover - requires TIP runtime
                    result.warnings.append(f"EPAB group `{group}` could not be materialized from TIP: {exc}")

        merged: dict[str, Any] = {}
        for group, frames in group_frames.items():
            if not frames:
                continue
            df = pd.concat(frames, ignore_index=True)
            if group == "publication":
                df = _filter_epab_publication_df(df, allowed_pairs)
            merged[group] = df
        return merged
    finally:
        close_tip_client(epab)


def _copy_if_exists(source_path: Path | None, out_path: Path, metrics_key: str, result: StageResult) -> None:
    """Copy a full reference/support file into the bounded raw area when available."""
    if source_path is None:
        result.warnings.append(f"Skipped `{metrics_key}` because no source file was found.")
        return
    row_count = _copy_query_to_parquet(f"select * from {_relation_sql(source_path)}", out_path)
    result.inputs.append(str(source_path))
    result.outputs.append(str(out_path))
    result.metrics[f"{metrics_key}_bounded_count"] = row_count


def _string_seed_list(seed_path: Path, column: str) -> set[str]:
    """Return a set of non-empty string values from a seed parquet column."""
    if not seed_path.exists():
        return set()
    con = duckdb.connect()
    rows = con.execute(
        f"select distinct cast({column} as varchar) from read_parquet(?) where {column} is not null",
        [str(seed_path)],
    ).fetchall()
    return {row[0] for row in rows if row[0]}


def _table_count(path: Path) -> int:
    """Return the row count of a source table without extracting it."""
    con = duckdb.connect()
    return int(con.execute(f"select count(*) from {_relation_sql(path)}").fetchone()[0])


def _seed_patstat_scope(settings: BuildSettings, result: StageResult) -> dict[str, Path]:
    """Build the bounded PATSTAT seed universe for applications, families, publications, and persons."""
    appln_path = _resolve_source(settings.raw_patstat_dir, "bronze_patstat_appln", PATSTAT_TABLES)
    publn_path = _resolve_source(settings.raw_patstat_dir, "bronze_patstat_pat_publn", PATSTAT_TABLES)
    pers_appln_path = _resolve_source(settings.raw_patstat_dir, "bronze_patstat_pers_appln", PATSTAT_TABLES)
    tech_path = _resolve_source(settings.raw_patstat_dir, "bronze_patstat_appln_techn_field", PATSTAT_TABLES)
    ipc_path = _resolve_source(settings.raw_patstat_dir, "bronze_patstat_appln_ipc", PATSTAT_TABLES)
    ref_path = _resolve_source(settings.raw_refs_dir, "bronze_ref_techn_field_ipc", REFERENCE_TABLES)

    if appln_path is None or publn_path is None:
        result.status = "failed"
        result.warnings.append("PATSTAT application and publication sources are required for bounded raw extraction.")
        return {}

    ensure_dir(settings.bounded_seed_dir)
    selected_fields_sql = ", ".join(f"'{field}'" for field in settings.selected_wipo_fields)
    appln_columns = _source_columns(appln_path)
    appln_id_col = _find_column(appln_columns, ["appln_id"])
    docdb_family_col = _find_column(appln_columns, ["docdb_family_id"])
    appln_auth_col = _find_column(appln_columns, ["appln_auth"])
    appln_nr_col = _find_column(appln_columns, ["appln_nr", "appln_nr_epodoc", "appln_nr_original"])

    if appln_id_col is None or docdb_family_col is None:
        result.status = "failed"
        result.warnings.append("PATSTAT application source is missing appln_id or docdb_family_id.")
        return {}

    if tech_path is not None:
        tech_columns = _source_columns(tech_path)
        tech_appln_col = _find_column(tech_columns, ["appln_id"])
        tech_field_col = _find_column(tech_columns, ["techn_field", "wipo_industry_code"])
        if tech_appln_col and tech_field_col:
            seed_appln_query = f"""
                select
                    cast({tech_appln_col} as bigint) as appln_id,
                    cast({tech_field_col} as varchar) as wipo_field
                from {_relation_sql(tech_path)}
                where cast({tech_field_col} as varchar) in ({selected_fields_sql})
            """
        else:
            tech_path = None

    if tech_path is None:
        if ipc_path is None or ref_path is None:
            result.status = "failed"
            result.warnings.append("PATSTAT scope seed requires technology-field source or IPC fallback concordance.")
            return {}
        ipc_columns = _source_columns(ipc_path)
        ref_columns = _source_columns(ref_path)
        ipc_appln_col = _find_column(ipc_columns, ["appln_id"])
        ipc_symbol_col = _find_column(ipc_columns, ["ipc_class_symbol"])
        ref_ipc_col = _find_column(ref_columns, ["ipc_subclass", "ipc_maingroup_symbol", "ipc_code"])
        ref_field_col = _find_column(ref_columns, ["techn_field", "wipo_industry_code"])
        if None in {ipc_appln_col, ipc_symbol_col, ref_ipc_col, ref_field_col}:
            result.status = "failed"
            result.warnings.append("IPC fallback seed could not find appln_id, ipc symbol, or WIPO field columns.")
            return {}
        seed_appln_query = f"""
            select distinct
                cast(i.{ipc_appln_col} as bigint) as appln_id,
                cast(r.{ref_field_col} as varchar) as wipo_field
            from {_relation_sql(ipc_path)} i
            join {_relation_sql(ref_path)} r
              on regexp_replace(substr(cast(i.{ipc_symbol_col} as varchar), 1, length(cast(r.{ref_ipc_col} as varchar))), '[^A-Za-z0-9]', '', 'g')
                 = regexp_replace(cast(r.{ref_ipc_col} as varchar), '[^A-Za-z0-9]', '', 'g')
            where cast(r.{ref_field_col} as varchar) in ({selected_fields_sql})
        """

    seed_appln_path = settings.bounded_seed_dir / "seed_appln_ids.parquet"
    seed_family_path = settings.bounded_seed_dir / "seed_family_ids.parquet"
    seed_publn_path = settings.bounded_seed_dir / "seed_publn_ids.parquet"
    seed_person_path = settings.bounded_seed_dir / "seed_person_ids.parquet"
    seed_ep_appln_path = settings.bounded_seed_dir / "seed_ep_appln_ids.parquet"
    seed_us_publn_path = settings.bounded_seed_dir / "seed_us_publication_numbers.parquet"
    seed_ep_publn_path = settings.bounded_seed_dir / "seed_ep_publication_numbers.parquet"
    seed_field_family_path = settings.bounded_seed_dir / "seed_family_field_counts.parquet"

    result.metrics["patstat_appln_raw_count"] = _table_count(appln_path)
    result.metrics["patstat_publn_raw_count"] = _table_count(publn_path)
    if pers_appln_path is not None:
        result.metrics["patstat_pers_appln_raw_count"] = _table_count(pers_appln_path)

    result.metrics["seed_appln_count"] = _write_seed(
        f"select distinct appln_id, wipo_field from ({seed_appln_query}) where appln_id is not null",
        seed_appln_path,
    )
    result.outputs.append(str(seed_appln_path))

    result.metrics["seed_family_count"] = _write_seed(
        f"""
        select distinct
            cast(a.{docdb_family_col} as bigint) as docdb_family_id
        from {_relation_sql(appln_path)} a
        join read_parquet('{seed_appln_path}') s
          on cast(a.{appln_id_col} as bigint) = s.appln_id
        where a.{docdb_family_col} is not null
        """,
        seed_family_path,
    )
    result.outputs.append(str(seed_family_path))

    publn_columns = _source_columns(publn_path)
    publn_id_col = _find_column(publn_columns, ["pat_publn_id"])
    publn_appln_col = _find_column(publn_columns, ["appln_id"])
    publn_auth_col = _find_column(publn_columns, ["publn_auth"])
    publn_nr_col = _find_column(publn_columns, ["publn_nr", "publn_nr_epodoc"])
    publn_kind_col = _find_column(publn_columns, ["publn_kind"])
    if None in {publn_id_col, publn_appln_col}:
        result.status = "failed"
        result.warnings.append("PATSTAT publication source is missing pat_publn_id or appln_id.")
        return {}

    publication_number_expr = (
        f"concat(coalesce(cast({publn_auth_col} as varchar), ''), coalesce(cast({publn_nr_col} as varchar), ''), "
        f"coalesce(cast({publn_kind_col} as varchar), ''))"
        if publn_auth_col and publn_nr_col and publn_kind_col
        else "null::varchar"
    )
    publn_auth_expr = f"cast({publn_auth_col} as varchar)" if publn_auth_col else "null::varchar"
    publn_nr_expr = f"cast({publn_nr_col} as varchar)" if publn_nr_col else "null::varchar"
    publn_kind_expr = f"cast({publn_kind_col} as varchar)" if publn_kind_col else "null::varchar"
    publn_date_col = _find_column(publn_columns, ["publn_date"])
    publn_date_expr = f"try_cast({publn_date_col} as date)" if publn_date_col else "null::date"
    result.metrics["seed_publn_count"] = _write_seed(
        f"""
        select distinct
            cast(p.{publn_id_col} as bigint) as pat_publn_id,
            cast(p.{publn_appln_col} as bigint) as appln_id,
            {publication_number_expr} as publication_number_full,
            {publn_auth_expr} as publn_auth,
            {publn_nr_expr} as publication_number,
            {publn_kind_expr} as publication_kind,
            {publn_date_expr} as publication_date
        from {_relation_sql(publn_path)} p
        join read_parquet('{seed_appln_path}') s
          on cast(p.{publn_appln_col} as bigint) = s.appln_id
        where p.{publn_id_col} is not null
        """,
        seed_publn_path,
    )
    result.outputs.append(str(seed_publn_path))

    if pers_appln_path is not None:
        pers_appln_columns = _source_columns(pers_appln_path)
        pers_appln_appln_col = _find_column(pers_appln_columns, ["appln_id"])
        person_id_col = _find_column(pers_appln_columns, ["person_id"])
        if pers_appln_appln_col and person_id_col:
            result.metrics["seed_person_count"] = _write_seed(
                f"""
                select distinct
                    cast({person_id_col} as bigint) as person_id
                from {_relation_sql(pers_appln_path)}
                where cast({pers_appln_appln_col} as bigint) in (
                    select appln_id from read_parquet('{seed_appln_path}')
                )
                and {person_id_col} is not null
                """,
                seed_person_path,
            )
            result.outputs.append(str(seed_person_path))

    if appln_auth_col is not None:
        result.metrics["seed_ep_appln_count"] = _write_seed(
            f"""
            select distinct
                cast({appln_id_col} as bigint) as appln_id
            from {_relation_sql(appln_path)}
            where cast({appln_id_col} as bigint) in (
                select appln_id from read_parquet('{seed_appln_path}')
            )
              and upper(cast({appln_auth_col} as varchar)) = 'EP'
            """,
            seed_ep_appln_path,
        )
        result.outputs.append(str(seed_ep_appln_path))

    if appln_nr_col is not None and appln_auth_col is not None:
        appln_number_expr = (
            f"concat(coalesce(cast({appln_auth_col} as varchar), ''), coalesce(cast({appln_nr_col} as varchar), ''))"
        )
        ep_appln_number_path = settings.bounded_seed_dir / "seed_ep_application_numbers.parquet"
        result.metrics["seed_ep_application_number_count"] = _write_seed(
            f"""
            select distinct
                {appln_number_expr} as application_number_full
            from {_relation_sql(appln_path)}
            where cast({appln_id_col} as bigint) in (
                select appln_id from read_parquet('{seed_ep_appln_path}')
            )
            """,
            ep_appln_number_path,
        )
        result.outputs.append(str(ep_appln_number_path))

    if publn_auth_col is not None:
        result.metrics["seed_us_publication_count"] = _write_seed(
            f"""
            select distinct publication_number_full
            from read_parquet('{seed_publn_path}')
            where upper(coalesce(publn_auth, '')) = 'US'
              and publication_number_full is not null
            """,
            seed_us_publn_path,
        )
        result.outputs.append(str(seed_us_publn_path))
        result.metrics["seed_ep_publication_count"] = _write_seed(
            f"""
            select distinct publication_number_full
            from read_parquet('{seed_publn_path}')
            where upper(coalesce(publn_auth, '')) = 'EP'
              and publication_number_full is not null
            """,
            seed_ep_publn_path,
        )
        result.outputs.append(str(seed_ep_publn_path))

    result.metrics["seed_field_family_count_rows"] = _write_seed(
        f"""
        select
            s.wipo_field,
            count(distinct cast(a.{docdb_family_col} as bigint)) as family_count
        from {_relation_sql(appln_path)} a
        join read_parquet('{seed_appln_path}') s
          on cast(a.{appln_id_col} as bigint) = s.appln_id
        group by 1
        """,
        seed_field_family_path,
    )
    result.outputs.append(str(seed_field_family_path))

    field_counts = duckdb.connect().execute(
        "select wipo_field, family_count from read_parquet(?)",
        [str(seed_field_family_path)],
    ).fetchall()
    for field_name, family_count in field_counts:
        result.metrics[f"seed_family_count__{field_name}"] = int(family_count)

    result.inputs.extend(str(path) for path in [appln_path, publn_path] if path is not None)
    if pers_appln_path is not None:
        result.inputs.append(str(pers_appln_path))
    if tech_path is not None:
        result.inputs.append(str(tech_path))
    if ipc_path is not None:
        result.inputs.append(str(ipc_path))
    if ref_path is not None:
        result.inputs.append(str(ref_path))

    return {
        "seed_appln_ids": seed_appln_path,
        "seed_family_ids": seed_family_path,
        "seed_publn_ids": seed_publn_path,
        "seed_person_ids": seed_person_path,
        "seed_ep_appln_ids": seed_ep_appln_path,
        "seed_us_publication_numbers": seed_us_publn_path,
        "seed_ep_publication_numbers": seed_ep_publn_path,
    }


def _extract_patstat_bounded_raw(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Extract bounded PATSTAT raw slices for Bronze landing."""
    appln_seed = seeds.get("seed_appln_ids")
    family_seed = seeds.get("seed_family_ids")
    publn_seed = seeds.get("seed_publn_ids")
    person_seed = seeds.get("seed_person_ids")
    if appln_seed is None or family_seed is None or publn_seed is None:
        result.status = "failed"
        result.warnings.append("PATSTAT bounded extraction could not start because the core seeds are missing.")
        return

    rule_map = {
        "bronze_patstat_appln": ("family", ["docdb_family_id"]),
        "bronze_patstat_appln_title": ("appln", ["appln_id"]),
        "bronze_patstat_appln_abstr": ("appln", ["appln_id"]),
        "bronze_patstat_appln_prior": ("appln", ["appln_id"]),
        "bronze_patstat_person": ("person", ["person_id"]),
        "bronze_patstat_pers_appln": ("appln", ["appln_id"]),
        "bronze_patstat_appln_ipc": ("appln", ["appln_id"]),
        "bronze_patstat_pat_publn": ("appln", ["appln_id"]),
        "bronze_patstat_appln_contn": ("appln", ["appln_id", "parent_appln_id"]),
        "bronze_patstat_appln_cpc": ("appln", ["appln_id"]),
        "bronze_patstat_appln_techn_field": ("appln", ["appln_id"]),
        "bronze_patstat_inpadoc_legal_event": ("appln", ["appln_id"]),
        "bronze_patstat_citation": ("publn", ["pat_publn_id"]),
        "bronze_patstat_docdb_fam_citn": ("family", ["docdb_family_id"]),
    }

    seed_config = {
        "appln": (appln_seed, "appln_id"),
        "family": (family_seed, "docdb_family_id"),
        "publn": (publn_seed, "pat_publn_id"),
        "person": (person_seed, "person_id"),
    }

    for logical_name in PATSTAT_TABLES:
        source_path = _resolve_source(settings.raw_patstat_dir, logical_name, PATSTAT_TABLES)
        if source_path is None:
            result.warnings.append(f"Skipped `{logical_name}` bounded extraction because no source file was found.")
            continue
        out_path = settings.bounded_patstat_dir / f"{PATSTAT_TABLES[logical_name][0]}.parquet"
        result.metrics[f"{logical_name}_raw_count"] = _table_count(source_path)

        if logical_name == "bronze_patstat_npl_publn":
            citation_out = settings.bounded_patstat_dir / f"{PATSTAT_TABLES['bronze_patstat_citation'][0]}.parquet"
            if not citation_out.exists():
                result.warnings.append("Skipped bounded NPL extraction because bounded citation rows were not produced.")
                continue
            columns = _source_columns(source_path)
            npl_col = _find_column(columns, ["cited_npl_publn_id", "npl_publn_id"])
            if npl_col is None:
                result.warnings.append("Skipped bounded NPL extraction because no NPL citation column is available.")
                continue
            citation_npl_col = _citation_npl_column_from_parquet(citation_out)
            if citation_npl_col is None:
                result.warnings.append("Skipped bounded NPL extraction because bounded citation output has no NPL citation column.")
                continue
            row_count = _copy_query_to_parquet(
                f"""
                select *
                from {_relation_sql(source_path)}
                where cast({npl_col} as bigint) in (
                    select distinct cast({citation_npl_col} as bigint)
                    from read_parquet('{citation_out}')
                    where {citation_npl_col} is not null
                )
                """,
                out_path,
            )
        elif logical_name == "bronze_ref_legal_event_code":
            row_count = _copy_query_to_parquet(f"select * from {_relation_sql(source_path)}", out_path)
        else:
            seed_type, candidates = rule_map.get(logical_name, ("appln", ["appln_id"]))
            seed_path, seed_column = seed_config[seed_type]
            if seed_path is None or not seed_path.exists():
                result.warnings.append(f"Skipped `{logical_name}` because the `{seed_type}` seed was unavailable.")
                continue
            columns = _source_columns(source_path)
            filter_column = _find_column(columns, candidates)
            if filter_column is None:
                result.warnings.append(f"Skipped `{logical_name}` because no filter column matched {candidates}.")
                continue
            row_count = _copy_query_to_parquet(
                f"""
                select *
                from {_relation_sql(source_path)}
                where cast({filter_column} as bigint) in (
                    select distinct {seed_column} from read_parquet('{seed_path}')
                )
                """,
                out_path,
            )

        result.inputs.append(str(source_path))
        result.outputs.append(str(out_path))
        result.metrics[f"{logical_name}_bounded_count"] = row_count

    citation_out = settings.bounded_patstat_dir / f"{PATSTAT_TABLES['bronze_patstat_citation'][0]}.parquet"
    if citation_out.exists():
        con = duckdb.connect()
        citation_metrics = con.execute(
            f"""
            select
                count(*) as edge_count,
                count(distinct pat_publn_id) as source_publn_count,
                count(distinct cited_pat_publn_id) as cited_publn_count,
                count(distinct case when cited_pat_publn_id is not null
                    and cast(cited_pat_publn_id as bigint) not in (
                        select pat_publn_id from read_parquet('{publn_seed}')
                    )
                then cast(cited_pat_publn_id as bigint) end) as ghost_target_count
            from read_parquet('{citation_out}')
            """
        ).fetchone()
        result.metrics["bounded_citation_edge_count"] = int(citation_metrics[0] or 0)
        result.metrics["bounded_citation_source_publication_count"] = int(citation_metrics[1] or 0)
        result.metrics["bounded_citation_cited_publication_count"] = int(citation_metrics[2] or 0)
        result.metrics["bounded_citation_ghost_target_count"] = int(citation_metrics[3] or 0)


def _write_dynamic_filtered_register(
    source_path: Path,
    out_path: Path,
    *,
    id_seed_path: Path | None = None,
    appln_seed_path: Path | None = None,
    event_seed_path: Path | None = None,
    step_seed_path: Path | None = None,
) -> int | None:
    """Filter one Register source table using the most appropriate bounded seed available."""
    columns = _source_columns(source_path)
    id_col = _find_column(columns, ["id"])
    appln_col = _find_column(columns, ["appln_id"])
    event_col = _find_column(columns, ["event_code"])
    step_col = _find_column(columns, ["step_id"])

    if appln_seed_path is not None and appln_col is not None:
        return _copy_query_to_parquet(
            f"""
            select *
            from {_relation_sql(source_path)}
            where cast({appln_col} as bigint) in (
                select appln_id from read_parquet('{appln_seed_path}')
            )
            """,
            out_path,
        )
    if id_seed_path is not None and id_col is not None:
        return _copy_query_to_parquet(
            f"""
            select *
            from {_relation_sql(source_path)}
            where cast({id_col} as bigint) in (
                select id from read_parquet('{id_seed_path}')
            )
            """,
            out_path,
        )
    if event_seed_path is not None and event_col is not None:
        return _copy_query_to_parquet(
            f"""
            select *
            from {_relation_sql(source_path)}
            where cast({event_col} as varchar) in (
                select event_code from read_parquet('{event_seed_path}')
            )
            """,
            out_path,
        )
    if step_seed_path is not None and step_col is not None:
        return _copy_query_to_parquet(
            f"""
            select *
            from {_relation_sql(source_path)}
            where cast({step_col} as bigint) in (
                select step_id from read_parquet('{step_seed_path}')
            )
            """,
            out_path,
        )
    return None


def _extract_register_bounded_raw(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Extract bounded PATSTAT Register slices anchored to the in-scope EP application universe."""
    ep_appln_seed = seeds.get("seed_ep_appln_ids")
    if ep_appln_seed is None or not ep_appln_seed.exists():
        result.warnings.append("Skipped bounded Register extraction because no in-scope EP application seed was generated.")
        return

    reg101_source = _resolve_source(settings.raw_register_dir, "bronze_reg101_appln", REGISTER_TABLES)
    if reg101_source is None:
        result.warnings.append("Skipped bounded Register extraction because reg101_appln is missing.")
        return

    reg101_out = settings.bounded_register_dir / f"{REGISTER_TABLES['bronze_reg101_appln'][0]}.parquet"
    reg101_rows = _write_dynamic_filtered_register(reg101_source, reg101_out, appln_seed_path=ep_appln_seed)
    if reg101_rows is None:
        result.warnings.append("reg101_appln could not be bounded because appln_id was unavailable.")
        return
    result.inputs.append(str(reg101_source))
    result.outputs.append(str(reg101_out))
    result.metrics["bronze_reg101_appln_raw_count"] = _table_count(reg101_source)
    result.metrics["bronze_reg101_appln_bounded_count"] = reg101_rows

    reg101_id_seed = settings.bounded_seed_dir / "seed_reg101_ids.parquet"
    _write_seed(
        f"select distinct cast(id as bigint) as id from read_parquet('{reg101_out}') where id is not null",
        reg101_id_seed,
    )
    result.outputs.append(str(reg101_id_seed))
    result.metrics["seed_reg101_id_count"] = parquet_row_count(reg101_id_seed)

    reg201_event_seed = settings.bounded_seed_dir / "seed_register_step_ids.parquet"
    reg301_event_seed = settings.bounded_seed_dir / "seed_register_event_codes.parquet"
    reg701_id_seed = settings.bounded_seed_dir / "seed_reg701_ids.parquet"
    reg731_event_seed = settings.bounded_seed_dir / "seed_reg731_event_codes.parquet"

    for logical_name in REGISTER_TABLES:
        if logical_name == "bronze_reg101_appln":
            continue
        source_path = _resolve_source(settings.raw_register_dir, logical_name, REGISTER_TABLES)
        if source_path is None:
            result.warnings.append(f"Skipped `{logical_name}` bounded extraction because no source file was found.")
            continue
        out_path = settings.bounded_register_dir / f"{REGISTER_TABLES[logical_name][0]}.parquet"
        result.metrics[f"{logical_name}_raw_count"] = _table_count(source_path)

        row_count = None
        if logical_name in {"bronze_reg403_appln_status", "bronze_reg701_appln", "bronze_reg741_appln_status"}:
            row_count = _write_dynamic_filtered_register(
                source_path,
                out_path,
                id_seed_path=reg101_id_seed,
                appln_seed_path=ep_appln_seed,
            )
        elif logical_name in {"bronze_reg202_proc_step_text", "bronze_reg203_proc_step_date"}:
            row_count = _write_dynamic_filtered_register(source_path, out_path, step_seed_path=reg201_event_seed)
        elif logical_name in {"bronze_reg402_event_text", "bronze_reg742_event_text"}:
            event_seed = reg731_event_seed if reg731_event_seed.exists() else reg301_event_seed
            row_count = _write_dynamic_filtered_register(source_path, out_path, event_seed_path=event_seed)
        elif logical_name == "bronze_reg731_event_data":
            id_seed = reg701_id_seed if reg701_id_seed.exists() else reg101_id_seed
            row_count = _write_dynamic_filtered_register(source_path, out_path, id_seed_path=id_seed)
        else:
            row_count = _write_dynamic_filtered_register(source_path, out_path, id_seed_path=reg101_id_seed)

        if row_count is None:
            result.warnings.append(f"Skipped `{logical_name}` bounded extraction because no usable anchor column was found.")
            continue

        result.inputs.append(str(source_path))
        result.outputs.append(str(out_path))
        result.metrics[f"{logical_name}_bounded_count"] = row_count

        if logical_name == "bronze_reg201_proc_step":
            _write_seed(
                f"select distinct cast(step_id as bigint) as step_id from read_parquet('{out_path}') where step_id is not null",
                reg201_event_seed,
            )
            result.outputs.append(str(reg201_event_seed))
            result.metrics["seed_register_step_id_count"] = parquet_row_count(reg201_event_seed)
        elif logical_name == "bronze_reg301_event_data":
            _write_seed(
                f"select distinct cast(event_code as varchar) as event_code from read_parquet('{out_path}') where event_code is not null",
                reg301_event_seed,
            )
            result.outputs.append(str(reg301_event_seed))
            result.metrics["seed_register_event_code_count"] = parquet_row_count(reg301_event_seed)
        elif logical_name == "bronze_reg701_appln":
            _write_seed(
                f"select distinct cast(id as bigint) as id from read_parquet('{out_path}') where id is not null",
                reg701_id_seed,
            )
            result.outputs.append(str(reg701_id_seed))
            result.metrics["seed_reg701_id_count"] = parquet_row_count(reg701_id_seed)
        elif logical_name == "bronze_reg731_event_data":
            _write_seed(
                f"select distinct cast(event_code as varchar) as event_code from read_parquet('{out_path}') where event_code is not null",
                reg731_event_seed,
            )
            result.outputs.append(str(reg731_event_seed))
            result.metrics["seed_reg731_event_code_count"] = parquet_row_count(reg731_event_seed)


def _extract_uspto_bounded_raw(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Select only the in-scope USPTO raw XML payloads needed for Bronze parsing."""
    publication_seed = seeds.get("seed_us_publication_numbers")
    if publication_seed is None or not publication_seed.exists():
        result.warnings.append("Skipped bounded USPTO selection because no in-scope US publication seed was generated.")
        return

    publication_numbers = _string_seed_list(publication_seed, "publication_number_full")
    xml_files = list(settings.raw_uspto_dir.glob("*.XML")) + list(settings.raw_uspto_dir.glob("*.xml"))
    result.metrics["uspto_source_xml_count"] = len(xml_files)
    matched_count = 0
    for xml_path in xml_files:
        file_publications = extract_publication_numbers(xml_path)
        if publication_numbers.intersection(file_publications):
            ensure_dir(settings.bounded_uspto_dir)
            shutil.copy2(xml_path, settings.bounded_uspto_dir / xml_path.name)
            matched_count += 1

    result.metrics["uspto_bounded_xml_count"] = matched_count
    result.metrics["uspto_unmatched_seed_count"] = max(len(publication_numbers) - len({num for path in xml_files for num in extract_publication_numbers(path) if num in publication_numbers}), 0)
    result.inputs.extend(str(path) for path in xml_files[: min(len(xml_files), 20)])
    result.outputs.append(str(settings.bounded_uspto_dir))


def _extract_epab_bounded_raw(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Select only the in-scope EPAB raw records needed for Bronze parsing."""
    publication_seed = seeds.get("seed_ep_publication_numbers")
    publication_numbers = _string_seed_list(publication_seed, "publication_number_full") if publication_seed else set()
    if not publication_numbers:
        result.warnings.append("Skipped bounded EPAB selection because no in-scope EP publication seed was generated.")
        return

    records = _iter_records(settings.raw_epab_dir)
    result.metrics["epab_source_record_count"] = len(records)
    bounded_records: list[dict[str, Any]] = []
    for record in records:
        publication = record.get("publication") or {}
        publication_number_full = publication.get("publication_number_full")
        if not publication_number_full:
            authority = publication.get("authority") or ""
            number = publication.get("number") or ""
            kind = publication.get("kind") or ""
            publication_number_full = f"{authority}{number}{kind}" if authority or number or kind else None
        if publication_number_full and publication_number_full in publication_numbers:
            bounded_records.append(record)

    ensure_dir(settings.bounded_epab_dir)
    out_path = settings.bounded_epab_dir / "epab_bounded.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for record in bounded_records:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")

    result.inputs.append(str(settings.raw_epab_dir))
    result.outputs.append(str(out_path))
    result.metrics["epab_bounded_record_count"] = len(bounded_records)
    result.metrics["epab_unmatched_seed_count"] = max(len(publication_numbers) - len(bounded_records), 0)


def _copy_reference_inputs(settings: BuildSettings, result: StageResult) -> None:
    """Copy small reference and OECD support tables in full into the bounded raw area."""
    for logical_name in REFERENCE_TABLES:
        source_path = _resolve_source(settings.raw_refs_dir, logical_name, REFERENCE_TABLES)
        out_path = settings.bounded_refs_dir / f"{REFERENCE_TABLES[logical_name][0]}.parquet"
        _copy_if_exists(source_path, out_path, logical_name, result)


def _write_tip_dataframe(df, out_path: Path, metrics_key: str, result: StageResult) -> None:
    """Write one TIP query result DataFrame to parquet and record standard stage metadata."""
    row_count = write_dataframe_parquet(df, out_path)
    result.outputs.append(str(out_path))
    result.metrics[f"{metrics_key}_bounded_count"] = row_count


def _register_existing_seed(path: Path, metric_key: str, result: StageResult) -> int:
    """Record one already-materialized seed parquet without regenerating it."""
    row_count = tip_parquet_row_count(path)
    result.outputs.append(str(path))
    result.metrics[metric_key] = row_count
    return row_count


def _write_tip_seed_dataframe(df, path: Path, metric_key: str, result: StageResult) -> int:
    """Write one TIP seed DataFrame and register its standard metrics/output path."""
    row_count = write_dataframe_parquet(df, path)
    result.outputs.append(str(path))
    result.metrics[metric_key] = row_count
    return row_count


def _seed_patstat_scope_tip(
    settings: BuildSettings,
    result: StageResult,
    *,
    seed_dir: Path | None = None,
    requested_seed_keys: set[str] | None = None,
):
    """Build the bounded PATSTAT seed universe from TIP clients."""
    from sqlalchemy import func

    patstat = None
    try:
        patstat, db = get_patstat_client(settings.tip_env)
        database_module = get_patstat_database_module()
        TLS201 = resolve_patstat_model(database_module, "bronze_patstat_appln")
        TLS211 = resolve_patstat_model(database_module, "bronze_patstat_pat_publn")
        TLS207 = resolve_patstat_model(database_module, "bronze_patstat_pers_appln")
        TLS230 = resolve_patstat_model(database_module, "bronze_patstat_appln_techn_field")
        TLS901 = resolve_patstat_model(database_module, "bronze_ref_techn_field_ipc")

        if None in {TLS201, TLS211, TLS230, TLS901}:
            result.status = "failed"
            result.warnings.append("TIP PATSTAT seed extraction requires TLS201, TLS211, TLS230, and TLS901 models.")
            return {}

        seed_dir = ensure_dir(seed_dir or settings.bounded_seed_dir)
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
        requested = set(requested_seed_keys or seed_paths.keys())
        seed_appln_q = (
            db.query(
                TLS230.appln_id.label("appln_id"),
                TLS901.techn_field.label("wipo_field"),
            )
            .join(TLS201, TLS230.appln_id == TLS201.appln_id)
            .join(TLS901, TLS230.techn_field_nr == TLS901.techn_field_nr)
            .filter(TLS901.techn_field.in_(settings.selected_wipo_fields))
            .distinct()
        )
        seed_appln_q = apply_year_window_filter(
            seed_appln_q,
            TLS201,
            settings.year_window_start,
            settings.year_window_end,
        )
        if "seed_appln_ids" in requested:
            seed_appln_path = seed_paths["seed_appln_ids"]
            if seed_appln_path.exists():
                _register_existing_seed(seed_appln_path, "seed_appln_count", result)
            else:
                seed_appln_df = query_to_dataframe(patstat, seed_appln_q)
                _write_tip_seed_dataframe(seed_appln_df, seed_appln_path, "seed_appln_count", result)
                del seed_appln_df

        seed_appln_sq = seed_appln_q.subquery()
        seed_family_q = (
            db.query(TLS201.docdb_family_id.label("docdb_family_id"))
            .join(seed_appln_sq, TLS201.appln_id == seed_appln_sq.c.appln_id)
            .filter(TLS201.docdb_family_id.isnot(None))
            .distinct()
        )
        if "seed_family_ids" in requested:
            seed_family_path = seed_paths["seed_family_ids"]
            if seed_family_path.exists():
                _register_existing_seed(seed_family_path, "seed_family_count", result)
            else:
                seed_family_df = query_to_dataframe(patstat, seed_family_q)
                _write_tip_seed_dataframe(seed_family_df, seed_family_path, "seed_family_count", result)
                del seed_family_df

        seed_publn_q = (
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
            .join(seed_appln_sq, TLS211.appln_id == seed_appln_sq.c.appln_id)
            .filter(TLS211.pat_publn_id.isnot(None))
            .distinct()
        )
        if "seed_publn_ids" in requested:
            seed_publn_path = seed_paths["seed_publn_ids"]
            if seed_publn_path.exists():
                _register_existing_seed(seed_publn_path, "seed_publn_count", result)
            else:
                seed_publn_df = query_to_dataframe(patstat, seed_publn_q)
                _write_tip_seed_dataframe(seed_publn_df, seed_publn_path, "seed_publn_count", result)
                del seed_publn_df

        if "seed_person_ids" in requested:
            seed_person_path = seed_paths["seed_person_ids"]
            if seed_person_path.exists():
                _register_existing_seed(seed_person_path, "seed_person_count", result)
            elif TLS207 is not None:
                seed_person_q = (
                    db.query(TLS207.person_id.label("person_id"))
                    .join(seed_appln_sq, TLS207.appln_id == seed_appln_sq.c.appln_id)
                    .filter(TLS207.person_id.isnot(None))
                    .distinct()
                )
                seed_person_df = query_to_dataframe(patstat, seed_person_q)
                _write_tip_seed_dataframe(seed_person_df, seed_person_path, "seed_person_count", result)
                del seed_person_df
            else:
                result.metrics["seed_person_count"] = 0

        seed_ep_appln_q = (
            db.query(TLS201.appln_id.label("appln_id"))
            .join(seed_appln_sq, TLS201.appln_id == seed_appln_sq.c.appln_id)
            .filter(TLS201.appln_auth == "EP")
            .distinct()
        )
        if "seed_ep_appln_ids" in requested:
            seed_ep_appln_path = seed_paths["seed_ep_appln_ids"]
            if seed_ep_appln_path.exists():
                _register_existing_seed(seed_ep_appln_path, "seed_ep_appln_count", result)
            else:
                seed_ep_appln_df = query_to_dataframe(patstat, seed_ep_appln_q)
                _write_tip_seed_dataframe(seed_ep_appln_df, seed_ep_appln_path, "seed_ep_appln_count", result)
                del seed_ep_appln_df

        if "seed_ep_publication_numbers" in requested:
            seed_ep_publn_q = seed_publn_q.filter(TLS211.publn_auth == "EP")
            seed_ep_publn_path = seed_paths["seed_ep_publication_numbers"]
            if seed_ep_publn_path.exists():
                _register_existing_seed(seed_ep_publn_path, "seed_ep_publication_count", result)
            else:
                seed_ep_publn_df = query_to_dataframe(patstat, seed_ep_publn_q)
                _write_tip_seed_dataframe(seed_ep_publn_df, seed_ep_publn_path, "seed_ep_publication_count", result)
                del seed_ep_publn_df

        if "seed_us_publication_numbers" in requested:
            seed_us_publn_q = seed_publn_q.filter(TLS211.publn_auth == "US")
            seed_us_publn_path = seed_paths["seed_us_publication_numbers"]
            if seed_us_publn_path.exists():
                _register_existing_seed(seed_us_publn_path, "seed_us_publication_count", result)
            else:
                seed_us_publn_df = query_to_dataframe(patstat, seed_us_publn_q)
                _write_tip_seed_dataframe(seed_us_publn_df, seed_us_publn_path, "seed_us_publication_count", result)
                del seed_us_publn_df

        field_family_q = (
            db.query(
                seed_appln_sq.c.wipo_field.label("wipo_field"),
                func.count(func.distinct(TLS201.docdb_family_id)).label("family_count"),
            )
            .join(seed_appln_sq, TLS201.appln_id == seed_appln_sq.c.appln_id)
            .filter(TLS201.docdb_family_id.isnot(None))
            .group_by(seed_appln_sq.c.wipo_field)
        )
        if "seed_family_field_counts" in requested:
            seed_field_family_path = seed_paths["seed_family_field_counts"]
            if seed_field_family_path.exists():
                result.metrics["seed_field_family_count_rows"] = _register_existing_seed(seed_field_family_path, "seed_field_family_count_rows", result)
            else:
                field_family_df = query_to_dataframe(patstat, field_family_q)
                row_count = write_dataframe_parquet(field_family_df, seed_field_family_path)
                result.outputs.append(str(seed_field_family_path))
                result.metrics["seed_field_family_count_rows"] = row_count
                for _, row in field_family_df.iterrows():
                    result.metrics[f"seed_family_count__{row['wipo_field']}"] = int(row["family_count"])
                del field_family_df

            if seed_field_family_path.exists():
                field_family_rows = query_to_dataframe(patstat, field_family_q)
                for _, row in field_family_rows.iterrows():
                    result.metrics[f"seed_family_count__{row['wipo_field']}"] = int(row["family_count"])
                del field_family_rows

        result.inputs.append(f"tip://patstat/{settings.tip_env}")
        return {key: path for key, path in seed_paths.items() if key in requested}
    finally:
        close_tip_client(patstat)


def _extract_patstat_bounded_raw_tip(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Extract bounded PATSTAT raw tables from TIP PATSTAT ORM queries."""
    patstat = None
    try:
        patstat, db = get_patstat_client(settings.tip_env)
        database_module = get_patstat_database_module()

        seed_appln = seeds["seed_appln_ids"]
        seed_family = seeds["seed_family_ids"]
        seed_publn = seeds["seed_publn_ids"]
        seed_person = seeds.get("seed_person_ids")

        seed_frames = {
            "appln": duckdb.connect().execute("select appln_id from read_parquet(?)", [str(seed_appln)]).df(),
            "family": duckdb.connect().execute("select docdb_family_id from read_parquet(?)", [str(seed_family)]).df(),
            "publn": duckdb.connect().execute("select pat_publn_id from read_parquet(?)", [str(seed_publn)]).df(),
        }
        if seed_person and seed_person.exists():
            seed_frames["person"] = duckdb.connect().execute("select person_id from read_parquet(?)", [str(seed_person)]).df()

        filter_specs = {
            "bronze_patstat_appln": ("family", "docdb_family_id"),
            "bronze_patstat_appln_title": ("appln", "appln_id"),
            "bronze_patstat_appln_abstr": ("appln", "appln_id"),
            "bronze_patstat_appln_prior": ("appln", "appln_id"),
            "bronze_patstat_person": ("person", "person_id"),
            "bronze_patstat_pers_appln": ("appln", "appln_id"),
            "bronze_patstat_appln_ipc": ("appln", "appln_id"),
            "bronze_patstat_pat_publn": ("appln", "appln_id"),
            "bronze_patstat_appln_contn": ("appln", "appln_id"),
            "bronze_patstat_appln_cpc": ("appln", "appln_id"),
            "bronze_patstat_appln_techn_field": ("appln", "appln_id"),
            "bronze_patstat_inpadoc_legal_event": ("appln", "appln_id"),
            "bronze_patstat_citation": ("publn", "pat_publn_id"),
            "bronze_patstat_docdb_fam_citn": ("family", "docdb_family_id"),
        }

        for logical_name, (seed_type, column_name) in filter_specs.items():
            model = resolve_patstat_model(database_module, logical_name)
            if model is None:
                result.warnings.append(f"Skipped TIP extract for `{logical_name}` because the ORM model was unavailable.")
                continue
            if seed_type not in seed_frames:
                result.warnings.append(f"Skipped TIP extract for `{logical_name}` because the `{seed_type}` seed was unavailable.")
                continue
            seed_values = seed_frames[seed_type].iloc[:, 0].dropna().tolist()
            if not seed_values:
                continue
            query = db.query(model).filter(getattr(model, column_name).in_(seed_values))
            df = query_to_dataframe(patstat, query)
            _write_tip_dataframe(df, settings.bounded_patstat_dir / f"{PATSTAT_TABLES[logical_name][0]}.parquet", logical_name, result)

        legal_model = resolve_patstat_model(database_module, "bronze_ref_legal_event_code")
        if legal_model is not None:
            df = query_to_dataframe(patstat, db.query(legal_model))
            _write_tip_dataframe(df, settings.bounded_patstat_dir / f"{PATSTAT_TABLES['bronze_ref_legal_event_code'][0]}.parquet", "bronze_ref_legal_event_code", result)

        npl_model = resolve_patstat_model(database_module, "bronze_patstat_npl_publn")
        citation_path = settings.bounded_patstat_dir / f"{PATSTAT_TABLES['bronze_patstat_citation'][0]}.parquet"
        if npl_model is not None and citation_path.exists():
            citation_npl_col = _citation_npl_column_from_parquet(citation_path)
            if citation_npl_col is not None:
                npl_ids = duckdb.connect().execute(
                    f"select distinct {citation_npl_col} as npl_publn_id from read_parquet(?) where {citation_npl_col} is not null",
                    [str(citation_path)],
                ).df()
            else:
                npl_ids = duckdb.connect().execute("select null::bigint as npl_publn_id where false").df()
            if not npl_ids.empty:
                query = db.query(npl_model).filter(getattr(npl_model, "npl_publn_id").in_(npl_ids["npl_publn_id"].tolist()))
                df = query_to_dataframe(patstat, query)
                _write_tip_dataframe(df, settings.bounded_patstat_dir / f"{PATSTAT_TABLES['bronze_patstat_npl_publn'][0]}.parquet", "bronze_patstat_npl_publn", result)

        if citation_path.exists():
            con = duckdb.connect()
            citation_metrics = con.execute(
                """
                select
                    count(*) as edge_count,
                    count(distinct pat_publn_id) as source_publn_count,
                    count(distinct cited_pat_publn_id) as cited_publn_count
                from read_parquet(?)
                """,
                [str(citation_path)],
            ).fetchone()
            result.metrics["bounded_citation_edge_count"] = int(citation_metrics[0] or 0)
            result.metrics["bounded_citation_source_publication_count"] = int(citation_metrics[1] or 0)
            result.metrics["bounded_citation_cited_publication_count"] = int(citation_metrics[2] or 0)
    finally:
        close_tip_client(patstat)


def _extract_register_bounded_raw_tip(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Extract bounded Register tables from TIP PATSTAT/Register ORM models."""
    patstat = None
    try:
        patstat, db = get_patstat_client(settings.tip_env)
        database_module = get_patstat_database_module()
        ep_seed_df = duckdb.connect().execute("select appln_id from read_parquet(?)", [str(seeds["seed_ep_appln_ids"])]).df()
        if ep_seed_df.empty:
            return

        reg101_model = resolve_register_model(database_module, "bronze_reg101_appln")
        if reg101_model is None:
            result.warnings.append("Skipped TIP Register extraction because REG101_APPLN was unavailable.")
            return

        reg101_query = db.query(reg101_model).filter(getattr(reg101_model, "appln_id").in_(ep_seed_df["appln_id"].tolist()))
        reg101_df = query_to_dataframe(patstat, reg101_query)
        reg101_path = settings.bounded_register_dir / f"{REGISTER_TABLES['bronze_reg101_appln'][0]}.parquet"
        _write_tip_dataframe(reg101_df, reg101_path, "bronze_reg101_appln", result)
        if reg101_df.empty:
            return

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
                query = db.query(model).filter(getattr(model, "appln_id").in_(ep_seed_df["appln_id"].tolist()))
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
            df = query_to_dataframe(patstat, query)
            out_path = settings.bounded_register_dir / f"{REGISTER_TABLES[logical_name][0]}.parquet"
            _write_tip_dataframe(df, out_path, logical_name, result)
            if logical_name == "bronze_reg201_proc_step" and "step_id" in df.columns:
                step_ids = df["step_id"].dropna().tolist()
            elif logical_name == "bronze_reg301_event_data" and "event_code" in df.columns:
                event_codes = df["event_code"].dropna().tolist()
            elif logical_name == "bronze_reg701_appln" and "id" in df.columns:
                reg701_ids = df["id"].dropna().tolist()
            elif logical_name == "bronze_reg731_event_data" and "event_code" in df.columns:
                reg731_event_codes = df["event_code"].dropna().tolist()
    finally:
        close_tip_client(patstat)


def _extract_epab_bounded_raw_tip(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Extract bounded EPAB result groups from TIP EPAB queries."""
    seed_path = seeds.get("seed_ep_publication_numbers")
    if seed_path is None or not seed_path.exists():
        result.warnings.append("Skipped TIP EPAB extraction because no in-scope EP publication seed was generated.")
        return
    seed_df = duckdb.connect().execute(
        "select publication_number, publication_kind, publication_date from read_parquet(?) where upper(coalesce(publn_auth, 'EP')) = 'EP'",
        [str(seed_path)],
    ).df() if "publn_auth" in duckdb.connect().execute("describe select * from read_parquet(?)", [str(seed_path)]).df()["column_name"].tolist() else duckdb.connect().execute(
        "select publication_number, publication_kind, publication_date from read_parquet(?)",
        [str(seed_path)],
    ).df()
    if seed_df.empty:
        return

    for group, df in _extract_epab_tip_groups(settings, seed_df, result).items():
        group_name = EPAB_GROUP_NAME_MAP[group]
        out_path = settings.bounded_epab_dir / f"epab_{group_name}.parquet"
        _write_tip_dataframe(df, out_path, f"epab_{group_name}", result)


def _write_extraction_summary(settings: BuildSettings, seeds: dict[str, Path], result: StageResult) -> None:
    """Persist a compact extraction-summary artifact for later debugging and Data Room provenance."""
    summary_path = settings.manifests_dir / "stats" / "prebronze-extraction-summary.json"
    payload = {
        "release_id": settings.release_id,
        "snapshot_date": settings.snapshot_date,
        "selected_wipo_fields": settings.selected_wipo_fields,
        "seed_outputs": {key: str(value) for key, value in seeds.items()},
        "metrics": result.metrics,
        "warnings": result.warnings,
    }
    write_text_json(summary_path, payload)
    result.artifacts["extraction_summary"] = str(summary_path)


def extract_bounded_raw(settings: BuildSettings) -> StageResult:
    """Build the bounded raw slice that Bronze consumes for the mega-cluster warehouse."""
    result = StageResult(
        stage="pre-bronze-extraction",
        status="success",
        summary="Built the bounded raw PATSTAT/Register/USPTO/EPAB slice that Bronze parquet generation consumes.",
        methods=[
            "Built the in-scope PATSTAT application seed from technology fields with IPC fallback.",
            "Expanded the seed to bounded family, publication, person, and EP-application universes before extracting raw slices.",
            "Preserved ghost-node citation and NPL support rows by keeping all out-of-scope cited targets referenced by in-scope source publications.",
            "Selected only the in-scope USPTO XML files and EPAB records needed for Bronze text-provider parsing.",
            "Supports a local USPTO ODP stream path that writes direct Bronze parquet outputs with immediate ZIP/XML cleanup.",
        ],
        calculations=[
            "Application seeds are restricted to the configured 10 WIPO fields.",
            "Family, publication, and person seeds are deterministic expansions from the bounded PATSTAT application seed.",
            "Citation support is source-bounded on the citing side but intentionally not bounded on the cited side.",
        ],
        downstream_impacts=[
            "These bounded raw slices become the only supported Bronze inputs for the mega-cluster warehouse build.",
            "Any collapse in seed counts or bridge coverage here propagates directly into Bronze, Silver, Gold, Market Intelligence, and semantic outputs.",
            "Ghost-node under-extraction here will specifically corrupt citation, OECD, and family influence calculations downstream.",
        ],
        doc_refs=DOC_REFS,
    )

    ensure_dir(settings.bounded_patstat_dir)
    ensure_dir(settings.bounded_register_dir)
    ensure_dir(settings.bounded_uspto_dir)
    ensure_dir(settings.bounded_epab_dir)
    ensure_dir(settings.bounded_refs_dir)
    ensure_dir(settings.bounded_seed_dir)
    ensure_dir(settings.bronze_dir)

    if settings.patstat_source_mode == "tip":
        seeds = _seed_patstat_scope_tip(settings, result)
    else:
        seeds = _seed_patstat_scope(settings, result)
    if result.status == "failed":
        _write_extraction_summary(settings, seeds, result)
        return result

    if settings.patstat_source_mode == "tip":
        _extract_patstat_bounded_raw_tip(settings, seeds, result)
    else:
        _extract_patstat_bounded_raw(settings, seeds, result)

    if settings.register_source_mode == "tip":
        _extract_register_bounded_raw_tip(settings, seeds, result)
    else:
        _extract_register_bounded_raw(settings, seeds, result)

    if settings.uspto_source_mode == "local_files":
        _extract_uspto_bounded_raw(settings, seeds, result)
    elif settings.uspto_source_mode == "odp_api":
        extract_uspto_odp_to_bronze(settings, seeds["seed_us_publication_numbers"], result)

    if settings.epab_source_mode == "tip":
        _extract_epab_bounded_raw_tip(settings, seeds, result)
    else:
        _extract_epab_bounded_raw(settings, seeds, result)

    if settings.refs_source_mode == "local_files":
        _copy_reference_inputs(settings, result)

    result.metrics["bounded_total_seed_output_count"] = len([path for path in seeds.values() if path.exists()])
    result.metrics["bounded_total_artifact_count"] = len(result.outputs)
    _write_extraction_summary(settings, seeds, result)
    return result
