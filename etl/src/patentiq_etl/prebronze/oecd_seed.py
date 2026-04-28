from __future__ import annotations

from datetime import date
from pathlib import Path
from shutil import copy2
from tempfile import NamedTemporaryFile

import duckdb

from patentiq_etl.common.io import ensure_dir, parquet_row_count
from patentiq_etl.common.types import BuildSettings, StageResult


COHORT_MIN_SIZE = 30

BASE_INDICATORS: list[tuple[str, str, str, str]] = [
    ("fwd_cits5", "fwd_cits5_raw", "fwd_cits5_observation_window_years", "fwd_cits5_is_truncation_sensitive"),
    ("fwd_cits7", "fwd_cits7_raw", "fwd_cits7_observation_window_years", "fwd_cits7_is_truncation_sensitive"),
    ("generality", "generality_raw", "generality_observation_window_years", "generality_is_truncation_sensitive"),
    ("originality", "originality_raw", "originality_observation_window_years", "originality_is_truncation_sensitive"),
    ("radicalness", "radicalness_raw", "radicalness_observation_window_years", "radicalness_is_truncation_sensitive"),
    ("bwd_cits", "bwd_cits_raw", "bwd_cits_observation_window_years", "bwd_cits_is_truncation_sensitive"),
    ("npl_cits", "npl_cits_raw", "npl_cits_observation_window_years", "npl_cits_is_truncation_sensitive"),
    ("science_grounding", "science_grounding_raw", "science_grounding_observation_window_years", "science_grounding_is_truncation_sensitive"),
    ("family_size", "family_size_raw", "family_size_observation_window_years", "family_size_is_truncation_sensitive"),
    ("grant_lag", "grant_lag_raw", "grant_lag_observation_window_years", "grant_lag_is_truncation_sensitive"),
]


def _write_parquet(con: duckdb.DuckDBPyConnection, query: str, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    with NamedTemporaryFile(suffix=".parquet", delete=False, dir="/tmp") as handle:
        tmp_path = Path(handle.name)
    con.execute(f"copy ({query}) to '{tmp_path}' (format parquet, compression zstd)")
    copy2(tmp_path, out_path)
    tmp_path.unlink(missing_ok=True)


def _indicator_long_union(source_path: Path, include_metadata: bool) -> str:
    selects: list[str] = []
    for indicator_name, raw_col, window_col, trunc_col in BASE_INDICATORS:
        if include_metadata:
            selects.append(
                f"""
                select
                    appln_id,
                    docdb_family_id,
                    snapshot_year,
                    family_priority_year,
                    primary_wipo_field,
                    family_anchor_date,
                    '{indicator_name}' as indicator_name,
                    cast({raw_col} as double) as indicator_value_raw,
                    {window_col} as observation_window_years,
                    cast({trunc_col} as boolean) as is_truncation_sensitive,
                    cast(is_proxy as boolean) as is_proxy,
                    cast(method_version as varchar) as method_version,
                    cast(source_family_grain as varchar) as source_family_grain
                from read_parquet('{source_path}')
                where {raw_col} is not null
                """
            )
        else:
            selects.append(
                f"""
                select
                    family_priority_year,
                    primary_wipo_field,
                    '{indicator_name}' as indicator_name,
                    cast({raw_col} as double) as indicator_value_raw,
                    {window_col} as observation_window_years
                from read_parquet('{source_path}')
                where {raw_col} is not null
                """
            )
    return "\nunion all\n".join(selects)


def build_oecd_indicator_seed(settings: BuildSettings) -> StageResult:
    """Build a family-first OECD indicator seed from the existing Silver citation and field layers."""
    family_core = settings.silver_dir / "silver_family_core.parquet"
    family_wipo = settings.silver_dir / "silver_family_wipo_fields.parquet"
    member_pub = settings.silver_dir / "silver_family_member_publications.parquet"
    citation_metrics = settings.silver_dir / "silver_family_citation_metrics.parquet"
    npl_backlinks = settings.silver_dir / "silver_family_npl_backlinks.parquet"
    citation_network = settings.silver_dir / "silver_enriched_citation_network.parquet"
    appln_seed = settings.silver_dir / "silver_scope_appln_seed.parquet"
    kind_norm = settings.silver_dir / "silver_kind_code_normalization.parquet"

    rich_out = settings.raw_refs_dir / "oecd_indicator_seed.parquet"
    result = StageResult(
        stage="build-oecd-indicator-seed",
        status="success",
        summary="Built a family-first OECD indicator seed in wide family-level raw form from existing Silver citation, field, family-size, and grant-lag layers without rerunning Bronze.",
        inputs=[
            str(path)
            for path in [family_core, family_wipo, member_pub, citation_metrics, npl_backlinks, citation_network, appln_seed, kind_norm]
            if path.exists()
        ],
        methods=[
            "Used family-first collapse and deduplicated family-to-family citation pools rather than patent-level averaging.",
            "Anchored OECD cohort normalization on `family_priority_year x primary_wipo_field` and forward-citation windows on `family_earliest_publication_date`.",
            "Computed family-level grant lag from the first granted member publication minus that member application filing date.",
            "Kept the raw seed wide and family-grain so richer normalized or Bronze-facing projections can be materialized separately.",
        ],
        calculations=[
            "Computed `fwd_cits5`, `fwd_cits7`, `generality`, `originality`, `radicalness`, `bwd_cits`, `npl_cits`, `science_grounding`, `family_size`, and `grant_lag` at family grain.",
            "Preserved raw values and truncation flags per indicator in the wide seed.",
            "Marked fixed-window forward-citation rows as truncation-sensitive when the family publication anchor is too recent for a complete observation window.",
        ],
        downstream_impacts=[
            "The rich seed can feed Bronze or direct Silver/Gold benchmark overlays without recomputing the citation pools.",
            "Recent-cohort forward-window indicators remain usable but are explicitly marked as truncation-sensitive.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md",
            "docs/new-feature-ideas/oecd-indicator-seed-build-spec.md",
            "docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md",
        ],
    )

    required = [family_core, family_wipo, member_pub, citation_metrics, npl_backlinks, citation_network, appln_seed, kind_norm]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append("OECD seed build requires existing Silver support outputs. Missing: " + ", ".join(missing))
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=2")

    snapshot_dt = date.fromisoformat(settings.snapshot_date)
    snapshot_year = snapshot_dt.year
    method_version = f"{settings.method_version}_family_first_oecd_seed_v2"

    con.execute(
        f"""
        create or replace temp view family_anchor as
        with family_pub as (
            select
                docdb_family_id,
                min(publn_date) as family_earliest_publication_date
            from read_parquet('{member_pub}')
            group by 1
        ),
        representative_appln as (
            select
                docdb_family_id,
                appln_id
            from (
                select
                    docdb_family_id,
                    appln_id,
                    row_number() over (
                        partition by docdb_family_id
                        order by publn_date nulls last, appln_id
                    ) as rn
                from read_parquet('{member_pub}')
            )
            where rn = 1
        )
        select
            c.docdb_family_id,
            r.appln_id,
            c.family_priority_year,
            c.family_earliest_priority_date,
            c.family_size_docdb,
            coalesce(p.family_earliest_publication_date, c.family_earliest_priority_date) as family_anchor_date,
            w.primary_wipo_field,
            w.covered_wipo_fields
        from read_parquet('{family_core}') c
        left join family_pub p using (docdb_family_id)
        left join representative_appln r using (docdb_family_id)
        left join read_parquet('{family_wipo}') w using (docdb_family_id)
        """
    )

    con.execute(
        f"""
        create or replace temp view forward_family_pool as
        select
            cited_docdb_family_id as docdb_family_id,
            source_docdb_family_id as related_family_id,
            min(citation_date) as first_citation_date,
            any_value(citing_primary_wipo_field) as related_primary_wipo_field
        from read_parquet('{citation_network}')
        where clean_edge_weight > 0
          and not is_out_of_bounds
          and citing_primary_wipo_field is not null
        group by 1, 2
        """
    )

    con.execute(
        f"""
        create or replace temp view backward_family_pool as
        select
            c.source_docdb_family_id as docdb_family_id,
            c.cited_docdb_family_id as related_family_id,
            w.primary_wipo_field as related_primary_wipo_field
        from (
            select distinct
                source_docdb_family_id,
                cited_docdb_family_id
            from read_parquet('{citation_network}')
            where clean_edge_weight > 0
              and not is_out_of_bounds
        ) c
        left join read_parquet('{family_wipo}') w
          on c.cited_docdb_family_id = w.docdb_family_id
        where w.primary_wipo_field is not null
        """
    )

    con.execute(
        f"""
        create or replace temp view grant_lag_pool as
        select
            m.docdb_family_id,
            min(date_diff('day', a.appln_filing_date, m.publn_date))::double as grant_lag_days
        from read_parquet('{member_pub}') m
        join read_parquet('{appln_seed}') a
          on m.appln_id = a.appln_id
        join read_parquet('{kind_norm}') k
          on m.publn_auth = k.jurisdiction_code
         and m.publn_kind = k.kind_code
        where upper(coalesce(k.universal_stage, '')) in ('STANDARD_GRANT', 'OPPOSITION_SURVIVOR', 'UNITARY_GRANT')
          and m.publn_date is not null
          and a.appln_filing_date is not null
          and m.publn_date >= a.appln_filing_date
        group by 1
        """
    )

    con.execute(
        f"""
        create or replace temp view oecd_indicator_wide as
        with forward_counts as (
            select
                f.docdb_family_id,
                sum(case when f.first_citation_date <= a.family_anchor_date + interval '5 years' then 1 else 0 end) as fwd_cits5,
                sum(case when f.first_citation_date <= a.family_anchor_date + interval '7 years' then 1 else 0 end) as fwd_cits7
            from forward_family_pool f
            join family_anchor a using (docdb_family_id)
            group by 1
        ),
        forward_field_dist as (
            select
                docdb_family_id,
                related_primary_wipo_field,
                count(*) as field_family_count
            from forward_family_pool
            group by 1, 2
        ),
        forward_generality as (
            select
                d.docdb_family_id,
                1 - sum(power(d.field_family_count::double / t.total_forward_families::double, 2)) as generality
            from forward_field_dist d
            join (
                select docdb_family_id, sum(field_family_count) as total_forward_families
                from forward_field_dist
                group by 1
            ) t using (docdb_family_id)
            group by 1
        ),
        backward_field_dist as (
            select
                docdb_family_id,
                related_primary_wipo_field,
                count(*) as field_family_count
            from backward_family_pool
            group by 1, 2
        ),
        backward_originality as (
            select
                d.docdb_family_id,
                1 - sum(power(d.field_family_count::double / t.total_backward_families::double, 2)) as originality
            from backward_field_dist d
            join (
                select docdb_family_id, sum(field_family_count) as total_backward_families
                from backward_field_dist
                group by 1
            ) t using (docdb_family_id)
            group by 1
        ),
        backward_radicalness as (
            select
                b.docdb_family_id,
                avg(
                    case
                        when a.covered_wipo_fields is not null then
                            case when list_contains(a.covered_wipo_fields, b.related_primary_wipo_field) then 0.0 else 1.0 end
                        when a.primary_wipo_field is not null then
                            case when a.primary_wipo_field = b.related_primary_wipo_field then 0.0 else 1.0 end
                        else null
                    end
                ) as radicalness
            from backward_family_pool b
            join family_anchor a using (docdb_family_id)
            group by 1
        ),
        npl_counts as (
            select
                docdb_family_id,
                count(distinct npl_publn_id) as npl_cits
            from read_parquet('{npl_backlinks}')
            group by 1
        )
        select
            a.appln_id,
            a.docdb_family_id,
            a.family_priority_year,
            a.family_anchor_date,
            a.primary_wipo_field,
            coalesce(cm.family_fwd_cits5, fc.fwd_cits5, 0) as fwd_cits5,
            coalesce(cm.family_fwd_cits7, fc.fwd_cits7, 0) as fwd_cits7,
            coalesce(fg.generality, 0.0) as generality,
            coalesce(bo.originality, 0.0) as originality,
            coalesce(br.radicalness, 0.0) as radicalness,
            coalesce(cm.family_backward_citations_clean, 0) as bwd_cits,
            coalesce(cm.family_backward_npl_citation_count, nc.npl_cits, 0) as npl_cits,
            coalesce(cm.family_science_grounding_score, 0.0) as science_grounding,
            cast(coalesce(a.family_size_docdb, 0) as double) as family_size,
            gl.grant_lag_days as grant_lag
        from family_anchor a
        left join read_parquet('{citation_metrics}') cm using (docdb_family_id)
        left join forward_counts fc using (docdb_family_id)
        left join forward_generality fg using (docdb_family_id)
        left join backward_originality bo using (docdb_family_id)
        left join backward_radicalness br using (docdb_family_id)
        left join npl_counts nc using (docdb_family_id)
        left join grant_lag_pool gl using (docdb_family_id)
        """
    )

    con.execute(
        f"""
        create or replace temp view oecd_indicator_seed_rich as
        select
            b.appln_id,
            b.docdb_family_id,
            {snapshot_year}::bigint as snapshot_year,
            b.family_priority_year,
            b.primary_wipo_field,
            b.family_anchor_date,
            false as is_proxy,
            '{method_version}' as method_version,
            'family_collapsed_deduplicated' as source_family_grain,
            cast(b.fwd_cits5 as double) as fwd_cits5_raw,
            5::bigint as fwd_cits5_observation_window_years,
            case when b.family_anchor_date > date '{snapshot_dt.isoformat()}' - interval '5 years' then true else false end as fwd_cits5_is_truncation_sensitive,
            cast(b.fwd_cits7 as double) as fwd_cits7_raw,
            7::bigint as fwd_cits7_observation_window_years,
            case when b.family_anchor_date > date '{snapshot_dt.isoformat()}' - interval '7 years' then true else false end as fwd_cits7_is_truncation_sensitive,
            b.generality as generality_raw,
            null::bigint as generality_observation_window_years,
            false as generality_is_truncation_sensitive,
            b.originality as originality_raw,
            null::bigint as originality_observation_window_years,
            false as originality_is_truncation_sensitive,
            b.radicalness as radicalness_raw,
            null::bigint as radicalness_observation_window_years,
            false as radicalness_is_truncation_sensitive,
            cast(b.bwd_cits as double) as bwd_cits_raw,
            null::bigint as bwd_cits_observation_window_years,
            false as bwd_cits_is_truncation_sensitive,
            cast(b.npl_cits as double) as npl_cits_raw,
            null::bigint as npl_cits_observation_window_years,
            false as npl_cits_is_truncation_sensitive,
            b.science_grounding as science_grounding_raw,
            null::bigint as science_grounding_observation_window_years,
            false as science_grounding_is_truncation_sensitive,
            cast(b.family_size as double) as family_size_raw,
            null::bigint as family_size_observation_window_years,
            false as family_size_is_truncation_sensitive,
            cast(b.grant_lag as double) as grant_lag_raw,
            null::bigint as grant_lag_observation_window_years,
            false as grant_lag_is_truncation_sensitive
        from oecd_indicator_wide b
        """
    )

    _write_parquet(con, "select * from oecd_indicator_seed_rich", rich_out)

    result.outputs.append(str(rich_out))
    result.metrics["oecd_indicator_seed_rows"] = parquet_row_count(rich_out)
    result.metrics["oecd_indicator_seed_indicator_count"] = len(BASE_INDICATORS)
    result.metrics["oecd_indicator_seed_family_count"] = parquet_row_count(family_core)
    return result


def build_oecd_indicator_cohort_stats(settings: BuildSettings) -> StageResult:
    """Build the OECD cohort-stat companion from the wide raw OECD seed."""
    seed_path = settings.raw_refs_dir / "oecd_indicator_seed.parquet"
    cohort_out = settings.raw_refs_dir / "oecd_indicator_cohort_stats.parquet"

    result = StageResult(
        stage="build-oecd-indicator-cohort-stats",
        status="success",
        summary="Built the OECD cohort-stat companion from the wide raw family-level OECD seed.",
        inputs=[str(seed_path)] if seed_path.exists() else [],
        methods=[
            "Read the existing wide family-level OECD seed rather than recomputing the citation and field joins.",
            "Aggregated cohort statistics by `family_priority_year x primary_wipo_field x indicator_name`.",
            "Used approximate quantiles for cohort percentiles to keep local generation tractable on the bounded mega-cluster slice.",
        ],
        calculations=[
            "Computed cohort size, mean, standard deviation, and percentile checkpoints for the OECD base indicator set including `family_size` and `grant_lag`.",
            "Kept the cohort companion separate from the raw seed so normalized benchmarking can be added later without changing the base family-level artifact.",
        ],
        downstream_impacts=[
            "This companion enables cohort-relative interpretation and later percentile/z-score derivation without rerunning the raw OECD seed build.",
            "Portfolio hit-rate and top-decile OECD views can now be built from the current local artifact set.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md",
            "docs/new-feature-ideas/oecd-indicator-seed-build-spec.md",
        ],
    )
    if not seed_path.exists():
        result.status = "failed"
        result.warnings.append("`etl/data/raw/refs/oecd_indicator_seed.parquet` must exist before building OECD cohort statistics.")
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=2")

    snapshot_year = date.fromisoformat(settings.snapshot_date).year
    method_version = f"{settings.method_version}_family_first_oecd_seed_v2"
    long_union = _indicator_long_union(seed_path, include_metadata=False)

    con.execute(
        f"""
        create or replace temp view oecd_indicator_cohort_stats as
        with indicator_long as (
            {long_union}
        ),
        raw_stats as (
            select
                family_priority_year,
                primary_wipo_field,
                indicator_name,
                count(*) as cohort_size,
                avg(indicator_value_raw) as mean_value,
                stddev_pop(indicator_value_raw) as std_dev_value,
                approx_quantile(indicator_value_raw, 0.10) as raw_p10_value,
                approx_quantile(indicator_value_raw, 0.50) as raw_p50_value,
                approx_quantile(indicator_value_raw, 0.90) as raw_p90_value,
                approx_quantile(indicator_value_raw, 0.99) as raw_p99_value,
                max(indicator_value_raw) as max_value,
                max(observation_window_years) as observation_window_years
            from indicator_long
            where family_priority_year is not null
              and primary_wipo_field is not null
              and indicator_value_raw is not null
            group by 1, 2, 3
        )
        select
            family_priority_year,
            primary_wipo_field,
            indicator_name,
            cohort_size,
            mean_value,
            std_dev_value,
            greatest(0.0, least(max_value, raw_p10_value)) as p10_value,
            greatest(greatest(0.0, least(max_value, raw_p10_value)), least(max_value, raw_p50_value)) as p50_value,
            greatest(greatest(greatest(0.0, least(max_value, raw_p10_value)), least(max_value, raw_p50_value)), least(max_value, raw_p90_value)) as p90_value,
            greatest(greatest(greatest(greatest(0.0, least(max_value, raw_p10_value)), least(max_value, raw_p50_value)), least(max_value, raw_p90_value)), least(max_value, raw_p99_value)) as p99_value,
            max_value,
            observation_window_years,
            {snapshot_year}::bigint as snapshot_year,
            '{method_version}' as method_version
        from raw_stats
        """
    )

    _write_parquet(con, "select * from oecd_indicator_cohort_stats", cohort_out)
    result.outputs.append(str(cohort_out))
    result.metrics["oecd_indicator_cohort_rows"] = parquet_row_count(cohort_out)
    result.metrics["oecd_indicator_cohort_indicator_count"] = len(BASE_INDICATORS)
    return result


def build_oecd_indicator_longform(settings: BuildSettings) -> StageResult:
    """Build the normalized long-form OECD indicator projection from the raw seed and cohort stats."""
    seed_path = settings.raw_refs_dir / "oecd_indicator_seed.parquet"
    cohort_path = settings.raw_refs_dir / "oecd_indicator_cohort_stats.parquet"
    longform_out = settings.raw_refs_dir / "oecd_indicator_longform.parquet"

    result = StageResult(
        stage="build-oecd-indicator-longform",
        status="success",
        summary="Built the normalized long-form OECD indicator projection, including explicit family-first composite variants.",
        inputs=[str(path) for path in [seed_path, cohort_path] if path.exists()],
        methods=[
            "Expanded the wide family-level OECD seed into one row per `family x indicator` for downstream benchmarking and Bronze-compatible projections.",
            "Computed exact within-cohort percentile ranks and z-scores by `family_priority_year x primary_wipo_field x indicator_name`.",
            "Built `quality_index_4` and `quality_index_6` as explicit family-first composite variants with the claims component omitted and labeled in-schema.",
        ],
        calculations=[
            "Percentile rank is the canonical exposed normalized value; z-score is preserved for analytical use.",
            "Grant-lag normalization is inverted so faster grants receive higher normalized scores.",
            "Composite rows are built from normalized components only and carry explicit component policy metadata.",
        ],
        downstream_impacts=[
            "This artifact can feed Bronze/Silver OECD overlays and direct portfolio benchmarking without recomputing cohort windows.",
            "The long-form shape supports explainable indicator drilldowns and future Bronze-compatible ingestion.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md",
            "docs/new-feature-ideas/oecd-indicator-seed-build-spec.md",
        ],
    )

    missing = [str(path) for path in [seed_path, cohort_path] if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append("OECD long-form build requires both the raw seed and cohort-stat companion. Missing: " + ", ".join(missing))
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=1")

    tmp_parts: list[Path] = []

    for indicator_name, raw_col, window_col, trunc_col in BASE_INDICATORS:
        tmp_path = settings.raw_refs_dir / f"tmp_oecd_indicator_longform_{indicator_name}.parquet"
        sort_expr = "-1.0 * indicator_value_raw" if indicator_name == "grant_lag" else "indicator_value_raw"
        z_expr = (
            "(mean_value - indicator_value_raw) / std_dev_value"
            if indicator_name == "grant_lag"
            else "(indicator_value_raw - mean_value) / std_dev_value"
        )
        _write_parquet(
            con,
            f"""
            with base as (
                select
                    appln_id,
                    docdb_family_id,
                    snapshot_year,
                    family_priority_year,
                    primary_wipo_field,
                    family_anchor_date,
                    cast({raw_col} as double) as indicator_value_raw,
                    {window_col} as observation_window_years,
                    cast({trunc_col} as boolean) as is_truncation_sensitive,
                    cast(is_proxy as boolean) as is_proxy,
                    cast(method_version as varchar) as method_version,
                    cast(source_family_grain as varchar) as source_family_grain
                from read_parquet('{seed_path}')
                where {raw_col} is not null
            ),
            enriched as (
                select
                    b.*,
                    c.cohort_size,
                    c.mean_value,
                    c.std_dev_value
                from base b
                join read_parquet('{cohort_path}') c
                  on b.family_priority_year = c.family_priority_year
                 and b.primary_wipo_field = c.primary_wipo_field
                 and c.indicator_name = '{indicator_name}'
                where c.cohort_size >= {COHORT_MIN_SIZE}
            )
            select
                appln_id,
                docdb_family_id,
                snapshot_year,
                family_priority_year,
                primary_wipo_field,
                family_anchor_date,
                '{indicator_name}' as indicator_name,
                indicator_value_raw,
                cume_dist() over (
                    partition by family_priority_year, primary_wipo_field
                    order by {sort_expr} asc, docdb_family_id
                ) as indicator_percentile_rank,
                case
                    when coalesce(std_dev_value, 0.0) = 0.0 then 0.0
                    else {z_expr}
                end as indicator_z_score,
                cohort_size,
                observation_window_years,
                is_truncation_sensitive,
                is_proxy,
                'family_priority_year_primary_wipo_field' as normalization_basis,
                null::varchar as component_policy,
                1::bigint as component_count,
                method_version,
                source_family_grain
            from enriched
            """,
            tmp_path,
        )
        tmp_parts.append(tmp_path)

    fwd_cits5_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_fwd_cits5.parquet"
    family_size_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_family_size.parquet"
    generality_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_generality.parquet"
    bwd_cits_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_bwd_cits.parquet"
    grant_lag_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_grant_lag.parquet"

    q4_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_quality_index_4.parquet"
    _write_parquet(
        con,
        f"""
        select
            f.appln_id,
            f.docdb_family_id,
            f.snapshot_year,
            f.family_priority_year,
            f.primary_wipo_field,
            f.family_anchor_date,
            'quality_index_4' as indicator_name,
            (f.indicator_percentile_rank + s.indicator_percentile_rank + g.indicator_percentile_rank) / 3.0 as indicator_value_raw,
            (f.indicator_percentile_rank + s.indicator_percentile_rank + g.indicator_percentile_rank) / 3.0 as indicator_percentile_rank,
            (f.indicator_z_score + s.indicator_z_score + g.indicator_z_score) / 3.0 as indicator_z_score,
            least(f.cohort_size, s.cohort_size, g.cohort_size) as cohort_size,
            null::bigint as observation_window_years,
            coalesce(f.is_truncation_sensitive, false) or coalesce(s.is_truncation_sensitive, false) or coalesce(g.is_truncation_sensitive, false) as is_truncation_sensitive,
            true as is_proxy,
            'family_priority_year_primary_wipo_field' as normalization_basis,
            'claims_omitted_family_first_variant' as component_policy,
            3::bigint as component_count,
            greatest(f.method_version, s.method_version, g.method_version) as method_version,
            greatest(f.source_family_grain, s.source_family_grain, g.source_family_grain) as source_family_grain
        from read_parquet('{fwd_cits5_tmp}') f
        join read_parquet('{family_size_tmp}') s using (docdb_family_id)
        join read_parquet('{generality_tmp}') g using (docdb_family_id)
        """,
        q4_tmp,
    )
    tmp_parts.append(q4_tmp)

    q6_tmp = settings.raw_refs_dir / "tmp_oecd_indicator_longform_quality_index_6.parquet"
    _write_parquet(
        con,
        f"""
        select
            f.appln_id,
            f.docdb_family_id,
            f.snapshot_year,
            f.family_priority_year,
            f.primary_wipo_field,
            f.family_anchor_date,
            'quality_index_6' as indicator_name,
            (f.indicator_percentile_rank + s.indicator_percentile_rank + g.indicator_percentile_rank + b.indicator_percentile_rank + l.indicator_percentile_rank) / 5.0 as indicator_value_raw,
            (f.indicator_percentile_rank + s.indicator_percentile_rank + g.indicator_percentile_rank + b.indicator_percentile_rank + l.indicator_percentile_rank) / 5.0 as indicator_percentile_rank,
            (f.indicator_z_score + s.indicator_z_score + g.indicator_z_score + b.indicator_z_score + l.indicator_z_score) / 5.0 as indicator_z_score,
            least(f.cohort_size, s.cohort_size, g.cohort_size, b.cohort_size, l.cohort_size) as cohort_size,
            null::bigint as observation_window_years,
            coalesce(f.is_truncation_sensitive, false)
                or coalesce(s.is_truncation_sensitive, false)
                or coalesce(g.is_truncation_sensitive, false)
                or coalesce(b.is_truncation_sensitive, false)
                or coalesce(l.is_truncation_sensitive, false) as is_truncation_sensitive,
            true as is_proxy,
            'family_priority_year_primary_wipo_field' as normalization_basis,
            'claims_omitted_family_first_variant' as component_policy,
            5::bigint as component_count,
            greatest(f.method_version, s.method_version, g.method_version, b.method_version, l.method_version) as method_version,
            greatest(f.source_family_grain, s.source_family_grain, g.source_family_grain, b.source_family_grain, l.source_family_grain) as source_family_grain
        from read_parquet('{fwd_cits5_tmp}') f
        join read_parquet('{family_size_tmp}') s using (docdb_family_id)
        join read_parquet('{generality_tmp}') g using (docdb_family_id)
        join read_parquet('{bwd_cits_tmp}') b using (docdb_family_id)
        join read_parquet('{grant_lag_tmp}') l using (docdb_family_id)
        """,
        q6_tmp,
    )
    tmp_parts.append(q6_tmp)

    parts_union = "\nunion all\n".join(f"select * from read_parquet('{path}')" for path in tmp_parts)
    _write_parquet(con, parts_union, longform_out)
    for path in tmp_parts:
        path.unlink(missing_ok=True)

    result.outputs.append(str(longform_out))
    result.metrics["oecd_indicator_longform_rows"] = parquet_row_count(longform_out)
    result.metrics["oecd_indicator_longform_indicator_count"] = len(BASE_INDICATORS) + 2
    return result


def build_oecd_indicator_bronze_projection(settings: BuildSettings) -> StageResult:
    """Project the richer OECD long-form artifact into the Bronze-facing reference contract."""
    longform_path = settings.raw_refs_dir / "oecd_indicator_longform.parquet"
    bounded_out = settings.bounded_refs_dir / "oecd_quality_indicator_seed.parquet"
    bronze_out = settings.bronze_dir / "bronze_ext_oecd_indicator_seed.parquet"

    result = StageResult(
        stage="build-oecd-indicator-bronze-projection",
        status="success",
        summary="Projected the richer OECD long-form artifact into the Bronze-facing reference contract and landed the typed Bronze parquet directly.",
        inputs=[str(longform_path)] if longform_path.exists() else [],
        methods=[
            "Read the normalized OECD long-form artifact rather than recomputing family metrics again.",
            "Used percentile rank as the canonical `indicator_value` for the Bronze-facing contract while preserving raw and z-score companions.",
            "Wrote both the bounded reference source file and the Bronze parquet directly so future Bronze reruns have a stable OECD input.",
        ],
        calculations=[
            "Projected one row per `family x indicator` with normalized value, raw value, z-score, cohort size, and component metadata.",
        ],
        downstream_impacts=[
            "This closes the Bronze contract gap for the OECD indicator seed without disturbing the richer raw family-level seed artifacts.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/oecd-indicator-seed-build-spec.md",
            "docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md",
        ],
    )
    if not longform_path.exists():
        result.status = "failed"
        result.warnings.append("`etl/data/raw/refs/oecd_indicator_longform.parquet` must exist before building the Bronze OECD projection.")
        return result

    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=1")

    projection_sql = f"""
        select
            appln_id,
            docdb_family_id,
            indicator_name,
            indicator_percentile_rank as indicator_value,
            indicator_value_raw,
            indicator_percentile_rank,
            indicator_z_score,
            normalization_basis,
            cohort_size,
            snapshot_year,
            observation_window_years,
            is_truncation_sensitive,
            is_proxy,
            component_policy,
            component_count,
            method_version
        from read_parquet('{longform_path}')
    """

    _write_parquet(con, projection_sql, bounded_out)
    _write_parquet(con, projection_sql, bronze_out)

    result.outputs.extend([str(bounded_out), str(bronze_out)])
    result.metrics["oecd_indicator_bronze_projection_rows"] = parquet_row_count(bronze_out)
    return result
