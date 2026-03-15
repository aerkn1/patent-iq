from __future__ import annotations

import duckdb

from patentiq_etl.common.io import parquet_columns, parquet_row_count, sanitize_semantic_text, table_exists
from patentiq_etl.common.types import BuildSettings, StageResult


def build_enrichment_silver(settings: BuildSettings) -> list[StageResult]:
    """Execute all enrichment-oriented Silver builders after the core entity layer exists."""
    return [
        build_citation_and_market_layers(settings),
        build_semantic_representative_text(settings),
    ]


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
    pat_publn = settings.bronze_dir / "bronze_patstat_pat_publn.parquet"
    owner = settings.silver_dir / "silver_assignee_harmonized.parquet"

    result = StageResult(
        stage="silver-enrichment",
        status="success",
        summary="Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.",
        inputs=[str(path) for path in [family_core, appln_seed, publn_seed, fields, family_status, family_jur, market_weight, citation, pat_publn, owner] if path.exists()],
        methods=[
            "Mapped in-scope publications to citation edges and flagged out-of-scope references as ghost-node candidates.",
            "Derived market-intelligence segment tables from field-year family activity inside the bounded universe.",
            "Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.",
        ],
        calculations=[
            "Family adjusted citation score is an MVP proxy based on in-scope citation volume and out-of-scope citation share.",
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

    out_citation = settings.silver_dir / "silver_family_citation_metrics.parquet"
    out_trend = settings.silver_dir / "silver_family_trend_tables.parquet"
    out_coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    out_enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    out_oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"
    out_market = settings.silver_dir / "silver_market_intelligence_segments.parquet"
    out_market_ts = settings.silver_dir / "silver_market_intelligence_timeseries.parquet"

    if citation.exists() and pat_publn.exists():
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
                        select pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
                    ),
                    edges as (
                        select
                            s.docdb_family_id,
                            count(*) as raw_family_citation_count,
                            sum(case when t.docdb_family_id is null then 1 else 0 end) as out_of_bounds_citation_count
                        from read_parquet('{citation}') c
                        join scoped_pub s on cast(c.{source_publn_id} as bigint) = cast(s.pat_publn_id as bigint)
                        left join scoped_pub t on cast(c.{cited_publn_id} as bigint) = cast(t.pat_publn_id as bigint)
                        group by s.docdb_family_id
                    )
                    select
                        docdb_family_id,
                        raw_family_citation_count,
                        out_of_bounds_citation_count,
                        case
                            when raw_family_citation_count = 0 then 0.0
                            else cast(out_of_bounds_citation_count as double) / cast(raw_family_citation_count as double)
                        end as out_of_bounds_citation_share,
                        raw_family_citation_count * (1.0 - case
                            when raw_family_citation_count = 0 then 0.0
                            else cast(out_of_bounds_citation_count as double) / cast(raw_family_citation_count as double)
                        end) as family_rcf_score
                    from edges
                ) to '{out_citation}' (format parquet, compression zstd)
                """
            )
        else:
            result.warnings.append("Citation table lacks `cited_pat_publn_id`; citation metrics were skipped.")
    else:
        result.warnings.append("Citation metrics were skipped because Bronze citation/publication tables were unavailable.")

    if not out_citation.exists():
        con.execute(
            f"""
            copy (
                select
                    docdb_family_id,
                    0::bigint as raw_family_citation_count,
                    0::bigint as out_of_bounds_citation_count,
                    0.0::double as out_of_bounds_citation_share,
                    0.0::double as family_rcf_score
                from read_parquet('{family_core}')
            ) to '{out_citation}' (format parquet, compression zstd)
            """
        )
    if citation.exists() and pat_publn.exists():
        cited_expr = f"cast(c.{cited_publn_id} as bigint)" if cited_publn_id else "null::bigint"
        cited_join = f"cast(c.{cited_publn_id} as bigint) = cast(t.pat_publn_id as bigint)" if cited_publn_id else "false"
        citation_stats = con.execute(
            f"""
            with scoped_pub as (
                select pat_publn_id, docdb_family_id from read_parquet('{publn_seed}')
            ),
            base_edges as (
                select
                    cast(c.{source_publn_id} as bigint) as source_pat_publn_id,
                    {cited_expr} as cited_pat_publn_id,
                    s.docdb_family_id as source_family_id,
                    t.docdb_family_id as cited_family_id
                from read_parquet('{citation}') c
                join scoped_pub s on cast(c.{source_publn_id} as bigint) = cast(s.pat_publn_id as bigint)
                left join scoped_pub t on {cited_join}
            )
            select
                count(*) as citation_edge_count,
                count(distinct source_pat_publn_id) as citation_unique_source_publication_count,
                count(distinct cited_pat_publn_id) as citation_unique_cited_publication_count,
                count(distinct source_family_id) as citation_unique_source_family_count,
                count(distinct cited_family_id) as citation_unique_cited_family_count
            from base_edges
            """
        ).fetchone()
        result.metrics["citation_edge_count"] = int(citation_stats[0])
        result.metrics["citation_unique_source_publication_count"] = int(citation_stats[1])
        result.metrics["citation_unique_cited_publication_count"] = int(citation_stats[2])
        result.metrics["citation_unique_source_family_count"] = int(citation_stats[3])
        result.metrics["citation_unique_cited_family_count"] = int(citation_stats[4])

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
            select
                docdb_family_id,
                count(distinct publn_auth) as family_jurisdiction_count,
                sum(case when is_grant_stage then 1 else 0 end) as family_grant_publication_count,
                sum(case when is_application_stage then 1 else 0 end) as family_application_publication_count
            from read_parquet('{settings.silver_dir / "silver_family_member_publications.parquet"}')
            group by docdb_family_id
        ) to '{out_coverage}' (format parquet, compression zstd)
        """
    )
    if family_status.exists() and family_jur.exists() and market_weight.exists():
        con.execute(
            f"""
            copy (
                with weighted_jur as (
                    select
                        j.docdb_family_id,
                        sum(coalesce(m.final_market_multiplier, 0.2)) as summed_market_multiplier,
                        count(distinct j.jurisdiction_code) as unrolled_jurisdiction_count
                    from read_parquet('{family_jur}') j
                    left join read_parquet('{market_weight}') m
                      on j.jurisdiction_code = m.jurisdiction_code
                     and m.snapshot_year = {settings.snapshot_date[:4]}
                    group by j.docdb_family_id
                )
                select
                    c.docdb_family_id,
                    coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                    coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                    (
                        coalesce(w.summed_market_multiplier, 0.0)
                        * case when coalesce(s.has_any_active_grant, false) then 1.0 else 0.2 end
                    ) as branch_enforceability_contribution_raw
                from read_parquet('{family_core}') c
                left join read_parquet('{out_coverage}') v using (docdb_family_id)
                left join read_parquet('{family_status}') s using (docdb_family_id)
                left join weighted_jur w using (docdb_family_id)
            ) to '{out_enforce}' (format parquet, compression zstd)
            """
        )
    else:
        con.execute(
            f"""
            copy (
                select
                    c.docdb_family_id,
                    coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                    coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                    (coalesce(v.family_jurisdiction_count, 0) * 0.6) + (coalesce(v.family_grant_publication_count, 0) * 0.4) as branch_enforceability_contribution_raw
                from read_parquet('{family_core}') c
                left join read_parquet('{out_coverage}') v using (docdb_family_id)
            ) to '{out_enforce}' (format parquet, compression zstd)
            """
        )
        result.warnings.append("Enforceability remained on the fallback coverage proxy because status/jurisdiction/market-weight tables were unavailable.")
    con.execute(
        f"""
        copy (
            select
                c.docdb_family_id,
                coalesce(x.family_rcf_score, 0.0) as family_rcf_score,
                coalesce(v.family_jurisdiction_count, 0) as family_jurisdiction_count,
                coalesce(v.family_grant_publication_count, 0) as family_grant_publication_count,
                coalesce(x.family_rcf_score, 0.0) + (coalesce(v.family_grant_publication_count, 0) * 0.5) + (coalesce(e.branch_enforceability_contribution_raw, 0.0) * 0.1) as oecd_quality_proxy_score
            from read_parquet('{family_core}') c
            left join read_parquet('{out_coverage}') v using (docdb_family_id)
            left join read_parquet('{out_citation}') x using (docdb_family_id)
            left join read_parquet('{out_enforce}') e using (docdb_family_id)
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
                end as market_state
            from lagged
        ) to '{out_market_ts}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                wipo_industry_code as segment_id,
                wipo_industry_code,
                max_by(market_state, family_priority_year) as market_state,
                sum(family_count) as total_family_count,
                max(family_priority_year) as latest_year
            from read_parquet('{out_market_ts}')
            group by wipo_industry_code
        ) to '{out_market}' (format parquet, compression zstd)
        """
    )

    for output in [out_citation, out_trend, out_coverage, out_enforce, out_oecd, out_market, out_market_ts]:
        if output.exists():
            result.outputs.append(str(output))
            result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    return result


def build_semantic_representative_text(settings: BuildSettings) -> StageResult:
    """Select one representative semantic payload per family using the documented hierarchy."""
    result = StageResult(
        stage="silver-semantic",
        status="success",
        summary="Built representative family text and semantic eligibility according to the USPTO/EPAB/PATSTAT hierarchy.",
        methods=[
            "Selected one representative text payload per family using the US grant claim, EP grant claim, then PATSTAT abstract fallback hierarchy.",
            "Materialized semantic sample eligibility as a bounded active-grant cohort for MVP.",
        ],
        calculations=[
            "Claim-space payloads exclude A-document claims and prefer claim 1 only.",
            "Abstract fallback is marked explicitly through `is_abstract_fallback`.",
        ],
        downstream_impacts=[
            "These representative text and eligibility tables feed vector payload generation and the semantic comparison UI.",
            "If empty or degraded, semantic FTO radar and whitespace-map surfaces should be treated as unavailable in the app.",
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
    us_claims = settings.bronze_dir / "bronze_uspto_ft_claims.parquet"
    us_abstract = settings.bronze_dir / "bronze_uspto_ft_abstract.parquet"
    ep_claims = settings.bronze_dir / "bronze_epab_claims.parquet"
    ep_document = settings.bronze_dir / "bronze_epab_document.parquet"
    ep_abstract = settings.bronze_dir / "bronze_epab_abstract.parquet"
    patstat_abs = settings.bronze_dir / "bronze_patstat_appln_abstr.parquet"
    appln_seed = settings.silver_dir / "silver_scope_appln_seed.parquet"
    kind_norm = settings.silver_dir / "silver_kind_code_normalization.parquet"

    result.inputs = [str(path) for path in [family_core, publn_seed, us_claims, ep_claims, ep_document, patstat_abs, appln_seed, kind_norm] if path.exists()]
    if not family_core.exists() or not appln_seed.exists() or not publn_seed.exists():
        result.status = "failed"
        result.warnings.append("Scope and Silver core seeds are required before representative text generation.")
        return result

    con = duckdb.connect()
    con.create_function("sanitize_semantic_text", sanitize_semantic_text)
    us_claims_sql = (
        f"select * from read_parquet('{us_claims}')"
        if us_claims.exists()
        else "select null::varchar as publication_number_full, null::varchar as claim_num, null::varchar as claim_text_plain where false"
    )
    ep_document_sql = (
        f"select * from read_parquet('{ep_document}')"
        if ep_document.exists()
        else "select null::varchar as epab_doc_id, null::varchar as publication_number_full where false"
    )
    ep_claims_sql = (
        f"select * from read_parquet('{ep_claims}')"
        if ep_claims.exists()
        else "select null::varchar as epab_doc_id, null::varchar as language_code, null::bigint as claim_sequence_no, null::varchar as claim_text_plain where false"
    )
    patstat_abs_sql = (
        f"select * from read_parquet('{patstat_abs}')"
        if patstat_abs.exists()
        else "select null::bigint as appln_id, null::varchar as appln_abstract, null::varchar as appln_abstract_lg where false"
    )
    con.execute(
        f"""
        copy (
            with us_claim1 as (
                select
                    p.docdb_family_id,
                    p.appln_id,
                    p.pat_publn_id,
                    sanitize_semantic_text(u.claim_text_plain) as representative_claim_1_en,
                    null::varchar as representative_abstract_en,
                    concat('USPTO_', p.publication_number_full) as text_provenance,
                    false as is_abstract_fallback,
                    row_number() over (partition by p.docdb_family_id order by p.pat_publn_id desc) as rn
                from read_parquet('{publn_seed}') p
                join read_parquet('{kind_norm}') k
                  on p.publn_auth = k.jurisdiction_code
                 and p.publn_kind = k.kind_code
                join ({us_claims_sql}) u
                  on p.publication_number_full = u.publication_number_full
                where k.is_enforceable = true
                  and try_cast(u.claim_num as bigint) = 1
                  and p.publn_auth = 'US'
            ),
            ep_claim1 as (
                select
                    p.docdb_family_id,
                    p.appln_id,
                    p.pat_publn_id,
                    sanitize_semantic_text(e.claim_text_plain) as representative_claim_1_en,
                    null::varchar as representative_abstract_en,
                    concat('EPAB_', p.publication_number_full) as text_provenance,
                    false as is_abstract_fallback,
                    row_number() over (partition by p.docdb_family_id order by p.pat_publn_id desc) as rn
                from read_parquet('{publn_seed}') p
                join read_parquet('{kind_norm}') k
                  on p.publn_auth = k.jurisdiction_code
                 and p.publn_kind = k.kind_code
                join ({ep_document_sql}) d
                  on p.publication_number_full = d.publication_number_full
                join ({ep_claims_sql}) e
                  on d.epab_doc_id = e.epab_doc_id
                where k.is_enforceable = true
                  and lower(coalesce(e.language_code, '')) = 'en'
                  and try_cast(e.claim_sequence_no as bigint) = 1
                  and p.publn_auth = 'EP'
            ),
            patstat_fallback as (
                select
                    a.docdb_family_id,
                    a.appln_id,
                    null::bigint as pat_publn_id,
                    null::varchar as representative_claim_1_en,
                    sanitize_semantic_text(t.appln_abstract) as representative_abstract_en,
                    'PATSTAT_ABSTRACT' as text_provenance,
                    true as is_abstract_fallback,
                    row_number() over (partition by a.docdb_family_id order by a.appln_id desc) as rn
                from read_parquet('{appln_seed}') a
                join ({patstat_abs_sql}) t
                  on a.appln_id = t.appln_id
                where lower(coalesce(t.appln_abstract_lg, 'en')) = 'en'
            ),
            selected as (
                select * from us_claim1 where rn = 1
                union all
                select * from ep_claim1 e
                where rn = 1
                  and not exists (
                    select 1 from us_claim1 u
                    where u.docdb_family_id = e.docdb_family_id and u.rn = 1
                  )
                union all
                select * from patstat_fallback p
                where rn = 1
                  and not exists (
                    select 1 from us_claim1 u
                    where u.docdb_family_id = p.docdb_family_id and u.rn = 1
                  )
                  and not exists (
                    select 1 from ep_claim1 e
                    where e.docdb_family_id = p.docdb_family_id and e.rn = 1
                  )
            )
            select * from selected
        ) to '{out_rep}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                c.docdb_family_id,
                coalesce(sum(case when k.is_enforceable then 1 else 0 end), 0) > 0 as has_grant_right,
                coalesce(sum(case when k.is_enforceable and p.publn_auth in ('US', 'EP') then 1 else 0 end), 0) > 0 as has_us_or_ep_grant,
                row_number() over (order by c.docdb_family_id) as family_rank,
                case
                    when coalesce(sum(case when k.is_enforceable then 1 else 0 end), 0) > 0 then true
                    else false
                end as is_semantic_candidate
            from read_parquet('{family_core}') c
            left join read_parquet('{publn_seed}') p using (docdb_family_id)
            left join read_parquet('{kind_norm}') k
              on p.publn_auth = k.jurisdiction_code
             and p.publn_kind = k.kind_code
            group by c.docdb_family_id
            qualify family_rank <= greatest(1, cast((select count(*) from read_parquet('{family_core}')) * {settings.vector_sample_pct} as bigint))
        ) to '{out_elig}' (format parquet, compression zstd)
        """
    )

    result.outputs.extend([str(out_rep), str(out_elig)])
    result.metrics["silver_family_text_representative_rows"] = parquet_row_count(out_rep)
    result.metrics["silver_semantic_sampling_eligibility_rows"] = parquet_row_count(out_elig)
    if result.metrics["silver_family_text_representative_rows"] == 0:
        result.status = "degraded"
        result.warnings.append("Representative text output is empty. Semantic layer will be unavailable.")
    return result
