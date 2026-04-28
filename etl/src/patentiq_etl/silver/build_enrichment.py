from __future__ import annotations

from pathlib import Path

import duckdb

from patentiq_etl.common.io import parquet_columns, parquet_row_count, table_exists
from patentiq_etl.common.types import BuildSettings, StageResult


def build_enrichment_silver(settings: BuildSettings) -> list[StageResult]:
    """Execute all enrichment-oriented Silver builders after the core entity layer exists."""
    return [
        build_citation_and_market_layers(settings),
        build_semantic_representative_text(settings),
    ]


def _sql_sanitize_text(column_expr: str) -> str:
    """Return a pure-SQL semantic text sanitizer equivalent to the Python helper."""
    return (
        "nullif(trim("
        "regexp_replace("
        "regexp_replace("
        f"regexp_replace(cast({column_expr} as varchar), '<[^>]+>', ' ', 'g'), "
        "'\\(\\d+[A-Za-z]?\\)', '', 'g'"
        "), "
        "'\\s+', ' ', 'g'"
        ")"
        "), '')"
    )


def _oecd_quality_select(
    settings: BuildSettings,
    *,
    family_core: Path,
    fields: Path,
    out_coverage: Path,
    out_citation: Path,
    enforce_rollup_sql: str,
    family_filter_sql: str = "",
    indicator_filter_sql: str = "",
) -> str:
    """Return the OECD-family mart select, preferring the richer normalized OECD seed when present."""
    oecd_longform = settings.raw_refs_dir / "oecd_indicator_longform.parquet"
    if oecd_longform.exists():
        return f"""
            with indicator_pivot as (
                select
                    l.docdb_family_id,
                    max(l.family_priority_year) as priority_year,
                    max(l.primary_wipo_field) as primary_wipo_field,
                    max(case when l.indicator_name = 'generality' then l.indicator_value_raw end) as family_generality_score,
                    max(case when l.indicator_name = 'generality' then l.indicator_percentile_rank end) as family_generality_percentile,
                    max(case when l.indicator_name = 'originality' then l.indicator_value_raw end) as family_originality_score,
                    max(case when l.indicator_name = 'originality' then l.indicator_percentile_rank end) as family_originality_percentile,
                    max(case when l.indicator_name = 'radicalness' then l.indicator_value_raw end) as family_radicalness_score,
                    max(case when l.indicator_name = 'radicalness' then l.indicator_percentile_rank end) as family_radicalness_percentile,
                    max(case when l.indicator_name = 'npl_cits' then l.indicator_value_raw end) as family_backward_npl_citation_count,
                    max(case when l.indicator_name = 'npl_cits' then l.indicator_percentile_rank end) as family_backward_npl_citation_percentile,
                    max(case when l.indicator_name = 'science_grounding' then l.indicator_value_raw end) as family_science_grounding_score,
                    max(case when l.indicator_name = 'science_grounding' then l.indicator_percentile_rank end) as family_science_grounding_percentile,
                    max(case when l.indicator_name = 'fwd_cits5' then l.indicator_value_raw end) as family_fwd_cits5,
                    max(case when l.indicator_name = 'fwd_cits5' then l.indicator_percentile_rank end) as family_fwd_cits5_percentile,
                    max(case when l.indicator_name = 'fwd_cits7' then l.indicator_value_raw end) as family_fwd_cits7,
                    max(case when l.indicator_name = 'fwd_cits7' then l.indicator_percentile_rank end) as family_fwd_cits7_percentile,
                    max(case when l.indicator_name = 'family_size' then l.indicator_value_raw end) as family_size_docdb,
                    max(case when l.indicator_name = 'family_size' then l.indicator_percentile_rank end) as family_size_percentile,
                    max(case when l.indicator_name = 'grant_lag' then l.indicator_value_raw end) as family_grant_lag_days,
                    max(case when l.indicator_name = 'grant_lag' then l.indicator_percentile_rank end) as family_grant_lag_speed_percentile,
                    max(case when l.indicator_name = 'quality_index_4' then l.indicator_value_raw end) as family_quality_index_4_score,
                    max(case when l.indicator_name = 'quality_index_4' then l.component_policy end) as family_quality_index_4_policy,
                    max(case when l.indicator_name = 'quality_index_6' then l.indicator_value_raw end) as family_quality_index_6_score,
                    max(case when l.indicator_name = 'quality_index_6' then l.component_policy end) as family_quality_index_6_policy
                from read_parquet('{oecd_longform}') l
                {indicator_filter_sql}
                group by l.docdb_family_id
            )
            select
                c.docdb_family_id,
                coalesce(i.priority_year, c.family_priority_year) as priority_year,
                coalesce(i.primary_wipo_field, f.primary_wipo_field) as primary_wipo_field,
                coalesce(x.family_adjusted_citation_score_raw, 0.0) as family_adjusted_citation_score_raw,
                coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                coalesce(i.family_generality_score, 0.0) as family_generality_score,
                coalesce(i.family_generality_percentile, 0.0) as family_generality_percentile,
                coalesce(i.family_originality_score, 0.0) as family_originality_score,
                coalesce(i.family_originality_percentile, 0.0) as family_originality_percentile,
                coalesce(i.family_radicalness_score, 0.0) as family_radicalness_score,
                coalesce(i.family_radicalness_percentile, 0.0) as family_radicalness_percentile,
                cast(coalesce(i.family_backward_npl_citation_count, 0.0) as bigint) as family_backward_npl_citation_count,
                coalesce(i.family_backward_npl_citation_percentile, 0.0) as family_backward_npl_citation_percentile,
                coalesce(i.family_science_grounding_score, 0.0) as family_science_grounding_score,
                coalesce(i.family_science_grounding_percentile, 0.0) as family_science_grounding_percentile,
                cast(coalesce(i.family_fwd_cits5, 0.0) as bigint) as family_fwd_cits5,
                coalesce(i.family_fwd_cits5_percentile, 0.0) as family_fwd_cits5_percentile,
                cast(coalesce(i.family_fwd_cits7, 0.0) as bigint) as family_fwd_cits7,
                coalesce(i.family_fwd_cits7_percentile, 0.0) as family_fwd_cits7_percentile,
                cast(coalesce(i.family_size_docdb, c.family_size_docdb, 0.0) as bigint) as family_size_docdb,
                coalesce(i.family_size_percentile, 0.0) as family_size_percentile,
                i.family_grant_lag_days as family_grant_lag_days,
                coalesce(i.family_grant_lag_speed_percentile, 0.0) as family_grant_lag_speed_percentile,
                i.family_quality_index_4_score as family_quality_index_4_score,
                i.family_quality_index_4_policy as family_quality_index_4_policy,
                i.family_quality_index_6_score as family_quality_index_6_score,
                i.family_quality_index_6_policy as family_quality_index_6_policy,
                coalesce(i.family_quality_index_6_score, i.family_quality_index_4_score, 0.0) as oecd_quality_percentile,
                coalesce(i.family_quality_index_6_score, i.family_quality_index_4_score, coalesce(x.family_adjusted_citation_score_raw, 0.0) + (coalesce(v.family_grant_publication_count, 0) * 0.5) + (coalesce(e.branch_enforceability_contribution_raw, 0.0) * 0.1)) as oecd_quality_proxy_score
            from read_parquet('{family_core}') c
            {family_filter_sql}
            left join indicator_pivot i
              on c.docdb_family_id = i.docdb_family_id
            left join read_parquet('{fields}') f
              on c.docdb_family_id = f.docdb_family_id
            left join read_parquet('{out_coverage}') v
              on c.docdb_family_id = v.docdb_family_id
            left join read_parquet('{out_citation}') x
              on c.docdb_family_id = x.docdb_family_id
            left join ({enforce_rollup_sql}) e
              on c.docdb_family_id = e.docdb_family_id
        """

    return f"""
        select
            c.docdb_family_id,
            c.family_priority_year as priority_year,
            f.primary_wipo_field as primary_wipo_field,
            coalesce(x.family_adjusted_citation_score_raw, 0.0) as family_adjusted_citation_score_raw,
            coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
            coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
            0.0 as family_generality_score,
            0.0 as family_generality_percentile,
            0.0 as family_originality_score,
            0.0 as family_originality_percentile,
            0.0 as family_radicalness_score,
            0.0 as family_radicalness_percentile,
            0::bigint as family_backward_npl_citation_count,
            0.0 as family_backward_npl_citation_percentile,
            0.0 as family_science_grounding_score,
            0.0 as family_science_grounding_percentile,
            0::bigint as family_fwd_cits5,
            0.0 as family_fwd_cits5_percentile,
            0::bigint as family_fwd_cits7,
            0.0 as family_fwd_cits7_percentile,
            cast(coalesce(c.family_size_docdb, 0) as bigint) as family_size_docdb,
            0.0 as family_size_percentile,
            null::double as family_grant_lag_days,
            0.0 as family_grant_lag_speed_percentile,
            null::double as family_quality_index_4_score,
            null::varchar as family_quality_index_4_policy,
            null::double as family_quality_index_6_score,
            null::varchar as family_quality_index_6_policy,
            coalesce(x.family_adjusted_citation_score_raw, 0.0) + (coalesce(v.family_grant_publication_count, 0) * 0.5) + (coalesce(e.branch_enforceability_contribution_raw, 0.0) * 0.1) as oecd_quality_percentile,
            coalesce(x.family_adjusted_citation_score_raw, 0.0) + (coalesce(v.family_grant_publication_count, 0) * 0.5) + (coalesce(e.branch_enforceability_contribution_raw, 0.0) * 0.1) as oecd_quality_proxy_score
        from read_parquet('{family_core}') c
        {family_filter_sql}
        left join read_parquet('{fields}') f
          on c.docdb_family_id = f.docdb_family_id
        left join read_parquet('{out_coverage}') v
          on c.docdb_family_id = v.docdb_family_id
        left join read_parquet('{out_citation}') x
          on c.docdb_family_id = x.docdb_family_id
        left join ({enforce_rollup_sql}) e
          on c.docdb_family_id = e.docdb_family_id
    """


def _build_kindcode_dependent_outputs(
    con: duckdb.DuckDBPyConnection,
    settings: BuildSettings,
    result: StageResult,
    *,
    family_core: Path,
    publn_seed: Path,
    fields: Path,
    family_status: Path,
    family_jur: Path,
    market_weight: Path,
    citation: Path,
    pat_publn: Path,
    npl_publn: Path,
    owner: Path,
    up_status: Path,
    member_pub: Path,
    legal_ledger: Path,
    kind_norm: Path,
    out_citation_edges: Path,
    out_npl: Path,
    out_trend: Path,
    out_global_trend: Path,
    out_local_trend: Path,
    out_coverage: Path,
    out_citation: Path,
    out_citation_network: Path,
    out_enforce: Path,
    out_field_contrib: Path,
    out_oecd: Path,
    include_legal_outputs: bool = True,
) -> None:
    npl_backlinks_sql = (
        f"select * from read_parquet('{out_npl}')"
        if out_npl.exists()
        else "select null::bigint as docdb_family_id, null::varchar as npl_publn_id, 0::bigint as npl_reference_count, false as science_linkage_flag where false"
    )

    if citation.exists() and pat_publn.exists():
        pub_cols = parquet_columns(pat_publn)
        citation_cols = parquet_columns(citation)
        cited_publn_id = next((col for col in citation_cols if col.lower() == "cited_pat_publn_id"), None)
        source_publn_id = next(col for col in citation_cols if col.lower() == "pat_publn_id")
        if cited_publn_id is not None:
            con.execute(
                f"""
                copy (
                    with scoped_pub as (
                        select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                    ),
                    member_pub_base as (
                        select distinct
                            pat_publn_id,
                            docdb_family_id,
                            publn_auth,
                            trim(publn_kind) as publn_kind,
                            publn_date
                        from read_parquet('{member_pub}')
                    ),
                    raw_edges as (
                        select
                            s.docdb_family_id as source_docdb_family_id,
                            t.docdb_family_id as cited_docdb_family_id,
                            t.docdb_family_id is null as is_out_of_bounds,
                            cast(sp.pat_publn_id as bigint) as citing_pat_publn_id,
                            cast(c.{cited_publn_id} as bigint) as cited_pat_publn_id,
                            cast(sp.publn_date as date) as citation_date,
                            extract(year from cast(sp.publn_date as date)) as citation_year,
                            cast(sp.publn_auth as varchar) as citing_jurisdiction_code,
                            trim(cast(sp.publn_kind as varchar)) as citing_kind_code,
                            coalesce(f.primary_wipo_field, 'UNMAPPED_WIPO_FIELD') as citing_primary_wipo_field
                        from read_parquet('{citation}') c
                        join scoped_pub s
                          on cast(c.{source_publn_id} as bigint) = cast(s.pat_publn_id as bigint)
                        join member_pub_base sp
                          on cast(c.{source_publn_id} as bigint) = cast(sp.pat_publn_id as bigint)
                        left join scoped_pub t
                          on cast(c.{cited_publn_id} as bigint) = cast(t.pat_publn_id as bigint)
                        left join read_parquet('{fields}') f
                          on s.docdb_family_id = f.docdb_family_id
                        where cast(c.{source_publn_id} as bigint) > 0
                          and cast(c.{cited_publn_id} as bigint) > 0
                          and sp.publn_date is not null
                    ),
                    edge_flags as (
                        select
                            e.*,
                            e.source_docdb_family_id = e.cited_docdb_family_id
                                and e.cited_docdb_family_id is not null as is_intra_family_citation,
                            coalesce(src.owner_name_harmonized, '') <> ''
                                and src.owner_name_harmonized = tgt.owner_name_harmonized as is_self_citation,
                            case
                                when e.source_docdb_family_id = e.cited_docdb_family_id and e.cited_docdb_family_id is not null then 0.0
                                when coalesce(src.owner_name_harmonized, '') <> ''
                                 and src.owner_name_harmonized = tgt.owner_name_harmonized then 0.0
                                else 1.0
                            end as clean_edge_weight
                        from raw_edges e
                        left join read_parquet('{owner}') src
                          on e.source_docdb_family_id = src.docdb_family_id
                        left join read_parquet('{owner}') tgt
                          on e.cited_docdb_family_id = tgt.docdb_family_id
                    ),
                    enriched as (
                        select
                            e.source_docdb_family_id,
                            e.cited_docdb_family_id,
                            e.is_out_of_bounds,
                            e.citing_pat_publn_id,
                            e.cited_pat_publn_id,
                            e.citation_date,
                            cast(e.citation_year as bigint) as citation_year,
                            e.citing_jurisdiction_code,
                            e.citing_kind_code,
                            e.citing_primary_wipo_field,
                            coalesce(src.owner_name_harmonized, 'UNKNOWN_OWNER') as citing_assignee_name,
                            e.is_intra_family_citation,
                            e.is_self_citation,
                            cast(e.clean_edge_weight as double) as clean_edge_weight,
                            coalesce(k.stage_multiplier, 0.0) as citing_stage_multiplier,
                            coalesce(m.final_market_multiplier, 1.0) as citing_market_multiplier,
                            coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0) as raw_trend_coefficient,
                            least(3.0, greatest(0.5, coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0))) as clipped_trend_coefficient,
                            case
                                when l.local_trend_coefficient is not null then 'localized'
                                when g.global_trend_coefficient is not null then 'global_fallback'
                                else 'unity_fallback'
                            end as trend_source,
                            cast(e.clean_edge_weight as double)
                                * coalesce(k.stage_multiplier, 0.0)
                                * coalesce(m.final_market_multiplier, 1.0)
                                * least(3.0, greatest(0.5, coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)))
                                as citation_lethality_score
                        from edge_flags e
                        left join read_parquet('{owner}') src
                          on e.source_docdb_family_id = src.docdb_family_id
                        left join read_parquet('{kind_norm}') k
                          on e.citing_jurisdiction_code = k.jurisdiction_code
                         and e.citing_kind_code = k.kind_code
                        left join read_parquet('{market_weight}') m
                          on e.citing_jurisdiction_code = m.jurisdiction_code
                         and e.citation_year = m.snapshot_year
                        left join read_parquet('{out_local_trend}') l
                          on e.citation_year = l.snapshot_year
                         and e.citing_jurisdiction_code = l.jurisdiction_code
                         and e.citing_primary_wipo_field = l.wipo_industry_code
                        left join read_parquet('{out_global_trend}') g
                          on e.citation_year = g.snapshot_year
                         and e.citing_primary_wipo_field = g.wipo_industry_code
                    )
                    select distinct * from enriched
                ) to '{out_citation_network}' (format parquet, compression zstd)
                """
            )

            con.execute(
                f"""
                copy (
                    with family_pub_anchor as (
                        select
                            m.docdb_family_id,
                            min(m.publn_date) filter (where m.publn_date is not null) as family_earliest_publication_date
                        from read_parquet('{member_pub}') m
                        group by m.docdb_family_id
                    ),
                    family_base as (
                        select
                            c.docdb_family_id,
                            c.family_priority_year,
                            coalesce(f.primary_wipo_field, 'UNMAPPED_WIPO_FIELD') as primary_wipo_field,
                            coalesce(a.family_earliest_publication_date, c.family_earliest_priority_date) as family_citation_anchor_date
                        from read_parquet('{family_core}') c
                        left join family_pub_anchor a using (docdb_family_id)
                        left join read_parquet('{fields}') f using (docdb_family_id)
                    ),
                    backward_patent as (
                        select
                            s.docdb_family_id,
                            count(*) as family_backward_patent_citation_count,
                            sum(case when t.docdb_family_id is null then 1 else 0 end) as out_of_bounds_citation_count
                        from read_parquet('{citation}') c
                        join (
                            select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                        ) s on cast(c.{source_publn_id} as bigint) = cast(s.pat_publn_id as bigint)
                        left join (
                            select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                        ) t on cast(c.{cited_publn_id} as bigint) = cast(t.pat_publn_id as bigint)
                        where cast(c.{source_publn_id} as bigint) > 0
                          and cast(c.{cited_publn_id} as bigint) > 0
                        group by s.docdb_family_id
                    ),
                    backward_clean as (
                        select
                            source_docdb_family_id as docdb_family_id,
                            count(distinct cited_docdb_family_id) as family_backward_citations_clean
                        from read_parquet('{out_citation_network}')
                        where cited_docdb_family_id is not null
                          and not is_out_of_bounds
                          and not is_intra_family_citation
                          and not is_self_citation
                        group by source_docdb_family_id
                    ),
                    backward_npl as (
                        select
                            docdb_family_id,
                            count(distinct npl_publn_id) as family_backward_npl_citation_count
                        from ({npl_backlinks_sql})
                        group by docdb_family_id
                    ),
                    raw_family_events as (
                        select
                            cited_docdb_family_id as docdb_family_id,
                            source_docdb_family_id,
                            min(citation_date) as first_citation_date
                        from read_parquet('{out_citation_network}')
                        where cited_docdb_family_id is not null
                          and not is_out_of_bounds
                        group by cited_docdb_family_id, source_docdb_family_id
                    ),
                    clean_family_events as (
                        select
                            cited_docdb_family_id as docdb_family_id,
                            source_docdb_family_id,
                            min(citation_date) as first_citation_date,
                            max(citation_lethality_score) as max_citation_lethality_score
                        from read_parquet('{out_citation_network}')
                        where cited_docdb_family_id is not null
                          and not is_out_of_bounds
                          and not is_intra_family_citation
                          and not is_self_citation
                        group by cited_docdb_family_id, source_docdb_family_id
                    ),
                    forward_raw as (
                        select
                            docdb_family_id,
                            count(*) as family_forward_citations_raw
                        from raw_family_events
                        group by docdb_family_id
                    ),
                    forward_clean as (
                        select
                            docdb_family_id,
                            count(*) as family_forward_citations_clean
                        from clean_family_events
                        group by docdb_family_id
                    ),
                    forward_windowed as (
                        select
                            b.docdb_family_id,
                            count(*) filter (
                                where e.first_citation_date <= b.family_citation_anchor_date + interval '5 years'
                            ) as family_fwd_cits5,
                            count(*) filter (
                                where e.first_citation_date <= b.family_citation_anchor_date + interval '7 years'
                            ) as family_fwd_cits7,
                            sum(e.max_citation_lethality_score) filter (
                                where e.first_citation_date <= b.family_citation_anchor_date + interval '7 years'
                            ) as family_forward_citations_weighted
                        from family_base b
                        left join clean_family_events e
                          on b.docdb_family_id = e.docdb_family_id
                        group by b.docdb_family_id, b.family_citation_anchor_date
                    ),
                    scoring_base as (
                        select
                            b.docdb_family_id,
                            b.family_priority_year,
                            b.primary_wipo_field,
                            coalesce(bp.family_backward_patent_citation_count, 0) as family_backward_patent_citation_count,
                            coalesce(bc.family_backward_citations_clean, 0) as family_backward_citations_clean,
                            coalesce(bp.out_of_bounds_citation_count, 0) as out_of_bounds_citation_count,
                            coalesce(fr.family_forward_citations_raw, 0) as family_forward_citations_raw,
                            coalesce(fc.family_forward_citations_clean, 0) as family_forward_citations_clean,
                            coalesce(fw.family_fwd_cits5, 0) as family_fwd_cits5,
                            coalesce(fw.family_fwd_cits7, 0) as family_fwd_cits7,
                            coalesce(fw.family_forward_citations_weighted, 0.0) as family_forward_citations_weighted,
                            coalesce(bn.family_backward_npl_citation_count, 0) as family_backward_npl_citation_count
                        from family_base b
                        left join backward_patent bp using (docdb_family_id)
                        left join backward_clean bc using (docdb_family_id)
                        left join backward_npl bn using (docdb_family_id)
                        left join forward_raw fr using (docdb_family_id)
                        left join forward_clean fc using (docdb_family_id)
                        left join forward_windowed fw using (docdb_family_id)
                    ),
                    cohort_avg as (
                        select
                            family_priority_year,
                            primary_wipo_field,
                            avg(family_forward_citations_weighted) as cohort_avg_forward_citations_weighted
                        from scoring_base
                        group by family_priority_year, primary_wipo_field
                    )
                    select
                        c.docdb_family_id,
                        coalesce(s.family_backward_patent_citation_count, 0) as raw_family_citation_count,
                        coalesce(s.family_backward_patent_citation_count, 0) as family_backward_patent_citation_count,
                        coalesce(s.family_backward_citations_clean, 0) as family_backward_citations_clean,
                        coalesce(s.out_of_bounds_citation_count, 0) as out_of_bounds_citation_count,
                        case
                            when coalesce(s.family_backward_patent_citation_count, 0) = 0 then 0.0
                            else cast(s.out_of_bounds_citation_count as double) / cast(s.family_backward_patent_citation_count as double)
                        end as out_of_bounds_citation_share,
                        coalesce(s.family_forward_citations_raw, 0) as family_forward_citations_raw,
                        coalesce(s.family_forward_citations_clean, 0) as family_forward_citations_clean,
                        coalesce(s.family_forward_citations_weighted, 0.0) as family_forward_citations_weighted,
                        coalesce(s.family_fwd_cits5, 0) as family_fwd_cits5,
                        coalesce(s.family_fwd_cits7, 0) as family_fwd_cits7,
                        coalesce(s.family_backward_npl_citation_count, 0) as family_backward_npl_citation_count,
                        ln(1.0 + coalesce(s.family_backward_npl_citation_count, 0)) as family_science_grounding_score,
                        case
                            when coalesce(a.cohort_avg_forward_citations_weighted, 0.0) = 0.0 then coalesce(s.family_forward_citations_weighted, 0.0)
                            else coalesce(s.family_forward_citations_weighted, 0.0) / a.cohort_avg_forward_citations_weighted
                        end as family_rcf_score,
                        case
                            when coalesce(a.cohort_avg_forward_citations_weighted, 0.0) = 0.0 then coalesce(s.family_forward_citations_weighted, 0.0)
                            else coalesce(s.family_forward_citations_weighted, 0.0) / a.cohort_avg_forward_citations_weighted
                        end as family_adjusted_citation_score_raw
                    from read_parquet('{family_core}') c
                    left join scoring_base s using (docdb_family_id)
                    left join cohort_avg a
                      on s.family_priority_year = a.family_priority_year
                     and s.primary_wipo_field = a.primary_wipo_field
                ) to '{out_citation}' (format parquet, compression zstd)
                """
            )
        else:
            result.warnings.append("Citation table lacks `cited_pat_publn_id`; enriched citation network and citation metrics were skipped.")
    else:
        result.warnings.append("Citation metrics were skipped because Bronze citation/publication tables were unavailable.")

    if not out_citation_network.exists():
        con.execute(
            f"""
            copy (
                select
                    null::bigint as source_docdb_family_id,
                    null::bigint as cited_docdb_family_id,
                    false as is_out_of_bounds,
                    null::bigint as citing_pat_publn_id,
                    null::bigint as cited_pat_publn_id,
                    null::date as citation_date,
                    null::bigint as citation_year,
                    null::varchar as citing_jurisdiction_code,
                    null::varchar as citing_kind_code,
                    null::varchar as citing_primary_wipo_field,
                    null::varchar as citing_assignee_name,
                    false as is_intra_family_citation,
                    false as is_self_citation,
                    0.0::double as clean_edge_weight,
                    0.0::double as citing_stage_multiplier,
                    0.0::double as citing_market_multiplier,
                    1.0::double as raw_trend_coefficient,
                    1.0::double as clipped_trend_coefficient,
                    null::varchar as trend_source,
                    0.0::double as citation_lethality_score
                where false
            ) to '{out_citation_network}' (format parquet, compression zstd)
            """
        )

    if not out_citation.exists():
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    0::bigint as raw_family_citation_count,
                    0::bigint as family_backward_patent_citation_count,
                    0::bigint as family_backward_citations_clean,
                    0::bigint as out_of_bounds_citation_count,
                    0.0::double as out_of_bounds_citation_share,
                    0::bigint as family_forward_citations_raw,
                    0::bigint as family_forward_citations_clean,
                    0.0::double as family_forward_citations_weighted,
                    0::bigint as family_fwd_cits5,
                    0::bigint as family_fwd_cits7,
                    0::bigint as family_backward_npl_citation_count,
                    0.0::double as family_science_grounding_score,
                    0.0::double as family_rcf_score,
                    0.0::double as family_adjusted_citation_score_raw
                from read_parquet('{family_core}')
            ) to '{out_citation}' (format parquet, compression zstd)
            """
        )

    if not include_legal_outputs:
        return

    con.execute(
        f"""
        copy (
            with branch_fields as (
                select
                    j.docdb_family_id,
                    j.jurisdiction_code,
                    j.source_auth,
                    j.is_up_unrolled,
                    j.is_classic_validation,
                    j.is_global_member,
                    f.primary_wipo_field,
                    f.family_field_fraction,
                    u.wipo_industry_code
                from read_parquet('{family_jur}') j
                join read_parquet('{fields}') f using (docdb_family_id),
                     unnest(f.covered_wipo_fields) as u(wipo_industry_code)
            ),
            branch_latest as (
                select
                    j.docdb_family_id,
                    j.jurisdiction_code,
                    max(case when l.is_grant_event then 1 else 0 end) as has_grant_event,
                    max(case when l.is_lapse_event then 1 else 0 end) as has_lapse_event,
                    max(case when l.is_expiry_event then 1 else 0 end) as has_expiry_event,
                    max(case when l.is_opposition_event then 1 else 0 end) as has_opposition_event,
                    max(case when upper(coalesce(l.event_type, '')) like '%PENDING%' then 1 else 0 end) as has_pending_event
                from read_parquet('{family_jur}') j
                left join read_parquet('{legal_ledger}') l
                  on j.docdb_family_id = l.docdb_family_id
                 and j.jurisdiction_code = l.jurisdiction_code
                 and l.event_date <= date '{settings.snapshot_date}'
                group by j.docdb_family_id, j.jurisdiction_code
            ),
            branch_stage as (
                select
                    m.docdb_family_id,
                    m.publn_auth as jurisdiction_code,
                    max(case when k.is_enforceable then 1 else 0 end) as has_enforceable_publication,
                    max(case when k.is_application_stage then 1 else 0 end) as has_application_publication,
                    max(case when k.universal_stage = 'POST_GRANT_MODIFIER' then 1 else 0 end) as has_modifier_publication,
                    max(case when k.universal_stage in ('OTHER', 'NON_ENFORCEABLE_PUBLICATION') then 1 else 0 end) as has_other_publication,
                    max(case when k.is_enforceable then coalesce(k.stage_multiplier, 1.0) end) as enforceable_stage_multiplier,
                    max(case when k.is_application_stage then coalesce(k.stage_multiplier, 0.2) end) as pending_stage_multiplier,
                    max(coalesce(k.stage_multiplier, 0.0)) as strongest_stage_multiplier,
                    max_by(k.universal_stage, coalesce(k.stage_multiplier, 0.0)) as representative_branch_stage
                from read_parquet('{member_pub}') m
                join read_parquet('{kind_norm}') k
                  on m.publn_auth = k.jurisdiction_code
                 and m.publn_kind = k.kind_code
                group by m.docdb_family_id, m.publn_auth
            ),
            global_latest as (
                select
                    wipo_industry_code,
                    global_family_filings,
                    global_trend_coefficient
                from (
                    select
                        *,
                        row_number() over (partition by wipo_industry_code order by snapshot_year desc) as rn
                    from read_parquet('{out_global_trend}')
                )
                where rn = 1
            ),
            local_latest as (
                select
                    jurisdiction_code,
                    wipo_industry_code,
                    local_family_filings,
                    local_trend_coefficient
                from (
                    select
                        *,
                        row_number() over (
                            partition by jurisdiction_code, wipo_industry_code
                            order by snapshot_year desc
                        ) as rn
                    from read_parquet('{out_local_trend}')
                )
                where rn = 1
            )
            select
                b.docdb_family_id,
                date '{settings.snapshot_date}' as snapshot_date,
                b.jurisdiction_code,
                b.wipo_industry_code,
                b.source_auth,
                b.is_up_unrolled,
                b.is_classic_validation,
                b.is_global_member,
                coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                coalesce(v.active_jurisdiction_count, 0) as active_jurisdiction_count,
                coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                coalesce(b.family_field_fraction, 1.0) as family_field_fraction,
                coalesce(m.final_market_multiplier, 0.2) as final_market_multiplier,
                coalesce(g.global_family_filings, 0) as global_family_filings,
                coalesce(g.global_trend_coefficient, 1.0) as global_field_trend_coefficient,
                coalesce(l.local_family_filings, 0) as local_family_filings,
                case
                    when coalesce(l.local_family_filings, 0) >= 25 then coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                    when coalesce(l.local_family_filings, 0) between 5 and 24 then (coalesce(l.local_trend_coefficient, 1.0) + coalesce(g.global_trend_coefficient, 1.0)) / 2.0
                    else coalesce(g.global_trend_coefficient, 1.0)
                end as local_field_trend_coefficient,
                case
                    when coalesce(l.local_family_filings, 0) >= 25 then 'localized'
                    when coalesce(l.local_family_filings, 0) between 5 and 24 then 'mixed'
                    else 'global_fallback'
                end as branch_coefficient_mode,
                (
                    coalesce(bl.has_grant_event, 0) = 1
                    and coalesce(bl.has_lapse_event, 0) = 0
                    and coalesce(bl.has_expiry_event, 0) = 0
                )
                or (
                    b.is_up_unrolled
                    and coalesce(u.has_up_registration, false)
                    and coalesce(s.family_composite_status, '') = 'fully_active'
                ) as active_branch_flag,
                coalesce(bl.has_opposition_event, 0) = 1 as is_opposed_branch,
                coalesce(
                    bs.representative_branch_stage,
                    case
                        when b.is_up_unrolled and coalesce(u.has_up_registration, false) then 'UNITARY_GRANT'
                        when coalesce(bl.has_pending_event, 0) = 1
                          or coalesce(bs.has_application_publication, 0) = 1 then 'PENDING_APPLICATION'
                        when coalesce(bs.has_modifier_publication, 0) = 1 then 'POST_GRANT_MODIFIER'
                        else 'OTHER'
                    end
                ) as representative_branch_stage,
                case
                    when b.is_up_unrolled
                     and coalesce(u.has_up_registration, false)
                     and coalesce(s.family_composite_status, '') = 'fully_active' then 'ACTIVE_GRANT'
                    when b.is_up_unrolled
                     and coalesce(u.has_up_registration, false)
                     and coalesce(s.family_composite_status, '') in ('dead', 'partially_lapsed') then 'LAPSED_OR_EXPIRED'
                    when coalesce(bl.has_grant_event, 0) = 1
                     and coalesce(bl.has_lapse_event, 0) = 0
                     and coalesce(bl.has_expiry_event, 0) = 0
                     and coalesce(bl.has_opposition_event, 0) = 1 then 'ACTIVE_OPPOSED_GRANT'
                    when coalesce(bl.has_grant_event, 0) = 1
                     and coalesce(bl.has_lapse_event, 0) = 0
                     and coalesce(bl.has_expiry_event, 0) = 0 then 'ACTIVE_GRANT'
                    when coalesce(bl.has_grant_event, 0) = 1
                     and (coalesce(bl.has_lapse_event, 0) = 1 or coalesce(bl.has_expiry_event, 0) = 1) then 'LAPSED_OR_EXPIRED'
                    when b.is_global_member or b.jurisdiction_code = 'WO' then 'GLOBAL_PLACEHOLDER'
                    when coalesce(bl.has_pending_event, 0) = 1
                      or (
                          coalesce(bs.has_application_publication, 0) = 1
                          and coalesce(bs.has_enforceable_publication, 0) = 0
                          and coalesce(bl.has_grant_event, 0) = 0
                      ) then 'PENDING_ONLY'
                    when coalesce(bs.has_modifier_publication, 0) = 1
                      or coalesce(bs.representative_branch_stage, '') = 'POST_GRANT_MODIFIER' then 'POST_GRANT_INACTIVE'
                    when (
                          coalesce(bl.has_lapse_event, 0) = 1
                          or coalesce(bl.has_expiry_event, 0) = 1
                          or (
                              coalesce(s.family_composite_status, '') = 'dead'
                              and coalesce(bs.has_enforceable_publication, 0) = 1
                          )
                      ) then 'LAPSED_OR_EXPIRED'
                    when coalesce(bs.has_other_publication, 0) = 1
                      and coalesce(bs.has_enforceable_publication, 0) = 0
                      and coalesce(bs.has_application_publication, 0) = 0
                      and coalesce(bs.has_modifier_publication, 0) = 0 then 'NON_ENFORCEABLE_PUBLICATION'
                    when bs.representative_branch_stage is not null then 'NON_ENFORCEABLE_PUBLICATION'
                    else 'UNCLASSIFIED_KIND'
                end as branch_state_label,
                case
                    when b.is_up_unrolled
                     and coalesce(u.has_up_registration, false)
                     and coalesce(s.family_composite_status, '') = 'fully_active' then 1.0
                    when coalesce(bl.has_grant_event, 0) = 1
                     and coalesce(bl.has_lapse_event, 0) = 0
                     and coalesce(bl.has_expiry_event, 0) = 0 then coalesce(bs.enforceable_stage_multiplier, bs.strongest_stage_multiplier, 1.0)
                    when coalesce(bl.has_pending_event, 0) = 1
                      or coalesce(bs.has_application_publication, 0) = 1 then greatest(coalesce(bs.pending_stage_multiplier, 0.2), 0.2)
                    else 0.0
                end as branch_stage_multiplier,
                (
                    case
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') = 'fully_active' then 1.0
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0 then coalesce(bs.enforceable_stage_multiplier, bs.strongest_stage_multiplier, 1.0)
                        when coalesce(bl.has_pending_event, 0) = 1 then greatest(coalesce(bs.pending_stage_multiplier, 0.2), 0.2)
                        else 0.0
                    end
                    * coalesce(m.final_market_multiplier, 0.2)
                    * coalesce(b.family_field_fraction, 1.0)
                    * case
                        when coalesce(l.local_family_filings, 0) >= 25 then coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                        when coalesce(l.local_family_filings, 0) between 5 and 24 then (coalesce(l.local_trend_coefficient, 1.0) + coalesce(g.global_trend_coefficient, 1.0)) / 2.0
                        else coalesce(g.global_trend_coefficient, 1.0)
                    end
                    * case
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0 then 1.0
                        else 0.0
                    end
                ) as branch_enforceability_contribution_raw
            from branch_fields b
            left join branch_latest bl
              on b.docdb_family_id = bl.docdb_family_id
             and b.jurisdiction_code = bl.jurisdiction_code
            left join branch_stage bs
              on b.docdb_family_id = bs.docdb_family_id
             and b.jurisdiction_code = bs.jurisdiction_code
            left join read_parquet('{out_coverage}') v
              on b.docdb_family_id = v.docdb_family_id
            left join read_parquet('{family_status}') s
              on b.docdb_family_id = s.docdb_family_id
            left join read_parquet('{up_status}') u
              on b.docdb_family_id = u.docdb_family_id
            left join read_parquet('{market_weight}') m
              on b.jurisdiction_code = m.jurisdiction_code
             and m.snapshot_year = {settings.snapshot_date[:4]}
            left join (
                select
                    wipo_industry_code,
                    global_family_filings,
                    global_trend_coefficient
                from (
                    select *, row_number() over (partition by wipo_industry_code order by snapshot_year desc) as rn
                    from read_parquet('{out_global_trend}')
                ) where rn = 1
            ) g
              on b.wipo_industry_code = g.wipo_industry_code
            left join (
                select
                    jurisdiction_code,
                    wipo_industry_code,
                    local_family_filings,
                    local_trend_coefficient
                from (
                    select *, row_number() over (partition by jurisdiction_code, wipo_industry_code order by snapshot_year desc) as rn
                    from read_parquet('{out_local_trend}')
                ) where rn = 1
            ) l
              on b.jurisdiction_code = l.jurisdiction_code
             and b.wipo_industry_code = l.wipo_industry_code
        ) to '{out_enforce}' (format parquet, compression zstd)
        """
    )

    enforce_rollup_sql = f"""
        select
            docdb_family_id,
            sum(branch_enforceability_contribution_raw) as branch_enforceability_contribution_raw
        from read_parquet('{out_enforce}')
        group by docdb_family_id
    """
    con.execute(
        f"""
        copy (
            with field_base as (
                select
                    docdb_family_id,
                    u.wipo_industry_code,
                    family_field_fraction
                from read_parquet('{fields}'),
                     unnest(covered_wipo_fields) as u(wipo_industry_code)
            ),
            enforce_by_field as (
                select
                    docdb_family_id,
                    wipo_industry_code,
                    sum(branch_enforceability_contribution_raw) as family_field_enforceability_contribution_score
                from read_parquet('{out_enforce}')
                group by docdb_family_id, wipo_industry_code
            )
            select
                f.docdb_family_id,
                date '{settings.snapshot_date}' as snapshot_date,
                f.wipo_industry_code,
                f.family_field_fraction as base_fraction,
                coalesce(e.family_field_enforceability_contribution_score, 0.0) as family_field_enforceability_contribution_score,
                coalesce(f.family_field_fraction, 1.0) * coalesce(c.family_adjusted_citation_score_raw, 0.0) as family_field_heritage_contribution_score,
                '{settings.method_version}' as method_version
            from field_base f
            left join enforce_by_field e
              on f.docdb_family_id = e.docdb_family_id
             and f.wipo_industry_code = e.wipo_industry_code
            left join read_parquet('{out_citation}') c
              on f.docdb_family_id = c.docdb_family_id
        ) to '{out_field_contrib}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            {_oecd_quality_select(settings, family_core=family_core, fields=fields, out_coverage=out_coverage, out_citation=out_citation, enforce_rollup_sql=enforce_rollup_sql)}
        ) to '{out_oecd}' (format parquet, compression zstd)
        """
    )


def build_citation_and_market_layers(settings: BuildSettings) -> StageResult:
    """Build citation, coverage, enforceability, quality, and Market Intelligence Silver tables."""
    family_core = settings.silver_dir / "silver_family_core.parquet"
    appln_seed = settings.silver_dir / "silver_scope_appln_seed.parquet"
    publn_seed = settings.silver_dir / "silver_scope_publn_seed.parquet"
    fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_jur = settings.silver_dir / "silver_family_jurisdiction_unrolled.parquet"
    market_weight = settings.silver_dir / "silver_tiered_market_weighting.parquet"
    citation = settings.bronze_dir / "bronze_patstat_citation.parquet"
    docdb_fam_citn = settings.bronze_dir / "bronze_patstat_docdb_fam_citn.parquet"
    pat_publn = settings.bronze_dir / "bronze_patstat_pat_publn.parquet"
    npl_publn = settings.bronze_dir / "bronze_patstat_npl_publn.parquet"
    owner = settings.silver_dir / "silver_assignee_harmonized.parquet"
    up_status = settings.silver_dir / "silver_up_status.parquet"

    member_pub = settings.silver_dir / "silver_family_member_publications.parquet"
    legal_ledger = settings.silver_dir / "silver_legal_status_event_ledger.parquet"
    kind_norm = settings.silver_dir / "silver_kind_code_normalization.parquet"

    result = StageResult(
        stage="silver-enrichment",
        status="success",
        summary="Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.",
        inputs=[str(path) for path in [family_core, appln_seed, publn_seed, fields, family_status, family_jur, market_weight, up_status, member_pub, legal_ledger, kind_norm, citation, docdb_fam_citn, pat_publn, npl_publn, owner] if path.exists()],
        methods=[
            "Mapped PATSTAT publication and DOCDB family citation sources into bounded family citation edges and cleaned family-level impact inputs.",
            "Materialized a publication-dated enriched citation network with citing-side assignee, stage, market, and trend context.",
            "Derived market-intelligence segment tables from field-year family activity inside the bounded universe.",
            "Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.",
        ],
        calculations=[
            "Family adjusted citation score now uses 7-year clean weighted forward citation influence with a cohort normalization fallback.",
            "Market-state labels use recent family-count momentum by field-year segment.",
        ],
        downstream_impacts=[
            "These Silver enrichment tables feed Gold blocking power, Market Intelligence, attacker summaries, portfolio summaries, and forecast feature generation.",
            "Weak citation coverage or legal weighting here directly distorts compare, portfolio, and family-level UI cards.",
        ],
        doc_refs=[
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
            "docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md",
            "docs/new-feature-ideas/parallel-global-and-local-trend-engines-requirements.md",
        ],
    )

    if not family_core.exists() or not appln_seed.exists() or not fields.exists():
        result.status = "failed"
        result.warnings.append("Silver core, scope seed, and field mappings are required before Silver enrichment.")
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=2")

    out_citation = settings.silver_dir / "silver_family_citation_metrics.parquet"
    out_citation_edges = settings.silver_dir / "silver_family_citation_edges.parquet"
    out_citation_edges_clean = settings.silver_dir / "silver_family_citation_edges_clean.parquet"
    out_citation_network = settings.silver_dir / "silver_enriched_citation_network.parquet"
    out_npl = settings.silver_dir / "silver_family_npl_backlinks.parquet"
    out_trend = settings.silver_dir / "silver_family_trend_tables.parquet"
    out_global_trend = settings.silver_dir / "silver_global_tech_trends_timeseries.parquet"
    out_local_trend = settings.silver_dir / "silver_local_tech_trends_timeseries.parquet"
    out_coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    out_enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    out_field_contrib = settings.silver_dir / "silver_family_field_contributions.parquet"
    out_oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"
    out_market = settings.silver_dir / "silver_market_intelligence_segments.parquet"
    out_market_ts = settings.silver_dir / "silver_market_intelligence_timeseries.parquet"

    if docdb_fam_citn.exists():
        con.execute(
            f"""
            copy (
                select
                    cast(c.docdb_family_id as bigint) as source_docdb_family_id,
                    cast(c.cited_docdb_family_id as bigint) as cited_docdb_family_id,
                    tgt.docdb_family_id is null as is_out_of_bounds,
                    src.family_earliest_priority_date as source_family_earliest_priority_date,
                    src.family_priority_year as source_family_priority_year,
                    f.primary_wipo_field as source_primary_wipo_field
                from read_parquet('{docdb_fam_citn}') c
                join read_parquet('{family_core}') src
                  on cast(c.docdb_family_id as bigint) = src.docdb_family_id
                left join read_parquet('{family_core}') tgt
                  on cast(c.cited_docdb_family_id as bigint) = tgt.docdb_family_id
                left join read_parquet('{fields}') f
                  on src.docdb_family_id = f.docdb_family_id
            ) to '{out_citation_edges}' (format parquet, compression zstd)
            """
        )
        con.execute(
            f"""
            copy (
                select
                    e.source_docdb_family_id,
                    e.cited_docdb_family_id,
                    e.is_out_of_bounds,
                    e.source_family_earliest_priority_date,
                    e.source_family_priority_year,
                    e.source_primary_wipo_field,
                    e.source_docdb_family_id = e.cited_docdb_family_id as is_intra_family_citation,
                    coalesce(src.owner_name_harmonized, '') <> ''
                    and src.owner_name_harmonized = tgt.owner_name_harmonized as is_self_citation,
                    case
                        when e.source_docdb_family_id = e.cited_docdb_family_id then 0.0
                        when coalesce(src.owner_name_harmonized, '') <> ''
                         and src.owner_name_harmonized = tgt.owner_name_harmonized then 0.0
                        else 1.0
                    end as clean_edge_weight
                from read_parquet('{out_citation_edges}') e
                left join read_parquet('{owner}') src
                  on e.source_docdb_family_id = src.docdb_family_id
                left join read_parquet('{owner}') tgt
                  on e.cited_docdb_family_id = tgt.docdb_family_id
            ) to '{out_citation_edges_clean}' (format parquet, compression zstd)
            """
        )
    else:
        result.warnings.append("DOCDB family citation table was unavailable; family citation edge tables were skipped.")

    if citation.exists() and pat_publn.exists() and npl_publn.exists():
        con.execute(
            f"""
            copy (
                with scoped_pub as (
                    select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                )
                select
                    s.docdb_family_id,
                    cast(c.cited_npl_publn_id as varchar) as npl_publn_id,
                    count(*) as npl_reference_count,
                    true as science_linkage_flag
                from read_parquet('{citation}') c
                join scoped_pub s
                  on cast(c.pat_publn_id as bigint) = cast(s.pat_publn_id as bigint)
                join read_parquet('{npl_publn}') n
                  on cast(c.cited_npl_publn_id as varchar) = cast(n.npl_publn_id as varchar)
                where cast(c.cited_npl_publn_id as varchar) is not null
                  and trim(cast(c.cited_npl_publn_id as varchar)) <> ''
                group by s.docdb_family_id, cast(c.cited_npl_publn_id as varchar)
            ) to '{out_npl}' (format parquet, compression zstd)
            """
        )
    else:
        result.warnings.append("NPL backlink registry was skipped because Bronze citation/NPL inputs were unavailable.")

    con.execute(
        f"""
        copy (
            select
                s.docdb_family_id,
                extract(year from s.family_earliest_priority_date) as family_priority_year,
                unnest(f.covered_wipo_fields) as wipo_industry_code
            from read_parquet('{family_core}') s
            join read_parquet('{fields}') f using (docdb_family_id)
        ) to '{out_trend}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            with field_year as (
                select
                    family_priority_year as snapshot_year,
                    wipo_industry_code,
                    count(*) as global_family_filings
                from read_parquet('{out_trend}')
                group by family_priority_year, wipo_industry_code
            ),
            lagged as (
                select
                    *,
                    lag(global_family_filings) over (partition by wipo_industry_code order by snapshot_year) as prior_period_global_family_filings
                from field_year
            )
            select
                snapshot_year,
                wipo_industry_code,
                global_family_filings,
                coalesce(prior_period_global_family_filings, global_family_filings) as prior_period_global_family_filings,
                case
                    when coalesce(prior_period_global_family_filings, 0) = 0 then 0.0
                    else (cast(global_family_filings as double) - cast(prior_period_global_family_filings as double))
                        / cast(prior_period_global_family_filings as double)
                end as global_growth_rate,
                greatest(
                    0.1,
                    1.0 +
                    case
                        when coalesce(prior_period_global_family_filings, 0) = 0 then 0.0
                        else (cast(global_family_filings as double) - cast(prior_period_global_family_filings as double))
                            / cast(prior_period_global_family_filings as double)
                    end
                ) as global_trend_coefficient,
                'family_count' as counting_unit,
                '{settings.scope_type}' as family_model,
                '{settings.method_version}' as method_version
            from lagged
        ) to '{out_global_trend}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            with local_base as (
                select
                    extract(year from c.family_earliest_priority_date) as snapshot_year,
                    j.jurisdiction_code,
                    u.wipo_field as wipo_industry_code,
                    count(distinct c.docdb_family_id) as local_family_filings
                from read_parquet('{family_core}') c
                join read_parquet('{family_jur}') j using (docdb_family_id)
                join read_parquet('{fields}') f using (docdb_family_id),
                     unnest(f.covered_wipo_fields) as u(wipo_field)
                where c.family_earliest_priority_date is not null
                group by 1, 2, 3
            ),
            lagged as (
                select
                    *,
                    lag(local_family_filings) over (
                        partition by jurisdiction_code, wipo_industry_code
                        order by snapshot_year
                    ) as prior_period_local_family_filings
                from local_base
            )
            select
                snapshot_year,
                jurisdiction_code,
                wipo_industry_code,
                local_family_filings,
                coalesce(prior_period_local_family_filings, local_family_filings) as prior_period_local_family_filings,
                case
                    when coalesce(prior_period_local_family_filings, 0) = 0 then 0.0
                    else (cast(local_family_filings as double) - cast(prior_period_local_family_filings as double))
                        / cast(prior_period_local_family_filings as double)
                end as local_growth_rate,
                greatest(
                    0.1,
                    1.0 +
                    case
                        when coalesce(prior_period_local_family_filings, 0) = 0 then 0.0
                        else (cast(local_family_filings as double) - cast(prior_period_local_family_filings as double))
                            / cast(prior_period_local_family_filings as double)
                    end
                ) as local_trend_coefficient,
                'family_count' as counting_unit,
                '{settings.scope_type}' as family_model,
                '{settings.method_version}' as method_version
            from lagged
        ) to '{out_local_trend}' (format parquet, compression zstd)
        """
    )

    if citation.exists() and pat_publn.exists():
        npl_backlinks_sql = (
            f"select * from read_parquet('{out_npl}')"
            if out_npl.exists()
            else "select null::bigint as docdb_family_id, null::varchar as npl_publn_id, 0::bigint as npl_reference_count, false as science_linkage_flag where false"
        )
        pub_cols = parquet_columns(pat_publn)
        citation_cols = parquet_columns(citation)
        publn_id = next(col for col in pub_cols if col.lower() == "pat_publn_id")
        cited_publn_id = next((col for col in citation_cols if col.lower() == "cited_pat_publn_id"), None)
        source_publn_id = next(col for col in citation_cols if col.lower() == "pat_publn_id")
        if cited_publn_id is not None:
            con.execute(
                f"""
                copy (
                    with scoped_pub as (
                        select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                    ),
                    member_pub_base as (
                        select distinct
                            pat_publn_id,
                            docdb_family_id,
                            publn_auth,
                            trim(publn_kind) as publn_kind,
                            publn_date
                        from read_parquet('{member_pub}')
                    ),
                    raw_edges as (
                        select
                            s.docdb_family_id as source_docdb_family_id,
                            t.docdb_family_id as cited_docdb_family_id,
                            t.docdb_family_id is null as is_out_of_bounds,
                            cast(sp.pat_publn_id as bigint) as citing_pat_publn_id,
                            cast(c.{cited_publn_id} as bigint) as cited_pat_publn_id,
                            cast(sp.publn_date as date) as citation_date,
                            extract(year from cast(sp.publn_date as date)) as citation_year,
                            cast(sp.publn_auth as varchar) as citing_jurisdiction_code,
                            trim(cast(sp.publn_kind as varchar)) as citing_kind_code,
                            coalesce(f.primary_wipo_field, 'UNMAPPED_WIPO_FIELD') as citing_primary_wipo_field
                        from read_parquet('{citation}') c
                        join scoped_pub s
                          on cast(c.{source_publn_id} as bigint) = cast(s.pat_publn_id as bigint)
                        join member_pub_base sp
                          on cast(c.{source_publn_id} as bigint) = cast(sp.pat_publn_id as bigint)
                        left join scoped_pub t
                          on cast(c.{cited_publn_id} as bigint) = cast(t.pat_publn_id as bigint)
                        left join read_parquet('{fields}') f
                          on s.docdb_family_id = f.docdb_family_id
                        where cast(c.{source_publn_id} as bigint) > 0
                          and cast(c.{cited_publn_id} as bigint) > 0
                          and sp.publn_date is not null
                    ),
                    edge_flags as (
                        select
                            e.*,
                            e.source_docdb_family_id = e.cited_docdb_family_id
                                and e.cited_docdb_family_id is not null as is_intra_family_citation,
                            coalesce(src.owner_name_harmonized, '') <> ''
                                and src.owner_name_harmonized = tgt.owner_name_harmonized as is_self_citation,
                            case
                                when e.source_docdb_family_id = e.cited_docdb_family_id and e.cited_docdb_family_id is not null then 0.0
                                when coalesce(src.owner_name_harmonized, '') <> ''
                                 and src.owner_name_harmonized = tgt.owner_name_harmonized then 0.0
                                else 1.0
                            end as clean_edge_weight
                        from raw_edges e
                        left join read_parquet('{owner}') src
                          on e.source_docdb_family_id = src.docdb_family_id
                        left join read_parquet('{owner}') tgt
                          on e.cited_docdb_family_id = tgt.docdb_family_id
                    ),
                    enriched as (
                        select
                            e.source_docdb_family_id,
                            e.cited_docdb_family_id,
                            e.is_out_of_bounds,
                            e.citing_pat_publn_id,
                            e.cited_pat_publn_id,
                            e.citation_date,
                            cast(e.citation_year as bigint) as citation_year,
                            e.citing_jurisdiction_code,
                            e.citing_kind_code,
                            e.citing_primary_wipo_field,
                            coalesce(src.owner_name_harmonized, 'UNKNOWN_OWNER') as citing_assignee_name,
                            e.is_intra_family_citation,
                            e.is_self_citation,
                            cast(e.clean_edge_weight as double) as clean_edge_weight,
                            coalesce(k.stage_multiplier, 0.0) as citing_stage_multiplier,
                            coalesce(m.final_market_multiplier, 1.0) as citing_market_multiplier,
                            coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0) as raw_trend_coefficient,
                            least(3.0, greatest(0.5, coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0))) as clipped_trend_coefficient,
                            case
                                when l.local_trend_coefficient is not null then 'localized'
                                when g.global_trend_coefficient is not null then 'global_fallback'
                                else 'unity_fallback'
                            end as trend_source,
                            cast(e.clean_edge_weight as double)
                                * coalesce(k.stage_multiplier, 0.0)
                                * coalesce(m.final_market_multiplier, 1.0)
                                * least(3.0, greatest(0.5, coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)))
                                as citation_lethality_score
                        from edge_flags e
                        left join read_parquet('{owner}') src
                          on e.source_docdb_family_id = src.docdb_family_id
                        left join read_parquet('{kind_norm}') k
                          on e.citing_jurisdiction_code = k.jurisdiction_code
                         and e.citing_kind_code = k.kind_code
                        left join read_parquet('{market_weight}') m
                          on e.citing_jurisdiction_code = m.jurisdiction_code
                         and e.citation_year = m.snapshot_year
                        left join read_parquet('{out_local_trend}') l
                          on e.citation_year = l.snapshot_year
                         and e.citing_jurisdiction_code = l.jurisdiction_code
                         and e.citing_primary_wipo_field = l.wipo_industry_code
                        left join read_parquet('{out_global_trend}') g
                          on e.citation_year = g.snapshot_year
                         and e.citing_primary_wipo_field = g.wipo_industry_code
                    )
                    select distinct * from enriched
                ) to '{out_citation_network}' (format parquet, compression zstd)
                """
            )

            con.execute(
                f"""
                copy (
                    with family_pub_anchor as (
                        select
                            m.docdb_family_id,
                            min(m.publn_date) filter (where m.publn_date is not null) as family_earliest_publication_date
                        from read_parquet('{member_pub}') m
                        group by m.docdb_family_id
                    ),
                    family_base as (
                        select
                            c.docdb_family_id,
                            c.family_priority_year,
                            coalesce(f.primary_wipo_field, 'UNMAPPED_WIPO_FIELD') as primary_wipo_field,
                            coalesce(a.family_earliest_publication_date, c.family_earliest_priority_date) as family_citation_anchor_date
                        from read_parquet('{family_core}') c
                        left join family_pub_anchor a using (docdb_family_id)
                        left join read_parquet('{fields}') f using (docdb_family_id)
                    ),
                    backward_patent as (
                        select
                            s.docdb_family_id,
                            count(*) as family_backward_patent_citation_count,
                            sum(case when t.docdb_family_id is null then 1 else 0 end) as out_of_bounds_citation_count
                        from read_parquet('{citation}') c
                        join (
                            select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                        ) s on cast(c.{source_publn_id} as bigint) = cast(s.pat_publn_id as bigint)
                        left join (
                            select distinct pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                        ) t on cast(c.{cited_publn_id} as bigint) = cast(t.pat_publn_id as bigint)
                        where cast(c.{source_publn_id} as bigint) > 0
                          and cast(c.{cited_publn_id} as bigint) > 0
                        group by s.docdb_family_id
                    ),
                    backward_clean as (
                        select
                            source_docdb_family_id as docdb_family_id,
                            count(distinct cited_docdb_family_id) as family_backward_citations_clean
                        from read_parquet('{out_citation_network}')
                        where cited_docdb_family_id is not null
                          and not is_out_of_bounds
                          and not is_intra_family_citation
                          and not is_self_citation
                        group by source_docdb_family_id
                    ),
                    backward_npl as (
                        select
                            docdb_family_id,
                            count(distinct npl_publn_id) as family_backward_npl_citation_count
                        from ({npl_backlinks_sql})
                        group by docdb_family_id
                    ),
                    raw_family_events as (
                        select
                            cited_docdb_family_id as docdb_family_id,
                            source_docdb_family_id,
                            min(citation_date) as first_citation_date
                        from read_parquet('{out_citation_network}')
                        where cited_docdb_family_id is not null
                          and not is_out_of_bounds
                        group by cited_docdb_family_id, source_docdb_family_id
                    ),
                    clean_family_events as (
                        select
                            cited_docdb_family_id as docdb_family_id,
                            source_docdb_family_id,
                            min(citation_date) as first_citation_date,
                            max(citation_lethality_score) as max_citation_lethality_score
                        from read_parquet('{out_citation_network}')
                        where cited_docdb_family_id is not null
                          and not is_out_of_bounds
                          and not is_intra_family_citation
                          and not is_self_citation
                        group by cited_docdb_family_id, source_docdb_family_id
                    ),
                    forward_raw as (
                        select
                            docdb_family_id,
                            count(*) as family_forward_citations_raw
                        from raw_family_events
                        group by docdb_family_id
                    ),
                    forward_clean as (
                        select
                            docdb_family_id,
                            count(*) as family_forward_citations_clean
                        from clean_family_events
                        group by docdb_family_id
                    ),
                    forward_windowed as (
                        select
                            b.docdb_family_id,
                            count(*) filter (
                                where e.first_citation_date <= b.family_citation_anchor_date + interval '5 years'
                            ) as family_fwd_cits5,
                            count(*) filter (
                                where e.first_citation_date <= b.family_citation_anchor_date + interval '7 years'
                            ) as family_fwd_cits7,
                            sum(e.max_citation_lethality_score) filter (
                                where e.first_citation_date <= b.family_citation_anchor_date + interval '7 years'
                            ) as family_forward_citations_weighted
                        from family_base b
                        left join clean_family_events e
                          on b.docdb_family_id = e.docdb_family_id
                        group by b.docdb_family_id, b.family_citation_anchor_date
                    ),
                    scoring_base as (
                        select
                            b.docdb_family_id,
                            b.family_priority_year,
                            b.primary_wipo_field,
                            coalesce(bp.family_backward_patent_citation_count, 0) as family_backward_patent_citation_count,
                            coalesce(bc.family_backward_citations_clean, 0) as family_backward_citations_clean,
                            coalesce(bp.out_of_bounds_citation_count, 0) as out_of_bounds_citation_count,
                            coalesce(fr.family_forward_citations_raw, 0) as family_forward_citations_raw,
                            coalesce(fc.family_forward_citations_clean, 0) as family_forward_citations_clean,
                            coalesce(fw.family_fwd_cits5, 0) as family_fwd_cits5,
                            coalesce(fw.family_fwd_cits7, 0) as family_fwd_cits7,
                            coalesce(fw.family_forward_citations_weighted, 0.0) as family_forward_citations_weighted,
                            coalesce(bn.family_backward_npl_citation_count, 0) as family_backward_npl_citation_count
                        from family_base b
                        left join backward_patent bp using (docdb_family_id)
                        left join backward_clean bc using (docdb_family_id)
                        left join backward_npl bn using (docdb_family_id)
                        left join forward_raw fr using (docdb_family_id)
                        left join forward_clean fc using (docdb_family_id)
                        left join forward_windowed fw using (docdb_family_id)
                    ),
                    cohort_avg as (
                        select
                            family_priority_year,
                            primary_wipo_field,
                            avg(family_forward_citations_weighted) as cohort_avg_forward_citations_weighted
                        from scoring_base
                        group by family_priority_year, primary_wipo_field
                    )
                    select
                        c.docdb_family_id,
                        coalesce(s.family_backward_patent_citation_count, 0) as raw_family_citation_count,
                        coalesce(s.family_backward_patent_citation_count, 0) as family_backward_patent_citation_count,
                        coalesce(s.family_backward_citations_clean, 0) as family_backward_citations_clean,
                        coalesce(s.out_of_bounds_citation_count, 0) as out_of_bounds_citation_count,
                        case
                            when coalesce(s.family_backward_patent_citation_count, 0) = 0 then 0.0
                            else cast(s.out_of_bounds_citation_count as double) / cast(s.family_backward_patent_citation_count as double)
                        end as out_of_bounds_citation_share,
                        coalesce(s.family_forward_citations_raw, 0) as family_forward_citations_raw,
                        coalesce(s.family_forward_citations_clean, 0) as family_forward_citations_clean,
                        coalesce(s.family_forward_citations_weighted, 0.0) as family_forward_citations_weighted,
                        coalesce(s.family_fwd_cits5, 0) as family_fwd_cits5,
                        coalesce(s.family_fwd_cits7, 0) as family_fwd_cits7,
                        coalesce(s.family_backward_npl_citation_count, 0) as family_backward_npl_citation_count,
                        ln(1.0 + coalesce(s.family_backward_npl_citation_count, 0)) as family_science_grounding_score,
                        case
                            when coalesce(a.cohort_avg_forward_citations_weighted, 0.0) = 0.0 then coalesce(s.family_forward_citations_weighted, 0.0)
                            else coalesce(s.family_forward_citations_weighted, 0.0) / a.cohort_avg_forward_citations_weighted
                        end as family_rcf_score,
                        case
                            when coalesce(a.cohort_avg_forward_citations_weighted, 0.0) = 0.0 then coalesce(s.family_forward_citations_weighted, 0.0)
                            else coalesce(s.family_forward_citations_weighted, 0.0) / a.cohort_avg_forward_citations_weighted
                        end as family_adjusted_citation_score_raw
                    from read_parquet('{family_core}') c
                    left join scoring_base s using (docdb_family_id)
                    left join cohort_avg a
                      on s.family_priority_year = a.family_priority_year
                     and s.primary_wipo_field = a.primary_wipo_field
                ) to '{out_citation}' (format parquet, compression zstd)
                """
            )
        else:
            result.warnings.append("Citation table lacks `cited_pat_publn_id`; enriched citation network and citation metrics were skipped.")
    else:
        result.warnings.append("Citation metrics were skipped because Bronze citation/publication tables were unavailable.")

    if not out_citation_network.exists():
        con.execute(
            f"""
            copy (
                select
                    null::bigint as source_docdb_family_id,
                    null::bigint as cited_docdb_family_id,
                    false as is_out_of_bounds,
                    null::bigint as citing_pat_publn_id,
                    null::bigint as cited_pat_publn_id,
                    null::date as citation_date,
                    null::bigint as citation_year,
                    null::varchar as citing_jurisdiction_code,
                    null::varchar as citing_kind_code,
                    null::varchar as citing_primary_wipo_field,
                    null::varchar as citing_assignee_name,
                    false as is_intra_family_citation,
                    false as is_self_citation,
                    0.0::double as clean_edge_weight,
                    0.0::double as citing_stage_multiplier,
                    0.0::double as citing_market_multiplier,
                    1.0::double as raw_trend_coefficient,
                    1.0::double as clipped_trend_coefficient,
                    null::varchar as trend_source,
                    0.0::double as citation_lethality_score
                where false
            ) to '{out_citation_network}' (format parquet, compression zstd)
            """
        )

    if not out_citation.exists():
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    0::bigint as raw_family_citation_count,
                    0::bigint as family_backward_patent_citation_count,
                    0::bigint as family_backward_citations_clean,
                    0::bigint as out_of_bounds_citation_count,
                    0.0::double as out_of_bounds_citation_share,
                    0::bigint as family_forward_citations_raw,
                    0::bigint as family_forward_citations_clean,
                    0.0::double as family_forward_citations_weighted,
                    0::bigint as family_fwd_cits5,
                    0::bigint as family_fwd_cits7,
                    0::bigint as family_backward_npl_citation_count,
                    0.0::double as family_science_grounding_score,
                    0.0::double as family_rcf_score,
                    0.0::double as family_adjusted_citation_score_raw
                from read_parquet('{family_core}')
            ) to '{out_citation}' (format parquet, compression zstd)
            """
        )

    citation_edges_sql = (
        f"select * from read_parquet('{out_citation_edges}')"
        if out_citation_edges.exists()
        else "select null::bigint as source_docdb_family_id, null::bigint as cited_docdb_family_id, false as is_out_of_bounds, null::date as source_family_earliest_priority_date, null::bigint as source_family_priority_year, null::varchar as source_primary_wipo_field where false"
    )
    if citation.exists() and pat_publn.exists():
        citation_stats = con.execute(
            f"""
            select
                count(*) as citation_edge_count,
                count(distinct source_docdb_family_id) as citation_unique_source_family_count,
                count(distinct cited_docdb_family_id) filter (where cited_docdb_family_id is not null and not is_out_of_bounds) as citation_unique_cited_family_count,
                count(*) filter (where is_out_of_bounds) as citation_out_of_bounds_edge_count
            from ({citation_edges_sql})
            """
        ).fetchone()
        result.metrics["citation_edge_count"] = int(citation_stats[0])
        result.metrics["citation_unique_source_family_count"] = int(citation_stats[1])
        result.metrics["citation_unique_cited_family_count"] = int(citation_stats[2])
        result.metrics["citation_out_of_bounds_edge_count"] = int(citation_stats[3])
    con.execute(
        f"""
        copy (
            with jur_weight as (
                select
                    j.docdb_family_id,
                    count(distinct j.jurisdiction_code) as family_jurisdiction_count,
                    sum(coalesce(m.final_market_multiplier, 0.2)) as family_market_coverage_weight_raw
                from read_parquet('{family_jur}') j
                left join read_parquet('{market_weight}') m
                  on j.jurisdiction_code = m.jurisdiction_code
                 and m.snapshot_year = {settings.snapshot_date[:4]}
                group by j.docdb_family_id
            ),
            pub_counts as (
                select
                    docdb_family_id,
                    sum(case when is_grant_stage then 1 else 0 end) as family_grant_publication_count,
                    sum(case when is_application_stage then 1 else 0 end) as family_application_publication_count
                from read_parquet('{settings.silver_dir / "silver_family_member_publications.parquet"}')
                group by docdb_family_id
            )
            select
                c.docdb_family_id,
                coalesce(j.family_jurisdiction_count, 0) as family_jurisdiction_count,
                coalesce(s.active_jurisdiction_count, 0) as active_jurisdiction_count,
                coalesce(s.active_grant_branch_count, 0) as active_grant_branch_count,
                coalesce(s.lapsed_jurisdiction_count, 0) as lapsed_jurisdiction_count,
                coalesce(p.family_grant_publication_count, 0) as family_grant_publication_count,
                coalesce(p.family_application_publication_count, 0) as family_application_publication_count,
                coalesce(j.family_market_coverage_weight_raw, 0.0) as family_market_coverage_weight_raw,
                case
                    when coalesce(j.family_jurisdiction_count, 0) = 0 then 0.0
                    else cast(coalesce(s.active_jurisdiction_count, 0) as double) / cast(j.family_jurisdiction_count as double)
                end as family_coverage_stability_score
            from read_parquet('{family_core}') c
            left join jur_weight j using (docdb_family_id)
            left join pub_counts p using (docdb_family_id)
            left join read_parquet('{family_status}') s using (docdb_family_id)
        ) to '{out_coverage}' (format parquet, compression zstd)
        """
    )
    if family_status.exists() and family_jur.exists() and market_weight.exists() and legal_ledger.exists() and kind_norm.exists() and member_pub.exists():
        con.execute(
            f"""
            copy (
                with branch_fields as (
                    select
                        j.docdb_family_id,
                        j.jurisdiction_code,
                        j.source_auth,
                        j.is_up_unrolled,
                        j.is_classic_validation,
                        j.is_global_member,
                        f.primary_wipo_field,
                        f.family_field_fraction,
                        u.wipo_industry_code
                    from read_parquet('{family_jur}') j
                    join read_parquet('{fields}') f using (docdb_family_id),
                         unnest(f.covered_wipo_fields) as u(wipo_industry_code)
                ),
                branch_latest as (
                    select
                        j.docdb_family_id,
                        j.jurisdiction_code,
                        max(case when l.is_grant_event then 1 else 0 end) as has_grant_event,
                        max(case when l.is_lapse_event then 1 else 0 end) as has_lapse_event,
                        max(case when l.is_expiry_event then 1 else 0 end) as has_expiry_event,
                        max(case when l.is_opposition_event then 1 else 0 end) as has_opposition_event,
                        max(case when upper(coalesce(l.event_type, '')) like '%PENDING%' then 1 else 0 end) as has_pending_event
                    from read_parquet('{family_jur}') j
                    left join read_parquet('{legal_ledger}') l
                      on j.docdb_family_id = l.docdb_family_id
                     and j.jurisdiction_code = l.jurisdiction_code
                     and l.event_date <= date '{settings.snapshot_date}'
                    group by j.docdb_family_id, j.jurisdiction_code
                ),
                branch_stage as (
                    select
                        m.docdb_family_id,
                        m.publn_auth as jurisdiction_code,
                        max(case when k.is_enforceable then 1 else 0 end) as has_enforceable_publication,
                        max(case when k.is_application_stage then 1 else 0 end) as has_application_publication,
                        max(case when k.universal_stage = 'POST_GRANT_MODIFIER' then 1 else 0 end) as has_modifier_publication,
                        max(case when k.universal_stage in ('OTHER', 'NON_ENFORCEABLE_PUBLICATION') then 1 else 0 end) as has_other_publication,
                        max(case when k.is_enforceable then coalesce(k.stage_multiplier, 1.0) end) as enforceable_stage_multiplier,
                        max(case when k.is_application_stage then coalesce(k.stage_multiplier, 0.2) end) as pending_stage_multiplier,
                        max(coalesce(k.stage_multiplier, 0.0)) as strongest_stage_multiplier,
                        max_by(k.universal_stage, coalesce(k.stage_multiplier, 0.0)) as representative_branch_stage
                    from read_parquet('{member_pub}') m
                    join read_parquet('{kind_norm}') k
                      on m.publn_auth = k.jurisdiction_code
                     and m.publn_kind = k.kind_code
                    group by m.docdb_family_id, m.publn_auth
                ),
                global_latest as (
                    select
                        wipo_industry_code,
                        global_family_filings,
                        global_trend_coefficient
                    from (
                        select
                            *,
                            row_number() over (partition by wipo_industry_code order by snapshot_year desc) as rn
                        from read_parquet('{out_global_trend}')
                    )
                    where rn = 1
                ),
                local_latest as (
                    select
                        jurisdiction_code,
                        wipo_industry_code,
                        local_family_filings,
                        local_trend_coefficient
                    from (
                        select
                            *,
                            row_number() over (
                                partition by jurisdiction_code, wipo_industry_code
                                order by snapshot_year desc
                            ) as rn
                        from read_parquet('{out_local_trend}')
                    )
                    where rn = 1
                )
                select
                    b.docdb_family_id,
                    date '{settings.snapshot_date}' as snapshot_date,
                    b.jurisdiction_code,
                    b.wipo_industry_code,
                    b.source_auth,
                    b.is_up_unrolled,
                    b.is_classic_validation,
                    b.is_global_member,
                    coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                    coalesce(v.active_jurisdiction_count, 0) as active_jurisdiction_count,
                    coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                    coalesce(b.family_field_fraction, 1.0) as family_field_fraction,
                    coalesce(m.final_market_multiplier, 0.2) as final_market_multiplier,
                    coalesce(g.global_family_filings, 0) as global_family_filings,
                    coalesce(g.global_trend_coefficient, 1.0) as global_field_trend_coefficient,
                    coalesce(l.local_family_filings, 0) as local_family_filings,
                    case
                        when coalesce(l.local_family_filings, 0) >= 25 then coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                        when coalesce(l.local_family_filings, 0) between 5 and 24 then (coalesce(l.local_trend_coefficient, 1.0) + coalesce(g.global_trend_coefficient, 1.0)) / 2.0
                        else coalesce(g.global_trend_coefficient, 1.0)
                    end as local_field_trend_coefficient,
                    case
                        when coalesce(l.local_family_filings, 0) >= 25 then 'localized'
                        when coalesce(l.local_family_filings, 0) between 5 and 24 then 'mixed'
                        else 'global_fallback'
                    end as branch_coefficient_mode,
                    (
                        coalesce(bl.has_grant_event, 0) = 1
                        and coalesce(bl.has_lapse_event, 0) = 0
                        and coalesce(bl.has_expiry_event, 0) = 0
                    )
                    or (
                        b.is_up_unrolled
                        and coalesce(u.has_up_registration, false)
                        and coalesce(s.family_composite_status, '') = 'fully_active'
                    ) as active_branch_flag,
                    coalesce(bl.has_opposition_event, 0) = 1 as is_opposed_branch,
                    coalesce(
                        bs.representative_branch_stage,
                        case
                            when b.is_up_unrolled and coalesce(u.has_up_registration, false) then 'UNITARY_GRANT'
                            when coalesce(bl.has_pending_event, 0) = 1
                              or coalesce(bs.has_application_publication, 0) = 1 then 'PENDING_APPLICATION'
                            when coalesce(bs.has_modifier_publication, 0) = 1 then 'POST_GRANT_MODIFIER'
                            else 'OTHER'
                        end
                    ) as representative_branch_stage,
                    case
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') = 'fully_active' then 'ACTIVE_GRANT'
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') in ('dead', 'partially_lapsed') then 'LAPSED_OR_EXPIRED'
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0
                         and coalesce(bl.has_opposition_event, 0) = 1 then 'ACTIVE_OPPOSED_GRANT'
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0 then 'ACTIVE_GRANT'
                        when coalesce(bl.has_grant_event, 0) = 1
                         and (coalesce(bl.has_lapse_event, 0) = 1 or coalesce(bl.has_expiry_event, 0) = 1) then 'LAPSED_OR_EXPIRED'
                        when b.is_global_member or b.jurisdiction_code = 'WO' then 'GLOBAL_PLACEHOLDER'
                        when coalesce(bl.has_pending_event, 0) = 1
                          or (
                              coalesce(bs.has_application_publication, 0) = 1
                              and coalesce(bs.has_enforceable_publication, 0) = 0
                              and coalesce(bl.has_grant_event, 0) = 0
                          ) then 'PENDING_ONLY'
                        when coalesce(bs.has_modifier_publication, 0) = 1
                          or coalesce(bs.representative_branch_stage, '') = 'POST_GRANT_MODIFIER' then 'POST_GRANT_INACTIVE'
                        when (
                              coalesce(bl.has_lapse_event, 0) = 1
                              or coalesce(bl.has_expiry_event, 0) = 1
                              or (
                                  coalesce(s.family_composite_status, '') = 'dead'
                                  and coalesce(bs.has_enforceable_publication, 0) = 1
                              )
                          ) then 'LAPSED_OR_EXPIRED'
                        when coalesce(bs.has_other_publication, 0) = 1
                          and coalesce(bs.has_enforceable_publication, 0) = 0
                          and coalesce(bs.has_application_publication, 0) = 0
                          and coalesce(bs.has_modifier_publication, 0) = 0 then 'NON_ENFORCEABLE_PUBLICATION'
                        when bs.representative_branch_stage is not null then 'NON_ENFORCEABLE_PUBLICATION'
                        else 'UNCLASSIFIED_KIND'
                    end as branch_state_label,
                    case
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') = 'fully_active' then 1.0
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0 then coalesce(bs.enforceable_stage_multiplier, bs.strongest_stage_multiplier, 1.0)
                        when coalesce(bl.has_pending_event, 0) = 1
                          or coalesce(bs.has_application_publication, 0) = 1 then greatest(coalesce(bs.pending_stage_multiplier, 0.2), 0.2)
                        else 0.0
                    end as branch_stage_multiplier,
                    (
                        case
                            when b.is_up_unrolled
                             and coalesce(u.has_up_registration, false)
                             and coalesce(s.family_composite_status, '') = 'fully_active' then 1.0
                            when coalesce(bl.has_grant_event, 0) = 1
                             and coalesce(bl.has_lapse_event, 0) = 0
                             and coalesce(bl.has_expiry_event, 0) = 0 then coalesce(bs.enforceable_stage_multiplier, bs.strongest_stage_multiplier, 1.0)
                            when coalesce(bl.has_pending_event, 0) = 1 then greatest(coalesce(bs.pending_stage_multiplier, 0.2), 0.2)
                            else 0.0
                        end
                        * coalesce(m.final_market_multiplier, 0.2)
                        * coalesce(b.family_field_fraction, 1.0)
                        * case
                            when coalesce(l.local_family_filings, 0) >= 25 then coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                            when coalesce(l.local_family_filings, 0) between 5 and 24 then (coalesce(l.local_trend_coefficient, 1.0) + coalesce(g.global_trend_coefficient, 1.0)) / 2.0
                            else coalesce(g.global_trend_coefficient, 1.0)
                        end
                        * case
                            when coalesce(bl.has_grant_event, 0) = 1
                             and coalesce(bl.has_lapse_event, 0) = 0
                             and coalesce(bl.has_expiry_event, 0) = 0 then 1.0
                            else 0.0
                        end
                    ) as branch_enforceability_contribution_raw
                from branch_fields b
                left join branch_latest bl
                  on b.docdb_family_id = bl.docdb_family_id
                 and b.jurisdiction_code = bl.jurisdiction_code
                left join branch_stage bs
                  on b.docdb_family_id = bs.docdb_family_id
                 and b.jurisdiction_code = bs.jurisdiction_code
                left join read_parquet('{out_coverage}') v
                  on b.docdb_family_id = v.docdb_family_id
                left join read_parquet('{family_status}') s
                  on b.docdb_family_id = s.docdb_family_id
                left join read_parquet('{up_status}') u
                  on b.docdb_family_id = u.docdb_family_id
                left join read_parquet('{market_weight}') m
                  on b.jurisdiction_code = m.jurisdiction_code
                 and m.snapshot_year = {settings.snapshot_date[:4]}
                left join global_latest g
                  on b.wipo_industry_code = g.wipo_industry_code
                left join local_latest l
                  on b.jurisdiction_code = l.jurisdiction_code
                 and b.wipo_industry_code = l.wipo_industry_code
            ) to '{out_enforce}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                with branch_fields as (
                    select
                        j.docdb_family_id,
                        j.jurisdiction_code,
                        j.source_auth,
                        j.is_up_unrolled,
                        j.is_classic_validation,
                        j.is_global_member,
                        f.primary_wipo_field,
                        f.family_field_fraction,
                        u.wipo_industry_code
                    from read_parquet('{family_jur}') j
                    join read_parquet('{fields}') f using (docdb_family_id),
                         unnest(f.covered_wipo_fields) as u(wipo_industry_code)
                )
                select
                    b.docdb_family_id,
                    date '{settings.snapshot_date}' as snapshot_date,
                    b.jurisdiction_code,
                    b.wipo_industry_code,
                    b.source_auth,
                    b.is_up_unrolled,
                    b.is_classic_validation,
                    b.is_global_member,
                    coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                    coalesce(v.active_jurisdiction_count, 0) as active_jurisdiction_count,
                    coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                    coalesce(b.family_field_fraction, 1.0) as family_field_fraction,
                    0.2 as final_market_multiplier,
                    0::bigint as global_family_filings,
                    1.0 as global_field_trend_coefficient,
                    0::bigint as local_family_filings,
                    1.0 as local_field_trend_coefficient,
                    'global_fallback' as branch_coefficient_mode,
                    coalesce(s.has_any_active_grant, false) as active_branch_flag,
                    false as is_opposed_branch,
                    case
                        when coalesce(s.has_any_active_grant, false) then 'STANDARD_GRANT'
                        when coalesce(s.family_composite_status, '') = 'pending_emerging' then 'PENDING_APPLICATION'
                        else 'OTHER'
                    end as representative_branch_stage,
                    case
                        when coalesce(s.has_any_active_grant, false) then 'ACTIVE_GRANT'
                        when coalesce(s.family_composite_status, '') = 'pending_emerging' then 'PENDING_ONLY'
                        when coalesce(s.family_composite_status, '') in ('partially_lapsed', 'dead') then 'LAPSED_OR_EXPIRED'
                        else 'UNCLASSIFIED_KIND'
                    end as branch_state_label,
                    case
                        when coalesce(s.has_any_active_grant, false) then 1.0
                        when coalesce(s.family_composite_status, '') = 'pending_emerging' then 0.2
                        else 0.0
                    end as branch_stage_multiplier,
                    (
                        case
                            when coalesce(s.has_any_active_grant, false) then 1.0
                            else 0.0
                        end
                        * 0.2
                        * coalesce(b.family_field_fraction, 1.0)
                    ) as branch_enforceability_contribution_raw
                from branch_fields b
                left join read_parquet('{out_coverage}') v
                  on b.docdb_family_id = v.docdb_family_id
                left join read_parquet('{family_status}') s
                  on b.docdb_family_id = s.docdb_family_id
            ) to '{out_enforce}' (format parquet, compression zstd)
            """
        )
        result.warnings.append("Enforceability remained on the fallback branch proxy because localized legal and trend inputs were unavailable.")
    enforce_rollup_sql = f"""
        select
            docdb_family_id,
            sum(branch_enforceability_contribution_raw) as branch_enforceability_contribution_raw
        from read_parquet('{out_enforce}')
        group by docdb_family_id
    """
    con.execute(
        f"""
        copy (
            with field_base as (
                select
                    docdb_family_id,
                    u.wipo_industry_code,
                    family_field_fraction
                from read_parquet('{fields}'),
                     unnest(covered_wipo_fields) as u(wipo_industry_code)
            ),
            enforce_by_field as (
                select
                    docdb_family_id,
                    wipo_industry_code,
                    sum(branch_enforceability_contribution_raw) as family_field_enforceability_contribution_score
                from read_parquet('{out_enforce}')
                group by docdb_family_id, wipo_industry_code
            )
            select
                f.docdb_family_id,
                date '{settings.snapshot_date}' as snapshot_date,
                f.wipo_industry_code,
                f.family_field_fraction as base_fraction,
                coalesce(e.family_field_enforceability_contribution_score, 0.0) as family_field_enforceability_contribution_score,
                coalesce(f.family_field_fraction, 1.0) * coalesce(c.family_adjusted_citation_score_raw, 0.0) as family_field_heritage_contribution_score,
                '{settings.method_version}' as method_version
            from field_base f
            left join enforce_by_field e
              on f.docdb_family_id = e.docdb_family_id
             and f.wipo_industry_code = e.wipo_industry_code
            left join read_parquet('{out_citation}') c
              on f.docdb_family_id = c.docdb_family_id
        ) to '{out_field_contrib}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            {_oecd_quality_select(settings, family_core=family_core, fields=fields, out_coverage=out_coverage, out_citation=out_citation, enforce_rollup_sql=enforce_rollup_sql)}
        ) to '{out_oecd}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            with field_year as (
                select
                    family_priority_year,
                    wipo_industry_code,
                    count(*) as family_count
                from read_parquet('{out_trend}')
                group by family_priority_year, wipo_industry_code
            ),
            lagged as (
                select
                    *,
                    lag(family_count) over (partition by wipo_industry_code order by family_priority_year) as prior_family_count
                from field_year
            ),
            year_safety as (
                select
                    *,
                    cast(
                        make_date(family_priority_year, 12, 31) + interval '18 months' > date '{settings.snapshot_date}'
                        as boolean
                    ) as is_recent_priority_year_incomplete,
                    max(
                        case
                            when make_date(family_priority_year, 12, 31) + interval '18 months' <= date '{settings.snapshot_date}'
                                then family_priority_year
                            else null
                        end
                    ) over (partition by wipo_industry_code) as latest_comparable_year
                from lagged
            )
            select
                family_priority_year,
                wipo_industry_code,
                family_count,
                coalesce(prior_family_count, family_count) as prior_family_count,
                case
                    when family_count > coalesce(prior_family_count, family_count) then 'rising'
                    when family_count < coalesce(prior_family_count, family_count) then 'cooling'
                    else 'stable'
                end as market_state,
                is_recent_priority_year_incomplete,
                cast(not is_recent_priority_year_incomplete as boolean) as market_state_ui_safe,
                latest_comparable_year,
                date '{settings.snapshot_date}' as snapshot_date
            from year_safety
        ) to '{out_market_ts}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            with timeseries as (
                select *
                from read_parquet('{out_market_ts}')
            ),
            latest_safe as (
                select
                    wipo_industry_code,
                    max(family_priority_year) as latest_comparable_year
                from timeseries
                where coalesce(market_state_ui_safe, false)
                group by wipo_industry_code
            ),
            segment_rollup as (
                select
                    wipo_industry_code as segment_id,
                    wipo_industry_code,
                    sum(family_count) as total_family_count,
                    max(family_priority_year) as latest_year,
                    cast(max_by(cast(is_recent_priority_year_incomplete as integer), family_priority_year) as boolean) as latest_year_incomplete,
                    max(snapshot_date) as snapshot_date
                from timeseries
                group by wipo_industry_code
            )
            select
                sr.segment_id,
                sr.wipo_industry_code,
                safe.market_state as market_state,
                sr.total_family_count,
                sr.latest_year,
                ls.latest_comparable_year,
                sr.latest_year_incomplete,
                sr.snapshot_date
            from segment_rollup sr
            left join latest_safe ls
              on sr.wipo_industry_code = ls.wipo_industry_code
            left join timeseries safe
              on ls.wipo_industry_code = safe.wipo_industry_code
             and ls.latest_comparable_year = safe.family_priority_year
        ) to '{out_market}' (format parquet, compression zstd)
        """
    )

    for output in [
        out_citation_edges,
        out_citation_edges_clean,
        out_citation_network,
        out_npl,
        out_citation,
        out_trend,
        out_global_trend,
        out_local_trend,
        out_coverage,
        out_enforce,
        out_field_contrib,
        out_oecd,
        out_market,
        out_market_ts,
    ]:
        if output.exists():
            result.outputs.append(str(output))
            result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    return result


def build_kindcode_refresh_layers(settings: BuildSettings) -> StageResult:
    """Rebuild only Silver outputs whose values depend on kind-code normalization."""
    family_core = settings.silver_dir / "silver_family_core.parquet"
    publn_seed = settings.silver_dir / "silver_scope_publn_seed.parquet"
    fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_jur = settings.silver_dir / "silver_family_jurisdiction_unrolled.parquet"
    market_weight = settings.silver_dir / "silver_tiered_market_weighting.parquet"
    citation = settings.bronze_dir / "bronze_patstat_citation.parquet"
    pat_publn = settings.bronze_dir / "bronze_patstat_pat_publn.parquet"
    npl_publn = settings.bronze_dir / "bronze_patstat_npl_publn.parquet"
    owner = settings.silver_dir / "silver_assignee_harmonized.parquet"
    up_status = settings.silver_dir / "silver_up_status.parquet"
    member_pub = settings.silver_dir / "silver_family_member_publications.parquet"
    legal_ledger = settings.silver_dir / "silver_legal_status_event_ledger.parquet"
    kind_norm = settings.silver_dir / "silver_kind_code_normalization.parquet"

    out_citation_edges = settings.silver_dir / "silver_family_citation_edges.parquet"
    out_npl = settings.silver_dir / "silver_family_npl_backlinks.parquet"
    out_trend = settings.silver_dir / "silver_family_trend_tables.parquet"
    out_global_trend = settings.silver_dir / "silver_global_tech_trends_timeseries.parquet"
    out_local_trend = settings.silver_dir / "silver_local_tech_trends_timeseries.parquet"
    out_coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    out_citation = settings.silver_dir / "silver_family_citation_metrics.parquet"
    out_citation_network = settings.silver_dir / "silver_enriched_citation_network.parquet"
    out_enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    out_field_contrib = settings.silver_dir / "silver_family_field_contributions.parquet"
    out_oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"

    result = StageResult(
        stage="silver-enrichment-kind-refresh",
        status="success",
        summary="Rebuilt the refreshed kind-code-dependent citation weighting layer; legal-weighted marts should then be refreshed through the incremental legal refresh stage.",
        inputs=[
            str(path)
            for path in [
                family_core,
                publn_seed,
                fields,
                family_status,
                family_jur,
                market_weight,
                citation,
                pat_publn,
                npl_publn,
                owner,
                up_status,
                member_pub,
                legal_ledger,
                kind_norm,
                out_citation_edges,
                out_npl,
                out_trend,
                out_global_trend,
                out_local_trend,
                out_coverage,
            ]
            if path.exists()
        ],
        methods=[
            "Reused stable citation-edge, NPL, trend, and coverage support outputs from the latest Silver enrichment run.",
            "Recomputed only the kind-code-dependent citation weighting layer and left legal-weighted marts to the dedicated incremental legal refresh stage.",
        ],
        calculations=[
            "Citing-stage multipliers in the enriched citation network are refreshed from the current Silver kind-code normalization table.",
            "Use the follow-on silver-kind-legal-refresh stage to merge refreshed branch, field-contribution, and OECD rows for the affected families.",
        ],
        downstream_impacts=[
            "This refresh path is intended for iterative kind-code curation where the stable support outputs have not changed.",
            "Use the full silver-enrichment stage if citation edges, trend tables, or coverage support outputs are absent or stale for other reasons.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
        ],
    )

    required_inputs = [
        family_core,
        publn_seed,
        fields,
        family_status,
        family_jur,
        market_weight,
        member_pub,
        legal_ledger,
        kind_norm,
        out_citation_edges,
        out_global_trend,
        out_local_trend,
        out_coverage,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(
            "Kind-code refresh requires an existing full silver-enrichment support layer first. Missing: " + ", ".join(missing)
        )
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=2")

    _build_kindcode_dependent_outputs(
        con,
        settings,
        result,
        family_core=family_core,
        publn_seed=publn_seed,
        fields=fields,
        family_status=family_status,
        family_jur=family_jur,
        market_weight=market_weight,
        citation=citation,
        pat_publn=pat_publn,
        npl_publn=npl_publn,
        owner=owner,
        up_status=up_status,
        member_pub=member_pub,
        legal_ledger=legal_ledger,
        kind_norm=kind_norm,
        out_citation_edges=out_citation_edges,
        out_npl=out_npl,
        out_trend=out_trend,
        out_global_trend=out_global_trend,
        out_local_trend=out_local_trend,
        out_coverage=out_coverage,
        out_citation=out_citation,
        out_citation_network=out_citation_network,
        out_enforce=out_enforce,
        out_field_contrib=out_field_contrib,
        out_oecd=out_oecd,
        include_legal_outputs=False,
    )

    for output in [out_citation_network, out_citation]:
        if output.exists():
            result.outputs.append(str(output))
            result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    return result


def _build_incremental_legal_outputs(
    settings: BuildSettings,
    *,
    stage_name: str,
    summary: str,
    methods: list[str],
    calculations: list[str],
    doc_refs: list[str],
    affected_family_sql: str | None,
    affected_family_metric_name: str,
    refresh_coverage: bool,
    temp_prefix: str,
) -> StageResult:
    """Rebuild legal-weighted Silver marts, optionally merging only an affected family slice."""
    family_core = settings.silver_dir / "silver_family_core.parquet"
    fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_jur = settings.silver_dir / "silver_family_jurisdiction_unrolled.parquet"
    market_weight = settings.silver_dir / "silver_tiered_market_weighting.parquet"
    up_status = settings.silver_dir / "silver_up_status.parquet"
    member_pub = settings.silver_dir / "silver_family_member_publications.parquet"
    legal_ledger = settings.silver_dir / "silver_legal_status_event_ledger.parquet"
    kind_norm = settings.silver_dir / "silver_kind_code_normalization.parquet"

    out_global_trend = settings.silver_dir / "silver_global_tech_trends_timeseries.parquet"
    out_local_trend = settings.silver_dir / "silver_local_tech_trends_timeseries.parquet"
    out_coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    out_citation = settings.silver_dir / "silver_family_citation_metrics.parquet"
    out_enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    out_field_contrib = settings.silver_dir / "silver_family_field_contributions.parquet"
    out_oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"

    result = StageResult(
        stage=stage_name,
        status="success",
        summary=summary,
        inputs=[
            str(path)
            for path in [
                family_core,
                fields,
                family_status,
                family_jur,
                market_weight,
                up_status,
                member_pub,
                legal_ledger,
                kind_norm,
                out_global_trend,
                out_local_trend,
                out_citation,
            ]
            if path.exists()
        ],
        methods=methods,
        calculations=calculations,
        doc_refs=doc_refs,
    )

    required_inputs = [
        family_core,
        fields,
        family_status,
        family_jur,
        market_weight,
        up_status,
        member_pub,
        legal_ledger,
        kind_norm,
        out_global_trend,
        out_local_trend,
        out_citation,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(
            "Kind-code legal refresh requires existing citation/trend support outputs first. Missing: " + ", ".join(missing)
        )
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=2")

    snapshot_year = settings.snapshot_date[:4]

    def _write_coverage(target: Path) -> None:
        con.execute(
            f"""
            copy (
                with jur_weight as (
                    select
                        j.docdb_family_id,
                        count(distinct j.jurisdiction_code) as family_jurisdiction_count,
                        sum(coalesce(m.final_market_multiplier, 0.2)) as family_market_coverage_weight_raw
                    from read_parquet('{family_jur}') j
                    left join read_parquet('{market_weight}') m
                      on j.jurisdiction_code = m.jurisdiction_code
                     and m.snapshot_year = {snapshot_year}
                    group by j.docdb_family_id
                ),
                pub_counts as (
                    select
                        docdb_family_id,
                        sum(case when is_grant_stage then 1 else 0 end) as family_grant_publication_count,
                        sum(case when is_application_stage then 1 else 0 end) as family_application_publication_count
                    from read_parquet('{member_pub}')
                    group by docdb_family_id
                )
                select
                    c.docdb_family_id,
                    coalesce(j.family_jurisdiction_count, 0) as family_jurisdiction_count,
                    coalesce(s.active_jurisdiction_count, 0) as active_jurisdiction_count,
                    coalesce(s.active_grant_branch_count, 0) as active_grant_branch_count,
                    coalesce(s.lapsed_jurisdiction_count, 0) as lapsed_jurisdiction_count,
                    coalesce(p.family_grant_publication_count, 0) as family_grant_publication_count,
                    coalesce(p.family_application_publication_count, 0) as family_application_publication_count,
                    coalesce(j.family_market_coverage_weight_raw, 0.0) as family_market_coverage_weight_raw,
                    case
                        when coalesce(j.family_jurisdiction_count, 0) = 0 then 0.0
                        else cast(coalesce(s.active_jurisdiction_count, 0) as double) / cast(j.family_jurisdiction_count as double)
                    end as family_coverage_stability_score
                from read_parquet('{family_core}') c
                left join jur_weight j using (docdb_family_id)
                left join pub_counts p using (docdb_family_id)
                left join read_parquet('{family_status}') s using (docdb_family_id)
            ) to '{target}' (format parquet, compression zstd)
            """
        )

    def _write_legal_outputs(
        enforce_target: Path,
        field_target: Path,
        oecd_target: Path,
        *,
        affected_path: Path | None = None,
    ) -> None:
        branch_filter_fields = ""
        branch_filter_latest = ""
        branch_filter_stage = ""
        field_filter = ""
        oecd_filter = ""
        oecd_indicator_filter = ""
        if affected_path is not None:
            branch_filter_fields = f"join read_parquet('{affected_path}') a on j.docdb_family_id = a.docdb_family_id"
            branch_filter_latest = f"join read_parquet('{affected_path}') a on j.docdb_family_id = a.docdb_family_id"
            branch_filter_stage = f"join read_parquet('{affected_path}') a on m.docdb_family_id = a.docdb_family_id"
            field_filter = f"join read_parquet('{affected_path}') a on f.docdb_family_id = a.docdb_family_id"
            oecd_filter = f"join read_parquet('{affected_path}') a on c.docdb_family_id = a.docdb_family_id"
            oecd_indicator_filter = f"join read_parquet('{affected_path}') a on l.docdb_family_id = a.docdb_family_id"

        con.execute(
            f"""
            copy (
                with branch_fields as (
                    select
                        j.docdb_family_id,
                        j.jurisdiction_code,
                        j.source_auth,
                        j.is_up_unrolled,
                        j.is_classic_validation,
                        j.is_global_member,
                        f.primary_wipo_field,
                        f.family_field_fraction,
                        u.wipo_industry_code
                    from read_parquet('{family_jur}') j
                    {branch_filter_fields}
                    join read_parquet('{fields}') f
                      on j.docdb_family_id = f.docdb_family_id,
                         unnest(f.covered_wipo_fields) as u(wipo_industry_code)
                ),
                legal_flags as (
                    select
                        docdb_family_id,
                        jurisdiction_code,
                        max(case when is_grant_event then 1 else 0 end) as has_grant_event,
                        max(case when is_lapse_event then 1 else 0 end) as has_lapse_event,
                        max(case when is_expiry_event then 1 else 0 end) as has_expiry_event,
                        max(case when is_opposition_event then 1 else 0 end) as has_opposition_event,
                        max(case when upper(coalesce(event_type, '')) like '%PENDING%' then 1 else 0 end) as has_pending_event
                    from read_parquet('{legal_ledger}')
                    where event_date <= date '{settings.snapshot_date}'
                    group by docdb_family_id, jurisdiction_code
                ),
                branch_latest as (
                    select
                        j.docdb_family_id,
                        j.jurisdiction_code,
                        coalesce(l.has_grant_event, 0) as has_grant_event,
                        coalesce(l.has_lapse_event, 0) as has_lapse_event,
                        coalesce(l.has_expiry_event, 0) as has_expiry_event,
                        coalesce(l.has_opposition_event, 0) as has_opposition_event,
                        coalesce(l.has_pending_event, 0) as has_pending_event
                    from read_parquet('{family_jur}') j
                    {branch_filter_latest}
                    left join legal_flags l
                      on j.docdb_family_id = l.docdb_family_id
                     and j.jurisdiction_code = l.jurisdiction_code
                ),
                branch_stage as (
                    select
                        m.docdb_family_id,
                        m.publn_auth as jurisdiction_code,
                        max(case when k.is_enforceable then 1 else 0 end) as has_enforceable_publication,
                        max(case when k.is_application_stage then 1 else 0 end) as has_application_publication,
                        max(case when k.universal_stage = 'POST_GRANT_MODIFIER' then 1 else 0 end) as has_modifier_publication,
                        max(case when k.universal_stage in ('OTHER', 'NON_ENFORCEABLE_PUBLICATION') then 1 else 0 end) as has_other_publication,
                        max(case when k.is_enforceable then coalesce(k.stage_multiplier, 1.0) end) as enforceable_stage_multiplier,
                        max(case when k.is_application_stage then coalesce(k.stage_multiplier, 0.2) end) as pending_stage_multiplier,
                        max(coalesce(k.stage_multiplier, 0.0)) as strongest_stage_multiplier,
                        max_by(k.universal_stage, coalesce(k.stage_multiplier, 0.0)) as representative_branch_stage
                    from read_parquet('{member_pub}') m
                    {branch_filter_stage}
                    join read_parquet('{kind_norm}') k
                      on m.publn_auth = k.jurisdiction_code
                     and m.publn_kind = k.kind_code
                    group by m.docdb_family_id, m.publn_auth
                )
                select
                    b.docdb_family_id,
                    date '{settings.snapshot_date}' as snapshot_date,
                    b.jurisdiction_code,
                    b.wipo_industry_code,
                    b.source_auth,
                    b.is_up_unrolled,
                    b.is_classic_validation,
                    b.is_global_member,
                    coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                    coalesce(v.active_jurisdiction_count, 0) as active_jurisdiction_count,
                    coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                    coalesce(b.family_field_fraction, 1.0) as family_field_fraction,
                    coalesce(m.final_market_multiplier, 0.2) as final_market_multiplier,
                    coalesce(g.global_family_filings, 0) as global_family_filings,
                    coalesce(g.global_trend_coefficient, 1.0) as global_field_trend_coefficient,
                    coalesce(l.local_family_filings, 0) as local_family_filings,
                    case
                        when coalesce(l.local_family_filings, 0) >= 25 then coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                        when coalesce(l.local_family_filings, 0) between 5 and 24 then (coalesce(l.local_trend_coefficient, 1.0) + coalesce(g.global_trend_coefficient, 1.0)) / 2.0
                        else coalesce(g.global_trend_coefficient, 1.0)
                    end as local_field_trend_coefficient,
                    case
                        when coalesce(l.local_family_filings, 0) >= 25 then 'localized'
                        when coalesce(l.local_family_filings, 0) between 5 and 24 then 'mixed'
                        else 'global_fallback'
                    end as branch_coefficient_mode,
                    (
                        coalesce(bl.has_grant_event, 0) = 1
                        and coalesce(bl.has_lapse_event, 0) = 0
                        and coalesce(bl.has_expiry_event, 0) = 0
                    )
                    or (
                        b.is_up_unrolled
                        and coalesce(u.has_up_registration, false)
                        and coalesce(s.family_composite_status, '') = 'fully_active'
                    ) as active_branch_flag,
                    coalesce(bl.has_opposition_event, 0) = 1 as is_opposed_branch,
                    coalesce(
                        bs.representative_branch_stage,
                        case
                            when b.is_up_unrolled and coalesce(u.has_up_registration, false) then 'UNITARY_GRANT'
                            when coalesce(bl.has_pending_event, 0) = 1
                              or coalesce(bs.has_application_publication, 0) = 1 then 'PENDING_APPLICATION'
                            when coalesce(bs.has_modifier_publication, 0) = 1 then 'POST_GRANT_MODIFIER'
                            else 'OTHER'
                        end
                    ) as representative_branch_stage,
                    case
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') = 'fully_active' then 'ACTIVE_GRANT'
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') in ('dead', 'partially_lapsed') then 'LAPSED_OR_EXPIRED'
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0
                         and coalesce(bl.has_opposition_event, 0) = 1 then 'ACTIVE_OPPOSED_GRANT'
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0 then 'ACTIVE_GRANT'
                        when coalesce(bl.has_grant_event, 0) = 1
                         and (coalesce(bl.has_lapse_event, 0) = 1 or coalesce(bl.has_expiry_event, 0) = 1) then 'LAPSED_OR_EXPIRED'
                        when b.is_global_member or b.jurisdiction_code = 'WO' then 'GLOBAL_PLACEHOLDER'
                        when coalesce(bl.has_pending_event, 0) = 1
                          or (
                              coalesce(bs.has_application_publication, 0) = 1
                              and coalesce(bs.has_enforceable_publication, 0) = 0
                              and coalesce(bl.has_grant_event, 0) = 0
                          ) then 'PENDING_ONLY'
                        when coalesce(bs.has_modifier_publication, 0) = 1
                          or coalesce(bs.representative_branch_stage, '') = 'POST_GRANT_MODIFIER' then 'POST_GRANT_INACTIVE'
                        when (
                              coalesce(bl.has_lapse_event, 0) = 1
                              or coalesce(bl.has_expiry_event, 0) = 1
                              or (
                                  coalesce(s.family_composite_status, '') = 'dead'
                                  and coalesce(bs.has_enforceable_publication, 0) = 1
                              )
                          ) then 'LAPSED_OR_EXPIRED'
                        when coalesce(bs.has_other_publication, 0) = 1
                          and coalesce(bs.has_enforceable_publication, 0) = 0
                          and coalesce(bs.has_application_publication, 0) = 0
                          and coalesce(bs.has_modifier_publication, 0) = 0 then 'NON_ENFORCEABLE_PUBLICATION'
                        when bs.representative_branch_stage is not null then 'NON_ENFORCEABLE_PUBLICATION'
                        else 'UNCLASSIFIED_KIND'
                    end as branch_state_label,
                    case
                        when b.is_up_unrolled
                         and coalesce(u.has_up_registration, false)
                         and coalesce(s.family_composite_status, '') = 'fully_active' then 1.0
                        when coalesce(bl.has_grant_event, 0) = 1
                         and coalesce(bl.has_lapse_event, 0) = 0
                         and coalesce(bl.has_expiry_event, 0) = 0 then coalesce(bs.enforceable_stage_multiplier, bs.strongest_stage_multiplier, 1.0)
                        when coalesce(bl.has_pending_event, 0) = 1
                          or coalesce(bs.has_application_publication, 0) = 1 then greatest(coalesce(bs.pending_stage_multiplier, 0.2), 0.2)
                        else 0.0
                    end as branch_stage_multiplier,
                    (
                        case
                            when b.is_up_unrolled
                             and coalesce(u.has_up_registration, false)
                             and coalesce(s.family_composite_status, '') = 'fully_active' then 1.0
                            when coalesce(bl.has_grant_event, 0) = 1
                             and coalesce(bl.has_lapse_event, 0) = 0
                             and coalesce(bl.has_expiry_event, 0) = 0 then coalesce(bs.enforceable_stage_multiplier, bs.strongest_stage_multiplier, 1.0)
                            when coalesce(bl.has_pending_event, 0) = 1 then greatest(coalesce(bs.pending_stage_multiplier, 0.2), 0.2)
                            else 0.0
                        end
                        * coalesce(m.final_market_multiplier, 0.2)
                        * coalesce(b.family_field_fraction, 1.0)
                        * case
                            when coalesce(l.local_family_filings, 0) >= 25 then coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                            when coalesce(l.local_family_filings, 0) between 5 and 24 then (coalesce(l.local_trend_coefficient, 1.0) + coalesce(g.global_trend_coefficient, 1.0)) / 2.0
                            else coalesce(g.global_trend_coefficient, 1.0)
                        end
                        * case
                            when coalesce(bl.has_grant_event, 0) = 1
                             and coalesce(bl.has_lapse_event, 0) = 0
                             and coalesce(bl.has_expiry_event, 0) = 0 then 1.0
                            else 0.0
                        end
                    ) as branch_enforceability_contribution_raw
                from branch_fields b
                left join branch_latest bl
                  on b.docdb_family_id = bl.docdb_family_id
                 and b.jurisdiction_code = bl.jurisdiction_code
                left join branch_stage bs
                  on b.docdb_family_id = bs.docdb_family_id
                 and b.jurisdiction_code = bs.jurisdiction_code
                left join read_parquet('{out_coverage}') v
                  on b.docdb_family_id = v.docdb_family_id
                left join read_parquet('{family_status}') s
                  on b.docdb_family_id = s.docdb_family_id
                left join read_parquet('{up_status}') u
                  on b.docdb_family_id = u.docdb_family_id
                left join read_parquet('{market_weight}') m
                  on b.jurisdiction_code = m.jurisdiction_code
                 and m.snapshot_year = {snapshot_year}
                left join (
                    select wipo_industry_code, global_family_filings, global_trend_coefficient
                    from (
                        select *, row_number() over (partition by wipo_industry_code order by snapshot_year desc) as rn
                        from read_parquet('{out_global_trend}')
                    ) where rn = 1
                ) g
                  on b.wipo_industry_code = g.wipo_industry_code
                left join (
                    select jurisdiction_code, wipo_industry_code, local_family_filings, local_trend_coefficient
                    from (
                        select *, row_number() over (partition by jurisdiction_code, wipo_industry_code order by snapshot_year desc) as rn
                        from read_parquet('{out_local_trend}')
                    ) where rn = 1
                ) l
                  on b.jurisdiction_code = l.jurisdiction_code
                 and b.wipo_industry_code = l.wipo_industry_code
            ) to '{enforce_target}' (format parquet, compression zstd)
            """
        )

        con.execute(
            f"""
            copy (
                with field_base as (
                    select
                        f.docdb_family_id,
                        u.wipo_industry_code,
                        f.family_field_fraction
                    from read_parquet('{fields}') f
                    {field_filter},
                         unnest(f.covered_wipo_fields) as u(wipo_industry_code)
                ),
                enforce_by_field as (
                    select
                        docdb_family_id,
                        wipo_industry_code,
                        sum(branch_enforceability_contribution_raw) as family_field_enforceability_contribution_score
                    from read_parquet('{enforce_target}')
                    group by docdb_family_id, wipo_industry_code
                )
                select
                    f.docdb_family_id,
                    date '{settings.snapshot_date}' as snapshot_date,
                    f.wipo_industry_code,
                    f.family_field_fraction as base_fraction,
                    coalesce(e.family_field_enforceability_contribution_score, 0.0) as family_field_enforceability_contribution_score,
                    coalesce(f.family_field_fraction, 1.0) * coalesce(c.family_adjusted_citation_score_raw, 0.0) as family_field_heritage_contribution_score,
                    '{settings.method_version}' as method_version
                from field_base f
                left join enforce_by_field e
                  on f.docdb_family_id = e.docdb_family_id
                 and f.wipo_industry_code = e.wipo_industry_code
                left join read_parquet('{out_citation}') c
                  on f.docdb_family_id = c.docdb_family_id
            ) to '{field_target}' (format parquet, compression zstd)
            """
        )

        con.execute(
            f"""
            copy (
                {_oecd_quality_select(
                    settings,
                    family_core=family_core,
                    fields=fields,
                    out_coverage=out_coverage,
                    out_citation=out_citation,
                    enforce_rollup_sql=f"select docdb_family_id, sum(branch_enforceability_contribution_raw) as branch_enforceability_contribution_raw from read_parquet('{enforce_target}') group by docdb_family_id",
                    family_filter_sql=oecd_filter,
                    indicator_filter_sql=oecd_indicator_filter,
                )}
            ) to '{oecd_target}' (format parquet, compression zstd)
            """
        )

    full_rebuild = not (out_enforce.exists() and out_field_contrib.exists() and out_oecd.exists())
    if refresh_coverage or not out_coverage.exists():
        _write_coverage(out_coverage)
        result.metrics[f"{out_coverage.stem}_rows"] = parquet_row_count(out_coverage)

    if full_rebuild:
        _write_legal_outputs(out_enforce, out_field_contrib, out_oecd)
    else:
        if affected_family_sql is None:
            _write_legal_outputs(out_enforce, out_field_contrib, out_oecd)
        else:
            affected_path = settings.silver_dir / f"tmp_{temp_prefix}_affected_families.parquet"
            tmp_enforce = settings.silver_dir / f"tmp_silver_family_enforceability_branches_{temp_prefix}.parquet"
            tmp_field = settings.silver_dir / f"tmp_silver_family_field_contributions_{temp_prefix}.parquet"
            tmp_oecd = settings.silver_dir / f"tmp_silver_family_oecd_quality_{temp_prefix}.parquet"
            merged_enforce = settings.silver_dir / f"tmp_silver_family_enforceability_branches_{temp_prefix}_merged.parquet"
            merged_field = settings.silver_dir / f"tmp_silver_family_field_contributions_{temp_prefix}_merged.parquet"
            merged_oecd = settings.silver_dir / f"tmp_silver_family_oecd_quality_{temp_prefix}_merged.parquet"

            con.execute(
                f"""
                copy (
                    {affected_family_sql}
                ) to '{affected_path}' (format parquet, compression zstd)
                """
            )
            affected_rows = parquet_row_count(affected_path)
            result.metrics[affected_family_metric_name] = affected_rows
            if affected_rows == 0:
                result.warnings.append(
                    "No affected families were identified for the incremental legal refresh; existing legal-weighted outputs were retained."
                )
            else:
                _write_legal_outputs(tmp_enforce, tmp_field, tmp_oecd, affected_path=affected_path)
                con.execute(
                    f"""
                    copy (
                        with affected as (select docdb_family_id from read_parquet('{affected_path}'))
                        select * from read_parquet('{out_enforce}')
                        where docdb_family_id not in (select docdb_family_id from affected)
                        union all
                        select * from read_parquet('{tmp_enforce}')
                    ) to '{merged_enforce}' (format parquet, compression zstd)
                    """
                )
                con.execute(
                    f"""
                    copy (
                        with affected as (select docdb_family_id from read_parquet('{affected_path}'))
                        select * from read_parquet('{out_field_contrib}')
                        where docdb_family_id not in (select docdb_family_id from affected)
                        union all
                        select * from read_parquet('{tmp_field}')
                    ) to '{merged_field}' (format parquet, compression zstd)
                    """
                )
                con.execute(
                    f"""
                    copy (
                        with affected as (select docdb_family_id from read_parquet('{affected_path}'))
                        select * from read_parquet('{out_oecd}')
                        where docdb_family_id not in (select docdb_family_id from affected)
                        union all
                        select * from read_parquet('{tmp_oecd}')
                    ) to '{merged_oecd}' (format parquet, compression zstd)
                    """
                )
                merged_enforce.replace(out_enforce)
                merged_field.replace(out_field_contrib)
                merged_oecd.replace(out_oecd)
                for temp_path in [tmp_enforce, tmp_field, tmp_oecd, merged_enforce, merged_field, merged_oecd]:
                    if temp_path.exists():
                        temp_path.unlink()
            if affected_path.exists():
                affected_path.unlink()

    for output in [out_coverage, out_enforce, out_field_contrib, out_oecd]:
        if output.exists():
            result.outputs.append(str(output))
            result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    return result


def build_kindcode_legal_refresh_layers(settings: BuildSettings) -> StageResult:
    """Rebuild only the legal-weighted Silver marts after citation outputs are already refreshed."""
    silver_dir = settings.silver_dir
    member_pub = silver_dir / "silver_family_member_publications.parquet"
    kind_norm = silver_dir / "silver_kind_code_normalization.parquet"
    affected_family_sql = f"""
        select distinct m.docdb_family_id
        from read_parquet('{member_pub}') m
        join read_parquet('{kind_norm}') k
          on m.publn_auth = k.jurisdiction_code
         and m.publn_kind = k.kind_code
        where upper(coalesce(k.mapping_basis, '')) = 'MANUAL_OVERRIDE'
    """
    return _build_incremental_legal_outputs(
        settings,
        stage_name="silver-enrichment-kind-legal-refresh",
        summary="Rebuilt only the legal-weighted Silver marts after kind-code curation using existing citation and trend support outputs.",
        methods=[
            "Reused refreshed citation metrics and existing trend support outputs.",
            "Recomputed only family coverage, enforceability branches, field contributions, and OECD proxy outputs from the current kind-code normalization layer.",
        ],
        calculations=[
            "Branch stage and field contribution values are refreshed from the current Silver kind-code normalization table without rebuilding the semantic layer.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
        ],
        affected_family_sql=affected_family_sql,
        affected_family_metric_name="kindcode_refresh_affected_family_rows",
        refresh_coverage=False,
        temp_prefix="kind_refresh",
    )


def build_legal_status_refresh_layers(settings: BuildSettings) -> StageResult:
    """Refresh legal-weighted Silver marts after legal-event date corrections changed current family state."""
    legal_ledger = settings.silver_dir / "silver_legal_status_event_ledger.parquet"
    affected_family_sql = f"""
        select distinct docdb_family_id
        from read_parquet('{legal_ledger}')
        where event_date <= date '{settings.snapshot_date}'
          and (coalesce(is_lapse_event, false) or coalesce(is_expiry_event, false))
    """
    return _build_incremental_legal_outputs(
        settings,
        stage_name="silver-enrichment-legal-status-refresh",
        summary="Rebuilt coverage and incrementally refreshed legal-weighted Silver marts for families affected by dated lapse/expiry events after legal-ledger date repair.",
        methods=[
            "Rebuilt family coverage metrics from the repaired current family-status snapshot.",
            "Merged refreshed enforceability, field-contribution, and OECD rows only for families touched by dated lapse/expiry events.",
        ],
        calculations=[
            "Affected-family slice is derived from current Silver legal-ledger rows with dated lapse/expiry events on or before the snapshot date.",
            "This refresh path is intended to propagate legal-state fixes without rerunning the semantic or citation-edge layers.",
        ],
        doc_refs=[
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
        ],
        affected_family_sql=affected_family_sql,
        affected_family_metric_name="legal_status_refresh_affected_family_rows",
        refresh_coverage=True,
        temp_prefix="legal_status_refresh",
    )


def build_oecd_quality_refresh(settings: BuildSettings) -> StageResult:
    """Rebuild only the Silver OECD family mart from existing enrichment outputs and the richer OECD seed."""
    family_core = settings.silver_dir / "silver_family_core.parquet"
    fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    out_coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    out_citation = settings.silver_dir / "silver_family_citation_metrics.parquet"
    out_enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    out_oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"

    result = StageResult(
        stage="silver-oecd-refresh",
        status="success",
        summary="Rebuilt only the Silver OECD family mart from the normalized OECD long-form artifact and existing legal/citation support tables.",
        inputs=[str(path) for path in [family_core, fields, out_coverage, out_citation, out_enforce] if path.exists()],
        methods=[
            "Preferred the normalized OECD long-form projection when present and fell back to the legacy proxy formula only if the richer artifact was unavailable.",
            "Reused existing Silver coverage, citation, and enforceability outputs rather than rerunning the full legal refresh.",
        ],
        calculations=[
            "Pivoted the OECD long-form indicators back to one row per family and preserved the legacy proxy columns for compatibility.",
            "Exposed richer raw and percentile OECD fields alongside `oecd_quality_percentile` and `oecd_quality_proxy_score`.",
        ],
        downstream_impacts=[
            "Gold, ML, and portfolio quality overlays can now consume richer OECD-style family signals without a full Silver rerun.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md",
            "docs/new-feature-ideas/oecd-indicator-seed-build-spec.md",
        ],
    )

    required = [family_core, fields, out_coverage, out_citation, out_enforce]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append("OECD refresh requires existing Silver support outputs. Missing: " + ", ".join(missing))
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=1")
    enforce_rollup_sql = f"""
        select
            docdb_family_id,
            sum(branch_enforceability_contribution_raw) as branch_enforceability_contribution_raw
        from read_parquet('{out_enforce}')
        group by docdb_family_id
    """
    con.execute(
        f"""
        copy (
            {_oecd_quality_select(settings, family_core=family_core, fields=fields, out_coverage=out_coverage, out_citation=out_citation, enforce_rollup_sql=enforce_rollup_sql)}
        ) to '{out_oecd}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_oecd))
    result.metrics[f"{out_oecd.stem}_rows"] = parquet_row_count(out_oecd)
    return result


def build_semantic_representative_text(settings: BuildSettings) -> StageResult:
    """Select one representative semantic payload per family using the documented hierarchy."""
    result = StageResult(
        stage="silver-semantic",
        status="success",
        summary="Built representative family text and semantic eligibility according to the EPAB/PATSTAT hierarchy.",
        methods=[
            "Selected one representative text payload per family using EP grant claim first, then PATSTAT abstract fallback.",
            "Materialized semantic eligibility across the full bounded family universe while preserving a separate vector-sample flag.",
        ],
        calculations=[
            "Claim-space payloads exclude A-document claims and prefer claim 1 only.",
            "Abstract fallback is marked explicitly through `is_abstract_fallback` and representative-stage metadata is retained for provenance.",
        ],
        downstream_impacts=[
            "These representative text and eligibility tables feed vector payload generation and the semantic comparison UI.",
            "If empty or degraded, semantic discovery and comparison surfaces should be treated as unavailable in the app.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md",
            "docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    family_core = settings.silver_dir / "silver_family_core.parquet"
    publn_seed = settings.silver_dir / "silver_scope_publn_seed.parquet"
    out_rep = settings.silver_dir / "silver_family_text_representative.parquet"
    out_elig = settings.silver_dir / "silver_semantic_sampling_eligibility.parquet"
    tmp_out_rep = settings.silver_dir / "tmp_silver_family_text_representative.parquet"
    tmp_out_elig = settings.silver_dir / "tmp_silver_semantic_sampling_eligibility.parquet"
    ep_claims = settings.bronze_dir / "bronze_epab_claims.parquet"
    patstat_abs = settings.bronze_dir / "bronze_patstat_appln_abstr.parquet"
    appln_seed = settings.silver_dir / "silver_scope_appln_seed.parquet"
    kind_norm = settings.silver_dir / "silver_kind_code_normalization.parquet"

    result.inputs = [str(path) for path in [family_core, publn_seed, ep_claims, patstat_abs, appln_seed, kind_norm] if path.exists()]
    if not family_core.exists() or not appln_seed.exists() or not publn_seed.exists():
        result.status = "failed"
        result.warnings.append("Scope and Silver core seeds are required before representative text generation.")
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    ep_claims_sql = (
        f"select * from read_parquet('{ep_claims}')"
        if ep_claims.exists()
        else "select null::varchar as publication_number_full, null::varchar as language_code, null::bigint as claim_sequence_no, null::varchar as claim_text_plain where false"
    )
    patstat_abs_sql = (
        f"select * from read_parquet('{patstat_abs}')"
        if patstat_abs.exists()
        else "select null::bigint as appln_id, null::varchar as appln_abstract, null::varchar as appln_abstract_lg where false"
    )
    ep_claim_key_path = settings.silver_dir / "tmp_semantic_ep_claim1_keys.parquet"
    ep_claim_selected_path = settings.silver_dir / "tmp_semantic_ep_claim1_selected.parquet"
    patstat_fallback_key_path = settings.silver_dir / "tmp_semantic_patstat_fallback_keys.parquet"
    patstat_fallback_selected_path = settings.silver_dir / "tmp_semantic_patstat_fallback_selected.parquet"
    temp_paths: list[Path] = [
        tmp_out_rep,
        tmp_out_elig,
        ep_claim_key_path,
        ep_claim_selected_path,
        patstat_fallback_key_path,
        patstat_fallback_selected_path,
    ]
    for path in temp_paths:
        path.unlink(missing_ok=True)

    con.execute(
        f"""
        copy (
            select
                p.docdb_family_id,
                max(p.pat_publn_id) as pat_publn_id
            from read_parquet('{publn_seed}') p
            join read_parquet('{kind_norm}') k
              on p.publn_auth = k.jurisdiction_code
             and p.publn_kind = k.kind_code
            join ({ep_claims_sql}) e
              on p.publication_number_full = e.publication_number_full
            where k.is_enforceable = true
              and lower(coalesce(e.language_code, '')) = 'en'
              and try_cast(e.claim_sequence_no as bigint) = 1
              and p.publn_auth = 'EP'
            group by p.docdb_family_id
        ) to '{ep_claim_key_path}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select distinct
                k.docdb_family_id,
                p.appln_id as representative_appln_id,
                p.pat_publn_id as representative_publn_id,
                k2.universal_stage as representative_stage,
                {_sql_sanitize_text("e.claim_text_plain")} as representative_claim_1_en,
                null::varchar as representative_abstract_en,
                'EPAB_CLAIM' as representative_source_type,
                concat('EPAB_', p.publication_number_full) as text_provenance,
                false as is_abstract_fallback
            from read_parquet('{ep_claim_key_path}') k
            join read_parquet('{publn_seed}') p
              on k.docdb_family_id = p.docdb_family_id
             and k.pat_publn_id = p.pat_publn_id
            join read_parquet('{kind_norm}') k2
              on p.publn_auth = k2.jurisdiction_code
             and p.publn_kind = k2.kind_code
            join ({ep_claims_sql}) e
              on p.publication_number_full = e.publication_number_full
            where lower(coalesce(e.language_code, '')) = 'en'
              and try_cast(e.claim_sequence_no as bigint) = 1
        ) to '{ep_claim_selected_path}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                a.docdb_family_id,
                max(a.appln_id) as appln_id
            from read_parquet('{appln_seed}') a
            join ({patstat_abs_sql}) t
              on a.appln_id = t.appln_id
            where lower(coalesce(t.appln_abstract_lg, 'en')) = 'en'
            group by a.docdb_family_id
        ) to '{patstat_fallback_key_path}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select distinct
                k.docdb_family_id,
                k.appln_id as representative_appln_id,
                null::bigint as representative_publn_id,
                'PATSTAT_ABSTRACT_FALLBACK' as representative_stage,
                null::varchar as representative_claim_1_en,
                {_sql_sanitize_text("t.appln_abstract")} as representative_abstract_en,
                'PATSTAT_ABSTRACT' as representative_source_type,
                'PATSTAT_ABSTRACT' as text_provenance,
                true as is_abstract_fallback
            from read_parquet('{patstat_fallback_key_path}') k
            join ({patstat_abs_sql}) t
              on k.appln_id = t.appln_id
            where lower(coalesce(t.appln_abstract_lg, 'en')) = 'en'
        ) to '{patstat_fallback_selected_path}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            with unified_rep as (
                select distinct *
                from read_parquet('{ep_claim_selected_path}')
                where representative_claim_1_en is not null
                union all
                select distinct p.*
                from read_parquet('{patstat_fallback_selected_path}') p
                left join read_parquet('{ep_claim_key_path}') e using (docdb_family_id)
                where e.docdb_family_id is null
                  and p.representative_abstract_en is not null
            )
            select
                docdb_family_id,
                representative_appln_id,
                representative_publn_id,
                representative_stage,
                representative_claim_1_en,
                representative_abstract_en,
                representative_source_type,
                text_provenance,
                is_abstract_fallback,
                representative_appln_id as appln_id,
                representative_publn_id as pat_publn_id
            from unified_rep
        ) to '{tmp_out_rep}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            with family_semantic_status as (
                select
                    c.docdb_family_id,
                    coalesce(sum(case when k.is_enforceable then 1 else 0 end), 0) > 0 as has_grant_right,
                    coalesce(sum(case when k.is_enforceable and p.publn_auth = 'EP' then 1 else 0 end), 0) > 0 as has_ep_grant,
                    coalesce(r.has_claim_text, false) as has_claim_text,
                    r.docdb_family_id is not null as has_representative_text
                from read_parquet('{family_core}') c
                left join read_parquet('{publn_seed}') p using (docdb_family_id)
                left join read_parquet('{kind_norm}') k
                  on p.publn_auth = k.jurisdiction_code
                 and p.publn_kind = k.kind_code
                left join (
                    select
                        docdb_family_id,
                        coalesce(nullif(trim(representative_claim_1_en), ''), null) is not null as has_claim_text
                    from read_parquet('{tmp_out_rep}')
                ) r using (docdb_family_id)
                group by c.docdb_family_id, r.docdb_family_id, r.has_claim_text
            ),
            ranked as (
                select
                    *,
                    row_number() over (order by hash(docdb_family_id), docdb_family_id) as family_rank,
                    row_number() over (
                        partition by case when has_representative_text and not has_claim_text then 1 else 0 end
                        order by hash(docdb_family_id), docdb_family_id
                    ) as abstract_only_rank,
                    sum(case when has_representative_text and has_claim_text then 1 else 0 end) over () as total_claim_candidate_count
                from family_semantic_status
            )
            select
                c.docdb_family_id,
                c.has_grant_right,
                c.has_ep_grant,
                c.family_rank,
                c.has_representative_text as is_semantic_candidate,
                case
                    when not c.has_representative_text then false
                    when c.has_claim_text then true
                    else c.abstract_only_rank <= greatest(
                        0,
                        cast((select count(*) from read_parquet('{family_core}')) * {settings.vector_sample_pct} as bigint)
                        - c.total_claim_candidate_count
                    )
                end as is_in_vector_sample
            from ranked c
        ) to '{tmp_out_elig}' (format parquet, compression zstd)
        """
    )

    result.metrics["silver_family_text_representative_rows"] = parquet_row_count(tmp_out_rep)
    result.metrics["silver_semantic_sampling_eligibility_rows"] = parquet_row_count(tmp_out_elig)
    if result.metrics["silver_family_text_representative_rows"] == 0:
        result.status = "degraded"
        result.warnings.append("Representative text output is empty. Semantic layer will be unavailable.")
    else:
        tmp_out_rep.replace(out_rep)
    if result.metrics["silver_semantic_sampling_eligibility_rows"] > 0:
        tmp_out_elig.replace(out_elig)
    result.outputs.extend([str(out_rep), str(out_elig)])
    for path in temp_paths:
        path.unlink(missing_ok=True)
    return result
