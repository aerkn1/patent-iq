from __future__ import annotations

import duckdb

from patentiq_etl.common.io import parquet_row_count
from patentiq_etl.common.types import BuildSettings, StageResult


def build_gold(settings: BuildSettings) -> StageResult:
    """Build the page-facing Gold marts consumed by the application layer."""
    result = StageResult(
        stage="gold",
        status="success",
        summary="Built Gold family, portfolio, Market Intelligence, and semantic-context marts from validated Silver tables.",
        methods=[
            "Composed page-facing marts from Silver reusable tables rather than recalculating directly from Bronze.",
            "Preserved bounded-scope labels and semantic fallback flags in downstream Gold surfaces.",
        ],
        calculations=[
            "Family blocking power is an MVP fusion of enforceability and adjusted citation score.",
            "Portfolio and Market Intelligence marts aggregate over the in-scope family universe only.",
        ],
        downstream_impacts=[
            "These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.",
            "Any drift here changes the API payload shape and the values shown in the contest MVP frontend.",
        ],
        doc_refs=[
            "docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
            "docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md",
        ],
    )

    con = duckdb.connect()
    family_core = settings.silver_dir / "silver_family_core.parquet"
    owner = settings.silver_dir / "silver_assignee_harmonized.parquet"
    fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    cite = settings.silver_dir / "silver_family_citation_metrics.parquet"
    enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    market_seg = settings.silver_dir / "silver_market_intelligence_segments.parquet"
    market_ts = settings.silver_dir / "silver_market_intelligence_timeseries.parquet"
    semantic_rep = settings.silver_dir / "silver_family_text_representative.parquet"
    semantic_elig = settings.silver_dir / "silver_semantic_sampling_eligibility.parquet"

    out_family_summary = settings.gold_dir / "gold_family_summary.parquet"
    out_blocking = settings.gold_dir / "gold_family_blocking_power.parquet"
    out_field = settings.gold_dir / "gold_family_field_contributions.parquet"
    out_portfolio = settings.gold_dir / "gold_portfolio_summary.parquet"
    out_market_overview = settings.gold_dir / "gold_market_intelligence_overview.parquet"
    out_market_segments = settings.gold_dir / "gold_market_intelligence_segments.parquet"
    out_market_timeseries = settings.gold_dir / "gold_market_intelligence_timeseries.parquet"
    out_semantic = settings.gold_dir / "gold_semantic_match_context.parquet"
    out_attacker = settings.gold_dir / "gold_family_attacker_summary.parquet"
    out_portfolio_forecast = settings.gold_dir / "gold_portfolio_forecast_summary.parquet"

    con.execute(
        f"""
        copy (
            select
                c.docdb_family_id,
                c.family_earliest_priority_date,
                c.family_priority_year,
                o.owner_name_harmonized,
                o.owner_name_display,
                f.covered_wipo_fields,
                s.family_composite_status,
                s.active_jurisdiction_count,
                s.has_any_active_grant,
                '{settings.scope_type}' as scope_type,
                '{settings.snapshot_date}' as snapshot_date
            from read_parquet('{family_core}') c
            left join read_parquet('{owner}') o using (docdb_family_id)
            left join read_parquet('{fields}') f using (docdb_family_id)
            left join read_parquet('{family_status}') s using (docdb_family_id)
        ) to '{out_family_summary}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                c.docdb_family_id,
                coalesce(e.branch_enforceability_contribution_raw, 0.0) as family_market_threat_score_raw,
                coalesce(x.family_rcf_score, 0.0) as family_adjusted_citation_score_raw,
                (coalesce(e.branch_enforceability_contribution_raw, 0.0) * 0.65) +
                (coalesce(x.family_rcf_score, 0.0) * 0.35) as family_raw_absolute_blocking_power,
                percent_rank() over (
                    order by
                        (coalesce(e.branch_enforceability_contribution_raw, 0.0) * 0.65) +
                        (coalesce(x.family_rcf_score, 0.0) * 0.35)
                ) * 100.0 as family_ui_blocking_power_score
            from read_parquet('{family_core}') c
            left join read_parquet('{enforce}') e using (docdb_family_id)
            left join read_parquet('{cite}') x using (docdb_family_id)
        ) to '{out_blocking}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                unnest(covered_wipo_fields) as wipo_industry_code
            from read_parquet('{fields}')
        ) to '{out_field}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                owner_name_harmonized,
                any_value(owner_name_display) as owner_name_display,
                count(distinct s.docdb_family_id) as portfolio_family_count_within_mega_cluster,
                avg(coalesce(b.family_ui_blocking_power_score, 0.0)) as portfolio_avg_blocking_power_within_mega_cluster,
                sum(case when s.has_any_active_grant then 1 else 0 end) as portfolio_active_grant_family_count,
                count(distinct case when sem.is_semantic_candidate then s.docdb_family_id end) as semantic_candidate_family_count
            from read_parquet('{out_family_summary}') s
            left join read_parquet('{out_blocking}') b using (docdb_family_id)
            left join read_parquet('{semantic_elig}') sem using (docdb_family_id)
            group by owner_name_harmonized
        ) to '{out_portfolio}' (format parquet, compression zstd)
        """
    )
    con.execute(f"copy (select * from read_parquet('{market_seg}')) to '{out_market_segments}' (format parquet, compression zstd)")
    con.execute(f"copy (select * from read_parquet('{market_ts}')) to '{out_market_timeseries}' (format parquet, compression zstd)")
    con.execute(
        f"""
        copy (
            select
                count(*) as segment_count,
                sum(case when market_state = 'rising' then 1 else 0 end) as rising_segment_count,
                sum(case when market_state = 'cooling' then 1 else 0 end) as cooling_segment_count,
                sum(total_family_count) as total_family_count,
                avg(total_family_count) as avg_segment_family_count
            from read_parquet('{market_seg}')
        ) to '{out_market_overview}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                s.docdb_family_id,
                s.text_provenance,
                s.is_abstract_fallback,
                e.is_semantic_candidate,
                f.covered_wipo_fields,
                b.family_ui_blocking_power_score
            from read_parquet('{semantic_rep}') s
            join read_parquet('{semantic_elig}') e using (docdb_family_id)
            left join read_parquet('{fields}') f using (docdb_family_id)
            left join read_parquet('{out_blocking}') b using (docdb_family_id)
        ) to '{out_semantic}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                coalesce(out_of_bounds_citation_share, 0.0) as out_of_bounds_citation_share,
                coalesce(raw_family_citation_count, 0) as raw_family_citation_count
            from read_parquet('{cite}')
        ) to '{out_attacker}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                owner_name_harmonized,
                portfolio_family_count_within_mega_cluster,
                portfolio_avg_blocking_power_within_mega_cluster,
                portfolio_active_grant_family_count,
                semantic_candidate_family_count,
                portfolio_avg_blocking_power_within_mega_cluster as forecast_proxy_score
            from read_parquet('{out_portfolio}')
        ) to '{out_portfolio_forecast}' (format parquet, compression zstd)
        """
    )

    for output in [
        out_family_summary,
        out_blocking,
        out_field,
        out_portfolio,
        out_market_overview,
        out_market_segments,
        out_market_timeseries,
        out_semantic,
        out_attacker,
        out_portfolio_forecast,
    ]:
        result.outputs.append(str(output))
        result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    return result
