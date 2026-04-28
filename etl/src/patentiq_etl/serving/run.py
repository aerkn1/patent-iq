from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

import duckdb

from patentiq_etl.common.io import ensure_dir, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult, utc_now_iso


_GIB = 1024**3
_MIB = 1024**2
_PUBLICATION_SHARD_COUNT = 256
_PUBLICATION_MEMBER_DATASET = "publication_member_by_number"
_APPLICATION_EVIDENCE_DATASET = "application_evidence_by_appln"
_PUBLICATION_CLAIM_DATASET = "publication_claim_by_number"
_FAMILY_PUBLICATIONS_DATASET = "family_publications_by_family"


def _serving_dir(settings: BuildSettings) -> Path:
    return ensure_dir(settings.repo_root / "etl" / "data" / "serving")


def _sql_path_literal(path: str | Path) -> str:
    return str(path).replace("'", "''")


def _duckdb_size_literal(byte_count: int) -> str:
    mebibytes = max(256, (int(byte_count) + _MIB - 1) // _MIB)
    return f"{mebibytes}MB"


def _serving_snapshot_temp_dir(snapshot_path: Path) -> Path:
    return snapshot_path.parent / "_duckdb_tmp" / snapshot_path.stem


def _cleanup_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    parent = path.parent
    if parent.exists():
        try:
            parent.rmdir()
        except OSError:
            pass


def _cleanup_snapshot_files(snapshot_path: Path) -> None:
    snapshot_path.unlink(missing_ok=True)
    snapshot_path.with_name(snapshot_path.name + ".wal").unlink(missing_ok=True)


def _serving_snapshot_threads(settings: BuildSettings) -> int:
    raw = settings.execution.get("serving_snapshot_threads", 1)
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return 1


def _serving_snapshot_temp_budget_bytes(settings: BuildSettings, temp_dir: Path) -> int:
    free_bytes = shutil.disk_usage(temp_dir).free
    configured_reserve_gb = settings.execution.get("serving_snapshot_temp_reserve_gb")
    try:
        reserve_bytes = max(1 * _GIB, int(configured_reserve_gb) * _GIB)
    except (TypeError, ValueError):
        reserve_bytes = min(16 * _GIB, max(4 * _GIB, free_bytes // 10))
    return max(1 * _GIB, free_bytes - reserve_bytes)


def _directory_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _snapshot_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute(
        """
        select table_name
        from information_schema.tables
        where table_schema = 'main'
        order by table_name
        """
    ).fetchall()
    return [str(row[0]) for row in rows]


def _table_stats(con: duckdb.DuckDBPyConnection, table_name: str) -> dict[str, int]:
    row_count = int(con.execute(f"select count(*) from {table_name}").fetchone()[0])
    column_count = int(
        con.execute(
            """
            select count(*)
            from information_schema.columns
            where table_schema = 'main' and table_name = ?
            """,
            [table_name],
        ).fetchone()[0]
    )
    return {"rows": row_count, "columns": column_count}


def _summarize_snapshot_path(snapshot_path: Path) -> dict[str, Any]:
    con = duckdb.connect(str(snapshot_path), read_only=True)
    try:
        tables = _snapshot_tables(con)
        return {
            "path": snapshot_path,
            "tables": tables,
            "table_stats": {table: _table_stats(con, table) for table in tables},
            "bytes": snapshot_path.stat().st_size if snapshot_path.exists() else 0,
        }
    finally:
        con.close()


def _copy_source_table(
    con: duckdb.DuckDBPyConnection,
    source_path: Path,
    target_table: str,
    warnings: list[str],
) -> bool:
    if not source_path.exists():
        warnings.append(f"Missing source parquet for `{target_table}`: {source_path}")
        return False
    con.execute(f"create or replace table {target_table} as select * from read_parquet(?)", [str(source_path)])
    return True


def _table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    row = con.execute(
        """
        select 1
        from information_schema.tables
        where table_schema = 'main'
          and table_name = ?
        limit 1
        """,
        [table_name],
    ).fetchone()
    return row is not None


def _overlay_family_summary_serving(
    con: duckdb.DuckDBPyConnection,
    summary_path: Path,
    register_core_path: Path,
    register_opposition_path: Path,
    warnings: list[str],
) -> bool:
    if not summary_path.exists() and not _table_exists(con, "family_summary"):
        warnings.append(
            "Skipped family current-status serving overlay because `family_summary` is unavailable: "
            f"{summary_path}"
        )
        return False

    if _table_exists(con, "family_summary"):
        con.execute("create or replace temp view family_summary_base as select * from family_summary")
    else:
        con.execute(
            f"""
            create or replace temp view family_summary_base as
            select *
            from read_parquet('{_sql_path_literal(summary_path)}')
            """
        )

    if register_core_path.exists() and register_opposition_path.exists():
        con.execute(
            f"""
            create or replace temp view family_active_opposition_overlay as
            select
                c.docdb_family_id,
                count(distinct c.appln_id) as active_opposition_application_count,
                true as opposition_overlay_active
            from read_parquet('{register_core_path}') c
            join read_parquet('{register_opposition_path}') o using (appln_id)
            where coalesce(cast(o.ep_opposition_active as boolean), false)
            group by c.docdb_family_id
            """
        )
    else:
        missing = ", ".join(
            str(path)
            for path in [register_core_path, register_opposition_path]
            if not path.exists()
        )
        warnings.append(
            "Serving opposition overlay fell back to mart-only status because required register sources are missing: "
            + missing
        )
        con.execute(
            """
            create or replace temp view family_active_opposition_overlay as
            select
                null::bigint as docdb_family_id,
                0::bigint as active_opposition_application_count,
                false as opposition_overlay_active
            where false
            """
        )

    con.execute(
        """
        create or replace table family_summary as
        with enriched as (
            select
                fs.* exclude (family_composite_status, opposed_branch_count),
                cast(fs.family_composite_status as varchar) as mart_family_composite_status,
                cast(coalesce(fs.opposed_branch_count, 0.0) as double) as mart_opposed_branch_count,
                cast(coalesce(o.active_opposition_application_count, 0) as bigint) as active_opposition_application_count,
                cast(coalesce(o.opposition_overlay_active, false) as boolean) as opposition_overlay_active,
                case
                    when lower(coalesce(fs.family_composite_status, '')) = 'under_fire' then 'under_fire'
                    when coalesce(fs.has_any_active_grant, false)
                     and coalesce(o.opposition_overlay_active, false) then 'under_fire'
                    else fs.family_composite_status
                end as effective_family_composite_status,
                greatest(
                    cast(coalesce(fs.opposed_branch_count, 0.0) as double),
                    case
                        when lower(coalesce(fs.family_composite_status, '')) = 'under_fire' then 1.0
                        when coalesce(fs.has_any_active_grant, false)
                         and coalesce(o.opposition_overlay_active, false) then 1.0
                        else 0.0
                    end
                ) as effective_opposed_branch_count
            from family_summary_base fs
            left join family_active_opposition_overlay o using (docdb_family_id)
        )
        select
            * exclude (effective_family_composite_status, effective_opposed_branch_count),
            effective_family_composite_status as family_composite_status,
            effective_opposed_branch_count as opposed_branch_count,
            effective_family_composite_status,
            effective_opposed_branch_count
        from enriched
        """
    )
    con.execute("create index if not exists idx_family_summary_id on family_summary(docdb_family_id)")
    return True


def _create_family_compare_current_serving(
    con: duckdb.DuckDBPyConnection,
    summary_path: Path,
    blocking_path: Path,
    compare_pit_path: Path,
    warnings: list[str],
) -> bool:
    required = [summary_path, blocking_path, compare_pit_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        warnings.append(
            "Skipped `family_compare_current_serving` because required sources are missing: " + ", ".join(missing)
        )
        return False

    con.execute(
        f"""
        create or replace table family_compare_current_serving as
        with latest_compare as (
            select *
            from read_parquet('{compare_pit_path}')
            where is_latest_observed_year
        ),
        compare_with_overlay as (
            select
                c.* exclude (family_composite_status_asof),
                cast(c.family_composite_status_asof as varchar) as mart_family_composite_status_asof,
                coalesce(
                    cast(s.effective_family_composite_status as varchar),
                    cast(c.family_composite_status_asof as varchar),
                    cast(s.family_composite_status as varchar)
                ) as family_composite_status_asof,
                cast(coalesce(s.active_opposition_application_count, 0) as bigint) as active_opposition_application_count,
                cast(coalesce(s.opposition_overlay_active, false) as boolean) as opposition_overlay_active,
                cast(coalesce(s.effective_opposed_branch_count, s.opposed_branch_count, 0.0) as double) as effective_opposed_branch_count_asof
            from latest_compare c
            left join family_summary s using (docdb_family_id)
        ),
        legal_ranked as (
            select
                docdb_family_id,
                100.0 * percent_rank() over (
                    partition by
                        coalesce(primary_wipo_field_current, 'unknown'),
                        coalesce(family_composite_status_asof, 'unknown')
                    order by coalesce(family_enforceability_score_asof, 0.0)
                ) as legal_durability_percentile
            from compare_with_overlay
        ),
        citation_ranked as (
            select
                s.docdb_family_id,
                100.0 * percent_rank() over (
                    partition by
                        coalesce(s.primary_wipo_field, 'unknown'),
                        coalesce(s.family_priority_year, -1)
                    order by coalesce(c.pre_asof_forward_citations_weighted, s.oecd_quality_proxy_score, 0.0)
                ) as citation_heritage_percentile
            from family_summary s
            left join compare_with_overlay c using (docdb_family_id)
        )
        select
            s.docdb_family_id,
            s.owner_name_harmonized,
            s.owner_name_display,
            s.primary_wipo_field,
            s.family_priority_year,
            s.family_composite_status,
            s.mart_family_composite_status,
            s.active_opposition_application_count,
            s.opposition_overlay_active,
            s.effective_family_composite_status,
            s.effective_opposed_branch_count,
            s.family_size_docdb,
            s.family_tech_breadth_wipo_count,
            s.active_jurisdiction_count,
            s.family_fwd_cits7_percentile,
            s.family_quality_index_6_score,
            s.oecd_quality_percentile,
            s.oecd_quality_proxy_score,
            b.family_ui_blocking_power_score,
            b.family_overall_legal_enforceability_score,
            b.family_market_threat_score_raw,
            c.primary_wipo_field_current,
            c.mart_family_composite_status_asof,
            c.family_composite_status_asof,
            c.family_enforceability_score_asof,
            c.family_active_jurisdiction_share_asof,
            c.family_jurisdiction_count_asof,
            c.pre_asof_forward_citations_weighted,
            c.data_completeness_pct_asof,
            c.historical_compare_safe,
            c.historical_oecd_supported,
            c.current_owner_metadata_only,
            c.effective_opposed_branch_count_asof,
            lr.legal_durability_percentile,
            cr.citation_heritage_percentile
        from family_summary s
        left join read_parquet('{blocking_path}') b using (docdb_family_id)
        left join compare_with_overlay c using (docdb_family_id)
        left join legal_ranked lr using (docdb_family_id)
        left join citation_ranked cr using (docdb_family_id)
        """
    )
    con.execute("create index if not exists idx_family_compare_current_serving_id on family_compare_current_serving(docdb_family_id)")
    return True


def _create_portfolio_compare_current_serving(
    con: duckdb.DuckDBPyConnection,
    portfolio_summary_path: Path,
    warnings: list[str],
) -> bool:
    if not portfolio_summary_path.exists():
        warnings.append(
            f"Skipped `portfolio_compare_current_serving` because required source is missing: {portfolio_summary_path}"
        )
        return False

    con.execute(
        f"""
        create or replace table portfolio_compare_current_serving as
        with latest_snapshot as (
            select max(snapshot_date) as snapshot_date
            from read_parquet('{portfolio_summary_path}')
            where trim(upper(coalesce(owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
        ),
        scoped as (
            select
                owner_name_harmonized,
                coalesce(owner_name_display, owner_name_harmonized) as owner_name_display,
                snapshot_date,
                case
                    when coalesce(portfolio_family_count_within_mega_cluster, 0) <= 1 then '1'
                    when portfolio_family_count_within_mega_cluster between 2 and 5 then '2_5'
                    when portfolio_family_count_within_mega_cluster between 6 and 20 then '6_20'
                    when portfolio_family_count_within_mega_cluster between 21 and 100 then '21_100'
                    when portfolio_family_count_within_mega_cluster between 101 and 500 then '101_500'
                    else '501_plus'
                end as peer_bucket,
                cast(coalesce(portfolio_total_mass_score, 0.0) as double) as portfolio_total_mass_score,
                cast(coalesce(portfolio_current_threat_score, 0.0) as double) as portfolio_current_threat_score,
                cast(coalesce(portfolio_heritage_score, 0.0) as double) as portfolio_heritage_score,
                cast(coalesce(portfolio_avg_blocking_power_within_mega_cluster, 0.0) as double) as portfolio_avg_blocking_power_within_mega_cluster,
                cast(coalesce(portfolio_hit_rate_top_decile, 0.0) as double) as portfolio_hit_rate_top_decile,
                cast(coalesce(portfolio_crown_jewel_index, 0.0) as double) as portfolio_crown_jewel_index
            from read_parquet('{portfolio_summary_path}')
            where snapshot_date = (select snapshot_date from latest_snapshot)
              and trim(upper(coalesce(owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
        )
        select
            *,
            count(*) over (partition by peer_bucket) as peer_bucket_size,
            percent_rank() over (partition by peer_bucket order by portfolio_total_mass_score) * 100.0 as portfolio_total_mass_score_percentile,
            percent_rank() over (partition by peer_bucket order by portfolio_current_threat_score) * 100.0 as portfolio_current_threat_score_percentile,
            percent_rank() over (partition by peer_bucket order by portfolio_heritage_score) * 100.0 as portfolio_heritage_score_percentile,
            percent_rank() over (partition by peer_bucket order by portfolio_avg_blocking_power_within_mega_cluster) * 100.0 as portfolio_avg_blocking_power_percentile,
            percent_rank() over (partition by peer_bucket order by portfolio_hit_rate_top_decile) * 100.0 as portfolio_hit_rate_top_decile_percentile,
            percent_rank() over (partition by peer_bucket order by portfolio_crown_jewel_index) * 100.0 as portfolio_crown_jewel_index_percentile
        from scoped
        """
    )
    con.execute(
        "create index if not exists idx_portfolio_compare_current_serving_owner on portfolio_compare_current_serving(owner_name_harmonized)"
    )
    return True


def _create_portfolio_classification_current_serving(
    con: duckdb.DuckDBPyConnection,
    classification_mix_path: Path,
    warnings: list[str],
) -> bool:
    if not classification_mix_path.exists():
        warnings.append(
            "Skipped `portfolio_classification_current_serving` because required source is missing: "
            f"{classification_mix_path}"
        )
        return False

    con.execute(
        f"""
        create or replace table portfolio_classification_current_serving as
        with owner_years as (
            select
                owner_name_harmonized,
                as_of_year,
                row_number() over (
                    partition by owner_name_harmonized
                    order by as_of_year desc
                ) as year_rank
            from (
                select distinct
                    cast(c.owner_name_harmonized as varchar) as owner_name_harmonized,
                    cast(c.as_of_year as integer) as as_of_year
                from read_parquet('{classification_mix_path}') c
                where trim(upper(coalesce(c.owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                  and c.classification_type in ('WIPO_FIELD', 'CPC_MAIN_GROUP')
            )
        ),
        selected_years as (
            select
                owner_name_harmonized,
                max(case when year_rank = 1 then as_of_year end) as latest_as_of_year,
                max(case when year_rank = 2 then as_of_year end) as previous_as_of_year
            from owner_years
            where year_rank <= 2
            group by owner_name_harmonized
        ),
        scoped as (
            select
                cast(c.owner_name_harmonized as varchar) as owner_name_harmonized,
                cast(coalesce(c.owner_name_display_current, c.owner_name_harmonized) as varchar) as owner_name_display,
                cast(c.as_of_year as integer) as as_of_year,
                cast(c.classification_code as varchar) as segment,
                cast(c.classification_label as varchar) as classification_label,
                cast(c.classification_type as varchar) as classification_type,
                cast(c.classification_rank_within_owner_year as integer) as rank,
                cast(coalesce(c.portfolio_family_share_asof, 0.0) as double) as family_share,
                cast(coalesce(c.portfolio_family_count_in_classification_asof, 0) as bigint) as active_family_count
            from read_parquet('{classification_mix_path}') c
            join selected_years y
              on cast(c.owner_name_harmonized as varchar) = y.owner_name_harmonized
             and cast(c.as_of_year as integer) in (y.latest_as_of_year, y.previous_as_of_year)
            where trim(upper(coalesce(c.owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
              and c.classification_type in ('WIPO_FIELD', 'CPC_MAIN_GROUP')
        ),
        current_rows as (
            select s.*
            from scoped s
            join selected_years y using (owner_name_harmonized)
            where s.as_of_year = y.latest_as_of_year
        ),
        previous_rows as (
            select
                s.owner_name_harmonized,
                s.classification_type,
                s.segment,
                s.family_share as previous_family_share
            from scoped s
            join selected_years y using (owner_name_harmonized)
            where s.as_of_year = y.previous_as_of_year
        )
        select
            c.*,
            case
                when p.previous_family_share is null then null
                else c.family_share - p.previous_family_share
            end as trajectory
        from current_rows c
        left join previous_rows p
          using (owner_name_harmonized, classification_type, segment)
        """
    )
    con.execute(
        "create index if not exists idx_portfolio_classification_current_owner_type on portfolio_classification_current_serving(owner_name_harmonized, classification_type)"
    )
    return True


def _publication_evidence_chunk_count(
    row_count: int,
    *,
    chunk_target_rows: int,
    chunk_max_count: int,
) -> int:
    target_rows = max(1, chunk_target_rows)
    max_chunks = max(1, chunk_max_count)
    desired_chunks = max(1, (max(0, row_count) + target_rows - 1) // target_rows)
    return min(max_chunks, desired_chunks)


def _publication_evidence_select_sql(member_relation: str) -> str:
    return f"""
        select
            m.pat_publn_id,
            m.appln_id,
            m.docdb_family_id,
            m.publication_number_full,
            m.publn_auth,
            m.publn_nr,
            m.publn_kind,
            m.publn_date,
            m.is_application_stage,
            m.is_grant_stage,
            m.is_modifier_stage,
            m.scope_type,
            m.snapshot_date,
            p.title_text,
            p.title_language_code,
            p.abstract_text,
            p.abstract_language_code,
            c.claim_1_text,
            c.claim_1_language_code,
            p.reg101_id,
            p.register_record_present,
            p.ep_registered_license_flag,
            p.ep_licensee_names,
            p.register_snapshot_date,
            p.ep_display_status_text,
            p.status_source,
            p.display_snapshot_date,
            p.ep_proc_step_maturity_score,
            p.ep_search_report_mailed_date,
            p.ep_latest_proc_phase_code,
            p.ep_latest_proc_result_code,
            p.ep_proc_time_limit_days,
            p.ep_register_is_unitary_patent,
            p.ep_register_up_status_code,
            p.ep_register_up_status_text,
            p.ep_register_up_event_latest_date,
            p.ep_opposition_active,
            p.ep_opposition_status_text,
            p.ep_opponent_names,
            p.ep_opponent_agent_names,
            p.ep_appeal_active,
            p.ep_appeal_result_text,
            p.ep_register_lead_agent_name,
            p.ep_register_lead_agent_country,
            fs.family_composite_status,
            fs.mart_family_composite_status,
            fs.effective_family_composite_status,
            fs.opposed_branch_count,
            fs.mart_opposed_branch_count,
            fs.effective_opposed_branch_count,
            fs.active_opposition_application_count,
            fs.opposition_overlay_active
        from {member_relation} m
        left join publication_appln_evidence_best p using (appln_id)
        left join publication_claim_best c using (publication_number_full)
        left join publication_family_status_best fs using (docdb_family_id)
    """


def _prepare_publication_evidence_support(
    con: duckdb.DuckDBPyConnection,
    application_path: Path,
    member_publications_path: Path,
    title_path: Path,
    abstract_path: Path,
    epab_publication_path: Path,
    epab_claims_path: Path,
    register_core_path: Path,
    register_display_path: Path,
    register_proc_path: Path,
    register_up_path: Path,
    register_opposition_path: Path,
    register_agent_path: Path,
    warnings: list[str],
) -> bool:
    member_source_table = "family_member_publications"
    if not _table_exists(con, member_source_table) and not member_publications_path.exists():
        warnings.append(
            f"Skipped `publication_evidence_serving` because required source is missing: {member_publications_path}"
        )
        return False

    member_source = (
        member_source_table
        if _table_exists(con, member_source_table)
        else f"read_parquet('{_sql_path_literal(member_publications_path)}')"
    )
    con.execute(
        """
        create or replace temp view publication_member_base as
        select
            cast(pat_publn_id as bigint) as pat_publn_id,
            cast(appln_id as bigint) as appln_id,
            cast(docdb_family_id as bigint) as docdb_family_id,
            upper(cast(publication_number_full as varchar)) as publication_number_full,
            cast(publn_auth as varchar) as publn_auth,
            cast(publn_nr as varchar) as publn_nr,
            cast(publn_kind as varchar) as publn_kind,
            cast(publn_date as date) as publn_date,
            cast(is_application_stage as boolean) as is_application_stage,
            cast(is_grant_stage as boolean) as is_grant_stage,
            cast(is_modifier_stage as boolean) as is_modifier_stage,
            cast(scope_type as varchar) as scope_type,
            cast(snapshot_date as varchar) as snapshot_date
        from {member_source}
        """.format(member_source=member_source)
    )
    con.execute(
        """
        create or replace temp table publication_member_appln_ids as
        select distinct appln_id
        from publication_member_base
        where appln_id is not null
        """
    )
    con.execute(
        """
        create or replace temp table publication_member_numbers as
        select distinct publication_number_full
        from publication_member_base
        where publication_number_full is not null
        """
    )

    if title_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_title_best as
            with ranked as (
                select
                    cast(appln_id as bigint) as appln_id,
                    nullif(trim(cast(appln_title as varchar)), '') as title_text,
                    lower(coalesce(cast(appln_title_lg as varchar), 'en')) as title_language_code,
                    row_number() over (
                        partition by cast(appln_id as bigint)
                        order by
                            case when lower(coalesce(cast(appln_title_lg as varchar), 'en')) = 'en' then 0 else 1 end,
                            lower(coalesce(cast(appln_title_lg as varchar), 'en')) asc,
                            length(cast(appln_title as varchar)) desc
                    ) as row_number
                from read_parquet('{title_path}')
                join publication_member_appln_ids using (appln_id)
                where nullif(trim(cast(appln_title as varchar)), '') is not null
            )
            select appln_id, title_text, title_language_code
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(f"Missing optional title source for `publication_evidence_serving`: {title_path}")
        con.execute(
            """
            create or replace temp table publication_title_best as
            select
                null::bigint as appln_id,
                null::varchar as title_text,
                null::varchar as title_language_code
            where false
            """
        )

    if abstract_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_abstract_best as
            with ranked as (
                select
                    cast(appln_id as bigint) as appln_id,
                    nullif(trim(cast(appln_abstract as varchar)), '') as abstract_text,
                    lower(coalesce(cast(appln_abstract_lg as varchar), 'en')) as abstract_language_code,
                    row_number() over (
                        partition by cast(appln_id as bigint)
                        order by
                            case when lower(coalesce(cast(appln_abstract_lg as varchar), 'en')) = 'en' then 0 else 1 end,
                            lower(coalesce(cast(appln_abstract_lg as varchar), 'en')) asc,
                            length(cast(appln_abstract as varchar)) desc
                    ) as row_number
                from read_parquet('{abstract_path}')
                join publication_member_appln_ids using (appln_id)
                where nullif(trim(cast(appln_abstract as varchar)), '') is not null
            )
            select appln_id, abstract_text, abstract_language_code
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(f"Missing optional abstract source for `publication_evidence_serving`: {abstract_path}")
        con.execute(
            """
            create or replace temp table publication_abstract_best as
            select
                null::bigint as appln_id,
                null::varchar as abstract_text,
                null::varchar as abstract_language_code
            where false
            """
        )

    if epab_publication_path.exists() and epab_claims_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_claim_best as
            with ranked as (
                select
                    upper(cast(p.publication_number_full as varchar)) as publication_number_full,
                    nullif(trim(cast(c.claim_text_plain as varchar)), '') as claim_1_text,
                    lower(coalesce(cast(c.language_code as varchar), 'en')) as claim_1_language_code,
                    row_number() over (
                        partition by upper(cast(p.publication_number_full as varchar))
                        order by lower(coalesce(cast(c.language_code as varchar), 'en')) asc
                    ) as row_number
                from read_parquet('{epab_publication_path}') p
                join publication_member_numbers pm
                  on upper(cast(p.publication_number_full as varchar)) = pm.publication_number_full
                join read_parquet('{epab_claims_path}') c using (epab_doc_id)
                where try_cast(c.claim_sequence_no as bigint) = 1
                  and lower(coalesce(cast(c.language_code as varchar), 'en')) = 'en'
                  and nullif(trim(cast(c.claim_text_plain as varchar)), '') is not null
            )
            select publication_number_full, claim_1_text, claim_1_language_code
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(
            "Missing optional EPAB claim sources for `publication_evidence_serving`: "
            + ", ".join(str(path) for path in [epab_publication_path, epab_claims_path] if not path.exists())
        )
        con.execute(
            """
            create or replace temp table publication_claim_best as
            select
                null::varchar as publication_number_full,
                null::varchar as claim_1_text,
                null::varchar as claim_1_language_code
            where false
            """
        )

    if register_core_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_register_core_best as
            with ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    cast(src.reg101_id as bigint) as reg101_id,
                    cast(src.register_record_present as boolean) as register_record_present,
                    cast(src.ep_registered_license_flag as boolean) as ep_registered_license_flag,
                    cast(src.ep_licensee_names as varchar) as ep_licensee_names,
                    cast(src.register_snapshot_date as date) as register_snapshot_date,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by
                            cast(src.register_snapshot_date as date) desc nulls last,
                            coalesce(cast(src.register_record_present as boolean), false) desc,
                            case
                                when nullif(trim(cast(src.ep_licensee_names as varchar)), '') is not null then 0
                                else 1
                            end,
                            cast(src.reg101_id as bigint) desc nulls last
                    ) as row_number
                from read_parquet('{register_core_path}') src
                join publication_member_appln_ids ids using (appln_id)
            )
            select
                appln_id,
                reg101_id,
                register_record_present,
                ep_registered_license_flag,
                ep_licensee_names,
                register_snapshot_date
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(f"Missing optional register core source for `publication_evidence_serving`: {register_core_path}")
        con.execute(
            """
            create or replace temp table publication_register_core_best as
            select
                null::bigint as appln_id,
                null::bigint as reg101_id,
                null::boolean as register_record_present,
                null::boolean as ep_registered_license_flag,
                null::varchar as ep_licensee_names,
                null::date as register_snapshot_date
            where false
            """
        )

    if register_display_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_register_display_best as
            with ranked as (
                select
                    cast(appln_id as bigint) as appln_id,
                    cast(snapshot_date as date) as display_snapshot_date,
                    cast(ep_display_status_text as varchar) as ep_display_status_text,
                    cast(status_source as varchar) as status_source,
                    row_number() over (
                        partition by cast(appln_id as bigint)
                        order by cast(snapshot_date as date) desc nulls last
                    ) as row_number
                from read_parquet('{register_display_path}')
                join publication_member_appln_ids using (appln_id)
            )
            select appln_id, display_snapshot_date, ep_display_status_text, status_source
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(
            f"Missing optional register display source for `publication_evidence_serving`: {register_display_path}"
        )
        con.execute(
            """
            create or replace temp table publication_register_display_best as
            select
                null::bigint as appln_id,
                null::date as display_snapshot_date,
                null::varchar as ep_display_status_text,
                null::varchar as status_source
            where false
            """
        )

    if register_proc_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_register_proc_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_proc_step_maturity_score as double) as ep_proc_step_maturity_score,
                cast(ep_search_report_mailed_date as date) as ep_search_report_mailed_date,
                cast(ep_latest_proc_phase_code as varchar) as ep_latest_proc_phase_code,
                cast(ep_latest_proc_result_code as varchar) as ep_latest_proc_result_code,
                cast(ep_proc_time_limit_days as bigint) as ep_proc_time_limit_days
            from read_parquet('{register_proc_path}')
            join publication_member_appln_ids using (appln_id)
            """
        )
    else:
        warnings.append(f"Missing optional register procedure source for `publication_evidence_serving`: {register_proc_path}")
        con.execute(
            """
            create or replace temp table publication_register_proc_best as
            select
                null::bigint as appln_id,
                null::double as ep_proc_step_maturity_score,
                null::date as ep_search_report_mailed_date,
                null::varchar as ep_latest_proc_phase_code,
                null::varchar as ep_latest_proc_result_code,
                null::bigint as ep_proc_time_limit_days
            where false
            """
        )

    if register_up_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_register_up_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_register_is_unitary_patent as boolean) as ep_register_is_unitary_patent,
                cast(ep_register_up_status_code as varchar) as ep_register_up_status_code,
                cast(ep_register_up_status_text as varchar) as ep_register_up_status_text,
                cast(ep_register_up_event_latest_date as date) as ep_register_up_event_latest_date
            from read_parquet('{register_up_path}')
            join publication_member_appln_ids using (appln_id)
            """
        )
    else:
        warnings.append(f"Missing optional register UP source for `publication_evidence_serving`: {register_up_path}")
        con.execute(
            """
            create or replace temp table publication_register_up_best as
            select
                null::bigint as appln_id,
                null::boolean as ep_register_is_unitary_patent,
                null::varchar as ep_register_up_status_code,
                null::varchar as ep_register_up_status_text,
                null::date as ep_register_up_event_latest_date
            where false
            """
        )

    if register_opposition_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_register_opposition_best as
            with ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    cast(src.ep_opposition_active as boolean) as ep_opposition_active,
                    cast(src.ep_opposition_status_text as varchar) as ep_opposition_status_text,
                    cast(src.ep_opponent_names as varchar) as ep_opponent_names,
                    cast(src.ep_opponent_agent_names as varchar) as ep_opponent_agent_names,
                    cast(src.ep_appeal_active as boolean) as ep_appeal_active,
                    cast(src.ep_appeal_result_text as varchar) as ep_appeal_result_text,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by
                            coalesce(cast(src.ep_opposition_active as boolean), false) desc,
                            coalesce(cast(src.ep_appeal_active as boolean), false) desc,
                            case
                                when nullif(trim(cast(src.ep_opposition_status_text as varchar)), '') is not null then 0
                                else 1
                            end,
                            case
                                when nullif(trim(cast(src.ep_opponent_names as varchar)), '') is not null then 0
                                else 1
                            end,
                            case
                                when nullif(trim(cast(src.ep_opponent_agent_names as varchar)), '') is not null then 0
                                else 1
                            end,
                            case
                                when nullif(trim(cast(src.ep_appeal_result_text as varchar)), '') is not null then 0
                                else 1
                            end
                    ) as row_number
                from read_parquet('{register_opposition_path}') src
                join publication_member_appln_ids ids using (appln_id)
            )
            select
                appln_id,
                ep_opposition_active,
                ep_opposition_status_text,
                ep_opponent_names,
                ep_opponent_agent_names,
                ep_appeal_active,
                ep_appeal_result_text
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(
            f"Missing optional register opposition source for `publication_evidence_serving`: {register_opposition_path}"
        )
        con.execute(
            """
            create or replace temp table publication_register_opposition_best as
            select
                null::bigint as appln_id,
                null::boolean as ep_opposition_active,
                null::varchar as ep_opposition_status_text,
                null::varchar as ep_opponent_names,
                null::varchar as ep_opponent_agent_names,
                null::boolean as ep_appeal_active,
                null::varchar as ep_appeal_result_text
            where false
            """
        )

    if register_agent_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_register_agent_best as
            select
                cast(appln_id as bigint) as appln_id,
                cast(ep_register_lead_agent_name as varchar) as ep_register_lead_agent_name,
                cast(ep_register_lead_agent_country as varchar) as ep_register_lead_agent_country
            from read_parquet('{register_agent_path}')
            join publication_member_appln_ids using (appln_id)
            """
        )
    else:
        warnings.append(f"Missing optional register agent source for `publication_evidence_serving`: {register_agent_path}")
        con.execute(
            """
            create or replace temp table publication_register_agent_best as
            select
                null::bigint as appln_id,
                null::varchar as ep_register_lead_agent_name,
                null::varchar as ep_register_lead_agent_country
            where false
            """
        )

    if _table_exists(con, "family_summary"):
        con.execute(
            """
            create or replace temp table publication_family_status_best as
            select
                cast(docdb_family_id as bigint) as docdb_family_id,
                cast(family_composite_status as varchar) as family_composite_status,
                cast(mart_family_composite_status as varchar) as mart_family_composite_status,
                cast(effective_family_composite_status as varchar) as effective_family_composite_status,
                cast(opposed_branch_count as double) as opposed_branch_count,
                cast(mart_opposed_branch_count as double) as mart_opposed_branch_count,
                cast(effective_opposed_branch_count as double) as effective_opposed_branch_count,
                cast(active_opposition_application_count as bigint) as active_opposition_application_count,
                cast(opposition_overlay_active as boolean) as opposition_overlay_active
            from family_summary
            """
        )
    else:
        con.execute(
            """
            create or replace temp table publication_family_status_best as
            select
                null::bigint as docdb_family_id,
                null::varchar as family_composite_status,
                null::varchar as mart_family_composite_status,
                null::varchar as effective_family_composite_status,
                null::double as opposed_branch_count,
                null::double as mart_opposed_branch_count,
                null::double as effective_opposed_branch_count,
                null::bigint as active_opposition_application_count,
                null::boolean as opposition_overlay_active
            where false
            """
        )
    con.execute(
        """
        create or replace temp table publication_appln_evidence_best as
        select
            ids.appln_id,
            t.title_text,
            t.title_language_code,
            a.abstract_text,
            a.abstract_language_code,
            rc.reg101_id,
            rc.register_record_present,
            rc.ep_registered_license_flag,
            rc.ep_licensee_names,
            rc.register_snapshot_date,
            rd.ep_display_status_text,
            rd.status_source,
            rd.display_snapshot_date,
            rp.ep_proc_step_maturity_score,
            rp.ep_search_report_mailed_date,
            rp.ep_latest_proc_phase_code,
            rp.ep_latest_proc_result_code,
            rp.ep_proc_time_limit_days,
            ru.ep_register_is_unitary_patent,
            ru.ep_register_up_status_code,
            ru.ep_register_up_status_text,
            ru.ep_register_up_event_latest_date,
            ro.ep_opposition_active,
            ro.ep_opposition_status_text,
            ro.ep_opponent_names,
            ro.ep_opponent_agent_names,
            ro.ep_appeal_active,
            ro.ep_appeal_result_text,
            ra.ep_register_lead_agent_name,
            ra.ep_register_lead_agent_country
        from publication_member_appln_ids ids
        left join publication_title_best t using (appln_id)
        left join publication_abstract_best a using (appln_id)
        left join publication_register_core_best rc using (appln_id)
        left join publication_register_display_best rd using (appln_id)
        left join publication_register_proc_best rp using (appln_id)
        left join publication_register_up_best ru using (appln_id)
        left join publication_register_opposition_best ro using (appln_id)
        left join publication_register_agent_best ra using (appln_id)
        """
    )
    _assert_unique_source_keys(
        con,
        "publication_appln_evidence_best",
        "select * from publication_appln_evidence_best",
        ["appln_id"],
    )
    con.execute(
        "create index if not exists idx_publication_appln_evidence_best_appln on publication_appln_evidence_best(appln_id)"
    )
    _assert_unique_source_keys(
        con,
        "publication_claim_best",
        "select * from publication_claim_best",
        ["publication_number_full"],
    )
    con.execute(
        "create index if not exists idx_publication_claim_best_number on publication_claim_best(publication_number_full)"
    )
    con.execute(
        "create index if not exists idx_publication_family_status_best_family on publication_family_status_best(docdb_family_id)"
    )
    if application_path.exists():
        con.execute(
            f"""
            create or replace temp table publication_application_filing_best as
            with ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    cast(src.appln_filing_date as date) as appln_filing_date,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by cast(src.appln_filing_date as date) asc nulls last
                    ) as row_number
                from read_parquet('{application_path}') src
                join publication_member_appln_ids ids using (appln_id)
                where src.appln_filing_date is not null
            )
            select appln_id, appln_filing_date
            from ranked
            where row_number = 1
            """
        )
    else:
        warnings.append(
            f"Missing optional application source for `publication_evidence_serving`: {application_path}"
        )
        con.execute(
            """
            create or replace temp table publication_application_filing_best as
            select
                null::bigint as appln_id,
                null::date as appln_filing_date
            where false
            """
        )
    for table_name in [
        "publication_member_appln_ids",
        "publication_member_numbers",
        "publication_title_best",
        "publication_abstract_best",
        "publication_register_core_best",
        "publication_register_display_best",
        "publication_register_proc_best",
        "publication_register_up_best",
        "publication_register_opposition_best",
        "publication_register_agent_best",
    ]:
        con.execute(f"drop table if exists {table_name}")
    con.execute("checkpoint")
    return True


def _publication_bucket_expr(column_expr: str) -> str:
    return f"lower(substr(sha256(upper(coalesce(cast({column_expr} as varchar), ''))), 1, 2))"


def _numeric_bucket_expr(column_expr: str, bucket_count: int) -> str:
    return f"cast(mod(abs(cast(coalesce({column_expr}, 0) as bigint)), {bucket_count}) as varchar)"


def _copy_partitioned_parquet_dataset(
    con: duckdb.DuckDBPyConnection,
    dataset_path: Path,
    select_sql: str,
    partition_column: str,
) -> None:
    _cleanup_dir(dataset_path)
    ensure_dir(dataset_path)
    con.execute(
        f"""
        copy (
            {select_sql}
        ) to '{_sql_path_literal(dataset_path)}' (
            format parquet,
            compression zstd,
            partition_by ({partition_column})
        )
        """
    )


def _copy_bucketed_parquet_dataset(
    con: duckdb.DuckDBPyConnection,
    dataset_path: Path,
    partition_column: str,
    bucket_values: list[str],
    select_sql_factory: Callable[[str], str],
) -> None:
    _cleanup_dir(dataset_path)
    ensure_dir(dataset_path)
    for bucket_value in bucket_values:
        bucket_dir = dataset_path / f"{partition_column}={bucket_value}"
        ensure_dir(bucket_dir)
        output_path = bucket_dir / "data.parquet"
        con.execute(
            f"""
            copy (
                {select_sql_factory(bucket_value)}
            ) to '{_sql_path_literal(output_path)}' (
                format parquet,
                compression zstd
            )
            """
        )


def _compact_partitioned_parquet_dataset(
    settings: BuildSettings,
    serving_dir: Path,
    dataset_path: Path,
    temp_name: str,
) -> None:
    if not dataset_path.exists():
        return
    partition_dirs = sorted(path for path in dataset_path.iterdir() if path.is_dir())
    if not partition_dirs:
        return
    con, temp_dir = _open_publication_build_connection(settings, serving_dir, temp_name)
    try:
        for partition_dir in partition_dirs:
            parquet_files = sorted(partition_dir.glob("*.parquet"))
            if not parquet_files:
                continue
            output_path = partition_dir / "data.parquet"
            if len(parquet_files) == 1:
                source_path = parquet_files[0]
                if source_path != output_path:
                    output_path.unlink(missing_ok=True)
                    source_path.replace(output_path)
                continue
            temp_output_path = partition_dir / "data.compacting.parquet"
            temp_output_path.unlink(missing_ok=True)
            partition_glob = str(partition_dir / "*.parquet")
            con.execute(
                f"""
                copy (
                    select *
                    from read_parquet('{_sql_path_literal(partition_glob)}', hive_partitioning=false)
                ) to '{_sql_path_literal(temp_output_path)}' (
                    format parquet,
                    compression zstd
                )
                """
            )
            for source_path in parquet_files:
                source_path.unlink(missing_ok=True)
            temp_output_path.replace(output_path)
    finally:
        con.close()
        _cleanup_dir(temp_dir)


def _compact_publication_serving_artifact(
    settings: BuildSettings,
    serving_dir: Path,
    artifact_path: Path,
) -> None:
    dataset_temp_names = {
        _PUBLICATION_MEMBER_DATASET: "publication_compact_member",
        _APPLICATION_EVIDENCE_DATASET: "publication_compact_application",
        _PUBLICATION_CLAIM_DATASET: "publication_compact_claim",
        _FAMILY_PUBLICATIONS_DATASET: "publication_compact_family",
    }
    for dataset_name, temp_name in dataset_temp_names.items():
        _compact_partitioned_parquet_dataset(
            settings,
            serving_dir,
            artifact_path / dataset_name,
            temp_name,
        )


def _open_publication_build_connection(
    settings: BuildSettings,
    serving_dir: Path,
    temp_name: str,
) -> tuple[duckdb.DuckDBPyConnection, Path]:
    temp_dir = serving_dir / "_duckdb_tmp" / temp_name
    _cleanup_dir(temp_dir)
    ensure_dir(temp_dir)
    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute(f"set threads={_serving_snapshot_threads(settings)}")
    con.execute(f"set temp_directory='{_sql_path_literal(temp_dir)}'")
    con.execute(
        f"set max_temp_directory_size='{_duckdb_size_literal(_serving_snapshot_temp_budget_bytes(settings, temp_dir))}'"
    )
    return con, temp_dir


def _publication_dataset_glob(dataset_path: Path) -> str:
    return str(dataset_path / "*/*.parquet")


def _duplicate_surplus_for_source(
    con: duckdb.DuckDBPyConnection,
    source_sql: str,
    key_columns: list[str],
    parameters: list[object] | tuple[object, ...] = (),
) -> int:
    key_expr = ", ".join(key_columns)
    value = con.execute(
        f"""
        select coalesce(sum(dup_count - 1), 0)
        from (
            select count(*) as dup_count
            from ({source_sql}) source_rows
            group by {key_expr}
            having count(*) > 1
        )
        """,
        list(parameters),
    ).fetchone()[0]
    return int(value or 0)


def _assert_unique_source_keys(
    con: duckdb.DuckDBPyConnection,
    label: str,
    source_sql: str,
    key_columns: list[str],
    parameters: list[object] | tuple[object, ...] = (),
) -> None:
    duplicate_surplus = _duplicate_surplus_for_source(
        con,
        source_sql,
        key_columns,
        parameters,
    )
    if duplicate_surplus:
        joined = ", ".join(key_columns)
        raise RuntimeError(
            f"{label} must be unique on [{joined}], but found {duplicate_surplus} duplicate surplus rows."
        )


def _publication_dataset_stats(con: duckdb.DuckDBPyConnection, dataset_path: Path) -> dict[str, int]:
    if not dataset_path.exists() or not any(dataset_path.glob("*/*.parquet")):
        return {"rows": 0, "columns": 0}
    glob = _publication_dataset_glob(dataset_path)
    row_count = int(con.execute("select count(*) from read_parquet(?, hive_partitioning=true)", [glob]).fetchone()[0])
    column_count = len(con.execute("describe select * from read_parquet(?, hive_partitioning=true)", [glob]).fetchall())
    return {"rows": row_count, "columns": column_count}


def _summarize_publication_serving_artifact(artifact_path: Path) -> dict[str, Any]:
    datasets = {
        _PUBLICATION_MEMBER_DATASET: artifact_path / _PUBLICATION_MEMBER_DATASET,
        _APPLICATION_EVIDENCE_DATASET: artifact_path / _APPLICATION_EVIDENCE_DATASET,
        _PUBLICATION_CLAIM_DATASET: artifact_path / _PUBLICATION_CLAIM_DATASET,
        _FAMILY_PUBLICATIONS_DATASET: artifact_path / _FAMILY_PUBLICATIONS_DATASET,
    }
    con = duckdb.connect()
    try:
        table_stats = {
            dataset_name: _publication_dataset_stats(con, dataset_path)
            for dataset_name, dataset_path in datasets.items()
            if dataset_path.exists()
        }
    finally:
        con.close()
    return {
        "path": artifact_path,
        "tables": list(table_stats.keys()),
        "table_stats": table_stats,
        "bytes": _directory_size(artifact_path),
    }


def _validate_publication_serving_artifact(artifact_path: Path) -> None:
    datasets = {
        _PUBLICATION_MEMBER_DATASET: (
            artifact_path / _PUBLICATION_MEMBER_DATASET,
            ["publication_number_full"],
        ),
        _APPLICATION_EVIDENCE_DATASET: (
            artifact_path / _APPLICATION_EVIDENCE_DATASET,
            ["appln_id"],
        ),
        _PUBLICATION_CLAIM_DATASET: (
            artifact_path / _PUBLICATION_CLAIM_DATASET,
            ["publication_number_full"],
        ),
        _FAMILY_PUBLICATIONS_DATASET: (
            artifact_path / _FAMILY_PUBLICATIONS_DATASET,
            ["docdb_family_id", "publication_number_full"],
        ),
    }
    con = duckdb.connect()
    try:
        for dataset_name, (dataset_path, key_columns) in datasets.items():
            if not dataset_path.exists() or not any(dataset_path.glob("*/*.parquet")):
                continue
            _assert_unique_source_keys(
                con,
                dataset_name,
                "select * from read_parquet(?, hive_partitioning=true)",
                key_columns,
                [_publication_dataset_glob(dataset_path)],
            )
    finally:
        con.close()


def _publication_partition_glob(dataset_path: Path, partition_column: str, partition_value: str) -> str:
    return str(dataset_path / f"{partition_column}={partition_value}" / "*.parquet")


def _publication_bucket_relation_sql(
    dataset_path: Path | None,
    partition_column: str,
    partition_value: str,
    empty_select_sql: str,
) -> str:
    if dataset_path is None:
        return f"select {empty_select_sql} where false"
    partition_dir = dataset_path / f"{partition_column}={partition_value}"
    if partition_dir.exists() and any(partition_dir.glob("*.parquet")):
        glob = _publication_partition_glob(dataset_path, partition_column, partition_value)
        return f"select * from read_parquet('{_sql_path_literal(glob)}', hive_partitioning=true)"
    return f"select {empty_select_sql} where false"


def _build_optional_publication_support_dataset(
    settings: BuildSettings,
    serving_dir: Path,
    support_root: Path,
    temp_name: str,
    source_path: Path,
    dataset_name: str,
    select_sql: str,
    warnings: list[str],
    missing_warning: str,
) -> Path | None:
    if not source_path.exists():
        warnings.append(missing_warning)
        return None
    dataset_path = support_root / dataset_name
    con, temp_dir = _open_publication_build_connection(settings, serving_dir, temp_name)
    try:
        _copy_partitioned_parquet_dataset(con, dataset_path, select_sql, "appln_bucket")
    finally:
        con.close()
        _cleanup_dir(temp_dir)
    return dataset_path


def _build_publication_application_dataset(
    settings: BuildSettings,
    serving_dir: Path,
    artifact_path: Path,
    member_publications_path: Path,
    shard_count: int,
    warnings: list[str],
) -> None:
    support_root = serving_dir / "_publication_application_support"
    _cleanup_dir(support_root)
    ensure_dir(support_root)
    bucket_values = [str(bucket) for bucket in range(shard_count)]
    ids_dataset_path = support_root / "member_appln_ids_by_bucket"

    try:
        con, temp_dir = _open_publication_build_connection(settings, serving_dir, "publication_application_ids")
        try:
            _copy_partitioned_parquet_dataset(
                con,
                ids_dataset_path,
                f"""
                select distinct
                    cast(appln_id as bigint) as appln_id,
                    {_numeric_bucket_expr("cast(appln_id as bigint)", shard_count)} as appln_bucket
                from read_parquet('{member_publications_path}')
                where appln_id is not null
                """,
                "appln_bucket",
            )
        finally:
            con.close()
            _cleanup_dir(temp_dir)

        ids_glob = _publication_dataset_glob(ids_dataset_path)
        title_path = settings.bronze_dir / "bronze_patstat_appln_title.parquet"
        abstract_path = settings.bronze_dir / "bronze_patstat_appln_abstr.parquet"
        register_core_path = settings.silver_dir / "silver_ep_register_core.parquet"
        register_display_path = settings.silver_dir / "silver_ep_register_display_ledger.parquet"
        register_proc_path = settings.silver_dir / "silver_ep_register_proc_step_features.parquet"
        register_up_path = settings.silver_dir / "silver_ep_register_up_status.parquet"
        register_opposition_path = settings.silver_dir / "silver_ep_register_current_opposition.parquet"
        register_agent_path = settings.silver_dir / "silver_ep_register_agent_summary.parquet"
        application_path = settings.bronze_dir / "bronze_patstat_appln.parquet"

        title_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_title",
            title_path,
            "title_best_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            ),
            ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    ids.appln_bucket,
                    nullif(trim(cast(src.appln_title as varchar)), '') as title_text,
                    lower(coalesce(cast(src.appln_title_lg as varchar), 'en')) as title_language_code,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by
                            case when lower(coalesce(cast(src.appln_title_lg as varchar), 'en')) = 'en' then 0 else 1 end,
                            lower(coalesce(cast(src.appln_title_lg as varchar), 'en')) asc,
                            length(cast(src.appln_title as varchar)) desc
                    ) as row_number
                from read_parquet('{title_path}') src
                join ids using (appln_id)
                where nullif(trim(cast(src.appln_title as varchar)), '') is not null
            )
            select appln_id, appln_bucket, title_text, title_language_code
            from ranked
            where row_number = 1
            """,
            warnings,
            f"Missing optional title source for publication serving: {title_path}",
        )
        abstract_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_abstract",
            abstract_path,
            "abstract_best_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            ),
            ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    ids.appln_bucket,
                    nullif(trim(cast(src.appln_abstract as varchar)), '') as abstract_text,
                    lower(coalesce(cast(src.appln_abstract_lg as varchar), 'en')) as abstract_language_code,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by
                            case when lower(coalesce(cast(src.appln_abstract_lg as varchar), 'en')) = 'en' then 0 else 1 end,
                            lower(coalesce(cast(src.appln_abstract_lg as varchar), 'en')) asc,
                            length(cast(src.appln_abstract as varchar)) desc
                    ) as row_number
                from read_parquet('{abstract_path}') src
                join ids using (appln_id)
                where nullif(trim(cast(src.appln_abstract as varchar)), '') is not null
            )
            select appln_id, appln_bucket, abstract_text, abstract_language_code
            from ranked
            where row_number = 1
            """,
            warnings,
            f"Missing optional abstract source for publication serving: {abstract_path}",
        )
        register_core_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_register_core",
            register_core_path,
            "register_core_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            ),
            ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    ids.appln_bucket,
                    cast(src.reg101_id as bigint) as reg101_id,
                    cast(src.register_record_present as boolean) as register_record_present,
                    cast(src.ep_registered_license_flag as boolean) as ep_registered_license_flag,
                    cast(src.ep_licensee_names as varchar) as ep_licensee_names,
                    cast(src.register_snapshot_date as date) as register_snapshot_date,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by
                            cast(src.register_snapshot_date as date) desc nulls last,
                            coalesce(cast(src.register_record_present as boolean), false) desc,
                            case
                                when nullif(trim(cast(src.ep_licensee_names as varchar)), '') is not null then 0
                                else 1
                            end,
                            cast(src.reg101_id as bigint) desc nulls last
                    ) as row_number
                from read_parquet('{register_core_path}') src
                join ids using (appln_id)
            )
            select
                appln_id,
                appln_bucket,
                reg101_id,
                register_record_present,
                ep_registered_license_flag,
                ep_licensee_names,
                register_snapshot_date
            from ranked
            where row_number = 1
            """,
            warnings,
            f"Missing optional register core source for publication serving: {register_core_path}",
        )
        register_display_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_register_display",
            register_display_path,
            "register_display_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            ),
            ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    ids.appln_bucket,
                    cast(src.snapshot_date as date) as display_snapshot_date,
                    cast(src.ep_display_status_text as varchar) as ep_display_status_text,
                    cast(src.status_source as varchar) as status_source,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by cast(src.snapshot_date as date) desc nulls last
                    ) as row_number
                from read_parquet('{register_display_path}') src
                join ids using (appln_id)
            )
            select appln_id, appln_bucket, display_snapshot_date, ep_display_status_text, status_source
            from ranked
            where row_number = 1
            """,
            warnings,
            f"Missing optional register display source for publication serving: {register_display_path}",
        )
        register_proc_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_register_proc",
            register_proc_path,
            "register_proc_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            )
            select
                cast(src.appln_id as bigint) as appln_id,
                ids.appln_bucket,
                cast(src.ep_proc_step_maturity_score as double) as ep_proc_step_maturity_score,
                cast(src.ep_search_report_mailed_date as date) as ep_search_report_mailed_date,
                cast(src.ep_latest_proc_phase_code as varchar) as ep_latest_proc_phase_code,
                cast(src.ep_latest_proc_result_code as varchar) as ep_latest_proc_result_code,
                cast(src.ep_proc_time_limit_days as bigint) as ep_proc_time_limit_days
            from read_parquet('{register_proc_path}') src
            join ids using (appln_id)
            """,
            warnings,
            f"Missing optional register procedure source for publication serving: {register_proc_path}",
        )
        register_up_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_register_up",
            register_up_path,
            "register_up_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            )
            select
                cast(src.appln_id as bigint) as appln_id,
                ids.appln_bucket,
                cast(src.ep_register_is_unitary_patent as boolean) as ep_register_is_unitary_patent,
                cast(src.ep_register_up_status_code as varchar) as ep_register_up_status_code,
                cast(src.ep_register_up_status_text as varchar) as ep_register_up_status_text,
                cast(src.ep_register_up_event_latest_date as date) as ep_register_up_event_latest_date
            from read_parquet('{register_up_path}') src
            join ids using (appln_id)
            """,
            warnings,
            f"Missing optional register UP source for publication serving: {register_up_path}",
        )
        register_opposition_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_register_opposition",
            register_opposition_path,
            "register_opposition_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            ),
            ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    ids.appln_bucket,
                    cast(src.ep_opposition_active as boolean) as ep_opposition_active,
                    cast(src.ep_opposition_status_text as varchar) as ep_opposition_status_text,
                    cast(src.ep_opponent_names as varchar) as ep_opponent_names,
                    cast(src.ep_opponent_agent_names as varchar) as ep_opponent_agent_names,
                    cast(src.ep_appeal_active as boolean) as ep_appeal_active,
                    cast(src.ep_appeal_result_text as varchar) as ep_appeal_result_text,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by
                            coalesce(cast(src.ep_opposition_active as boolean), false) desc,
                            coalesce(cast(src.ep_appeal_active as boolean), false) desc,
                            case
                                when nullif(trim(cast(src.ep_opposition_status_text as varchar)), '') is not null then 0
                                else 1
                            end,
                            case
                                when nullif(trim(cast(src.ep_opponent_names as varchar)), '') is not null then 0
                                else 1
                            end,
                            case
                                when nullif(trim(cast(src.ep_opponent_agent_names as varchar)), '') is not null then 0
                                else 1
                            end,
                            case
                                when nullif(trim(cast(src.ep_appeal_result_text as varchar)), '') is not null then 0
                                else 1
                            end
                    ) as row_number
                from read_parquet('{register_opposition_path}') src
                join ids using (appln_id)
            )
            select
                appln_id,
                appln_bucket,
                ep_opposition_active,
                ep_opposition_status_text,
                ep_opponent_names,
                ep_opponent_agent_names,
                ep_appeal_active,
                ep_appeal_result_text
            from ranked
            where row_number = 1
            """,
            warnings,
            f"Missing optional register opposition source for publication serving: {register_opposition_path}",
        )
        register_agent_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_register_agent",
            register_agent_path,
            "register_agent_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            )
            select
                cast(src.appln_id as bigint) as appln_id,
                ids.appln_bucket,
                cast(src.ep_register_lead_agent_name as varchar) as ep_register_lead_agent_name,
                cast(src.ep_register_lead_agent_country as varchar) as ep_register_lead_agent_country
            from read_parquet('{register_agent_path}') src
            join ids using (appln_id)
            """,
            warnings,
            f"Missing optional register agent source for publication serving: {register_agent_path}",
        )
        application_dataset_path = _build_optional_publication_support_dataset(
            settings,
            serving_dir,
            support_root,
            "publication_application_filing",
            application_path,
            "application_filing_by_appln",
            f"""
            with ids as (
                select appln_id, appln_bucket
                from read_parquet('{ids_glob}', hive_partitioning=true)
            ),
            ranked as (
                select
                    cast(src.appln_id as bigint) as appln_id,
                    ids.appln_bucket,
                    cast(src.appln_filing_date as date) as appln_filing_date,
                    row_number() over (
                        partition by cast(src.appln_id as bigint)
                        order by cast(src.appln_filing_date as date) asc nulls last
                    ) as row_number
                from read_parquet('{application_path}') src
                join ids using (appln_id)
                where src.appln_filing_date is not null
            )
            select appln_id, appln_bucket, appln_filing_date
            from ranked
            where row_number = 1
            """,
            warnings,
            f"Missing optional application source for publication serving: {application_path}",
        )

        con, temp_dir = _open_publication_build_connection(settings, serving_dir, "publication_application_export")
        try:
            _copy_bucketed_parquet_dataset(
                con,
                artifact_path / _APPLICATION_EVIDENCE_DATASET,
                "appln_bucket",
                bucket_values,
                lambda appln_bucket: f"""
                select
                    ids.appln_id,
                    t.title_text,
                    t.title_language_code,
                    a.abstract_text,
                    a.abstract_language_code,
                    f.appln_filing_date,
                    rc.reg101_id,
                    rc.register_record_present,
                    rc.ep_registered_license_flag,
                    rc.ep_licensee_names,
                    rc.register_snapshot_date,
                    rd.ep_display_status_text,
                    rd.status_source,
                    rd.display_snapshot_date,
                    rp.ep_proc_step_maturity_score,
                    rp.ep_search_report_mailed_date,
                    rp.ep_latest_proc_phase_code,
                    rp.ep_latest_proc_result_code,
                    rp.ep_proc_time_limit_days,
                    ru.ep_register_is_unitary_patent,
                    ru.ep_register_up_status_code,
                    ru.ep_register_up_status_text,
                    ru.ep_register_up_event_latest_date,
                    ro.ep_opposition_active,
                    ro.ep_opposition_status_text,
                    ro.ep_opponent_names,
                    ro.ep_opponent_agent_names,
                    ro.ep_appeal_active,
                    ro.ep_appeal_result_text,
                    ra.ep_register_lead_agent_name,
                    ra.ep_register_lead_agent_country
                from ({_publication_bucket_relation_sql(
                    ids_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket",
                )}) ids
                left join ({_publication_bucket_relation_sql(
                    title_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::varchar as title_text, null::varchar as title_language_code",
                )}) t using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    abstract_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::varchar as abstract_text, null::varchar as abstract_language_code",
                )}) a using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    application_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::date as appln_filing_date",
                )}) f using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    register_core_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::bigint as reg101_id, null::boolean as register_record_present, null::boolean as ep_registered_license_flag, null::varchar as ep_licensee_names, null::date as register_snapshot_date",
                )}) rc using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    register_display_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::date as display_snapshot_date, null::varchar as ep_display_status_text, null::varchar as status_source",
                )}) rd using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    register_proc_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::double as ep_proc_step_maturity_score, null::date as ep_search_report_mailed_date, null::varchar as ep_latest_proc_phase_code, null::varchar as ep_latest_proc_result_code, null::bigint as ep_proc_time_limit_days",
                )}) rp using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    register_up_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::boolean as ep_register_is_unitary_patent, null::varchar as ep_register_up_status_code, null::varchar as ep_register_up_status_text, null::date as ep_register_up_event_latest_date",
                )}) ru using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    register_opposition_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::boolean as ep_opposition_active, null::varchar as ep_opposition_status_text, null::varchar as ep_opponent_names, null::varchar as ep_opponent_agent_names, null::boolean as ep_appeal_active, null::varchar as ep_appeal_result_text",
                )}) ro using (appln_bucket, appln_id)
                left join ({_publication_bucket_relation_sql(
                    register_agent_dataset_path,
                    "appln_bucket",
                    appln_bucket,
                    "null::bigint as appln_id, null::varchar as appln_bucket, null::varchar as ep_register_lead_agent_name, null::varchar as ep_register_lead_agent_country",
                )}) ra using (appln_bucket, appln_id)
                """,
            )
        finally:
            con.close()
            _cleanup_dir(temp_dir)
    finally:
        _cleanup_dir(support_root)


def _build_publication_serving_artifact(
    settings: BuildSettings,
    serving_dir: Path,
    warnings: list[str],
) -> dict[str, Any]:
    artifact_path = serving_dir / "publication_serving"
    _cleanup_dir(artifact_path)
    ensure_dir(artifact_path)
    member_publications_path = settings.silver_dir / "silver_family_member_publications.parquet"
    shard_count = max(1, int(settings.execution.get("serving_publication_shard_count", _PUBLICATION_SHARD_COUNT)))

    if not member_publications_path.exists():
        warnings.append(
            f"Skipped publication serving artifact because required source is missing: {member_publications_path}"
        )
        return {
            "path": artifact_path,
            "tables": [],
            "table_stats": {},
            "bytes": _directory_size(artifact_path),
        }

    con, temp_dir = _open_publication_build_connection(settings, serving_dir, "publication_member")
    try:
        _overlay_family_summary_serving(
            con,
            settings.gold_dir / "gold_family_summary.parquet",
            settings.silver_dir / "silver_ep_register_core.parquet",
            settings.silver_dir / "silver_ep_register_current_opposition.parquet",
            warnings,
        )
        _copy_partitioned_parquet_dataset(
            con,
            artifact_path / _PUBLICATION_MEMBER_DATASET,
            f"""
            select
                cast(m.pat_publn_id as bigint) as pat_publn_id,
                cast(m.appln_id as bigint) as appln_id,
                cast(m.docdb_family_id as bigint) as docdb_family_id,
                upper(cast(m.publication_number_full as varchar)) as publication_number_full,
                cast(m.publn_auth as varchar) as publn_auth,
                cast(m.publn_nr as varchar) as publn_nr,
                cast(m.publn_kind as varchar) as publn_kind,
                cast(m.publn_date as date) as publn_date,
                cast(m.is_application_stage as boolean) as is_application_stage,
                cast(m.is_grant_stage as boolean) as is_grant_stage,
                cast(m.is_modifier_stage as boolean) as is_modifier_stage,
                cast(m.scope_type as varchar) as scope_type,
                cast(m.snapshot_date as varchar) as snapshot_date,
                cast(fs.family_composite_status as varchar) as family_composite_status,
                cast(fs.mart_family_composite_status as varchar) as mart_family_composite_status,
                cast(fs.effective_family_composite_status as varchar) as effective_family_composite_status,
                cast(fs.active_opposition_application_count as bigint) as active_opposition_application_count,
                cast(fs.opposition_overlay_active as boolean) as opposition_overlay_active,
                {_publication_bucket_expr("m.publication_number_full")} as publication_bucket
            from read_parquet('{member_publications_path}') m
            left join family_summary fs using (docdb_family_id)
            """,
            "publication_bucket",
        )
    finally:
        con.close()
        _cleanup_dir(temp_dir)

    _build_publication_application_dataset(
        settings,
        serving_dir,
        artifact_path,
        member_publications_path,
        shard_count,
        warnings,
    )

    con, temp_dir = _open_publication_build_connection(settings, serving_dir, "publication_claim")
    try:
        publication_numbers_path = artifact_path / _PUBLICATION_MEMBER_DATASET
        con.execute(
            f"""
            create or replace temp table publication_member_numbers as
            select distinct publication_number_full
            from read_parquet('{_publication_dataset_glob(publication_numbers_path)}', hive_partitioning=true)
            where publication_number_full is not null
            """
        )
        epab_publication_path = settings.bronze_dir / "bronze_epab_publication.parquet"
        epab_claims_path = settings.bronze_dir / "bronze_epab_claims.parquet"
        if epab_publication_path.exists() and epab_claims_path.exists():
            con.execute(
                f"""
                create or replace temp table publication_claim_best as
                with ranked as (
                    select
                        upper(cast(p.publication_number_full as varchar)) as publication_number_full,
                        nullif(trim(cast(c.claim_text_plain as varchar)), '') as claim_1_text,
                        lower(coalesce(cast(c.language_code as varchar), 'en')) as claim_1_language_code,
                        row_number() over (
                            partition by upper(cast(p.publication_number_full as varchar))
                            order by lower(coalesce(cast(c.language_code as varchar), 'en')) asc
                        ) as row_number
                    from read_parquet('{epab_publication_path}') p
                    join publication_member_numbers pm
                      on upper(cast(p.publication_number_full as varchar)) = pm.publication_number_full
                    join read_parquet('{epab_claims_path}') c using (epab_doc_id)
                    where try_cast(c.claim_sequence_no as bigint) = 1
                      and lower(coalesce(cast(c.language_code as varchar), 'en')) = 'en'
                      and nullif(trim(cast(c.claim_text_plain as varchar)), '') is not null
                )
                select publication_number_full, claim_1_text, claim_1_language_code
                from ranked
                where row_number = 1
                """
            )
            _copy_partitioned_parquet_dataset(
                con,
                artifact_path / _PUBLICATION_CLAIM_DATASET,
                f"""
                select
                    publication_number_full,
                    claim_1_text,
                    claim_1_language_code,
                    {_publication_bucket_expr("publication_number_full")} as publication_bucket
                from publication_claim_best
                where publication_number_full is not null
                """,
                "publication_bucket",
            )
        else:
            warnings.append(
                "Missing optional EPAB claim sources for publication serving: "
                + ", ".join(
                    str(path) for path in [epab_publication_path, epab_claims_path] if not path.exists()
                )
            )
            ensure_dir(artifact_path / _PUBLICATION_CLAIM_DATASET)
    finally:
        con.close()
        _cleanup_dir(temp_dir)

    con, temp_dir = _open_publication_build_connection(settings, serving_dir, "publication_family")
    try:
        _copy_partitioned_parquet_dataset(
            con,
            artifact_path / _FAMILY_PUBLICATIONS_DATASET,
            f"""
            select
                cast(docdb_family_id as bigint) as docdb_family_id,
                upper(cast(publication_number_full as varchar)) as publication_number_full,
                cast(publn_auth as varchar) as publn_auth,
                cast(publn_kind as varchar) as publn_kind,
                cast(publn_date as date) as publn_date,
                cast(is_application_stage as boolean) as is_application_stage,
                cast(is_grant_stage as boolean) as is_grant_stage,
                cast(is_modifier_stage as boolean) as is_modifier_stage,
                {_numeric_bucket_expr("docdb_family_id", shard_count)} as family_bucket
            from read_parquet('{member_publications_path}')
            where docdb_family_id is not null
            """,
            "family_bucket",
        )
    finally:
        con.close()
        _cleanup_dir(temp_dir)

    _compact_publication_serving_artifact(settings, serving_dir, artifact_path)
    _validate_publication_serving_artifact(artifact_path)

    return _summarize_publication_serving_artifact(artifact_path)


def _analytics_source_tables(settings: BuildSettings) -> dict[str, Path]:
    return {
        "family_summary": settings.gold_dir / "gold_family_summary.parquet",
        "family_blocking_power": settings.gold_dir / "gold_family_blocking_power.parquet",
        "family_heritage_summary": settings.gold_dir / "gold_family_heritage_summary.parquet",
        "family_blocking_power_timeseries": settings.gold_dir / "gold_family_blocking_power_timeseries.parquet",
        "family_field_contributions": settings.gold_dir / "gold_family_field_contributions.parquet",
        "family_field_contributions_timeseries": settings.gold_dir / "gold_family_field_contributions_timeseries.parquet",
        "family_citation_chronology": settings.gold_dir / "gold_family_citation_chronology.parquet",
        "family_compare_pit": settings.gold_dir / "gold_family_compare_pit.parquet",
        "family_classification_mix_pit": settings.gold_dir / "gold_family_classification_mix_pit.parquet",
        "family_classification_jurisdiction_pit": settings.gold_dir / "gold_family_classification_jurisdiction_pit.parquet",
        "family_citation_summary": settings.gold_dir / "gold_family_citation_summary.parquet",
        "family_citation_timeseries_pit": settings.gold_dir / "gold_family_citation_timeseries_pit.parquet",
        "portfolio_summary": settings.gold_dir / "gold_portfolio_summary.parquet",
        "portfolio_forecast_summary": settings.gold_dir / "gold_portfolio_forecast_summary.parquet",
        "portfolio_forecast_segments": settings.gold_dir / "gold_portfolio_forecast_segments.parquet",
        "portfolio_forecast_contributors": settings.gold_dir / "gold_portfolio_forecast_contributors.parquet",
        "portfolio_threat_matrix": settings.gold_dir / "gold_portfolio_threat_matrix.parquet",
        "portfolio_field_timeseries": settings.gold_dir / "gold_portfolio_field_timeseries.parquet",
        "portfolio_compare_pit": settings.gold_dir / "gold_portfolio_compare_pit.parquet",
        "portfolio_classification_mix_pit": settings.gold_dir / "gold_portfolio_classification_mix_pit.parquet",
        "portfolio_citation_summary": settings.gold_dir / "gold_portfolio_citation_summary.parquet",
        "portfolio_citation_timeseries": settings.gold_dir / "gold_portfolio_citation_timeseries.parquet",
        "portfolio_citation_family_leaderboard": settings.gold_dir / "gold_portfolio_citation_family_leaderboard.parquet",
        "portfolio_attacker_momentum": settings.gold_dir / "gold_portfolio_attacker_momentum.parquet",
        "portfolio_citation_pressure_by_field": settings.gold_dir / "gold_portfolio_citation_pressure_by_field.parquet",
        "portfolio_citation_pressure_by_jurisdiction": settings.gold_dir / "gold_portfolio_citation_pressure_by_jurisdiction.parquet",
        "portfolio_filing_timeseries": settings.gold_dir / "gold_portfolio_filing_timeseries.parquet",
        "market_summary_pit": settings.gold_dir / "gold_market_summary_pit.parquet",
        "market_leaderboard_pit": settings.gold_dir / "gold_market_leaderboard_pit.parquet",
        "market_cpc_trend_pit": settings.gold_dir / "gold_market_cpc_trend_pit.parquet",
        "market_cpc_jurisdiction_trend_pit": settings.gold_dir / "gold_market_cpc_jurisdiction_trend_pit.parquet",
        "market_citation_trend_pit": settings.gold_dir / "gold_market_citation_trend_pit.parquet",
        "market_citation_pressure_by_jurisdiction_pit": (
            settings.gold_dir / "gold_market_citation_pressure_by_jurisdiction_pit.parquet"
        ),
        "market_attacker_leaderboard_pit": settings.gold_dir / "gold_market_attacker_leaderboard_pit.parquet",
        "family_owner_bridge": settings.silver_dir / "silver_family_owner_bridge.parquet",
        "family_member_publications": settings.silver_dir / "silver_family_member_publications.parquet",
        "family_citation_metrics": settings.silver_dir / "silver_family_citation_metrics.parquet",
        "family_oecd_quality": settings.silver_dir / "silver_family_oecd_quality.parquet",
        "family_feature_snapshot_pit": settings.silver_dir / "silver_family_feature_snapshot_pit.parquet",
        "enriched_citation_network": settings.silver_dir / "silver_enriched_citation_network.parquet",
        "family_enforceability_branches": settings.silver_dir / "silver_family_enforceability_branches.parquet",
        "family_status_history": settings.silver_dir / "silver_family_status_history.parquet",
        "branch_status_history_dense": settings.silver_dir / "silver_branch_status_history_dense.parquet",
        "legal_status_event_ledger": settings.silver_dir / "silver_legal_status_event_ledger.parquet",
        "family_jurisdiction_unrolled": settings.silver_dir / "silver_family_jurisdiction_unrolled.parquet",
        "ep_register_up_status": settings.silver_dir / "silver_ep_register_up_status.parquet",
        "up_status": settings.silver_dir / "silver_up_status.parquet",
        "family_forecast_predictions": settings.ml_dir / "ml_prediction_family_future_citations.parquet",
        "family_lapse_risk_predictions": settings.ml_dir / "ml_prediction_family_jurisdiction_lapse_risk.parquet",
        "pending_grant_prediction_pipeline": settings.ml_dir / "ml_prediction_pending_grant_pipeline.parquet",
    }


def _build_snapshot(
    snapshot_path: Path,
    settings: BuildSettings,
    source_tables: dict[str, Path],
    warnings: list[str],
    derived_builders: list[tuple[str, callable]] | None = None,
    run_analyze: bool = True,
    run_checkpoint: bool = True,
    summarize_inline: bool = True,
) -> dict[str, Any]:
    _cleanup_snapshot_files(snapshot_path)
    ensure_dir(snapshot_path.parent)
    snapshot_temp_dir = _serving_snapshot_temp_dir(snapshot_path)
    _cleanup_dir(snapshot_temp_dir)
    ensure_dir(snapshot_temp_dir)
    con = duckdb.connect(str(snapshot_path))
    con.execute("set preserve_insertion_order=false")
    con.execute(f"set threads={_serving_snapshot_threads(settings)}")
    con.execute(f"set temp_directory='{_sql_path_literal(snapshot_temp_dir)}'")
    con.execute(
        f"set max_temp_directory_size='{_duckdb_size_literal(_serving_snapshot_temp_budget_bytes(settings, snapshot_temp_dir))}'"
    )
    try:
        for target_table, source_path in source_tables.items():
            _copy_source_table(con, source_path, target_table, warnings)
        for target_table, builder in derived_builders or []:
            built = builder(con, warnings)
            if not built:
                warnings.append(f"Derived serving table `{target_table}` was not materialized.")
        if run_analyze:
            con.execute("analyze")
        if run_checkpoint:
            con.execute("checkpoint")
        if summarize_inline:
            tables = _snapshot_tables(con)
            return {
                "path": snapshot_path,
                "tables": tables,
                "table_stats": {table: _table_stats(con, table) for table in tables},
                "bytes": snapshot_path.stat().st_size if snapshot_path.exists() else 0,
            }
        return {
            "path": snapshot_path,
            "tables": [],
            "table_stats": {},
            "bytes": snapshot_path.stat().st_size if snapshot_path.exists() else 0,
        }
    finally:
        con.close()
        _cleanup_dir(snapshot_temp_dir)


def build_serving_snapshots(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="serving-snapshots",
        status="success",
        summary="Materialized backend-ready serving DuckDB snapshots and serving manifest/audit artifacts for local and Azure-compatible V2 runtime consumption.",
        inputs=[
            str(settings.gold_dir / "gold_family_summary.parquet"),
            str(settings.gold_dir / "gold_family_blocking_power.parquet"),
            str(settings.gold_dir / "gold_family_compare_pit.parquet"),
            str(settings.gold_dir / "gold_portfolio_classification_mix_pit.parquet"),
            str(settings.bronze_dir / "bronze_patstat_appln.parquet"),
            str(settings.silver_dir / "silver_ep_register_core.parquet"),
            str(settings.silver_dir / "silver_ep_register_current_opposition.parquet"),
            str(settings.silver_dir / "silver_family_owner_bridge.parquet"),
            str(settings.gold_dir / "gold_portfolio_summary.parquet"),
            str(settings.gold_dir / "gold_portfolio_citation_family_leaderboard.parquet"),
            str(settings.gold_dir / "gold_portfolio_forecast_summary.parquet"),
            str(settings.gold_dir / "gold_portfolio_filing_timeseries.parquet"),
            str(settings.gold_dir / "gold_portfolio_threat_matrix.parquet"),
            str(settings.gold_dir / "gold_semantic_match_context.parquet"),
            str(settings.gold_dir / "gold_market_intelligence_overview.parquet"),
            str(settings.gold_dir / "gold_market_intelligence_segments.parquet"),
            str(settings.gold_dir / "gold_market_intelligence_timeseries.parquet"),
            str(settings.gold_dir / "gold_portfolio_citation_summary.parquet"),
            str(settings.gold_dir / "gold_portfolio_citation_timeseries.parquet"),
            str(settings.gold_dir / "gold_market_summary_pit.parquet"),
            str(settings.silver_dir / "silver_enriched_citation_network.parquet"),
            str(settings.ml_dir / "ml_prediction_family_future_citations.parquet"),
        ],
        methods=[
            "Materialized domain-split local DuckDB serving snapshots from Gold parquet artifacts.",
            "Overlaid current EP opposition support into serving-time family status so deployed backend reads current under-fire families without rebuilding silver/gold marts.",
            "Precomputed one-row-per-family compare serving payloads so backend compare routes can avoid request-time parquet window scans.",
            "Precomputed current portfolio classification mix so the hot portfolio classification route can avoid request-time PIT parquet scans.",
            "Packaged family, portfolio, compare-timeslice, market, citation, legal, and ML support marts into a dedicated analytics snapshot for parity-safe backend detail panels.",
            "Packaged heavyweight publication evidence into a dedicated sharded serving artifact so publication-page text/legal evidence no longer bloats the core runtime artifact.",
            "Emitted serving manifest and serving audit JSONs for local/cloud parity and release-safe artifact resolution.",
        ],
        calculations=[
            "family_summary serving overlays active EP opposition from Register support onto current family status and opposed-branch counts while retaining mart_* provenance columns.",
            "family_compare_current_serving computes lifecycle-aware legal durability percentiles and priority-year x field citation heritage percentiles at build time.",
            "portfolio_classification_current_serving retains latest-year shares plus previous-year trajectories for the current portfolio classification panel.",
            "analytics_serving preserves the existing derived mart contracts as indexed DuckDB tables so historical/detail routes can read serving tables instead of request-time parquet scans.",
            "Publication evidence is exported as keyed parquet shards by publication number, application id, and family id so backend point lookups avoid monolithic DuckDB checkpoint pressure.",
            "Snapshot manifests describe filenames, table lists, and byte sizes so backend artifact locators can resolve local or cached snapshot paths without inspecting raw parquet layouts.",
        ],
        doc_refs=[
            "docs/next-phase-v2/40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md",
            "docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md",
            "docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md",
        ],
        downstream_impacts=[
            "backend_v2 family compare can consume `core_serving.duckdb` in both local_fs and azure_blob_cached modes.",
            "backend_v2 portfolio classification can resolve current classification mix from serving tables without recomputing owner-year PIT scans at request time.",
            "backend_v2 family, portfolio, compare-timeslice, and deep market detail routes can resolve derived analytics tables from `analytics_serving.duckdb` instead of raw parquet marts.",
            "backend_v2 publication pages can resolve the dedicated `publication_serving` artifact independently, with raw parquet fallback preserved when that artifact is absent.",
            "release-manifest-driven serving artifact hydration can now point to one stable core snapshot instead of route-specific raw parquet paths.",
        ],
    )

    serving_dir = _serving_dir(settings)
    core_path = serving_dir / "core_serving.duckdb"
    analytics_path = serving_dir / "analytics_serving.duckdb"
    semantic_path = serving_dir / "semantic_serving.duckdb"
    market_path = serving_dir / "market_serving.duckdb"
    publication_path = serving_dir / "publication_serving"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    audit_path = serving_dir / "serving_snapshot_audit.json"

    warnings: list[str] = []

    core_sources = {
        "family_summary": settings.gold_dir / "gold_family_summary.parquet",
        "family_blocking_power": settings.gold_dir / "gold_family_blocking_power.parquet",
        "family_heritage_summary": settings.gold_dir / "gold_family_heritage_summary.parquet",
        "family_owner_bridge": settings.silver_dir / "silver_family_owner_bridge.parquet",
        "portfolio_summary": settings.gold_dir / "gold_portfolio_summary.parquet",
        "portfolio_citation_family_leaderboard": settings.gold_dir / "gold_portfolio_citation_family_leaderboard.parquet",
        "portfolio_forecast_summary": settings.gold_dir / "gold_portfolio_forecast_summary.parquet",
        "portfolio_forecast_segments": settings.gold_dir / "gold_portfolio_forecast_segments.parquet",
        "portfolio_forecast_contributors": settings.gold_dir / "gold_portfolio_forecast_contributors.parquet",
        "portfolio_filing_timeseries": settings.gold_dir / "gold_portfolio_filing_timeseries.parquet",
        "portfolio_heritage_summary": settings.gold_dir / "gold_portfolio_heritage_summary.parquet",
        "portfolio_threat_matrix": settings.gold_dir / "gold_portfolio_threat_matrix.parquet",
    }
    semantic_sources = {
        "semantic_match_context": settings.gold_dir / "gold_semantic_match_context.parquet",
    }
    market_sources = {
        "market_intelligence_overview": settings.gold_dir / "gold_market_intelligence_overview.parquet",
        "market_intelligence_segments": settings.gold_dir / "gold_market_intelligence_segments.parquet",
        "market_intelligence_timeseries": settings.gold_dir / "gold_market_intelligence_timeseries.parquet",
    }
    analytics_sources = _analytics_source_tables(settings)

    core_info = _build_snapshot(
        core_path,
        settings,
        core_sources,
        warnings,
        derived_builders=[
            (
                "family_summary",
                lambda con, local_warnings: _overlay_family_summary_serving(
                    con,
                    settings.gold_dir / "gold_family_summary.parquet",
                    settings.silver_dir / "silver_ep_register_core.parquet",
                    settings.silver_dir / "silver_ep_register_current_opposition.parquet",
                    local_warnings,
                ),
            ),
            (
                "family_compare_current_serving",
                lambda con, local_warnings: _create_family_compare_current_serving(
                    con,
                    settings.gold_dir / "gold_family_summary.parquet",
                    settings.gold_dir / "gold_family_blocking_power.parquet",
                    settings.gold_dir / "gold_family_compare_pit.parquet",
                    local_warnings,
                ),
            ),
            (
                "portfolio_compare_current_serving",
                lambda con, local_warnings: _create_portfolio_compare_current_serving(
                    con,
                    settings.gold_dir / "gold_portfolio_summary.parquet",
                    local_warnings,
                ),
            ),
            (
                "portfolio_classification_current_serving",
                lambda con, local_warnings: _create_portfolio_classification_current_serving(
                    con,
                    settings.gold_dir / "gold_portfolio_classification_mix_pit.parquet",
                    local_warnings,
                ),
            ),
        ],
    )
    analytics_info = _build_snapshot(analytics_path, settings, analytics_sources, warnings)
    semantic_info = _build_snapshot(semantic_path, settings, semantic_sources, warnings)
    market_info = _build_snapshot(market_path, settings, market_sources, warnings)
    publication_info: dict[str, Any] | None = None
    try:
        publication_info = _build_publication_serving_artifact(settings, serving_dir, warnings)
    except Exception as exc:
        _cleanup_dir(publication_path)
        warnings.append(
            "Publication serving snapshot failed and was skipped; backend publication routes will fall back to raw parquet evidence. "
            f"Cause: {exc}"
        )

    manifest_snapshots = {
        "core": {
            "filename": core_path.name,
            "tables": core_info["tables"],
            "bytes": core_info["bytes"],
        },
        "analytics": {
            "filename": analytics_path.name,
            "tables": analytics_info["tables"],
            "bytes": analytics_info["bytes"],
        },
        "semantic": {
            "filename": semantic_path.name,
            "tables": semantic_info["tables"],
            "bytes": semantic_info["bytes"],
        },
        "market": {
            "filename": market_path.name,
            "tables": market_info["tables"],
            "bytes": market_info["bytes"],
        },
    }
    if publication_info is not None and publication_path.exists():
        manifest_snapshots["publication"] = {
            "filename": publication_path.name,
            "tables": publication_info["tables"],
            "bytes": publication_info["bytes"],
        }

    manifest_payload = {
        "serving_release": f"{settings.snapshot_date}-serving",
        "contract_version": "1",
        "built_at": utc_now_iso(),
        "source_gold_release": settings.release_id,
        "snapshots": manifest_snapshots,
    }
    audit_snapshots = {
        "core": {
            "path": str(core_path),
            "bytes": core_info["bytes"],
            "table_stats": core_info["table_stats"],
        },
        "analytics": {
            "path": str(analytics_path),
            "bytes": analytics_info["bytes"],
            "table_stats": analytics_info["table_stats"],
        },
        "semantic": {
            "path": str(semantic_path),
            "bytes": semantic_info["bytes"],
            "table_stats": semantic_info["table_stats"],
        },
        "market": {
            "path": str(market_path),
            "bytes": market_info["bytes"],
            "table_stats": market_info["table_stats"],
        },
    }
    if publication_info is not None and publication_path.exists():
        audit_snapshots["publication"] = {
            "path": str(publication_path),
            "bytes": publication_info["bytes"],
            "table_stats": publication_info["table_stats"],
        }

    audit_payload = {
        "serving_release": manifest_payload["serving_release"],
        "source_gold_release": settings.release_id,
        "built_at": manifest_payload["built_at"],
        "snapshots": audit_snapshots,
        "warnings": warnings,
    }

    write_text_json(manifest_path, manifest_payload)
    write_text_json(audit_path, audit_payload)

    result.outputs.extend([str(core_path), str(analytics_path), str(semantic_path), str(market_path)])
    if publication_info is not None and publication_path.exists():
        result.outputs.append(str(publication_path))
    result.outputs.extend([str(manifest_path), str(audit_path)])
    result.artifacts.update(
        {
            "core_serving_duckdb": str(core_path),
            "analytics_serving_duckdb": str(analytics_path),
            "semantic_serving_duckdb": str(semantic_path),
            "market_serving_duckdb": str(market_path),
            "serving_snapshot_manifest": str(manifest_path),
            "serving_snapshot_audit": str(audit_path),
        }
    )
    if publication_info is not None and publication_path.exists():
        result.artifacts["publication_serving_duckdb"] = str(publication_path)
        result.artifacts["publication_serving_artifact"] = str(publication_path)
    result.metrics.update(
        {
            "core_tables": len(core_info["tables"]),
            "analytics_tables": len(analytics_info["tables"]),
            "semantic_tables": len(semantic_info["tables"]),
            "market_tables": len(market_info["tables"]),
            "core_bytes": core_info["bytes"],
            "analytics_bytes": analytics_info["bytes"],
            "semantic_bytes": semantic_info["bytes"],
            "market_bytes": market_info["bytes"],
            "family_compare_current_serving_rows": int(
                core_info["table_stats"].get("family_compare_current_serving", {}).get("rows", 0)
            ),
            "portfolio_classification_current_serving_rows": int(
                core_info["table_stats"].get("portfolio_classification_current_serving", {}).get("rows", 0)
            ),
        }
    )
    if publication_info is not None and publication_path.exists():
        result.metrics.update(
            {
                "publication_tables": len(publication_info["tables"]),
                "publication_bytes": publication_info["bytes"],
                "publication_member_serving_rows": int(
                    publication_info["table_stats"].get(_PUBLICATION_MEMBER_DATASET, {}).get("rows", 0)
                ),
            }
        )
    result.warnings.extend(warnings)
    return result


def run_serving_snapshots(settings: BuildSettings) -> list[StageResult]:
    return [build_serving_snapshots(settings)]
