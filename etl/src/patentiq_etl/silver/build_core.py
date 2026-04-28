from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, parquet_columns, parquet_row_count, table_exists
from patentiq_etl.common.types import BuildSettings, StageResult


LOGGER = logging.getLogger(__name__)


def _pick(columns: list[str], candidates: list[str], *, required: bool = True) -> str | None:
    """Return the first matching column name from a candidate list, case-insensitively."""
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    if required:
        raise ValueError(f"Missing required columns. Candidates: {candidates}")
    return None


def _sql_date_expr(column: str) -> str:
    """Return a DuckDB SQL expression that safely casts a column to `date`."""
    return f"try_cast({column} as date)"


def _sql_valid_date_expr(column: str) -> str:
    """Return a date expression that also nulls PATSTAT-style sentinel max dates."""
    return f"nullif(try_cast({column} as date), date '9999-12-31')"


def _sql_first_valid_date_expr(columns: list[str | None], *, alias: str | None = None) -> str:
    """Return the first non-null non-sentinel date expression from candidate columns."""
    exprs: list[str] = []
    for column in columns:
        if column is None:
            continue
        qualified = f"{alias}.{column}" if alias else column
        exprs.append(_sql_valid_date_expr(qualified))
    if not exprs:
        return "null::date"
    return f"coalesce({', '.join(exprs)})"


def _sql_first_valid_date_source_expr(columns: list[tuple[str | None, str]], *, alias: str | None = None) -> str:
    """Return a CASE expression naming the first non-null non-sentinel date source."""
    clauses: list[str] = []
    for column, label in columns:
        if column is None:
            continue
        qualified = f"{alias}.{column}" if alias else column
        clauses.append(f"when {_sql_valid_date_expr(qualified)} is not null then '{label}'")
    if not clauses:
        return "cast(null as varchar)"
    return "case " + " ".join(clauses) + " else null end"


def _sql_column_expr(alias: str, column: str | None, cast_type: str = "varchar") -> str:
    """Return a typed SQL expression for an optional column reference."""
    if column is None:
        return f"null::{cast_type}"
    return f"cast({alias}.{column} as {cast_type})"


def _sql_owner_name_expr(column: str) -> str:
    """Return a cleaned display-name SQL expression for owner names."""
    return (
        "case "
        f"when trim(coalesce(cast({column} as varchar), '')) = '' then 'Unknown Owner' "
        f"else trim(cast({column} as varchar)) end"
    )


def _sql_owner_harmonized_expr(column: str) -> str:
    """Return a normalized owner key with a controlled fallback for degenerate names."""
    cleaned = (
        f"upper(regexp_replace(regexp_replace(trim(coalesce(cast({column} as varchar), '')), "
        "'[^A-Za-z0-9]+', '_', 'g'), '^_+|_+$', '', 'g'))"
    )
    return f"case when {cleaned} = '' then 'UNKNOWN_OWNER' else {cleaned} end"


def _build_owner_contracts(
    con: duckdb.DuckDBPyConnection,
    *,
    owner_seed_path: Path,
    out_owner_bridge: Path,
    out_owner: Path,
) -> dict[str, int]:
    """Materialize owner bridge and deterministic primary-owner outputs from the scoped owner seed."""
    con.execute(
        f"""
        copy (
            with owner_seed as (
                select
                    cast(docdb_family_id as bigint) as docdb_family_id,
                    cast(appln_id as bigint) as appln_id,
                    case
                        when regexp_replace(trim(coalesce(cast(owner_name_harmonized as varchar), '')), '[^A-Za-z0-9]+', '', 'g') = '' then 'UNKNOWN_OWNER'
                        else trim(cast(owner_name_harmonized as varchar))
                    end as owner_name_harmonized,
                    case
                        when trim(coalesce(cast(owner_name as varchar), '')) = '' then 'Unknown Owner'
                        else trim(cast(owner_name as varchar))
                    end as owner_name_display,
                    nullif(trim(cast(owner_country as varchar)), '') as owner_country
                from read_parquet('{owner_seed_path}')
            ),
            owner_display_ranked as (
                select
                    docdb_family_id,
                    owner_name_harmonized,
                    owner_name_display,
                    count(distinct appln_id) as display_scope_appln_count,
                    row_number() over (
                        partition by docdb_family_id, owner_name_harmonized
                        order by count(distinct appln_id) desc, owner_name_display asc
                    ) as display_rank
                from owner_seed
                group by docdb_family_id, owner_name_harmonized, owner_name_display
            ),
            owner_country_ranked as (
                select
                    docdb_family_id,
                    owner_name_harmonized,
                    owner_country,
                    count(distinct appln_id) as country_scope_appln_count,
                    row_number() over (
                        partition by docdb_family_id, owner_name_harmonized
                        order by count(distinct appln_id) desc, owner_country asc nulls last
                    ) as country_rank
                from owner_seed
                group by docdb_family_id, owner_name_harmonized, owner_country
            ),
            bridge_base as (
                select
                    s.docdb_family_id,
                    s.owner_name_harmonized,
                    count(distinct s.appln_id) as owner_scope_appln_count,
                    count(distinct s.owner_name_display) as owner_display_variant_count,
                    count(distinct s.owner_country) as owner_country_variant_count
                from owner_seed s
                group by s.docdb_family_id, s.owner_name_harmonized
            ),
            bridge_ranked as (
                select
                    b.docdb_family_id,
                    b.owner_name_harmonized,
                    d.owner_name_display,
                    c.owner_country,
                    b.owner_scope_appln_count,
                    b.owner_display_variant_count,
                    b.owner_country_variant_count,
                    count(*) over (partition by b.docdb_family_id) as family_distinct_owner_count,
                    row_number() over (
                        partition by b.docdb_family_id
                        order by
                            case when b.owner_name_harmonized = 'UNKNOWN_OWNER' then 1 else 0 end asc,
                            b.owner_scope_appln_count desc,
                            b.owner_name_harmonized asc,
                            d.owner_name_display asc
                    ) as owner_family_rank
                from bridge_base b
                left join owner_display_ranked d
                  on b.docdb_family_id = d.docdb_family_id
                 and b.owner_name_harmonized = d.owner_name_harmonized
                 and d.display_rank = 1
                left join owner_country_ranked c
                  on b.docdb_family_id = c.docdb_family_id
                 and b.owner_name_harmonized = c.owner_name_harmonized
                 and c.country_rank = 1
            )
            select
                docdb_family_id,
                owner_name_harmonized,
                owner_name_display,
                owner_country,
                owner_scope_appln_count,
                owner_display_variant_count,
                owner_country_variant_count,
                family_distinct_owner_count,
                owner_family_rank,
                owner_family_rank = 1 as is_primary_owner,
                case
                    when owner_name_harmonized = 'UNKNOWN_OWNER' then 'unknown_owner_fallback'
                    else 'scope_appln_count_desc_then_owner_name'
                end as owner_selection_method
            from bridge_ranked
        ) to '{out_owner_bridge}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                owner_name_harmonized,
                owner_name_display,
                owner_country,
                owner_scope_appln_count,
                family_distinct_owner_count,
                owner_selection_method as primary_owner_selection_method
            from read_parquet('{out_owner_bridge}')
            where is_primary_owner
        ) to '{out_owner}' (format parquet, compression zstd)
        """
    )
    return {
        "silver_family_owner_bridge_rows": parquet_row_count(out_owner_bridge),
        "silver_assignee_harmonized_rows": parquet_row_count(out_owner),
    }


def build_scope_seed(settings: BuildSettings) -> StageResult:
    """Build the bounded in-scope application, family, publication, and owner seed tables."""
    appln_path = settings.bronze_dir / "bronze_patstat_appln.parquet"
    ipc_path = settings.bronze_dir / "bronze_patstat_appln_ipc.parquet"
    tech_field_path = settings.bronze_dir / "bronze_patstat_appln_techn_field.parquet"
    publn_path = settings.bronze_dir / "bronze_patstat_pat_publn.parquet"
    pers_appln_path = settings.bronze_dir / "bronze_patstat_pers_appln.parquet"
    person_path = settings.bronze_dir / "bronze_patstat_person.parquet"
    ref_path = settings.bronze_dir / "bronze_ref_techn_field_ipc.parquet"

    result = StageResult(
        stage="scope",
        status="success",
        summary="Built bounded-scope application, family, publication, and owner seeds for the mega-cluster universe.",
        inputs=[str(path) for path in [appln_path, ipc_path, tech_field_path, publn_path, pers_appln_path, person_path, ref_path] if path.exists()],
        methods=[
            "Resolved the in-scope family universe from selected WIPO field mappings before heavy downstream analytics.",
            "Preferred direct PATSTAT technology-field inputs when present and fell back to IPC subclass to WIPO field concordance otherwise.",
            "Bridged the in-scope applications to families, publications, and owners to create the canonical bounded universe.",
        ],
        calculations=[
            "An in-scope application is one whose technology-field mapping falls inside the selected 10 WIPO fields.",
            "An in-scope family is any DOCDB family reachable from the in-scope application seed.",
            "An in-scope portfolio owner seed is derived from applicant-side application-person links only.",
        ],
        downstream_impacts=[
            "These scope seeds bound every downstream family, publication, owner, and portfolio calculation in the MVP warehouse.",
            "An over-broad or under-broad seed will contaminate blocking power, Market Intelligence, forecasts, semantic sampling, and Data Room counts.",
        ],
        doc_refs=[
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
            "docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md",
            "docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md",
        ],
    )

    if not appln_path.exists() or not publn_path.exists():
        result.status = "failed"
        result.warnings.append("Bronze PATSTAT application/publication tables are required before scope seeding.")
        return result

    con = duckdb.connect()
    appln_cols = parquet_columns(appln_path)
    appln_id = _pick(appln_cols, ["appln_id"])
    family_id = _pick(appln_cols, ["docdb_family_id"])
    inpadoc_id = _pick(appln_cols, ["inpadoc_family_id"], required=False)
    appln_filing_date = _pick(appln_cols, ["appln_filing_date"], required=False)
    earliest_filing_date = _pick(appln_cols, ["earliest_filing_date"], required=False)
    appln_auth = _pick(appln_cols, ["appln_auth"], required=False)
    appln_kind = _pick(appln_cols, ["appln_kind"], required=False)

    selected_fields_sql = ", ".join([f"'{field}'" for field in settings.selected_wipo_fields])

    if table_exists(tech_field_path):
        tech_cols = parquet_columns(tech_field_path)
        tech_appln_id = _pick(tech_cols, ["appln_id"])
        tech_field_code = _pick(tech_cols, ["wipo_industry_code", "techn_field"], required=False)
        tech_field_nr = _pick(tech_cols, ["techn_field_nr"], required=False)
        if tech_field_code is not None:
            scope_source_sql = f"""
                select
                    cast({tech_appln_id} as bigint) as appln_id,
                    cast({tech_field_code} as varchar) as wipo_industry_code
                from read_parquet('{tech_field_path}')
            """
        elif tech_field_nr is not None and ref_path.exists():
            ref_cols = parquet_columns(ref_path)
            ref_field_nr = _pick(ref_cols, ["techn_field_nr"])
            ref_field = _pick(ref_cols, ["wipo_industry_code"])
            scope_source_sql = f"""
                select distinct
                    cast(t.{tech_appln_id} as bigint) as appln_id,
                    cast(r.{ref_field} as varchar) as wipo_industry_code
                from read_parquet('{tech_field_path}') t
                join read_parquet('{ref_path}') r
                  on cast(t.{tech_field_nr} as bigint) = cast(r.{ref_field_nr} as bigint)
            """
        else:
            result.status = "failed"
            result.warnings.append(
                "PATSTAT technology-field table exists but no usable WIPO field column was found, "
                "and techn_field_nr could not be resolved through the WIPO concordance."
            )
            return result
    else:
        if not ipc_path.exists() or not ref_path.exists():
            result.status = "failed"
            result.warnings.append("IPC-based scope fallback requires both appln_ipc and WIPO field concordance Bronze tables.")
            return result
        ipc_cols = parquet_columns(ipc_path)
        ipc_appln_id = _pick(ipc_cols, ["appln_id"])
        ipc_symbol = _pick(ipc_cols, ["ipc_class_symbol"])
        ref_cols = parquet_columns(ref_path)
        ref_ipc = _pick(ref_cols, ["ipc_subclass"])
        ref_field = _pick(ref_cols, ["wipo_industry_code"])
        scope_source_sql = f"""
            select distinct
                cast(i.{ipc_appln_id} as bigint) as appln_id,
                cast(r.{ref_field} as varchar) as wipo_industry_code
            from read_parquet('{ipc_path}') i
            join read_parquet('{ref_path}') r
              on regexp_replace(substr(cast(i.{ipc_symbol} as varchar), 1, 4), '[^A-Za-z0-9]', '', 'g') = cast(r.{ref_ipc} as varchar)
        """

    appln_seed_path = settings.silver_dir / "silver_scope_appln_seed.parquet"
    family_seed_path = settings.silver_dir / "silver_scope_family_seed.parquet"
    publn_seed_path = settings.silver_dir / "silver_scope_publn_seed.parquet"
    owner_seed_path = settings.silver_dir / "silver_scope_owner_seed.parquet"

    con.execute(
        f"""
        copy (
            with scope_source as (
                {scope_source_sql}
            )
            select distinct
                cast(a.{appln_id} as bigint) as appln_id,
                cast(a.{family_id} as bigint) as docdb_family_id,
                {_sql_column_expr('a', inpadoc_id, 'bigint')} as inpadoc_family_id,
                cast(s.wipo_industry_code as varchar) as wipo_industry_code,
                {_sql_date_expr(earliest_filing_date) if earliest_filing_date else (_sql_date_expr(appln_filing_date) if appln_filing_date else 'null::date')} as family_earliest_priority_date,
                {_sql_date_expr(appln_filing_date) if appln_filing_date else 'null::date'} as appln_filing_date,
                {_sql_column_expr('a', appln_auth)} as appln_auth,
                {_sql_column_expr('a', appln_kind)} as appln_kind,
                '{settings.scope_type}' as scope_type,
                '{settings.method_version}' as method_version,
                '{settings.snapshot_date}' as snapshot_date
            from read_parquet('{appln_path}') a
            join scope_source s
              on cast(a.{appln_id} as bigint) = s.appln_id
            where s.wipo_industry_code in ({selected_fields_sql})
              and cast(a.{family_id} as bigint) is not null
        ) to '{appln_seed_path}' (format parquet, compression zstd)
        """
    )

    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                any_value(inpadoc_family_id) as inpadoc_family_id,
                min(family_earliest_priority_date) as family_earliest_priority_date,
                list(distinct wipo_industry_code order by wipo_industry_code) as covered_wipo_fields,
                count(distinct appln_id) as scope_appln_count,
                '{settings.scope_type}' as scope_type,
                '{settings.method_version}' as method_version,
                '{settings.snapshot_date}' as snapshot_date
            from read_parquet('{appln_seed_path}')
            group by docdb_family_id
        ) to '{family_seed_path}' (format parquet, compression zstd)
        """
    )

    pub_cols = parquet_columns(publn_path)
    pub_appln_id = _pick(pub_cols, ["appln_id"])
    pub_id = _pick(pub_cols, ["pat_publn_id"])
    pub_auth = _pick(pub_cols, ["publn_auth"])
    pub_nr = _pick(pub_cols, ["publn_nr"])
    pub_kind = _pick(pub_cols, ["publn_kind"])
    pub_date = _pick(pub_cols, ["publn_date"], required=False)

    con.execute(
        f"""
        copy (
            select distinct
                cast(p.{pub_id} as bigint) as pat_publn_id,
                cast(p.{pub_appln_id} as bigint) as appln_id,
                cast(s.docdb_family_id as bigint) as docdb_family_id,
                cast(p.{pub_auth} as varchar) as publn_auth,
                cast(p.{pub_nr} as varchar) as publn_nr,
                trim(cast(p.{pub_kind} as varchar)) as publn_kind,
                {_sql_date_expr(f'p.{pub_date}') if pub_date else 'null::date'} as publn_date,
                concat(cast(p.{pub_auth} as varchar), cast(p.{pub_nr} as varchar), trim(cast(p.{pub_kind} as varchar))) as publication_number_full,
                '{settings.scope_type}' as scope_type,
                '{settings.snapshot_date}' as snapshot_date
            from read_parquet('{publn_path}') p
            join read_parquet('{appln_seed_path}') s
              on cast(p.{pub_appln_id} as bigint) = cast(s.appln_id as bigint)
        ) to '{publn_seed_path}' (format parquet, compression zstd)
        """
    )

    if pers_appln_path.exists() and person_path.exists():
        pers_cols = parquet_columns(pers_appln_path)
        person_cols = parquet_columns(person_path)
        pers_appln_id = _pick(pers_cols, ["appln_id"])
        pers_person_id = _pick(pers_cols, ["person_id"])
        applt_seq = _pick(pers_cols, ["applt_seq_nr"], required=False)
        person_id_col = _pick(person_cols, ["person_id"])
        person_name = _pick(person_cols, ["psn_name", "doc_std_name", "person_name", "han_name"], required=False) or person_id_col
        country = _pick(person_cols, ["person_ctry_code", "person_country", "ctry_code"], required=False)
        applicant_predicate = f"coalesce(cast(pa.{applt_seq} as bigint), 0) > 0" if applt_seq else "true"
        con.execute(
            f"""
            copy (
                select distinct
                    cast(s.docdb_family_id as bigint) as docdb_family_id,
                    cast(s.appln_id as bigint) as appln_id,
                    cast(pa.{pers_person_id} as bigint) as person_id,
                    {_sql_owner_name_expr(f'p.{person_name}')} as owner_name,
                    {_sql_column_expr('p', country)} as owner_country,
                    {_sql_owner_harmonized_expr(f'p.{person_name}')} as owner_name_harmonized,
                    '{settings.scope_type}' as scope_type,
                    '{settings.snapshot_date}' as snapshot_date
                from read_parquet('{appln_seed_path}') s
                join read_parquet('{pers_appln_path}') pa
                  on cast(s.appln_id as bigint) = cast(pa.{pers_appln_id} as bigint)
                join read_parquet('{person_path}') p
                  on cast(pa.{pers_person_id} as bigint) = cast(p.{person_id_col} as bigint)
                where {applicant_predicate}
            ) to '{owner_seed_path}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    appln_id,
                    null::bigint as person_id,
                    'UNKNOWN_OWNER' as owner_name,
                    null::varchar as owner_country,
                    'UNKNOWN_OWNER' as owner_name_harmonized,
                    scope_type,
                    snapshot_date
                from read_parquet('{appln_seed_path}')
            ) to '{owner_seed_path}' (format parquet, compression zstd)
            """
        )
        result.warnings.append("Owner seed fell back to UNKNOWN_OWNER because Bronze person linkage tables were unavailable.")

    result.outputs.extend([str(appln_seed_path), str(family_seed_path), str(publn_seed_path), str(owner_seed_path)])
    result.metrics["scope_appln_count"] = parquet_row_count(appln_seed_path)
    result.metrics["scope_family_count"] = parquet_row_count(family_seed_path)
    result.metrics["scope_publn_count"] = parquet_row_count(publn_seed_path)
    result.metrics["scope_owner_count"] = parquet_row_count(owner_seed_path)

    for field, appln_count, family_count, publn_count in con.execute(
        f"""
        with appln_field as (
            select
                wipo_industry_code,
                count(distinct appln_id) as appln_count,
                count(distinct docdb_family_id) as family_count
            from read_parquet('{appln_seed_path}')
            group by wipo_industry_code
        ),
        publn_field as (
            select
                a.wipo_industry_code,
                count(distinct p.pat_publn_id) as publn_count
            from read_parquet('{appln_seed_path}') a
            join read_parquet('{publn_seed_path}') p using (appln_id)
            group by a.wipo_industry_code
        )
        select
            a.wipo_industry_code,
            a.appln_count,
            a.family_count,
            coalesce(p.publn_count, 0) as publn_count
        from appln_field a
        left join publn_field p using (wipo_industry_code)
        """
    ).fetchall():
        result.metrics[f"scope_appln_count__{field}"] = appln_count
        result.metrics[f"scope_family_count__{field}"] = family_count
        result.metrics[f"scope_publn_count__{field}"] = publn_count

    if result.metrics["scope_family_count"] == 0:
        result.status = "failed"
        result.warnings.append("Scope seeding produced zero in-scope families.")

    return result


def build_core_silver(settings: BuildSettings) -> StageResult:
    """Build the canonical Silver entity, legal, market, UP, and Register support tables."""
    family_seed_path = settings.silver_dir / "silver_scope_family_seed.parquet"
    appln_seed_path = settings.silver_dir / "silver_scope_appln_seed.parquet"
    publn_seed_path = settings.silver_dir / "silver_scope_publn_seed.parquet"
    owner_seed_path = settings.silver_dir / "silver_scope_owner_seed.parquet"

    result = StageResult(
        stage="silver-core",
        status="success",
        summary="Built core family-first Silver entities and bounded ownership/field normalizations.",
        inputs=[str(path) for path in [family_seed_path, appln_seed_path, publn_seed_path, owner_seed_path] if path.exists()],
        methods=[
            "Collapsed in-scope applications to the canonical family core.",
            "Normalized publication stage semantics from publication kinds.",
            "Materialized owner harmonization and WIPO field assignment as reusable Silver entities.",
        ],
        calculations=[
            "Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.",
            "Portfolio ownership remains bounded to the in-scope family universe only.",
        ],
        downstream_impacts=[
            "silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.",
            "The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.",
        ],
        doc_refs=[
            "docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
            "docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md",
        ],
    )

    if not family_seed_path.exists():
        result.status = "failed"
        result.warnings.append("Scope family seed is required before building Silver core.")
        return result

    con = duckdb.connect()
    out_core = settings.silver_dir / "silver_family_core.parquet"
    out_member = settings.silver_dir / "silver_family_member_publications.parquet"
    out_kind = settings.silver_dir / "silver_kind_code_normalization.parquet"
    out_fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    out_owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    out_owner = settings.silver_dir / "silver_assignee_harmonized.parquet"
    out_codes = settings.silver_dir / "silver_family_ipc_cpc_canonical.parquet"
    out_legal = settings.silver_dir / "silver_legal_status_event_ledger.parquet"
    out_branch_history = settings.silver_dir / "silver_branch_status_history.parquet"
    out_family_history = settings.silver_dir / "silver_family_status_history.parquet"
    out_status = settings.silver_dir / "silver_family_status_pt.parquet"
    out_weight = settings.silver_dir / "silver_tiered_market_weighting.parquet"
    out_up = settings.silver_dir / "silver_up_status.parquet"
    out_jur = settings.silver_dir / "silver_family_jurisdiction_unrolled.parquet"
    out_register = settings.silver_dir / "silver_ep_register_core.parquet"
    out_register_agent = settings.silver_dir / "silver_ep_register_agent_summary.parquet"
    out_register_opposition = settings.silver_dir / "silver_ep_register_current_opposition.parquet"
    out_register_up = settings.silver_dir / "silver_ep_register_up_status.parquet"
    out_register_proc = settings.silver_dir / "silver_ep_register_proc_step_features.parquet"
    out_register_display = settings.silver_dir / "silver_ep_register_display_ledger.parquet"

    build_snapshot_year = int(settings.snapshot_date[:4])
    snapshot_date = settings.snapshot_date

    LOGGER.info("Building silver_family_core and family publication/member anchors")
    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                any_value(inpadoc_family_id) as inpadoc_family_id,
                min(family_earliest_priority_date) as family_earliest_priority_date,
                extract(year from min(family_earliest_priority_date)) as family_priority_year,
                extract(year from min(family_earliest_priority_date)) between {settings.year_window_start} and {settings.year_window_end} as is_main_window_family,
                extract(year from min(family_earliest_priority_date)) between {settings.heritage_backfill_start} and {settings.heritage_backfill_end} as is_heritage_backfill_family,
                false as is_out_of_bounds_ghost,
                max(scope_appln_count) as family_size_docdb,
                any_value(scope_type) as scope_type,
                any_value(method_version) as method_version,
                any_value(snapshot_date) as snapshot_date
            from read_parquet('{family_seed_path}')
            group by docdb_family_id
        ) to '{out_core}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select distinct
                pat_publn_id,
                appln_id,
                docdb_family_id,
                publn_auth,
                publn_nr,
                publn_kind,
                {_sql_date_expr('publn_date')} as publn_date,
                publication_number_full,
                starts_with(coalesce(publn_kind, ''), 'A') as is_application_stage,
                starts_with(coalesce(publn_kind, ''), 'B') as is_grant_stage,
                starts_with(coalesce(publn_kind, ''), 'C') as is_modifier_stage,
                scope_type,
                snapshot_date
            from read_parquet('{publn_seed_path}')
        ) to '{out_member}' (format parquet, compression zstd)
        """
    )
    LOGGER.info("Building silver_kind_code_normalization")
    kind_seed = settings.bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet"
    if kind_seed.exists():
        kind_seed_cols = parquet_columns(kind_seed)
        kind_jur = _pick(kind_seed_cols, ["jurisdiction_code"])
        kind_code = _pick(kind_seed_cols, ["kind_code"])
        universal_stage = _pick(kind_seed_cols, ["universal_stage"])
        stage_multiplier = _pick(kind_seed_cols, ["stage_multiplier"])
        is_enforceable = _pick(kind_seed_cols, ["is_enforceable"])
        legal_status_proxy = _pick(kind_seed_cols, ["legal_status_proxy"], required=False)
        mapping_basis = _pick(kind_seed_cols, ["mapping_basis"], required=False)
        review_status = _pick(kind_seed_cols, ["review_status"], required=False)
        source_reference = _pick(kind_seed_cols, ["source_reference"], required=False)
        con.execute(
            f"""
            copy (
                select
                    cast({kind_jur} as varchar) as jurisdiction_code,
                    trim(cast({kind_code} as varchar)) as kind_code,
                    upper(trim(cast({universal_stage} as varchar))) as universal_stage,
                    cast({stage_multiplier} as double) as stage_multiplier,
                    cast({is_enforceable} as boolean) as is_enforceable,
                    upper(trim(cast({universal_stage} as varchar))) like '%APPLICATION%' as is_application_stage,
                    upper(trim(cast({universal_stage} as varchar))) in ('OPPOSITION_SURVIVOR', 'UNITARY_GRANT', 'POST_GRANT_MODIFIER') as is_post_grant_modifier,
                    {f'cast({legal_status_proxy} as varchar)' if legal_status_proxy else 'cast(null as varchar)'} as legal_status_proxy,
                    {f'cast({mapping_basis} as varchar)' if mapping_basis else "'SEEDED_INPUT'"} as mapping_basis,
                    {f'cast({review_status} as varchar)' if review_status else "'seeded_unreviewed'"} as review_status,
                    {f'cast({source_reference} as varchar)' if source_reference else "'seed_input'"} as source_reference,
                    '{settings.method_version}' as method_version
                from read_parquet('{kind_seed}')
            ) to '{out_kind}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                select distinct
                    cast(publn_auth as varchar) as jurisdiction_code,
                    trim(cast(publn_kind as varchar)) as kind_code,
                    case
                        when trim(coalesce(publn_kind, '')) = 'C0' then 'UNITARY_GRANT'
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') and publn_auth = 'EP' and trim(coalesce(publn_kind, '')) = 'B2' then 'OPPOSITION_SURVIVOR'
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') then 'STANDARD_GRANT'
                        when starts_with(trim(coalesce(publn_kind, '')), 'A') then 'PENDING_APPLICATION'
                        when starts_with(trim(coalesce(publn_kind, '')), 'C') then 'POST_GRANT_MODIFIER'
                        else 'OTHER'
                    end as universal_stage,
                    case
                        when trim(coalesce(publn_kind, '')) = 'C0' then 1.0
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') and publn_auth = 'EP' and trim(coalesce(publn_kind, '')) = 'B2' then 3.0
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') then 1.0
                        when starts_with(trim(coalesce(publn_kind, '')), 'A') then 0.2
                        when starts_with(trim(coalesce(publn_kind, '')), 'C') then 0.8
                        else 0.0
                    end as stage_multiplier,
                    case
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') or trim(coalesce(publn_kind, '')) = 'C0' then true
                        else false
                    end as is_enforceable,
                    starts_with(trim(coalesce(publn_kind, '')), 'A') as is_application_stage,
                    trim(coalesce(publn_kind, '')) = 'C0' or starts_with(trim(coalesce(publn_kind, '')), 'C') as is_post_grant_modifier,
                    case
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') or trim(coalesce(publn_kind, '')) = 'C0' then 'active_grant'
                        when starts_with(trim(coalesce(publn_kind, '')), 'A') then 'pending_application'
                        when starts_with(trim(coalesce(publn_kind, '')), 'C') then 'post_grant_modifier'
                        else 'other'
                    end as legal_status_proxy,
                    case
                        when trim(coalesce(publn_kind, '')) = 'C0' then 'AUTO_EP_SPECIAL_RULE'
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') and publn_auth = 'EP' and trim(coalesce(publn_kind, '')) = 'B2' then 'AUTO_EP_SPECIAL_RULE'
                        when starts_with(trim(coalesce(publn_kind, '')), 'A') or starts_with(trim(coalesce(publn_kind, '')), 'B') or starts_with(trim(coalesce(publn_kind, '')), 'C') then 'AUTO_PREFIX_RULE'
                        else 'UNMAPPED_OTHER_AUTO'
                    end as mapping_basis,
                    case
                        when starts_with(trim(coalesce(publn_kind, '')), 'A') or starts_with(trim(coalesce(publn_kind, '')), 'B') or starts_with(trim(coalesce(publn_kind, '')), 'C') or trim(coalesce(publn_kind, '')) = 'C0' then 'needs_docdb_review'
                        else 'unmapped_needs_review'
                    end as review_status,
                    case
                        when trim(coalesce(publn_kind, '')) = 'C0' then 'EP_C0_SPECIAL_RULE'
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') and publn_auth = 'EP' and trim(coalesce(publn_kind, '')) = 'B2' then 'EP_B2_SPECIAL_RULE'
                        when starts_with(trim(coalesce(publn_kind, '')), 'A') then 'PREFIX_A'
                        when starts_with(trim(coalesce(publn_kind, '')), 'B') then 'PREFIX_B'
                        when starts_with(trim(coalesce(publn_kind, '')), 'C') then 'PREFIX_C'
                        else 'UNMAPPED'
                    end as source_reference,
                    '{settings.method_version}' as method_version
                from read_parquet('{out_member}')
            ) to '{out_kind}' (format parquet, compression zstd)
            """
        )
    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                list(distinct wipo_industry_code order by wipo_industry_code) as covered_wipo_fields,
                list_extract(list(distinct wipo_industry_code order by wipo_industry_code), 1) as primary_wipo_field,
                count(distinct wipo_industry_code) as family_tech_breadth_wipo_count,
                case
                    when count(distinct wipo_industry_code) = 0 then 0.0
                    else 1.0 / cast(count(distinct wipo_industry_code) as double)
                end as family_field_fraction,
                min(family_earliest_priority_date) as family_earliest_priority_date,
                count(distinct appln_id) as in_scope_appln_count
            from read_parquet('{appln_seed_path}')
            group by docdb_family_id
        ) to '{out_fields}' (format parquet, compression zstd)
        """
    )
    owner_metrics = _build_owner_contracts(
        con,
        owner_seed_path=owner_seed_path,
        out_owner_bridge=out_owner_bridge,
        out_owner=out_owner,
    )

    LOGGER.info("Building silver_family_ipc_cpc_canonical")
    ipc_path = settings.bronze_dir / "bronze_patstat_appln_ipc.parquet"
    cpc_path = settings.bronze_dir / "bronze_patstat_appln_cpc.parquet"
    if ipc_path.exists() or cpc_path.exists():
        ipc_sql = (
            f"""
            select
                a.docdb_family_id,
                regexp_replace(cast(i.{_pick(parquet_columns(ipc_path), ['ipc_class_symbol'])} as varchar), '\\s+', '', 'g') as code_symbol,
                'IPC' as code_system
            from read_parquet('{appln_seed_path}') a
            join read_parquet('{ipc_path}') i using (appln_id)
            """
            if ipc_path.exists()
            else "select null::bigint as docdb_family_id, null::varchar as code_symbol, null::varchar as code_system where false"
        )
        cpc_sql = (
            f"""
            select
                a.docdb_family_id,
                regexp_replace(cast(c.{_pick(parquet_columns(cpc_path), ['cpc_class_symbol'])} as varchar), '\\s+', '', 'g') as code_symbol,
                'CPC' as code_system
            from read_parquet('{appln_seed_path}') a
            join read_parquet('{cpc_path}') c using (appln_id)
            """
            if cpc_path.exists()
            else "select null::bigint as docdb_family_id, null::varchar as code_symbol, null::varchar as code_system where false"
        )
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    list(distinct code_symbol order by code_symbol) filter (where code_system = 'IPC') as ipc_symbols,
                    list(distinct code_symbol order by code_symbol) filter (where code_system = 'CPC') as cpc_symbols
                from (
                    {ipc_sql}
                    union all
                    {cpc_sql}
                )
                group by docdb_family_id
            ) to '{out_codes}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    []::varchar[] as ipc_symbols,
                    []::varchar[] as cpc_symbols
                from read_parquet('{out_core}')
            ) to '{out_codes}' (format parquet, compression zstd)
            """
        )

    LOGGER.info("Building silver_tiered_market_weighting")
    iso_path = settings.bronze_dir / "bronze_ext_iso_country_map.parquet"
    gdp_path = settings.bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet"
    ip_path = settings.bronze_dir / "bronze_ext_us_chamber_ip_index.parquet"
    if iso_path.exists() and gdp_path.exists():
        iso_cols = parquet_columns(iso_path)
        gdp_cols = parquet_columns(gdp_path)
        ip_cols = parquet_columns(ip_path) if ip_path.exists() else []
        iso2 = _pick(iso_cols, ["iso2"])
        iso3 = _pick(iso_cols, ["iso3"])
        gdp_iso3 = _pick(gdp_cols, ["iso3"])
        gdp_year = _pick(gdp_cols, ["snapshot_year"])
        gdp_value = _pick(gdp_cols, ["gdp_value"])
        ip_iso2 = _pick(ip_cols, ["iso2"], required=False) if ip_cols else None
        ip_year = _pick(ip_cols, ["snapshot_year"], required=False) if ip_cols else None
        ip_score = _pick(ip_cols, ["ip_score"], required=False) if ip_cols else None
        if ip_path.exists() and ip_iso2 and ip_year and ip_score:
            con.execute(
                f"""
                copy (
                    with gdp as (
                        select *
                        from read_parquet('{gdp_path}')
                        where cast({gdp_year} as int) <= {build_snapshot_year}
                    ),
                    ip as (
                        select *
                        from read_parquet('{ip_path}')
                        where cast({ip_year} as int) <= {build_snapshot_year}
                    )
                    select
                        cast(m.{iso2} as varchar) as jurisdiction_code,
                        cast(g.{gdp_year} as int) as snapshot_year,
                        cast(g.{gdp_value} as double) as gdp_value,
                        coalesce(cast(i.{ip_score} as double), 25.0) as ip_score,
                        case
                            when cast(g.{gdp_value} as double) >= 5000000000000 then 5.0
                            when cast(g.{gdp_value} as double) >= 1000000000000 then 3.0
                            when cast(g.{gdp_value} as double) >= 100000000000 then 1.0
                            else 0.2
                        end as gdp_tier_weight,
                        round(
                            (
                                case
                                    when cast(g.{gdp_value} as double) >= 5000000000000 then 5.0
                                    when cast(g.{gdp_value} as double) >= 1000000000000 then 3.0
                                    when cast(g.{gdp_value} as double) >= 100000000000 then 1.0
                                    else 0.2
                                end
                            ) * (coalesce(cast(i.{ip_score} as double), 25.0) / 100.0),
                            2
                        ) as final_market_multiplier
                    from gdp g
                    join read_parquet('{iso_path}') m
                      on cast(g.{gdp_iso3} as varchar) = cast(m.{iso3} as varchar)
                    left join ip i
                      on cast(m.{iso2} as varchar) = cast(i.{ip_iso2} as varchar)
                     and cast(g.{gdp_year} as int) = cast(i.{ip_year} as int)
                ) to '{out_weight}' (format parquet, compression zstd)
                """
            )
        else:
            con.execute(
                f"""
                copy (
                    with gdp as (
                        select *
                        from read_parquet('{gdp_path}')
                        where cast({gdp_year} as int) <= {build_snapshot_year}
                    )
                    select
                        cast(m.{iso2} as varchar) as jurisdiction_code,
                        cast(g.{gdp_year} as int) as snapshot_year,
                        cast(g.{gdp_value} as double) as gdp_value,
                        25.0::double as ip_score,
                        case
                            when cast(g.{gdp_value} as double) >= 5000000000000 then 5.0
                            when cast(g.{gdp_value} as double) >= 1000000000000 then 3.0
                            when cast(g.{gdp_value} as double) >= 100000000000 then 1.0
                            else 0.2
                        end as gdp_tier_weight,
                        round(
                            (
                                case
                                    when cast(g.{gdp_value} as double) >= 5000000000000 then 5.0
                                    when cast(g.{gdp_value} as double) >= 1000000000000 then 3.0
                                    when cast(g.{gdp_value} as double) >= 100000000000 then 1.0
                                    else 0.2
                                end
                            ) * 0.25,
                            2
                        ) as final_market_multiplier
                    from gdp g
                    join read_parquet('{iso_path}') m
                      on cast(g.{gdp_iso3} as varchar) = cast(m.{iso3} as varchar)
                ) to '{out_weight}' (format parquet, compression zstd)
                """
            )
    else:
        con.execute(
            f"""
            copy (
                select distinct
                    publn_auth as jurisdiction_code,
                    {build_snapshot_year} as snapshot_year,
                    null::double as gdp_value,
                    25.0::double as ip_score,
                    case
                        when publn_auth in ('US') then 5.0
                        when publn_auth in ('EP', 'JP', 'CN') then 3.0
                        when publn_auth in ('WO') then 0.2
                        else 1.0
                    end as gdp_tier_weight,
                    round(
                        (
                            case
                                when publn_auth in ('US') then 5.0
                                when publn_auth in ('EP', 'JP', 'CN') then 3.0
                                when publn_auth in ('WO') then 0.2
                                else 1.0
                            end
                        ) * 0.25,
                        2
                    ) as final_market_multiplier
                from read_parquet('{out_member}')
            ) to '{out_weight}' (format parquet, compression zstd)
            """
        )
        result.warnings.append("Tiered market weighting fell back to heuristic office buckets because GDP/IP reference tables were unavailable.")

    LOGGER.info("Building silver_up_status and silver_family_jurisdiction_unrolled")
    up_member_states = settings.bronze_dir / "bronze_ext_up_member_states.parquet"
    if up_member_states.exists():
        state_cols = parquet_columns(up_member_states)
        state_col = _pick(state_cols, ["jurisdiction_code", "country_code", "state_code", "country"], required=False) or parquet_columns(up_member_states)[0]
        con.execute(
            f"""
            copy (
                with classic as (
                    select distinct
                        docdb_family_id,
                        publn_auth as jurisdiction_code,
                        publn_auth as source_auth,
                        false as is_up_unrolled,
                        publn_auth = 'EP' and coalesce(publn_kind, '') <> 'C0' as is_classic_validation,
                        publn_auth = 'WO' as is_global_member
                    from read_parquet('{out_member}')
                ),
                up_expanded as (
                    select
                        m.docdb_family_id,
                        cast(s.{state_col} as varchar) as jurisdiction_code,
                        'EP' as source_auth,
                        true as is_up_unrolled,
                        false as is_classic_validation,
                        false as is_global_member
                    from read_parquet('{out_member}') m
                    cross join read_parquet('{up_member_states}') s
                    where m.publn_kind = 'C0'
                ),
                merged as (
                    select * from classic
                    union all
                    select * from up_expanded
                )
                select
                    docdb_family_id,
                    jurisdiction_code,
                    max_by(
                        source_auth,
                        case
                            when source_auth = jurisdiction_code then 2
                            when is_up_unrolled then 0
                            else 1
                        end
                    ) as source_auth,
                    max(cast(is_up_unrolled as integer)) > 0 as is_up_unrolled,
                    max(cast(is_classic_validation as integer)) > 0 as is_classic_validation,
                    max(cast(is_global_member as integer)) > 0 as is_global_member
                from merged
                group by docdb_family_id, jurisdiction_code
            ) to '{out_jur}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    publn_auth as jurisdiction_code,
                    publn_auth as source_auth,
                    false as is_up_unrolled,
                    max(cast(publn_auth = 'EP' and coalesce(publn_kind, '') <> 'C0' as integer)) > 0 as is_classic_validation,
                    max(cast(publn_auth = 'WO' as integer)) > 0 as is_global_member
                from read_parquet('{out_member}')
                group by docdb_family_id, publn_auth
            ) to '{out_jur}' (format parquet, compression zstd)
            """
        )
    con.execute(
        f"""
        copy (
            with up_flags as (
                select
                    docdb_family_id,
                    max(case when publn_kind = 'C0' then 1 else 0 end) > 0 as has_up_registration
                from read_parquet('{out_member}')
                group by docdb_family_id
            ),
            up_counts as (
                select
                    docdb_family_id,
                    count(distinct case when is_up_unrolled then jurisdiction_code end) as up_member_state_count
                from read_parquet('{out_jur}')
                group by docdb_family_id
            )
            select
                f.docdb_family_id,
                f.has_up_registration,
                case
                    when f.has_up_registration then 'EP_C0_PUBLICATION'
                    else 'NONE'
                end as up_detection_method,
                coalesce(c.up_member_state_count, 0) as up_member_state_count
            from up_flags f
            left join up_counts c
              on f.docdb_family_id = c.docdb_family_id
        ) to '{out_up}' (format parquet, compression zstd)
        """
    )

    LOGGER.info("Building silver_legal_status_event_ledger and silver_family_status_pt")
    legal_path = settings.bronze_dir / "bronze_patstat_inpadoc_legal_event.parquet"
    if legal_path.exists():
        legal_cols = parquet_columns(legal_path)
        legal_appln = _pick(legal_cols, ["appln_id"])
        legal_auth = _pick(legal_cols, ["event_auth", "publn_auth", "auth"], required=False)
        legal_event = _pick(legal_cols, ["event_code", "legal_event_code"], required=False)
        legal_effective_date = _pick(legal_cols, ["event_effective_date", "event_date", "lec_date"], required=False)
        legal_publn_date = _pick(legal_cols, ["event_publn_date", "published_date"], required=False)
        legal_filing_date = _pick(legal_cols, ["event_filing_date"], required=False)
        legal_lapse_date = _pick(legal_cols, ["lapse_date"], required=False)
        legal_spc_expiry_date = _pick(legal_cols, ["spc_patent_expiry_date", "spc_extension_date"], required=False)
        legal_auth_expr = _sql_column_expr("l", legal_auth)
        legal_event_expr = _sql_column_expr("l", legal_event)
        legal_event_upper = f"upper(coalesce({legal_event_expr}, ''))"
        legal_default_date_expr = _sql_first_valid_date_expr(
            [
                legal_effective_date,
                legal_publn_date,
                legal_filing_date,
                legal_lapse_date,
                legal_spc_expiry_date,
            ],
            alias="l",
        )
        legal_negative_date_expr = _sql_first_valid_date_expr(
            [
                legal_lapse_date,
                legal_spc_expiry_date,
                legal_effective_date,
                legal_publn_date,
                legal_filing_date,
            ],
            alias="l",
        )
        con.execute(
            f"""
            copy (
                with pub_events as (
                    select
                        m.docdb_family_id,
                        m.appln_id,
                        m.publn_auth as jurisdiction_code,
                        m.publn_date as event_date,
                        'publication_date' as event_date_source,
                        m.publn_kind as event_code,
                        k.universal_stage as event_type,
                        case
                            when k.is_enforceable then 'active'
                            when k.is_application_stage then 'pending'
                            else 'informational'
                        end as event_severity,
                        k.universal_stage in ('STANDARD_GRANT', 'OPPOSITION_SURVIVOR', 'UNITARY_GRANT') as is_grant_event,
                        false as is_lapse_event,
                        false as is_opposition_event,
                        false as is_expiry_event,
                        k.universal_stage = 'UNITARY_GRANT' as is_up_event
                    from read_parquet('{out_member}') m
                    join read_parquet('{out_kind}') k
                      on m.publn_auth = k.jurisdiction_code
                     and m.publn_kind = k.kind_code
                ),
                legal_events as (
                    select
                        a.docdb_family_id,
                        a.appln_id,
                        coalesce({legal_auth_expr}, a.appln_auth) as jurisdiction_code,
                        case
                            when {legal_event_upper} like '%LAP%' then {legal_negative_date_expr}
                            when {legal_event_upper} like '%EXP%' then {legal_negative_date_expr}
                            else {legal_default_date_expr}
                        end as event_date,
                        case
                            when {legal_event_upper} like '%LAP%' then {_sql_first_valid_date_source_expr([
                                (legal_lapse_date, "lapse_date"),
                                (legal_spc_expiry_date, "spc_patent_expiry_date"),
                                (legal_effective_date, "event_effective_date"),
                                (legal_publn_date, "event_publn_date"),
                                (legal_filing_date, "event_filing_date"),
                            ], alias="l")}
                            when {legal_event_upper} like '%EXP%' then {_sql_first_valid_date_source_expr([
                                (legal_lapse_date, "lapse_date"),
                                (legal_spc_expiry_date, "spc_patent_expiry_date"),
                                (legal_effective_date, "event_effective_date"),
                                (legal_publn_date, "event_publn_date"),
                                (legal_filing_date, "event_filing_date"),
                            ], alias="l")}
                            else {_sql_first_valid_date_source_expr([
                                (legal_effective_date, "event_effective_date"),
                                (legal_publn_date, "event_publn_date"),
                                (legal_filing_date, "event_filing_date"),
                                (legal_lapse_date, "lapse_date"),
                                (legal_spc_expiry_date, "spc_patent_expiry_date"),
                            ], alias="l")}
                        end as event_date_source,
                        {legal_event_expr} as event_code,
                        case
                            when {legal_event_upper} like '%LAP%' then 'LAPSE'
                            when {legal_event_upper} like '%EXP%' then 'EXPIRY'
                            when {legal_event_upper} like '%OPP%' then 'OPPOSITION'
                            when {legal_event_upper} like '%GRANT%' then 'GRANT'
                            when {legal_event_upper} like '%UP%' then 'UNITARY'
                            else 'LEGAL_EVENT'
                        end as event_type,
                        case
                            when {legal_event_upper} like '%LAP%' then 'inactive'
                            when {legal_event_upper} like '%EXP%' then 'inactive'
                            when {legal_event_upper} like '%OPP%' then 'contested'
                            when {legal_event_upper} like '%GRANT%' then 'active'
                            else 'informational'
                        end as event_severity,
                        {legal_event_upper} like '%GRANT%' as is_grant_event,
                        {legal_event_upper} like '%LAP%' as is_lapse_event,
                        {legal_event_upper} like '%OPP%' as is_opposition_event,
                        {legal_event_upper} like '%EXP%' as is_expiry_event,
                        {legal_event_upper} like '%UP%' as is_up_event
                    from read_parquet('{appln_seed_path}') a
                    join read_parquet('{legal_path}') l
                      on cast(a.appln_id as bigint) = cast(l.{legal_appln} as bigint)
                )
                select * from pub_events
                union all
                select * from legal_events
            ) to '{out_legal}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                select
                    m.docdb_family_id,
                    m.appln_id,
                    m.publn_auth as jurisdiction_code,
                    m.publn_date as event_date,
                    'publication_date' as event_date_source,
                    m.publn_kind as event_code,
                    k.universal_stage as event_type,
                    case
                        when k.is_enforceable then 'active'
                        when k.is_application_stage then 'pending'
                        else 'informational'
                    end as event_severity,
                    k.universal_stage in ('STANDARD_GRANT', 'OPPOSITION_SURVIVOR', 'UNITARY_GRANT') as is_grant_event,
                    false as is_lapse_event,
                    false as is_opposition_event,
                    false as is_expiry_event,
                    k.universal_stage = 'UNITARY_GRANT' as is_up_event
                from read_parquet('{out_member}') m
                join read_parquet('{out_kind}') k
                  on m.publn_auth = k.jurisdiction_code
                 and m.publn_kind = k.kind_code
            ) to '{out_legal}' (format parquet, compression zstd)
            """
        )
    con.execute(
        f"""
        copy (
            with current_branch_dates as (
                select
                    docdb_family_id,
                    jurisdiction_code,
                    max(case when is_grant_event then event_date end) as last_grant_event_date,
                    max(case when is_lapse_event then event_date end) as last_lapse_event_date,
                    max(case when is_expiry_event then event_date end) as last_expiry_event_date,
                    max(case when is_opposition_event then event_date end) as last_opposition_event_date,
                    max(case when upper(coalesce(event_type, '')) like '%PENDING%' then event_date end) as last_pending_event_date
                from read_parquet('{out_legal}')
                where event_date <= date '{snapshot_date}'
                group by docdb_family_id, jurisdiction_code
            ),
            current_branch_state as (
                select
                    j.docdb_family_id,
                    j.jurisdiction_code,
                    greatest(d.last_lapse_event_date, d.last_expiry_event_date) as last_negative_event_date,
                    d.last_grant_event_date,
                    d.last_lapse_event_date,
                    d.last_expiry_event_date,
                    d.last_opposition_event_date,
                    d.last_pending_event_date,
                    case
                        when d.last_grant_event_date is not null
                         and (greatest(d.last_lapse_event_date, d.last_expiry_event_date) is null
                              or d.last_grant_event_date > greatest(d.last_lapse_event_date, d.last_expiry_event_date))
                         and d.last_opposition_event_date is not null
                         and d.last_opposition_event_date >= d.last_grant_event_date then 'ACTIVE_OPPOSED_GRANT'
                        when d.last_grant_event_date is not null
                         and (greatest(d.last_lapse_event_date, d.last_expiry_event_date) is null
                              or d.last_grant_event_date > greatest(d.last_lapse_event_date, d.last_expiry_event_date)) then 'ACTIVE_GRANT'
                        when greatest(d.last_lapse_event_date, d.last_expiry_event_date) is not null
                         and (d.last_grant_event_date is null
                              or greatest(d.last_lapse_event_date, d.last_expiry_event_date) >= d.last_grant_event_date) then 'LAPSED_OR_EXPIRED'
                        when d.last_pending_event_date is not null
                         and d.last_grant_event_date is null then 'PENDING_ONLY'
                        else 'NO_ACTIVE_STATE'
                    end as replay_branch_state
                from read_parquet('{out_jur}') j
                left join current_branch_dates d
                  on j.docdb_family_id = d.docdb_family_id
                 and j.jurisdiction_code = d.jurisdiction_code
            )
            select
                docdb_family_id,
                date '{snapshot_date}' as snapshot_date,
                case
                    when sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) > 0
                     and sum(case when replay_branch_state = 'ACTIVE_OPPOSED_GRANT' then 1 else 0 end) > 0 then 'under_fire'
                    when sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) > 0
                     and sum(case when replay_branch_state = 'LAPSED_OR_EXPIRED' then 1 else 0 end) > 0 then 'partially_lapsed'
                    when sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) > 0 then 'fully_active'
                    when sum(case when replay_branch_state = 'PENDING_ONLY' then 1 else 0 end) > 0 then 'pending_emerging'
                    else 'dead'
                end as family_composite_status,
                sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) as active_jurisdiction_count,
                sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) as active_grant_branch_count,
                sum(case when replay_branch_state = 'LAPSED_OR_EXPIRED' then 1 else 0 end) as lapsed_jurisdiction_count,
                sum(case when replay_branch_state = 'ACTIVE_OPPOSED_GRANT' then 1 else 0 end) as opposed_branch_count,
                sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) > 0 as has_any_active_grant,
                sum(case when replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1 else 0 end) = 0
                  and sum(case when replay_branch_state = 'PENDING_ONLY' then 1 else 0 end) = 0 as is_dead_family
            from current_branch_state
            group by docdb_family_id
        ) to '{out_status}' (format parquet, compression zstd)
        """
    )

    history_base_sql = f"""
        with yearly_events as (
            select
                l.docdb_family_id,
                l.jurisdiction_code,
                extract(year from event_date) as snapshot_year,
                max(case when is_grant_event then event_date end) as grant_event_date_in_year,
                max(case when is_lapse_event then event_date end) as lapse_event_date_in_year,
                max(case when is_expiry_event then event_date end) as expiry_event_date_in_year,
                max(case when is_opposition_event then event_date end) as opposition_event_date_in_year,
                max(case when upper(coalesce(event_type, '')) like '%PENDING%' then event_date end) as pending_event_date_in_year
            from read_parquet('{out_legal}') l
            where event_date is not null
              and extract(year from event_date) <= {build_snapshot_year}
            group by l.docdb_family_id, l.jurisdiction_code, extract(year from event_date)
        ),
        history_years as (
            select distinct docdb_family_id, jurisdiction_code, snapshot_year
            from yearly_events
            union
            select distinct docdb_family_id, jurisdiction_code, {build_snapshot_year} as snapshot_year
            from read_parquet('{out_jur}')
        ),
        branch_year_replay as (
            select
                y.docdb_family_id,
                y.jurisdiction_code,
                y.snapshot_year,
                max(e.grant_event_date_in_year) over branch_window as last_grant_event_date,
                max(e.lapse_event_date_in_year) over branch_window as last_lapse_event_date,
                max(e.expiry_event_date_in_year) over branch_window as last_expiry_event_date,
                max(e.opposition_event_date_in_year) over branch_window as last_opposition_event_date,
                max(e.pending_event_date_in_year) over branch_window as last_pending_event_date
            from history_years y
            left join yearly_events e
              on y.docdb_family_id = e.docdb_family_id
             and y.jurisdiction_code = e.jurisdiction_code
             and y.snapshot_year = e.snapshot_year
            window branch_window as (
                partition by y.docdb_family_id, y.jurisdiction_code
                order by y.snapshot_year
                rows between unbounded preceding and current row
            )
        ),
        branch_year_state as (
            select
                r.docdb_family_id,
                r.jurisdiction_code,
                r.snapshot_year,
                case
                    when r.snapshot_year = {build_snapshot_year} then date '{snapshot_date}'
                    else make_date(r.snapshot_year, 12, 31)
                end as snapshot_date,
                r.last_grant_event_date,
                r.last_lapse_event_date,
                r.last_expiry_event_date,
                greatest(r.last_lapse_event_date, r.last_expiry_event_date) as last_negative_event_date,
                r.last_opposition_event_date,
                r.last_pending_event_date,
                case
                    when r.last_grant_event_date is not null
                     and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                          or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date))
                     and r.last_opposition_event_date is not null
                     and r.last_opposition_event_date >= r.last_grant_event_date then 'ACTIVE_OPPOSED_GRANT'
                    when r.last_grant_event_date is not null
                     and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                          or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date)) then 'ACTIVE_GRANT'
                    when greatest(r.last_lapse_event_date, r.last_expiry_event_date) is not null
                     and (r.last_grant_event_date is null
                          or greatest(r.last_lapse_event_date, r.last_expiry_event_date) >= r.last_grant_event_date) then 'LAPSED_OR_EXPIRED'
                    when r.last_pending_event_date is not null
                     and r.last_grant_event_date is null then 'PENDING_ONLY'
                    else 'NO_ACTIVE_STATE'
                end as replay_branch_state,
                case
                    when r.last_grant_event_date is not null
                     and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                          or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date)) then true
                    else false
                end as active_branch_flag,
                case
                    when greatest(r.last_lapse_event_date, r.last_expiry_event_date) is not null
                     and (r.last_grant_event_date is null
                          or greatest(r.last_lapse_event_date, r.last_expiry_event_date) >= r.last_grant_event_date) then true
                    else false
                end as lapsed_or_expired_flag,
                case
                    when (
                        r.last_pending_event_date is not null
                        and r.last_grant_event_date is null
                        and greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                    ) then true
                    else false
                end as pending_branch_flag,
                case
                    when r.last_grant_event_date is not null
                     and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                          or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date))
                     and r.last_opposition_event_date is not null
                     and r.last_opposition_event_date >= r.last_grant_event_date then true
                    else false
                end as opposed_branch_flag
            from branch_year_replay r
        )
    """

    con.execute(
        f"""
        copy (
            {history_base_sql},
            compact_branch_history as (
                select *
                from (
                    select
                        b.*,
                        lag(replay_branch_state) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_branch_state,
                        lag(active_branch_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_active_branch_flag,
                        lag(lapsed_or_expired_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_lapsed_or_expired_flag,
                        lag(pending_branch_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_pending_branch_flag,
                        lag(opposed_branch_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_opposed_branch_flag
                    from branch_year_state b
                )
                where prev_branch_state is null
                   or replay_branch_state <> prev_branch_state
                   or active_branch_flag <> prev_active_branch_flag
                   or lapsed_or_expired_flag <> prev_lapsed_or_expired_flag
                   or pending_branch_flag <> prev_pending_branch_flag
                   or opposed_branch_flag <> prev_opposed_branch_flag
                   or snapshot_year = {build_snapshot_year}
            )
            select
                h.docdb_family_id,
                h.jurisdiction_code,
                h.snapshot_year,
                h.snapshot_date,
                j.source_auth,
                j.is_up_unrolled,
                j.is_classic_validation,
                j.is_global_member,
                h.last_grant_event_date,
                h.last_lapse_event_date,
                h.last_expiry_event_date,
                h.last_negative_event_date,
                h.last_opposition_event_date,
                h.last_pending_event_date,
                h.replay_branch_state,
                h.active_branch_flag,
                h.lapsed_or_expired_flag,
                h.pending_branch_flag,
                h.opposed_branch_flag
            from compact_branch_history h
            left join read_parquet('{out_jur}') j
              on h.docdb_family_id = j.docdb_family_id
             and h.jurisdiction_code = j.jurisdiction_code
        ) to '{out_branch_history}' (format parquet, compression zstd)
        """
    )

    con.execute(
        f"""
        copy (
            with family_start_year as (
                select
                    docdb_family_id,
                    min(snapshot_year) as start_year
                from read_parquet('{out_branch_history}')
                group by docdb_family_id
            ),
            family_years as (
                select
                    s.docdb_family_id,
                    y.snapshot_year
                from family_start_year s
                cross join generate_series(
                    cast(s.start_year as bigint),
                    cast({build_snapshot_year} as bigint),
                    cast(1 as bigint)
                ) as y(snapshot_year)
            ),
            branch_deltas as (
                select
                    docdb_family_id,
                    snapshot_year,
                    sum(active_flag - prev_active_flag) as active_delta,
                    sum(lapsed_flag - prev_lapsed_flag) as lapsed_delta,
                    sum(opposed_flag - prev_opposed_flag) as opposed_delta,
                    sum(pending_flag - prev_pending_flag) as pending_delta
                from (
                    select
                        docdb_family_id,
                        jurisdiction_code,
                        snapshot_year,
                        case when coalesce(active_branch_flag, false) then 1 else 0 end as active_flag,
                        case when coalesce(lapsed_or_expired_flag, false) then 1 else 0 end as lapsed_flag,
                        case when coalesce(opposed_branch_flag, false) then 1 else 0 end as opposed_flag,
                        case when replay_branch_state = 'PENDING_ONLY' then 1 else 0 end as pending_flag,
                        lag(case when coalesce(active_branch_flag, false) then 1 else 0 end, 1, 0)
                            over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_active_flag,
                        lag(case when coalesce(lapsed_or_expired_flag, false) then 1 else 0 end, 1, 0)
                            over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_lapsed_flag,
                        lag(case when coalesce(opposed_branch_flag, false) then 1 else 0 end, 1, 0)
                            over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_opposed_flag,
                        lag(case when replay_branch_state = 'PENDING_ONLY' then 1 else 0 end, 1, 0)
                            over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_pending_flag
                    from read_parquet('{out_branch_history}')
                )
                group by docdb_family_id, snapshot_year
            ),
            running_family_counts as (
                select
                    y.docdb_family_id,
                    y.snapshot_year,
                    case
                        when y.snapshot_year = {build_snapshot_year} then date '{snapshot_date}'
                        else make_date(y.snapshot_year, 12, 31)
                    end as snapshot_date,
                    sum(coalesce(d.active_delta, 0)) over (
                        partition by y.docdb_family_id
                        order by y.snapshot_year
                        rows between unbounded preceding and current row
                    ) as active_jurisdiction_count,
                    sum(coalesce(d.lapsed_delta, 0)) over (
                        partition by y.docdb_family_id
                        order by y.snapshot_year
                        rows between unbounded preceding and current row
                    ) as lapsed_jurisdiction_count,
                    sum(coalesce(d.opposed_delta, 0)) over (
                        partition by y.docdb_family_id
                        order by y.snapshot_year
                        rows between unbounded preceding and current row
                    ) as opposed_branch_count,
                    sum(coalesce(d.pending_delta, 0)) over (
                        partition by y.docdb_family_id
                        order by y.snapshot_year
                        rows between unbounded preceding and current row
                    ) as pending_branch_count
                from family_years y
                left join branch_deltas d
                  on y.docdb_family_id = d.docdb_family_id
                 and y.snapshot_year = d.snapshot_year
            ),
            full_family_history as (
                select
                    docdb_family_id,
                    snapshot_year,
                    snapshot_date,
                    case
                        when active_jurisdiction_count > 0 and opposed_branch_count > 0 then 'under_fire'
                        when active_jurisdiction_count > 0 and lapsed_jurisdiction_count > 0 then 'partially_lapsed'
                        when active_jurisdiction_count > 0 then 'fully_active'
                        when pending_branch_count > 0 then 'pending_emerging'
                        else 'dead'
                    end as family_composite_status,
                    cast(active_jurisdiction_count as bigint) as active_jurisdiction_count,
                    cast(active_jurisdiction_count as bigint) as active_grant_branch_count,
                    cast(lapsed_jurisdiction_count as bigint) as lapsed_jurisdiction_count,
                    cast(opposed_branch_count as bigint) as opposed_branch_count,
                    active_jurisdiction_count > 0 as has_any_active_grant,
                    active_jurisdiction_count = 0 and pending_branch_count = 0 as is_dead_family
                from running_family_counts
            )
            select * from full_family_history
        ) to '{out_family_history}' (format parquet, compression zstd)
        """
    )

    LOGGER.info("Building silver_ep_register_* tables")
    reg101 = settings.bronze_dir / "bronze_reg101_appln.parquet"
    reg403 = settings.bronze_dir / "bronze_reg403_appln_status.parquet"
    reg111 = settings.bronze_dir / "bronze_reg111_licensee.parquet"
    reg107 = settings.bronze_dir / "bronze_reg107_parties.parquet"
    reg130 = settings.bronze_dir / "bronze_reg130_opponent.parquet"
    reg125 = settings.bronze_dir / "bronze_reg125_appeal.parquet"
    reg201 = settings.bronze_dir / "bronze_reg201_proc_step.parquet"
    reg202 = settings.bronze_dir / "bronze_reg202_proc_step_text.parquet"
    reg203 = settings.bronze_dir / "bronze_reg203_proc_step_date.parquet"
    reg301 = settings.bronze_dir / "bronze_reg301_event_data.parquet"
    reg402 = settings.bronze_dir / "bronze_reg402_event_text.parquet"
    reg701 = settings.bronze_dir / "bronze_reg701_appln.parquet"
    reg731 = settings.bronze_dir / "bronze_reg731_event_data.parquet"
    reg741 = settings.bronze_dir / "bronze_reg741_appln_status.parquet"

    if reg101.exists():
        reg101_cols = parquet_columns(reg101)
        reg_id = _pick(reg101_cols, ["id"])
        reg_appln_id = _pick(reg101_cols, ["appln_id"])
        reg_status = _pick(reg101_cols, ["status"], required=False)
        reg403_cols = parquet_columns(reg403) if reg403.exists() else []
        reg403_status = _pick(reg403_cols, ["status"], required=False) if reg403_cols else None
        reg403_text = _pick(reg403_cols, ["status_text"], required=False) if reg403_cols else None
        licensee_sql = "select null::bigint as id, false as ep_registered_license_flag, null::varchar as ep_licensee_names where false"
        if reg111.exists():
            reg111_cols = parquet_columns(reg111)
            lic_id = _pick(reg111_cols, ["id"])
            lic_name = _pick(reg111_cols, ["licensee_name", "name"], required=False) or lic_id
            licensee_sql = f"""
                select
                    cast({lic_id} as bigint) as id,
                    true as ep_registered_license_flag,
                    string_agg(distinct cast({lic_name} as varchar), '; ' order by cast({lic_name} as varchar)) as ep_licensee_names
                from read_parquet('{reg111}')
                group by 1
            """
        con.execute(
            f"""
            copy (
                select
                    cast(r.{reg_appln_id} as bigint) as appln_id,
                    a.docdb_family_id,
                    cast(r.{reg_id} as bigint) as reg101_id,
                    true as register_record_present,
                    coalesce(l.ep_registered_license_flag, false) as ep_registered_license_flag,
                    l.ep_licensee_names,
                    date '{snapshot_date}' as register_snapshot_date
                from read_parquet('{reg101}') r
                join read_parquet('{appln_seed_path}') a
                  on cast(r.{reg_appln_id} as bigint) = cast(a.appln_id as bigint)
                left join ({licensee_sql}) l
                  on cast(r.{reg_id} as bigint) = l.id
            ) to '{out_register}' (format parquet, compression zstd)
            """
        )

        if reg107.exists():
            reg107_cols = parquet_columns(reg107)
            p_id = _pick(reg107_cols, ["id"])
            p_name = _pick(reg107_cols, ["customer_name", "party_name", "name"], required=False) or p_id
            p_country = _pick(reg107_cols, ["country", "ctry_code", "address_country"], required=False)
            p_customer_id = _pick(reg107_cols, ["customer_id"], required=False)
            con.execute(
                f"""
                copy (
                    select
                        c.appln_id,
                        cast(max_by(cast(p.{p_name} as varchar), cast(p.{p_id} as bigint)) as varchar) as ep_register_lead_agent_name,
                        max_by({_sql_column_expr('p', p_country)}, cast(p.{p_id} as bigint)) as ep_register_lead_agent_country,
                        max_by({_sql_column_expr('p', p_customer_id, 'bigint')}, cast(p.{p_id} as bigint)) as ep_register_agent_customer_id
                    from read_parquet('{out_register}') c
                    join read_parquet('{reg107}') p
                      on c.reg101_id = cast(p.{p_id} as bigint)
                    group by c.appln_id
                ) to '{out_register_agent}' (format parquet, compression zstd)
                """
            )
        else:
            con.execute(f"copy (select appln_id, null::varchar as ep_register_lead_agent_name, null::varchar as ep_register_lead_agent_country, null::bigint as ep_register_agent_customer_id from read_parquet('{out_register}') where false) to '{out_register_agent}' (format parquet, compression zstd)")

        if reg130.exists() or reg125.exists():
            opp_sql = "select null::bigint as id, false as ep_opposition_active, null::varchar as ep_opposition_status_text, null::varchar as ep_opponent_names, null::varchar as ep_opponent_agent_names where false"
            if reg130.exists():
                reg130_cols = parquet_columns(reg130)
                opp_id = _pick(reg130_cols, ["id"])
                opp_name = _pick(reg130_cols, ["oppt_name"], required=False) or opp_id
                opp_agent = _pick(reg130_cols, ["agent_name"], required=False)
                opp_status = _pick(reg130_cols, ["oppt_status"], required=False)
                opp_sql = f"""
                    select
                        cast(o.{opp_id} as bigint) as id,
                        true as ep_opposition_active,
                        max({_sql_column_expr('o', opp_status)}) as ep_opposition_status_text,
                        string_agg(distinct cast(o.{opp_name} as varchar), '; ' order by cast(o.{opp_name} as varchar)) as ep_opponent_names,
                        string_agg(distinct {_sql_column_expr('o', opp_agent)}, '; ' order by {_sql_column_expr('o', opp_agent)}) as ep_opponent_agent_names
                    from read_parquet('{reg130}') o
                    group by 1
                """
            appeal_sql = "select null::bigint as id, false as ep_appeal_active, null::varchar as ep_appeal_result_text where false"
            if reg125.exists():
                reg125_cols = parquet_columns(reg125)
                app_id = _pick(reg125_cols, ["id"])
                app_result = _pick(reg125_cols, ["appeal_result", "result_text", "result", "status"], required=False)
                appeal_sql = f"""
                    select
                        cast(a.{app_id} as bigint) as id,
                        true as ep_appeal_active,
                        max({_sql_column_expr('a', app_result)}) as ep_appeal_result_text
                    from read_parquet('{reg125}') a
                    group by 1
                """
            con.execute(
                f"""
                copy (
                    select
                        c.appln_id,
                        coalesce(o.ep_opposition_active, false) as ep_opposition_active,
                        o.ep_opposition_status_text,
                        o.ep_opponent_names,
                        o.ep_opponent_agent_names,
                        coalesce(a.ep_appeal_active, false) as ep_appeal_active,
                        a.ep_appeal_result_text
                    from read_parquet('{out_register}') c
                    left join ({opp_sql}) o on c.reg101_id = o.id
                    left join ({appeal_sql}) a on c.reg101_id = a.id
                ) to '{out_register_opposition}' (format parquet, compression zstd)
                """
            )
        else:
            con.execute(f"copy (select appln_id, false as ep_opposition_active, null::varchar as ep_opposition_status_text, null::varchar as ep_opponent_names, null::varchar as ep_opponent_agent_names, false as ep_appeal_active, null::varchar as ep_appeal_result_text from read_parquet('{out_register}') where false) to '{out_register_opposition}' (format parquet, compression zstd)")

        if reg701.exists():
            reg701_cols = parquet_columns(reg701)
            reg701_id = _pick(reg701_cols, ["id"])
            reg701_appln = _pick(reg701_cols, ["appln_id"], required=False)
            reg741_cols = parquet_columns(reg741) if reg741.exists() else []
            reg741_status = _pick(reg741_cols, ["status"], required=False) if reg741_cols else None
            reg741_text = _pick(reg741_cols, ["status_text", "appln_status"], required=False) if reg741_cols else None
            reg731_cols = parquet_columns(reg731) if reg731.exists() else []
            reg731_id = _pick(reg731_cols, ["id"], required=False) if reg731_cols else None
            reg731_date = _pick(reg731_cols, ["event_date"], required=False) if reg731_cols else None
            reg741_join = (
                f"left join read_parquet('{reg741}') u on cast(r.status as varchar) = cast(u.{reg741_status} as varchar)"
                if reg741.exists() and reg741_status
                else ""
            )
            reg741_status_expr = _sql_column_expr("u", reg741_status)
            reg741_text_expr = _sql_column_expr("u", reg741_text)
            reg731_join = (
                f"left join read_parquet('{reg731}') e on cast(r.{reg701_id} as bigint) = cast(e.{reg731_id} as bigint)"
                if reg731.exists() and reg731_id
                else ""
            )
            con.execute(
                f"""
                copy (
                    select
                        c.appln_id,
                        true as ep_register_is_unitary_patent,
                        {reg741_status_expr} as ep_register_up_status_code,
                        {reg741_text_expr} as ep_register_up_status_text,
                        max({_sql_date_expr(f'e.{reg731_date}') if reg731_date else 'null::date'}) as ep_register_up_event_latest_date
                    from read_parquet('{out_register}') c
                    join read_parquet('{reg701}') r
                      on c.appln_id = cast(r.{reg701_appln or reg701_id} as bigint)
                    {reg741_join}
                    {reg731_join}
                    group by c.appln_id, {reg741_status_expr}, {reg741_text_expr}
                ) to '{out_register_up}' (format parquet, compression zstd)
                """
            )
        else:
            con.execute(f"copy (select appln_id, false as ep_register_is_unitary_patent, null::varchar as ep_register_up_status_code, null::varchar as ep_register_up_status_text, null::date as ep_register_up_event_latest_date from read_parquet('{out_register}') where false) to '{out_register_up}' (format parquet, compression zstd)")

        if reg201.exists():
            reg201_cols = parquet_columns(reg201)
            ps_id = _pick(reg201_cols, ["id"])
            step_id = _pick(reg201_cols, ["step_id"])
            step_phase = _pick(reg201_cols, ["step_phase"], required=False)
            step_result = _pick(reg201_cols, ["step_result"], required=False)
            time_limit = _pick(reg201_cols, ["time_limit"], required=False)
            reg202_cols = parquet_columns(reg202) if reg202.exists() else []
            reg203_cols = parquet_columns(reg203) if reg203.exists() else []
            text_step_id = _pick(reg202_cols, ["step_id"], required=False) if reg202_cols else None
            step_text = _pick(reg202_cols, ["step_text"], required=False) if reg202_cols else None
            date_step_id = _pick(reg203_cols, ["step_id"], required=False) if reg203_cols else None
            step_date = _pick(reg203_cols, ["step_date"], required=False) if reg203_cols else None
            reg202_join = (
                f"left join read_parquet('{reg202}') t on cast(p.{step_id} as bigint) = cast(t.{text_step_id} as bigint)"
                if reg202.exists() and text_step_id
                else ""
            )
            reg203_join = (
                f"left join read_parquet('{reg203}') d on cast(p.{step_id} as bigint) = cast(d.{date_step_id} as bigint)"
                if reg203.exists() and date_step_id
                else ""
            )
            con.execute(
                f"""
                copy (
                    with proc as (
                        select
                            c.appln_id,
                            cast(p.{step_id} as bigint) as step_id,
                            {_sql_column_expr('p', step_phase)} as step_phase,
                            {_sql_column_expr('p', step_result)} as step_result,
                            {_sql_column_expr('p', time_limit, 'bigint')} as time_limit_days,
                            {_sql_column_expr('t', step_text)} as step_text,
                            {_sql_date_expr(f'd.{step_date}') if step_date else 'null::date'} as step_date
                        from read_parquet('{out_register}') c
                        join read_parquet('{reg201}') p
                          on c.reg101_id = cast(p.{ps_id} as bigint)
                        {reg202_join}
                        {reg203_join}
                    )
                    select
                        appln_id,
                        count(*)::double as ep_proc_step_maturity_score,
                        min(case when lower(coalesce(step_text, '')) like '%search report%' then step_date else null end) as ep_search_report_mailed_date,
                        max_by(step_phase, coalesce(step_date, date '{snapshot_date}')) as ep_latest_proc_phase_code,
                        max_by(step_result, coalesce(step_date, date '{snapshot_date}')) as ep_latest_proc_result_code,
                        max(time_limit_days) as ep_proc_time_limit_days
                    from proc
                    group by appln_id
                ) to '{out_register_proc}' (format parquet, compression zstd)
                """
            )
        else:
            con.execute(f"copy (select appln_id, 0.0::double as ep_proc_step_maturity_score, null::date as ep_search_report_mailed_date, null::varchar as ep_latest_proc_phase_code, null::varchar as ep_latest_proc_result_code, null::bigint as ep_proc_time_limit_days from read_parquet('{out_register}') where false) to '{out_register_proc}' (format parquet, compression zstd)")

        con.execute(
            f"""
            copy (
                select
                    c.appln_id,
                    c.docdb_family_id,
                    date '{snapshot_date}' as snapshot_date,
                    coalesce(u.ep_register_up_status_text, o.ep_opposition_status_text, fs.family_composite_status, 'register_present') as ep_display_status_text,
                    case
                        when u.ep_register_up_status_text is not null then 'REGISTER_UP'
                        when o.ep_opposition_status_text is not null then 'REGISTER_OPPOSITION'
                        when fs.family_composite_status is not null then 'FAMILY_STATUS'
                        else 'REGISTER_CORE'
                    end as status_source
                from read_parquet('{out_register}') c
                left join read_parquet('{out_register_up}') u using (appln_id)
                left join read_parquet('{out_register_opposition}') o using (appln_id)
                left join read_parquet('{out_status}') fs using (docdb_family_id)
            ) to '{out_register_display}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(f"copy (select null::bigint as appln_id, null::bigint as docdb_family_id, null::bigint as reg101_id, false as register_record_present, false as ep_registered_license_flag, null::varchar as ep_licensee_names, null::date as register_snapshot_date where false) to '{out_register}' (format parquet, compression zstd)")
        con.execute(f"copy (select null::bigint as appln_id, null::varchar as ep_register_lead_agent_name, null::varchar as ep_register_lead_agent_country, null::bigint as ep_register_agent_customer_id where false) to '{out_register_agent}' (format parquet, compression zstd)")
        con.execute(f"copy (select null::bigint as appln_id, false as ep_opposition_active, null::varchar as ep_opposition_status_text, null::varchar as ep_opponent_names, null::varchar as ep_opponent_agent_names, false as ep_appeal_active, null::varchar as ep_appeal_result_text where false) to '{out_register_opposition}' (format parquet, compression zstd)")
        con.execute(f"copy (select null::bigint as appln_id, false as ep_register_is_unitary_patent, null::varchar as ep_register_up_status_code, null::varchar as ep_register_up_status_text, null::date as ep_register_up_event_latest_date where false) to '{out_register_up}' (format parquet, compression zstd)")
        con.execute(f"copy (select null::bigint as appln_id, 0.0::double as ep_proc_step_maturity_score, null::date as ep_search_report_mailed_date, null::varchar as ep_latest_proc_phase_code, null::varchar as ep_latest_proc_result_code, null::bigint as ep_proc_time_limit_days where false) to '{out_register_proc}' (format parquet, compression zstd)")
        con.execute(f"copy (select null::bigint as appln_id, null::bigint as docdb_family_id, null::date as snapshot_date, null::varchar as ep_display_status_text, null::varchar as status_source where false) to '{out_register_display}' (format parquet, compression zstd)")
        result.warnings.append("EP Register Silver tables were emitted empty because Register Bronze anchors were unavailable.")

    for output in [
        out_core,
        out_member,
        out_kind,
        out_fields,
        out_owner_bridge,
        out_owner,
        out_codes,
        out_weight,
        out_up,
        out_jur,
        out_legal,
        out_branch_history,
        out_family_history,
        out_status,
        out_register,
        out_register_agent,
        out_register_opposition,
        out_register_up,
        out_register_proc,
        out_register_display,
    ]:
        result.outputs.append(str(output))
        result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    result.metrics.update(owner_metrics)
    return result


def build_owner_refresh(settings: BuildSettings) -> StageResult:
    """Refresh Silver owner bridge and primary-owner outputs from the scoped owner seed."""
    owner_seed_path = settings.silver_dir / "silver_scope_owner_seed.parquet"
    out_owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    out_owner = settings.silver_dir / "silver_assignee_harmonized.parquet"

    result = StageResult(
        stage="silver-owner-refresh",
        status="success",
        summary="Rebuilt Silver family-owner bridge and deterministic primary-owner table from the scoped owner seed.",
        inputs=[str(path) for path in [owner_seed_path] if path.exists()],
        methods=[
            "Aggregated the scoped owner seed into one reusable row per family-owner combination.",
            "Selected the primary family owner deterministically by scoped application coverage with stable lexical tie-breaks.",
        ],
        calculations=[
            "Owner harmonization uses UNKNOWN_OWNER only for blank or degenerate normalized names.",
            "Primary-owner ranking prefers non-UNKNOWN_OWNER owners, then highest owner_scope_appln_count, then harmonized/display-name tie-breaks.",
        ],
        doc_refs=[
            "docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
        ],
    )
    if not owner_seed_path.exists():
        result.status = "failed"
        result.warnings.append("silver_scope_owner_seed is required before refreshing owner contracts.")
        return result

    con = duckdb.connect()
    owner_metrics = _build_owner_contracts(
        con,
        owner_seed_path=owner_seed_path,
        out_owner_bridge=out_owner_bridge,
        out_owner=out_owner,
    )
    for output in [out_owner_bridge, out_owner]:
        result.outputs.append(str(output))
        result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    result.metrics.update(owner_metrics)
    return result


def build_history_refresh(settings: BuildSettings, *, bucket_count: int = 16) -> StageResult:
    """Rebuild Silver legal-history sidecars in family buckets to avoid monolithic replay queries."""
    out_jur = settings.silver_dir / "silver_family_jurisdiction_unrolled.parquet"
    out_legal = settings.silver_dir / "silver_legal_status_event_ledger.parquet"
    out_family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    out_branch_history = settings.silver_dir / "silver_branch_status_history.parquet"
    out_branch_history_dense = settings.silver_dir / "silver_branch_status_history_dense.parquet"
    out_family_history = settings.silver_dir / "silver_family_status_history.parquet"

    result = StageResult(
        stage="silver-history-refresh",
        status="success",
        summary="Rebuilt Silver legal-history sidecars in family buckets from the replayable legal ledger.",
        inputs=[str(path) for path in [out_jur, out_legal, out_family_status] if path.exists()],
        methods=[
            "Partitioned families into deterministic buckets and replayed yearly branch state per bucket.",
            "Derived dense yearly branch and family history from compact branch-state deltas rather than one monolithic all-family query.",
        ],
        calculations=[
            "Branch history remains change-point based plus current year, with a separate dense branch-year expansion artifact.",
            "Family history is expanded yearly from the earliest observed branch-history year to the build snapshot year, with current-year rows anchored to silver_family_status_pt.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/blocking-power-lifecycle-and-point-in-time-scoring-requirements.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )
    if not out_jur.exists() or not out_legal.exists() or not out_family_status.exists():
        result.status = "failed"
        result.warnings.append("History refresh requires the Silver jurisdiction unroll, legal-event ledger, and current family status snapshot.")
        return result

    snapshot_date = settings.snapshot_date
    build_snapshot_year = int(snapshot_date[:4])
    temp_dir = ensure_dir(settings.silver_dir / "tmp_history_refresh")
    branch_glob = temp_dir / "branch_bucket_*.parquet"
    branch_dense_glob = temp_dir / "branch_dense_bucket_*.parquet"
    family_glob = temp_dir / "family_bucket_*.parquet"

    for stale in temp_dir.glob("*.parquet"):
        stale.unlink()

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=2")

    for bucket in range(bucket_count):
        branch_slice = temp_dir / f"branch_bucket_{bucket:02d}.parquet"
        branch_dense_slice = temp_dir / f"branch_dense_bucket_{bucket:02d}.parquet"
        family_slice = temp_dir / f"family_bucket_{bucket:02d}.parquet"
        history_base_sql = f"""
            with bucket_families as (
                select distinct docdb_family_id
                from read_parquet('{out_jur}')
                where mod(docdb_family_id, {bucket_count}) = {bucket}
            ),
            yearly_events as (
                select
                    l.docdb_family_id,
                    l.jurisdiction_code,
                    extract(year from event_date) as snapshot_year,
                    max(case when is_grant_event then event_date end) as grant_event_date_in_year,
                    max(case when is_lapse_event then event_date end) as lapse_event_date_in_year,
                    max(case when is_expiry_event then event_date end) as expiry_event_date_in_year,
                    max(case when is_opposition_event then event_date end) as opposition_event_date_in_year,
                    max(case when upper(coalesce(event_type, '')) like '%PENDING%' then event_date end) as pending_event_date_in_year
                from read_parquet('{out_legal}') l
                join bucket_families b
                  on l.docdb_family_id = b.docdb_family_id
                where event_date is not null
                  and extract(year from event_date) <= {build_snapshot_year}
                group by l.docdb_family_id, l.jurisdiction_code, extract(year from event_date)
            ),
            history_years as (
                select distinct docdb_family_id, jurisdiction_code, snapshot_year
                from yearly_events
                union
                select distinct j.docdb_family_id, j.jurisdiction_code, {build_snapshot_year} as snapshot_year
                from read_parquet('{out_jur}') j
                join bucket_families b
                  on j.docdb_family_id = b.docdb_family_id
            ),
            branch_year_replay as (
                select
                    y.docdb_family_id,
                    y.jurisdiction_code,
                    y.snapshot_year,
                    max(e.grant_event_date_in_year) over branch_window as last_grant_event_date,
                    max(e.lapse_event_date_in_year) over branch_window as last_lapse_event_date,
                    max(e.expiry_event_date_in_year) over branch_window as last_expiry_event_date,
                    max(e.opposition_event_date_in_year) over branch_window as last_opposition_event_date,
                    max(e.pending_event_date_in_year) over branch_window as last_pending_event_date
                from history_years y
                left join yearly_events e
                  on y.docdb_family_id = e.docdb_family_id
                 and y.jurisdiction_code = e.jurisdiction_code
                 and y.snapshot_year = e.snapshot_year
                window branch_window as (
                    partition by y.docdb_family_id, y.jurisdiction_code
                    order by y.snapshot_year
                    rows between unbounded preceding and current row
                )
            ),
            branch_year_state as (
                select
                    r.docdb_family_id,
                    r.jurisdiction_code,
                    r.snapshot_year,
                    case
                        when r.snapshot_year = {build_snapshot_year} then date '{snapshot_date}'
                        else make_date(r.snapshot_year, 12, 31)
                    end as snapshot_date,
                    r.last_grant_event_date,
                    r.last_lapse_event_date,
                    r.last_expiry_event_date,
                    greatest(r.last_lapse_event_date, r.last_expiry_event_date) as last_negative_event_date,
                    r.last_opposition_event_date,
                    r.last_pending_event_date,
                    case
                        when r.last_grant_event_date is not null
                         and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                              or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date))
                         and r.last_opposition_event_date is not null
                         and r.last_opposition_event_date >= r.last_grant_event_date then 'ACTIVE_OPPOSED_GRANT'
                        when r.last_grant_event_date is not null
                         and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                              or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date)) then 'ACTIVE_GRANT'
                        when greatest(r.last_lapse_event_date, r.last_expiry_event_date) is not null
                         and (r.last_grant_event_date is null
                              or greatest(r.last_lapse_event_date, r.last_expiry_event_date) >= r.last_grant_event_date) then 'LAPSED_OR_EXPIRED'
                        when r.last_pending_event_date is not null
                         and r.last_grant_event_date is null then 'PENDING_ONLY'
                        else 'NO_ACTIVE_STATE'
                    end as replay_branch_state,
                    case
                        when r.last_grant_event_date is not null
                         and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                              or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date)) then true
                        else false
                    end as active_branch_flag,
                    case
                        when greatest(r.last_lapse_event_date, r.last_expiry_event_date) is not null
                         and (r.last_grant_event_date is null
                              or greatest(r.last_lapse_event_date, r.last_expiry_event_date) >= r.last_grant_event_date) then true
                        else false
                    end as lapsed_or_expired_flag,
                case
                    when (
                        r.last_pending_event_date is not null
                        and r.last_grant_event_date is null
                        and greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                    ) then true
                    else false
                end as pending_branch_flag,
                    case
                        when r.last_grant_event_date is not null
                         and (greatest(r.last_lapse_event_date, r.last_expiry_event_date) is null
                              or r.last_grant_event_date > greatest(r.last_lapse_event_date, r.last_expiry_event_date))
                         and r.last_opposition_event_date is not null
                         and r.last_opposition_event_date >= r.last_grant_event_date then true
                        else false
                    end as opposed_branch_flag
                from branch_year_replay r
            )
        """
        con.execute(
            f"""
            copy (
                {history_base_sql},
                compact_branch_history as (
                    select *
                    from (
                        select
                            b.*,
                            lag(replay_branch_state) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_branch_state,
                            lag(active_branch_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_active_branch_flag,
                            lag(lapsed_or_expired_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_lapsed_or_expired_flag,
                            lag(pending_branch_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_pending_branch_flag,
                            lag(opposed_branch_flag) over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_opposed_branch_flag
                        from branch_year_state b
                    )
                    where prev_branch_state is null
                       or replay_branch_state <> prev_branch_state
                       or active_branch_flag <> prev_active_branch_flag
                       or lapsed_or_expired_flag <> prev_lapsed_or_expired_flag
                       or pending_branch_flag <> prev_pending_branch_flag
                       or opposed_branch_flag <> prev_opposed_branch_flag
                       or snapshot_year = {build_snapshot_year}
                )
                select * from compact_branch_history
            ) to '{branch_slice}' (format parquet, compression zstd)
            """
        )
        con.execute(
            f"""
            copy (
                with ordered_compact as (
                    select
                        b.*,
                        lead(snapshot_year, 1, {build_snapshot_year} + 1) over (
                            partition by docdb_family_id, jurisdiction_code
                            order by snapshot_year
                        ) as next_snapshot_year
                    from read_parquet('{branch_slice}') b
                )
                select
                    o.docdb_family_id,
                    o.jurisdiction_code,
                    y.snapshot_year,
                    case
                        when y.snapshot_year = {build_snapshot_year} then date '{snapshot_date}'
                        else make_date(y.snapshot_year, 12, 31)
                    end as snapshot_date,
                    j.source_auth,
                    j.is_up_unrolled,
                    j.is_classic_validation,
                    j.is_global_member,
                    o.last_grant_event_date,
                    o.last_lapse_event_date,
                    o.last_expiry_event_date,
                    o.last_negative_event_date,
                    o.last_opposition_event_date,
                    o.last_pending_event_date,
                    o.replay_branch_state,
                    o.active_branch_flag,
                    o.lapsed_or_expired_flag,
                    o.pending_branch_flag,
                    o.opposed_branch_flag
                from ordered_compact o
                left join read_parquet('{out_jur}') j
                  on o.docdb_family_id = j.docdb_family_id
                 and o.jurisdiction_code = j.jurisdiction_code
                cross join generate_series(
                    cast(o.snapshot_year as bigint),
                    cast(o.next_snapshot_year - 1 as bigint),
                    cast(1 as bigint)
                ) as y(snapshot_year)
            ) to '{branch_dense_slice}' (format parquet, compression zstd)
            """
        )
        con.execute(
            f"""
            copy (
                with family_start_year as (
                    select docdb_family_id, min(snapshot_year) as start_year
                    from read_parquet('{branch_slice}')
                    group by docdb_family_id
                ),
                family_years as (
                    select
                        s.docdb_family_id,
                        y.snapshot_year
                    from family_start_year s
                    cross join generate_series(cast(s.start_year as bigint), cast({build_snapshot_year} as bigint), cast(1 as bigint)) as y(snapshot_year)
                ),
                branch_deltas as (
                    select
                        docdb_family_id,
                        snapshot_year,
                        sum(active_flag - prev_active_flag) as active_delta,
                        sum(lapsed_flag - prev_lapsed_flag) as lapsed_delta,
                        sum(opposed_flag - prev_opposed_flag) as opposed_delta,
                        sum(pending_flag - prev_pending_flag) as pending_delta
                    from (
                        select
                            docdb_family_id,
                            jurisdiction_code,
                            snapshot_year,
                            case when coalesce(active_branch_flag, false) then 1 else 0 end as active_flag,
                            case when coalesce(lapsed_or_expired_flag, false) then 1 else 0 end as lapsed_flag,
                            case when coalesce(opposed_branch_flag, false) then 1 else 0 end as opposed_flag,
                            case when replay_branch_state = 'PENDING_ONLY' then 1 else 0 end as pending_flag,
                            lag(case when coalesce(active_branch_flag, false) then 1 else 0 end, 1, 0)
                                over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_active_flag,
                            lag(case when coalesce(lapsed_or_expired_flag, false) then 1 else 0 end, 1, 0)
                                over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_lapsed_flag,
                            lag(case when coalesce(opposed_branch_flag, false) then 1 else 0 end, 1, 0)
                                over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_opposed_flag,
                            lag(case when replay_branch_state = 'PENDING_ONLY' then 1 else 0 end, 1, 0)
                            over (partition by docdb_family_id, jurisdiction_code order by snapshot_year) as prev_pending_flag
                        from read_parquet('{branch_slice}')
                    )
                    group by docdb_family_id, snapshot_year
                ),
                running_family_counts as (
                    select
                        y.docdb_family_id,
                        y.snapshot_year,
                        case
                            when y.snapshot_year = {build_snapshot_year} then date '{snapshot_date}'
                            else make_date(y.snapshot_year, 12, 31)
                        end as snapshot_date,
                        sum(coalesce(d.active_delta, 0)) over (
                            partition by y.docdb_family_id
                            order by y.snapshot_year
                            rows between unbounded preceding and current row
                        ) as active_jurisdiction_count,
                        sum(coalesce(d.lapsed_delta, 0)) over (
                            partition by y.docdb_family_id
                            order by y.snapshot_year
                            rows between unbounded preceding and current row
                        ) as lapsed_jurisdiction_count,
                        sum(coalesce(d.opposed_delta, 0)) over (
                            partition by y.docdb_family_id
                            order by y.snapshot_year
                            rows between unbounded preceding and current row
                        ) as opposed_branch_count,
                        sum(coalesce(d.pending_delta, 0)) over (
                            partition by y.docdb_family_id
                            order by y.snapshot_year
                            rows between unbounded preceding and current row
                        ) as pending_branch_count
                    from family_years y
                    left join branch_deltas d
                      on y.docdb_family_id = d.docdb_family_id
                     and y.snapshot_year = d.snapshot_year
                )
                select
                    docdb_family_id,
                    snapshot_year,
                    snapshot_date,
                    case
                        when active_jurisdiction_count > 0 and opposed_branch_count > 0 then 'under_fire'
                        when active_jurisdiction_count > 0 and lapsed_jurisdiction_count > 0 then 'partially_lapsed'
                        when active_jurisdiction_count > 0 then 'fully_active'
                        when pending_branch_count > 0 then 'pending_emerging'
                        else 'dead'
                    end as family_composite_status,
                    cast(active_jurisdiction_count as bigint) as active_jurisdiction_count,
                    cast(active_jurisdiction_count as bigint) as active_grant_branch_count,
                    cast(lapsed_jurisdiction_count as bigint) as lapsed_jurisdiction_count,
                    cast(opposed_branch_count as bigint) as opposed_branch_count,
                    active_jurisdiction_count > 0 as has_any_active_grant,
                    active_jurisdiction_count = 0 and pending_branch_count = 0 as is_dead_family
                from running_family_counts
            ) to '{family_slice}' (format parquet, compression zstd)
            """
        )

    con.execute(f"copy (select * from read_parquet('{branch_glob}')) to '{out_branch_history}' (format parquet, compression zstd)")
    con.execute(f"copy (select * from read_parquet('{branch_dense_glob}')) to '{out_branch_history_dense}' (format parquet, compression zstd)")
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{family_glob}')
            where snapshot_year < {build_snapshot_year}
            union all
            select
                docdb_family_id,
                {build_snapshot_year} as snapshot_year,
                snapshot_date,
                family_composite_status,
                cast(active_jurisdiction_count as bigint) as active_jurisdiction_count,
                cast(active_grant_branch_count as bigint) as active_grant_branch_count,
                cast(lapsed_jurisdiction_count as bigint) as lapsed_jurisdiction_count,
                cast(opposed_branch_count as bigint) as opposed_branch_count,
                has_any_active_grant,
                is_dead_family
            from read_parquet('{out_family_status}')
        ) to '{out_family_history}' (format parquet, compression zstd)
        """
    )

    for stale in temp_dir.glob("*.parquet"):
        stale.unlink()
    temp_dir.rmdir()

    for output in [out_branch_history, out_branch_history_dense, out_family_history]:
        result.outputs.append(str(output))
        result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    result.metrics["history_refresh_bucket_count"] = bucket_count
    return result
