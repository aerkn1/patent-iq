from __future__ import annotations

from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult

OUTPUT_TABLE = "silver_family_feature_snapshot_pit.parquet"
AUDIT_TABLE = "silver_family_feature_snapshot_pit_audit.json"
DENSE_OUTPUT_TABLE = "silver_family_feature_snapshot_pit_dense.parquet"
DENSE_AUDIT_TABLE = "silver_family_feature_snapshot_pit_dense_audit.json"
CLASSIFICATION_VISIBILITY_OUTPUT_TABLE = "silver_family_classification_visibility_timeline.parquet"
CLASSIFICATION_VISIBILITY_AUDIT_TABLE = "silver_family_classification_visibility_timeline_audit.json"
CLASSIFICATION_DENSE_OUTPUT_TABLE = "silver_family_classification_pit_dense.parquet"
CLASSIFICATION_DENSE_AUDIT_TABLE = "silver_family_classification_pit_dense_audit.json"
DENSE_BUCKET_COUNT = 16
CLASSIFICATION_DENSE_BUCKET_COUNT = 64

# Columns tracked for data_completeness_pct_asof (references raw CTEs before COALESCE).
# These are joined-table references used inside the final SELECT's completeness expression.
_COMPLETENESS_EXPRS = [
    "l.family_composite_status_asof IS NOT NULL",
    "l.active_jurisdiction_count_asof IS NOT NULL",
    "l.active_grant_branch_count_asof IS NOT NULL",
    "cov.family_jurisdiction_count_asof IS NOT NULL",
    "(l.active_jurisdiction_count_asof IS NOT NULL AND cov.family_jurisdiction_count_asof IS NOT NULL)",
    "bk.family_blocking_power_score_asof IS NOT NULL",
    "bk.family_enforceability_score_asof IS NOT NULL",
    "fl.family_field_contribution_primary_asof IS NOT NULL",
    "c.pre_asof_citing_assignee_diversity IS NOT NULL",
    "c.pre_asof_attacker_density_score IS NOT NULL",
    # COUNT returns 0 not NULL, so these are always non-null but included for symmetric tracking
    "c.pre_asof_forward_citations_clean IS NOT NULL",
    "c.pre_asof_unique_citing_family_count IS NOT NULL",
]


def _required_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "family_summary": settings.gold_dir / "gold_family_summary.parquet",
        "status_history": settings.silver_dir / "silver_family_status_history.parquet",
        "branch_history": settings.silver_dir / "silver_branch_status_history_dense.parquet",
        "enriched_network": settings.silver_dir / "silver_enriched_citation_network.parquet",
        "blocking_ts": settings.gold_dir / "gold_family_blocking_power_timeseries.parquet",
        "field_ts": settings.gold_dir / "gold_family_field_contributions_timeseries.parquet",
        "member_publications": settings.silver_dir / "silver_family_member_publications.parquet",
    }


def _required_classification_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "pit_dense": settings.silver_dir / DENSE_OUTPUT_TABLE,
        "family_wipo_fields": settings.silver_dir / "silver_family_wipo_fields.parquet",
        "family_ipc_cpc_canonical": settings.silver_dir / "silver_family_ipc_cpc_canonical.parquet",
    }


def _required_classification_visibility_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "member_publications": settings.silver_dir / "silver_family_member_publications.parquet",
        "appln_cpc": settings.bronze_dir / "bronze_patstat_appln_cpc.parquet",
        "appln_ipc": settings.bronze_dir / "bronze_patstat_appln_ipc.parquet",
        "appln_techn_field": settings.bronze_dir / "bronze_patstat_appln_techn_field.parquet",
        "ref_techn_field_ipc": settings.bronze_dir / "bronze_ref_techn_field_ipc.parquet",
    }


def _build_pit_sql(
    family_summary: Path,
    status_history: Path,
    branch_history: Path,
    enriched_network: Path,
    blocking_ts: Path,
    field_ts: Path,
    member_publications: Path,
    snapshot_date: str,
    target_as_of_year: int | None = None,
) -> str:
    completeness_sum = " +\n            ".join(
        f"CASE WHEN {expr} THEN 1 ELSE 0 END" for expr in _COMPLETENESS_EXPRS
    )
    completeness_den = len(_COMPLETENESS_EXPRS)
    year_filter = (
        f"AND EXTRACT(year FROM CAST(g.family_earliest_priority_date AS DATE) + INTERVAL '2 years')::INTEGER = {target_as_of_year}"
        if target_as_of_year is not None
        else ""
    )
    return f"""
    WITH family_anchor AS (
        SELECT
            g.docdb_family_id,
            CAST(g.family_earliest_priority_date AS DATE) + INTERVAL '2 years' AS as_of_date,
            EXTRACT(year FROM CAST(g.family_earliest_priority_date AS DATE) + INTERVAL '2 years')::INTEGER AS as_of_year,
            CAST(g.family_earliest_priority_date AS DATE) AS family_earliest_priority_date,
            CAST(g.family_priority_year AS INTEGER) AS family_priority_year
        FROM read_parquet('{family_summary}') g
        WHERE COALESCE(g.is_main_window_family, true) = true
          AND g.family_earliest_priority_date IS NOT NULL
          {year_filter}
    ),

    legal_asof AS (
        SELECT
            a.docdb_family_id,
            h.family_composite_status           AS family_composite_status_asof,
            h.active_jurisdiction_count::DOUBLE  AS active_jurisdiction_count_asof,
            h.active_grant_branch_count::DOUBLE  AS active_grant_branch_count_asof,
            h.lapsed_jurisdiction_count::DOUBLE  AS lapsed_jurisdiction_count_asof
        FROM family_anchor a
        INNER JOIN read_parquet('{status_history}') h USING (docdb_family_id)
        WHERE h.snapshot_year <= a.as_of_year
        QUALIFY ROW_NUMBER() OVER (PARTITION BY a.docdb_family_id ORDER BY h.snapshot_year DESC) = 1
    ),

    branch_latest_asof AS (
        SELECT
            a.docdb_family_id,
            b.jurisdiction_code
        FROM family_anchor a
        LEFT JOIN read_parquet('{branch_history}') b
            ON b.docdb_family_id = a.docdb_family_id
           AND b.snapshot_year <= a.as_of_year
           AND b.jurisdiction_code IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY a.docdb_family_id, b.jurisdiction_code
            ORDER BY b.snapshot_year DESC
        ) = 1
    ),

    coverage_asof AS (
        SELECT
            docdb_family_id,
            COUNT(DISTINCT jurisdiction_code)::DOUBLE AS family_jurisdiction_count_asof
        FROM branch_latest_asof
        GROUP BY docdb_family_id
    ),

    family_size_asof AS (
        SELECT
            a.docdb_family_id,
            COUNT(DISTINCT m.appln_id)::DOUBLE AS family_size_docdb_asof
        FROM family_anchor a
        LEFT JOIN read_parquet('{member_publications}') m
            ON m.docdb_family_id = a.docdb_family_id
           AND m.appln_id IS NOT NULL
           AND m.publn_date IS NOT NULL
           AND CAST(m.publn_date AS DATE) <= a.as_of_date
           AND CAST(m.publn_date AS DATE) < DATE '9999-01-01'
        GROUP BY a.docdb_family_id
    ),

    citation_asof AS (
        SELECT
            a.docdb_family_id,
            COUNT(DISTINCT
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN n.source_docdb_family_id END
            )::DOUBLE AS pre_asof_forward_citations_clean,
            SUM(
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN COALESCE(n.clean_edge_weight, 0.0) ELSE 0.0 END
            )::DOUBLE AS pre_asof_forward_citations_weighted,
            COUNT(DISTINCT
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN n.source_docdb_family_id END
            )::DOUBLE AS pre_asof_unique_citing_family_count,
            CASE
                WHEN COUNT(DISTINCT
                    CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                         THEN n.source_docdb_family_id END) > 0
                THEN COUNT(DISTINCT
                        CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                              AND n.citing_assignee_name IS NOT NULL
                             THEN n.citing_assignee_name END)::DOUBLE
                     / COUNT(DISTINCT
                        CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                             THEN n.source_docdb_family_id END)::DOUBLE
                ELSE NULL::DOUBLE
            END AS pre_asof_citing_assignee_diversity,
            AVG(
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN n.clean_edge_weight END
            )::DOUBLE AS pre_asof_attacker_density_score
        FROM family_anchor a
        LEFT JOIN read_parquet('{enriched_network}') n
            ON n.cited_docdb_family_id = a.docdb_family_id
           AND NOT COALESCE(n.is_out_of_bounds, false)
           AND NOT COALESCE(n.is_intra_family_citation, false)
           AND NOT COALESCE(n.is_self_citation, false)
           AND n.citation_date IS NOT NULL
        GROUP BY a.docdb_family_id, a.as_of_date
    ),

    blocking_asof AS (
        SELECT
            a.docdb_family_id,
            b.ui_blocking_power_score           AS family_blocking_power_score_asof,
            b.overall_legal_enforceability_score AS family_enforceability_score_asof
        FROM family_anchor a
        INNER JOIN read_parquet('{blocking_ts}') b USING (docdb_family_id)
        WHERE EXTRACT(year FROM CAST(b.snapshot_date AS DATE))::INTEGER <= a.as_of_year
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY a.docdb_family_id
            ORDER BY CAST(b.snapshot_date AS DATE) DESC
        ) = 1
    ),

    field_asof AS (
        SELECT
            a.docdb_family_id,
            f.wipo_industry_code AS primary_wipo_field_asof,
            f.enforceability_contribution_score AS family_field_contribution_primary_asof,
            COUNT(DISTINCT f.wipo_industry_code) OVER (PARTITION BY a.docdb_family_id, f.snapshot_year)::DOUBLE
                AS family_tech_breadth_wipo_count_asof
        FROM family_anchor a
        INNER JOIN read_parquet('{field_ts}') f USING (docdb_family_id)
        WHERE f.snapshot_year <= a.as_of_year
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY a.docdb_family_id
            ORDER BY f.snapshot_year DESC, f.enforceability_contribution_score DESC NULLS LAST
        ) = 1
    )

    SELECT
        a.docdb_family_id,
        a.as_of_date,
        a.as_of_year,
        CAST(a.as_of_date <= DATE '{snapshot_date}' AS BOOLEAN)        AS is_observed_as_of_snapshot,
        COALESCE(l.family_composite_status_asof, 'unknown')      AS family_composite_status_asof,
        COALESCE(l.active_jurisdiction_count_asof, 0.0)          AS active_jurisdiction_count_asof,
        COALESCE(l.active_grant_branch_count_asof, 0.0)          AS active_grant_branch_count_asof,
        COALESCE(l.lapsed_jurisdiction_count_asof, 0.0)          AS lapsed_jurisdiction_count_asof,
        COALESCE(sz.family_size_docdb_asof, 0.0)                 AS family_size_docdb_asof,
        COALESCE(cov.family_jurisdiction_count_asof, 0.0)        AS family_jurisdiction_count_asof,
        CASE
            WHEN COALESCE(cov.family_jurisdiction_count_asof, 0.0) = 0.0 THEN 0.0
            ELSE COALESCE(l.active_jurisdiction_count_asof, 0.0) / cov.family_jurisdiction_count_asof
        END                                                     AS family_coverage_stability_score_asof,
        COALESCE(fl.family_tech_breadth_wipo_count_asof, 1.0)    AS family_tech_breadth_wipo_count_asof,
        fl.family_field_contribution_primary_asof,
        bk.family_blocking_power_score_asof,
        bk.family_enforceability_score_asof,
        COALESCE(c.pre_asof_forward_citations_clean, 0.0)        AS pre_asof_forward_citations_clean,
        COALESCE(c.pre_asof_forward_citations_weighted, 0.0)     AS pre_asof_forward_citations_weighted,
        CASE
            WHEN COALESCE(avg(COALESCE(c.pre_asof_forward_citations_weighted, 0.0)) OVER (
                PARTITION BY a.family_priority_year, COALESCE(fl.primary_wipo_field_asof, '__unknown__')
            ), 0.0) = 0.0
            THEN COALESCE(c.pre_asof_forward_citations_weighted, 0.0)
            ELSE COALESCE(c.pre_asof_forward_citations_weighted, 0.0)
                 / avg(COALESCE(c.pre_asof_forward_citations_weighted, 0.0)) OVER (
                    PARTITION BY a.family_priority_year, COALESCE(fl.primary_wipo_field_asof, '__unknown__')
                 )
        END                                                     AS family_rcf_score_asof,
        COALESCE(c.pre_asof_unique_citing_family_count, 0.0)     AS pre_asof_unique_citing_family_count,
        c.pre_asof_citing_assignee_diversity,
        c.pre_asof_attacker_density_score,
        ROUND(
            (
                {completeness_sum}
            )::DOUBLE / {completeness_den}.0,
            6
        ) AS data_completeness_pct_asof
    FROM family_anchor a
    LEFT JOIN citation_asof c USING (docdb_family_id)
    LEFT JOIN legal_asof l USING (docdb_family_id)
    LEFT JOIN coverage_asof cov USING (docdb_family_id)
    LEFT JOIN family_size_asof sz USING (docdb_family_id)
    LEFT JOIN blocking_asof bk USING (docdb_family_id)
    LEFT JOIN field_asof fl USING (docdb_family_id)
    """


def _build_dense_pit_year_sql(
    family_summary: Path,
    status_history: Path,
    branch_history: Path,
    enriched_network: Path,
    blocking_ts: Path,
    field_ts: Path,
    member_publications: Path,
    snapshot_date: str,
    target_as_of_year: int,
    bucket_id: int | None = None,
    bucket_count: int | None = None,
) -> str:
    completeness_sum = " +\n            ".join(
        f"CASE WHEN {expr} THEN 1 ELSE 0 END" for expr in _COMPLETENESS_EXPRS
    )
    completeness_den = len(_COMPLETENESS_EXPRS)
    snapshot_year = int(snapshot_date[:4])
    bucket_filter = (
        f"AND g.docdb_family_id % {bucket_count} = {bucket_id}"
        if bucket_id is not None and bucket_count is not None
        else ""
    )
    return f"""
    WITH family_anchor AS (
        SELECT
            g.docdb_family_id,
            CASE
                WHEN {target_as_of_year} = {snapshot_year} THEN DATE '{snapshot_date}'
                ELSE MAKE_DATE({target_as_of_year}, 12, 31)
            END AS as_of_date,
            {target_as_of_year}::INTEGER AS as_of_year,
            CAST(g.family_earliest_priority_date AS DATE) AS family_earliest_priority_date,
            COALESCE(
                CAST(g.family_priority_year AS INTEGER),
                EXTRACT(year FROM CAST(g.family_earliest_priority_date AS DATE))::INTEGER
            ) AS family_priority_year
        FROM read_parquet('{family_summary}') g
        WHERE COALESCE(g.is_main_window_family, true) = true
          AND g.family_earliest_priority_date IS NOT NULL
          AND COALESCE(
                CAST(g.family_priority_year AS INTEGER),
                EXTRACT(year FROM CAST(g.family_earliest_priority_date AS DATE))::INTEGER
          ) <= {target_as_of_year}
          {bucket_filter}
    ),

    legal_asof AS (
        SELECT
            a.docdb_family_id,
            h.family_composite_status             AS family_composite_status_asof,
            h.active_jurisdiction_count::DOUBLE   AS active_jurisdiction_count_asof,
            h.active_grant_branch_count::DOUBLE   AS active_grant_branch_count_asof,
            h.lapsed_jurisdiction_count::DOUBLE   AS lapsed_jurisdiction_count_asof
        FROM family_anchor a
        INNER JOIN read_parquet('{status_history}') h USING (docdb_family_id)
        WHERE h.snapshot_year <= a.as_of_year
        QUALIFY ROW_NUMBER() OVER (PARTITION BY a.docdb_family_id ORDER BY h.snapshot_year DESC) = 1
    ),

    branch_latest_asof AS (
        SELECT
            a.docdb_family_id,
            b.jurisdiction_code
        FROM family_anchor a
        LEFT JOIN read_parquet('{branch_history}') b
            ON b.docdb_family_id = a.docdb_family_id
           AND b.snapshot_year <= a.as_of_year
           AND b.jurisdiction_code IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY a.docdb_family_id, b.jurisdiction_code
            ORDER BY b.snapshot_year DESC
        ) = 1
    ),

    coverage_asof AS (
        SELECT
            docdb_family_id,
            COUNT(DISTINCT jurisdiction_code)::DOUBLE AS family_jurisdiction_count_asof
        FROM branch_latest_asof
        GROUP BY docdb_family_id
    ),

    family_size_asof AS (
        SELECT
            a.docdb_family_id,
            COUNT(DISTINCT m.appln_id)::DOUBLE AS family_size_docdb_asof
        FROM family_anchor a
        LEFT JOIN read_parquet('{member_publications}') m
            ON m.docdb_family_id = a.docdb_family_id
           AND m.appln_id IS NOT NULL
           AND m.publn_date IS NOT NULL
           AND CAST(m.publn_date AS DATE) <= a.as_of_date
           AND CAST(m.publn_date AS DATE) < DATE '9999-01-01'
        GROUP BY a.docdb_family_id
    ),

    citation_asof AS (
        SELECT
            a.docdb_family_id,
            COUNT(DISTINCT
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN n.source_docdb_family_id END
            )::DOUBLE AS pre_asof_forward_citations_clean,
            SUM(
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN COALESCE(n.clean_edge_weight, 0.0) ELSE 0.0 END
            )::DOUBLE AS pre_asof_forward_citations_weighted,
            COUNT(DISTINCT
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN n.source_docdb_family_id END
            )::DOUBLE AS pre_asof_unique_citing_family_count,
            CASE
                WHEN COUNT(DISTINCT
                    CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                         THEN n.source_docdb_family_id END) > 0
                THEN COUNT(DISTINCT
                        CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                              AND n.citing_assignee_name IS NOT NULL
                             THEN n.citing_assignee_name END)::DOUBLE
                     / COUNT(DISTINCT
                        CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                             THEN n.source_docdb_family_id END)::DOUBLE
                ELSE NULL::DOUBLE
            END AS pre_asof_citing_assignee_diversity,
            AVG(
                CASE WHEN CAST(n.citation_date AS DATE) <= a.as_of_date
                     THEN n.clean_edge_weight END
            )::DOUBLE AS pre_asof_attacker_density_score
        FROM family_anchor a
        LEFT JOIN read_parquet('{enriched_network}') n
            ON n.cited_docdb_family_id = a.docdb_family_id
           AND NOT COALESCE(n.is_out_of_bounds, false)
           AND NOT COALESCE(n.is_intra_family_citation, false)
           AND NOT COALESCE(n.is_self_citation, false)
           AND n.citation_date IS NOT NULL
        GROUP BY a.docdb_family_id, a.as_of_date
    ),

    blocking_asof AS (
        SELECT
            a.docdb_family_id,
            b.ui_blocking_power_score            AS family_blocking_power_score_asof,
            b.overall_legal_enforceability_score AS family_enforceability_score_asof
        FROM family_anchor a
        INNER JOIN read_parquet('{blocking_ts}') b USING (docdb_family_id)
        WHERE EXTRACT(year FROM CAST(b.snapshot_date AS DATE))::INTEGER <= a.as_of_year
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY a.docdb_family_id
            ORDER BY CAST(b.snapshot_date AS DATE) DESC
        ) = 1
    ),

    field_asof AS (
        SELECT
            a.docdb_family_id,
            f.wipo_industry_code AS primary_wipo_field_asof,
            f.enforceability_contribution_score AS family_field_contribution_primary_asof,
            COUNT(DISTINCT f.wipo_industry_code) OVER (PARTITION BY a.docdb_family_id, f.snapshot_year)::DOUBLE
                AS family_tech_breadth_wipo_count_asof
        FROM family_anchor a
        INNER JOIN read_parquet('{field_ts}') f USING (docdb_family_id)
        WHERE f.snapshot_year <= a.as_of_year
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY a.docdb_family_id
            ORDER BY f.snapshot_year DESC, f.enforceability_contribution_score DESC NULLS LAST
        ) = 1
    )

    SELECT
        a.docdb_family_id,
        a.as_of_date,
        a.as_of_year,
        CAST(true AS BOOLEAN) AS is_observed_as_of_snapshot,
        CAST({target_as_of_year} = {snapshot_year} AS BOOLEAN) AS is_partial_snapshot_year,
        COALESCE(l.family_composite_status_asof, 'unknown')     AS family_composite_status_asof,
        COALESCE(l.active_jurisdiction_count_asof, 0.0)         AS active_jurisdiction_count_asof,
        COALESCE(l.active_grant_branch_count_asof, 0.0)         AS active_grant_branch_count_asof,
        COALESCE(l.lapsed_jurisdiction_count_asof, 0.0)         AS lapsed_jurisdiction_count_asof,
        COALESCE(sz.family_size_docdb_asof, 0.0)                AS family_size_docdb_asof,
        COALESCE(cov.family_jurisdiction_count_asof, 0.0)       AS family_jurisdiction_count_asof,
        CASE
            WHEN COALESCE(cov.family_jurisdiction_count_asof, 0.0) = 0.0 THEN 0.0
            ELSE COALESCE(l.active_jurisdiction_count_asof, 0.0) / cov.family_jurisdiction_count_asof
        END                                                     AS family_coverage_stability_score_asof,
        COALESCE(fl.family_tech_breadth_wipo_count_asof, 1.0)   AS family_tech_breadth_wipo_count_asof,
        fl.family_field_contribution_primary_asof,
        bk.family_blocking_power_score_asof,
        bk.family_enforceability_score_asof,
        COALESCE(c.pre_asof_forward_citations_clean, 0.0)       AS pre_asof_forward_citations_clean,
        COALESCE(c.pre_asof_forward_citations_weighted, 0.0)    AS pre_asof_forward_citations_weighted,
        CASE
            WHEN COALESCE(avg(COALESCE(c.pre_asof_forward_citations_weighted, 0.0)) OVER (
                PARTITION BY a.as_of_year, COALESCE(fl.primary_wipo_field_asof, '__unknown__')
            ), 0.0) = 0.0
            THEN COALESCE(c.pre_asof_forward_citations_weighted, 0.0)
            ELSE COALESCE(c.pre_asof_forward_citations_weighted, 0.0)
                 / avg(COALESCE(c.pre_asof_forward_citations_weighted, 0.0)) OVER (
                    PARTITION BY a.as_of_year, COALESCE(fl.primary_wipo_field_asof, '__unknown__')
                 )
        END                                                     AS family_rcf_score_asof,
        COALESCE(c.pre_asof_unique_citing_family_count, 0.0)    AS pre_asof_unique_citing_family_count,
        c.pre_asof_citing_assignee_diversity,
        c.pre_asof_attacker_density_score,
        ROUND(
            (
                {completeness_sum}
            )::DOUBLE / {completeness_den}.0,
            6
        ) AS data_completeness_pct_asof
    FROM family_anchor a
    LEFT JOIN citation_asof c USING (docdb_family_id)
    LEFT JOIN legal_asof l USING (docdb_family_id)
    LEFT JOIN coverage_asof cov USING (docdb_family_id)
    LEFT JOIN family_size_asof sz USING (docdb_family_id)
    LEFT JOIN blocking_asof bk USING (docdb_family_id)
    LEFT JOIN field_asof fl USING (docdb_family_id)
    """


def _build_classification_dense_year_sql(
    pit_dense: Path,
    family_wipo_fields: Path,
    family_ipc_cpc_canonical: Path,
    visibility_timeline: Path | None,
    target_as_of_year: int,
    bucket_id: int | None = None,
    bucket_count: int | None = None,
) -> str:
    dense_bucket_filter = ""
    if bucket_id is not None and bucket_count is not None:
        dense_bucket_filter = (
            f"AND MOD(ABS(HASH(CAST(docdb_family_id AS BIGINT))), {int(bucket_count)}) = {int(bucket_id)}"
        )
    visibility_bucket_filter = dense_bucket_filter
    if visibility_timeline is not None:
        return f"""
        WITH dense AS (
            SELECT
                docdb_family_id,
                as_of_date,
                as_of_year,
                is_observed_as_of_snapshot,
                is_partial_snapshot_year
            FROM read_parquet('{pit_dense}')
            WHERE as_of_year = {target_as_of_year}
              {dense_bucket_filter}
        ),

        visible AS (
            SELECT
                docdb_family_id,
                classification_type,
                classification_code,
                classification_label
            FROM read_parquet('{visibility_timeline}')
            WHERE first_seen_year <= {target_as_of_year}
              {visibility_bucket_filter}
        ),

        wipo AS (
            SELECT
                docdb_family_id,
                list_sort(
                    list_distinct(
                        list(classification_label) FILTER (
                            WHERE classification_type = 'WIPO_FIELD' AND classification_label IS NOT NULL AND classification_label <> ''
                        )
                    )
                ) AS covered_wipo_fields_asof
            FROM visible
            GROUP BY docdb_family_id
        ),

        ipc AS (
            SELECT
                docdb_family_id,
                list_sort(
                    list_distinct(
                        list(classification_code) FILTER (
                            WHERE classification_type = 'IPC_SUBCLASS' AND classification_code IS NOT NULL AND classification_code <> ''
                        )
                    )
                ) AS ipc_subclasses_asof
            FROM visible
            GROUP BY docdb_family_id
        ),

        cpc AS (
            SELECT
                docdb_family_id,
                list_sort(
                    list_distinct(
                        list(classification_code) FILTER (
                            WHERE classification_type = 'CPC_SECTION' AND classification_code IS NOT NULL AND classification_code <> ''
                        )
                    )
                ) AS cpc_sections_asof,
                list_sort(
                    list_distinct(
                        list(classification_code) FILTER (
                            WHERE classification_type = 'CPC_SUBCLASS' AND classification_code IS NOT NULL AND classification_code <> ''
                        )
                    )
                ) AS cpc_subclasses_asof,
                list_sort(
                    list_distinct(
                        list(classification_code) FILTER (
                            WHERE classification_type = 'CPC_MAIN_GROUP' AND classification_code IS NOT NULL AND classification_code <> ''
                        )
                    )
                ) AS cpc_main_groups_asof
            FROM visible
            GROUP BY docdb_family_id
        )

        SELECT
            d.docdb_family_id,
            d.as_of_date,
            d.as_of_year,
            d.is_observed_as_of_snapshot,
            d.is_partial_snapshot_year,
            COALESCE(w.covered_wipo_fields_asof, []::VARCHAR[]) AS covered_wipo_fields_asof,
            list_extract(COALESCE(w.covered_wipo_fields_asof, []::VARCHAR[]), 1) AS primary_wipo_field_asof,
            COALESCE(list_count(w.covered_wipo_fields_asof), 0) AS wipo_field_count_asof,
            COALESCE(i.ipc_subclasses_asof, []::VARCHAR[]) AS ipc_subclasses_asof,
            COALESCE(c.cpc_sections_asof, []::VARCHAR[]) AS cpc_sections_asof,
            COALESCE(c.cpc_subclasses_asof, []::VARCHAR[]) AS cpc_subclasses_asof,
            COALESCE(c.cpc_main_groups_asof, []::VARCHAR[]) AS cpc_main_groups_asof,
            COALESCE(list_count(i.ipc_subclasses_asof), 0) AS ipc_subclass_count_asof,
            COALESCE(list_count(c.cpc_sections_asof), 0) AS cpc_section_count_asof,
            COALESCE(list_count(c.cpc_subclasses_asof), 0) AS cpc_subclass_count_asof,
            COALESCE(list_count(c.cpc_main_groups_asof), 0) AS cpc_main_group_count_asof,
            'first_seen_classification_visibility' AS classification_visibility_policy,
            CAST(true AS BOOLEAN) AS classification_membership_replayed_to_history,
            CAST(false AS BOOLEAN) AS historical_classification_truth_supported
        FROM dense d
        LEFT JOIN wipo w USING (docdb_family_id)
        LEFT JOIN ipc i USING (docdb_family_id)
        LEFT JOIN cpc c USING (docdb_family_id)
        """
    return f"""
    WITH dense AS (
        SELECT
            docdb_family_id,
            as_of_date,
            as_of_year,
            is_observed_as_of_snapshot,
            is_partial_snapshot_year
        FROM read_parquet('{pit_dense}')
        WHERE as_of_year = {target_as_of_year}
          {dense_bucket_filter}
    ),

    wipo AS (
        SELECT
            docdb_family_id,
            COALESCE(
                list_sort(list_distinct(covered_wipo_fields)),
                []::VARCHAR[]
            ) AS covered_wipo_fields_asof,
            COALESCE(
                primary_wipo_field,
                list_extract(
                    COALESCE(list_sort(list_distinct(covered_wipo_fields)), []::VARCHAR[]),
                    1
                )
            ) AS primary_wipo_field_asof,
            COALESCE(
                CAST(family_tech_breadth_wipo_count AS INTEGER),
                list_count(COALESCE(list_sort(list_distinct(covered_wipo_fields)), []::VARCHAR[])),
                0
            ) AS wipo_field_count_asof
        FROM read_parquet('{family_wipo_fields}')
    ),

    classification AS (
        SELECT
            docdb_family_id,
            list_sort(
                list_distinct(
                    list_filter(
                        list_transform(
                            COALESCE(ipc_symbols, []::VARCHAR[]),
                            x -> regexp_extract(x, '^([A-Z][0-9]{{2}}[A-Z])', 1)
                        ),
                        x -> x <> ''
                    )
                )
            ) AS ipc_subclasses_asof,
            list_sort(
                list_distinct(
                    list_filter(
                        list_transform(
                            COALESCE(cpc_symbols, []::VARCHAR[]),
                            x -> regexp_extract(x, '^([A-Z])', 1)
                        ),
                        x -> x <> ''
                    )
                )
            ) AS cpc_sections_asof,
            list_sort(
                list_distinct(
                    list_filter(
                        list_transform(
                            COALESCE(cpc_symbols, []::VARCHAR[]),
                            x -> regexp_extract(x, '^([A-Z][0-9]{{2}}[A-Z])', 1)
                        ),
                        x -> x <> ''
                    )
                )
            ) AS cpc_subclasses_asof,
            list_sort(
                list_distinct(
                    list_filter(
                        list_transform(
                            COALESCE(cpc_symbols, []::VARCHAR[]),
                            x -> regexp_replace(
                                regexp_extract(x, '^([A-Z][0-9]{{2}}[A-Z][0-9]+/[0-9]+)', 1),
                                '/[0-9]+$',
                                '/00'
                            )
                        ),
                        x -> x <> ''
                    )
                )
            ) AS cpc_main_groups_asof
        FROM read_parquet('{family_ipc_cpc_canonical}')
    )

    SELECT
        d.docdb_family_id,
        d.as_of_date,
        d.as_of_year,
        d.is_observed_as_of_snapshot,
        d.is_partial_snapshot_year,
        COALESCE(w.covered_wipo_fields_asof, []::VARCHAR[]) AS covered_wipo_fields_asof,
        w.primary_wipo_field_asof,
        COALESCE(w.wipo_field_count_asof, 0) AS wipo_field_count_asof,
        COALESCE(cl.ipc_subclasses_asof, []::VARCHAR[]) AS ipc_subclasses_asof,
        COALESCE(cl.cpc_sections_asof, []::VARCHAR[]) AS cpc_sections_asof,
        COALESCE(cl.cpc_subclasses_asof, []::VARCHAR[]) AS cpc_subclasses_asof,
        COALESCE(cl.cpc_main_groups_asof, []::VARCHAR[]) AS cpc_main_groups_asof,
        COALESCE(list_count(cl.ipc_subclasses_asof), 0) AS ipc_subclass_count_asof,
        COALESCE(list_count(cl.cpc_sections_asof), 0) AS cpc_section_count_asof,
        COALESCE(list_count(cl.cpc_subclasses_asof), 0) AS cpc_subclass_count_asof,
        COALESCE(list_count(cl.cpc_main_groups_asof), 0) AS cpc_main_group_count_asof,
        'stable_family_classification_replay' AS classification_visibility_policy,
        CAST(true AS BOOLEAN) AS classification_membership_replayed_to_history,
        CAST(false AS BOOLEAN) AS historical_classification_truth_supported
    FROM dense d
    LEFT JOIN wipo w USING (docdb_family_id)
    LEFT JOIN classification cl USING (docdb_family_id)
    """


def _build_classification_visibility_timeline_sql(
    member_publications: Path,
    appln_cpc: Path,
    appln_ipc: Path,
    appln_techn_field: Path,
    ref_techn_field_ipc: Path,
    bucket_id: int | None = None,
    bucket_count: int | None = None,
) -> str:
    bucket_filter = ""
    if bucket_id is not None and bucket_count is not None:
        bucket_filter = (
            f"AND MOD(ABS(HASH(CAST(docdb_family_id AS BIGINT))), {int(bucket_count)}) = {int(bucket_id)}"
        )
    return f"""
    WITH member_pub AS (
        SELECT DISTINCT
            appln_id,
            docdb_family_id,
            CAST(publn_date AS DATE) AS publn_date
        FROM read_parquet('{member_publications}')
        WHERE appln_id IS NOT NULL
          AND docdb_family_id IS NOT NULL
          AND publn_date IS NOT NULL
          AND CAST(publn_date AS DATE) < DATE '9999-01-01'
          {bucket_filter}
    ),

    cpc_raw AS (
        SELECT
            p.docdb_family_id,
            p.publn_date,
            regexp_replace(CAST(cpc_class_symbol AS VARCHAR), '\\s+', '', 'g') AS cpc_symbol
        FROM read_parquet('{appln_cpc}') c
        JOIN member_pub p USING (appln_id)
        WHERE cpc_class_symbol IS NOT NULL
    ),

    ipc_raw AS (
        SELECT
            p.docdb_family_id,
            p.publn_date,
            regexp_replace(CAST(ipc_class_symbol AS VARCHAR), '\\s+', '', 'g') AS ipc_symbol
        FROM read_parquet('{appln_ipc}') i
        JOIN member_pub p USING (appln_id)
        WHERE ipc_class_symbol IS NOT NULL
    ),

    wipo_raw AS (
        SELECT DISTINCT
            p.docdb_family_id,
            p.publn_date,
            CAST(r.wipo_industry_code AS VARCHAR) AS wipo_industry_code
        FROM read_parquet('{appln_techn_field}') t
        JOIN member_pub p USING (appln_id)
        JOIN read_parquet('{ref_techn_field_ipc}') r
          ON CAST(t.techn_field_nr AS BIGINT) = CAST(r.techn_field_nr AS BIGINT)
        WHERE r.wipo_industry_code IS NOT NULL
    ),

    unified AS (
        SELECT
            docdb_family_id,
            'WIPO_FIELD' AS classification_type,
            wipo_industry_code AS classification_code,
            wipo_industry_code AS classification_label,
            publn_date
        FROM wipo_raw

        UNION ALL

        SELECT
            docdb_family_id,
            'IPC_SUBCLASS' AS classification_type,
            regexp_extract(ipc_symbol, '^([A-Z][0-9]{{2}}[A-Z])', 1) AS classification_code,
            regexp_extract(ipc_symbol, '^([A-Z][0-9]{{2}}[A-Z])', 1) AS classification_label,
            publn_date
        FROM ipc_raw
        WHERE regexp_extract(ipc_symbol, '^([A-Z][0-9]{{2}}[A-Z])', 1) <> ''

        UNION ALL

        SELECT
            docdb_family_id,
            'CPC_SECTION' AS classification_type,
            regexp_extract(cpc_symbol, '^([A-Z])', 1) AS classification_code,
            regexp_extract(cpc_symbol, '^([A-Z])', 1) AS classification_label,
            publn_date
        FROM cpc_raw
        WHERE regexp_extract(cpc_symbol, '^([A-Z])', 1) <> ''

        UNION ALL

        SELECT
            docdb_family_id,
            'CPC_SUBCLASS' AS classification_type,
            regexp_extract(cpc_symbol, '^([A-Z][0-9]{{2}}[A-Z])', 1) AS classification_code,
            regexp_extract(cpc_symbol, '^([A-Z][0-9]{{2}}[A-Z])', 1) AS classification_label,
            publn_date
        FROM cpc_raw
        WHERE regexp_extract(cpc_symbol, '^([A-Z][0-9]{{2}}[A-Z])', 1) <> ''

        UNION ALL

        SELECT
            docdb_family_id,
            'CPC_MAIN_GROUP' AS classification_type,
            regexp_replace(
                regexp_extract(cpc_symbol, '^([A-Z][0-9]{{2}}[A-Z][0-9]+/[0-9]+)', 1),
                '/[0-9]+$',
                '/00'
            ) AS classification_code,
            regexp_replace(
                regexp_extract(cpc_symbol, '^([A-Z][0-9]{{2}}[A-Z][0-9]+/[0-9]+)', 1),
                '/[0-9]+$',
                '/00'
            ) AS classification_label,
            publn_date
        FROM cpc_raw
        WHERE regexp_extract(cpc_symbol, '^([A-Z][0-9]{{2}}[A-Z][0-9]+/[0-9]+)', 1) <> ''
    )

    SELECT
        docdb_family_id,
        classification_type,
        classification_code,
        classification_label,
        MIN(publn_date) AS first_seen_date,
        MIN(EXTRACT(year FROM publn_date))::INTEGER AS first_seen_year,
        'member_publication_first_seen' AS visibility_source,
        CAST(false AS BOOLEAN) AS historical_classification_truth_supported
    FROM unified
    WHERE classification_code IS NOT NULL
      AND classification_code <> ''
    GROUP BY
        docdb_family_id,
        classification_type,
        classification_code,
        classification_label
    """


def _build_classification_dense_audit(
    con: duckdb.DuckDBPyConnection,
    classification_table: Path,
    pit_dense_table: Path,
) -> dict[str, int | str]:
    row = con.execute(
        f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT (docdb_family_id, as_of_year)) AS duplicate_family_year_keys,
            COUNT(*) FILTER (WHERE list_count(covered_wipo_fields_asof) > 0) AS rows_with_wipo_fields,
            COUNT(*) FILTER (WHERE list_count(cpc_main_groups_asof) > 0) AS rows_with_cpc_main_groups,
            COUNT(*) FILTER (WHERE primary_wipo_field_asof IS NOT NULL) AS rows_with_primary_wipo_field,
            COUNT(*) FILTER (WHERE historical_classification_truth_supported) AS rows_with_historical_truth_supported,
            COUNT(*) FILTER (WHERE classification_membership_replayed_to_history) AS rows_replayed_to_history,
            MIN(as_of_year) AS min_as_of_year,
            MAX(as_of_year) AS max_as_of_year
        FROM read_parquet('{classification_table}')
        """
    ).fetchone()
    backbone_row_count = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{pit_dense_table}')"
    ).fetchone()[0]
    multi_year_families = con.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT docdb_family_id
            FROM read_parquet('{classification_table}')
            GROUP BY docdb_family_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    policy_row = con.execute(
        f"""
        SELECT classification_visibility_policy, COUNT(*) AS row_count
        FROM read_parquet('{classification_table}')
        GROUP BY classification_visibility_policy
        ORDER BY row_count DESC, classification_visibility_policy
        LIMIT 1
        """
    ).fetchone()
    return {
        "row_count": int(row[0]),
        "dense_backbone_row_count": int(backbone_row_count),
        "duplicate_family_year_keys": int(row[1]),
        "rows_with_wipo_fields": int(row[2]),
        "rows_with_cpc_main_groups": int(row[3]),
        "rows_with_primary_wipo_field": int(row[4]),
        "rows_with_historical_truth_supported": int(row[5]),
        "rows_replayed_to_history": int(row[6]),
        "min_as_of_year": int(row[7]),
        "max_as_of_year": int(row[8]),
        "families_with_multiple_year_rows": int(multi_year_families),
        "classification_visibility_policy": str(policy_row[0]) if policy_row is not None else "unknown",
    }


def _build_classification_visibility_audit(
    con: duckdb.DuckDBPyConnection,
    visibility_table: Path,
) -> dict[str, int | str]:
    row = con.execute(
        f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(*) FILTER (WHERE classification_type = 'WIPO_FIELD') AS wipo_rows,
            COUNT(*) FILTER (WHERE classification_type = 'IPC_SUBCLASS') AS ipc_rows,
            COUNT(*) FILTER (WHERE classification_type = 'CPC_SECTION') AS cpc_section_rows,
            COUNT(*) FILTER (WHERE classification_type = 'CPC_SUBCLASS') AS cpc_subclass_rows,
            COUNT(*) FILTER (WHERE classification_type = 'CPC_MAIN_GROUP') AS cpc_main_group_rows,
            COUNT(*) - COUNT(DISTINCT (docdb_family_id, classification_type, classification_code)) AS duplicate_family_classification_keys,
            MIN(first_seen_year) AS min_first_seen_year,
            MAX(first_seen_year) AS max_first_seen_year
        FROM read_parquet('{visibility_table}')
        """
    ).fetchone()
    families = con.execute(
        f"SELECT COUNT(DISTINCT docdb_family_id) FROM read_parquet('{visibility_table}')"
    ).fetchone()[0]
    return {
        "row_count": int(row[0]),
        "wipo_rows": int(row[1]),
        "ipc_rows": int(row[2]),
        "cpc_section_rows": int(row[3]),
        "cpc_subclass_rows": int(row[4]),
        "cpc_main_group_rows": int(row[5]),
        "duplicate_family_classification_keys": int(row[6]),
        "min_first_seen_year": int(row[7]),
        "max_first_seen_year": int(row[8]),
        "families_with_classification_visibility": int(families),
        "classification_visibility_policy": "first_seen_classification_visibility",
    }


def _build_pit_audit(con: duckdb.DuckDBPyConnection, pit_table: Path, family_summary: Path, snapshot_date: str) -> dict[str, object]:
    audit: dict[str, object] = {
        "snapshot_date": snapshot_date,
        "pit_table": str(pit_table),
    }
    rows, distinct_keys, dup_keys = con.execute(
        f"""
        select
            count(*) as rows,
            count(distinct (docdb_family_id, as_of_year)) as distinct_keys,
            count(*) - count(distinct (docdb_family_id, as_of_year)) as duplicate_keys
        from read_parquet('{pit_table}')
        """
    ).fetchone()
    audit["row_count"] = int(rows)
    audit["distinct_family_year_keys"] = int(distinct_keys)
    audit["duplicate_family_year_keys"] = int(dup_keys)

    anchor_row = con.execute(
        f"""
        with base as (
            select
                p.docdb_family_id,
                cast(p.as_of_date as date) as as_of_date,
                p.as_of_year,
                cast(g.family_earliest_priority_date as date) as priority_date,
                cast(cast(g.family_earliest_priority_date as date) + interval '2 years' as date) as expected_as_of
            from read_parquet('{pit_table}') p
            join read_parquet('{family_summary}') g using (docdb_family_id)
        )
        select
            sum(case when as_of_date <> expected_as_of then 1 else 0 end) as mismatched_as_of_date,
            sum(case when as_of_year <> extract(year from expected_as_of) then 1 else 0 end) as mismatched_as_of_year,
            sum(case when as_of_date < priority_date then 1 else 0 end) as before_priority,
            sum(case when as_of_date > date '{snapshot_date}' then 1 else 0 end) as future_anchor_rows
        from base
        """
    ).fetchone()
    audit["anchor_date_mismatches"] = int(anchor_row[0])
    audit["anchor_year_mismatches"] = int(anchor_row[1])
    audit["as_of_before_priority_rows"] = int(anchor_row[2])
    audit["future_anchor_rows"] = int(anchor_row[3])

    sanity_row = con.execute(
        f"""
        select
            sum(case when active_jurisdiction_count_asof < 0 then 1 else 0 end) as neg_active_j,
            sum(case when active_grant_branch_count_asof < 0 then 1 else 0 end) as neg_active_grant,
            sum(case when lapsed_jurisdiction_count_asof < 0 then 1 else 0 end) as neg_lapsed,
            sum(case when family_jurisdiction_count_asof < 0 then 1 else 0 end) as neg_family_jur,
            sum(case when family_coverage_stability_score_asof < 0 or family_coverage_stability_score_asof > 1 then 1 else 0 end) as bad_coverage,
            sum(case when pre_asof_forward_citations_clean < 0 then 1 else 0 end) as neg_cits,
            sum(case when pre_asof_forward_citations_weighted < 0 then 1 else 0 end) as neg_weighted,
            sum(case when pre_asof_unique_citing_family_count < 0 then 1 else 0 end) as neg_unique,
            sum(case when pre_asof_citing_assignee_diversity < 0 or pre_asof_citing_assignee_diversity > 1 then 1 else 0 end) as bad_diversity
        from read_parquet('{pit_table}')
        """
    ).fetchone()
    audit["negative_or_invalid_counts"] = {
        "active_jurisdiction": int(sanity_row[0]),
        "active_grant_branch": int(sanity_row[1]),
        "lapsed_jurisdiction": int(sanity_row[2]),
        "family_jurisdiction": int(sanity_row[3]),
        "coverage_stability_out_of_range": int(sanity_row[4]),
        "pre_asof_forward_citations_clean": int(sanity_row[5]),
        "pre_asof_forward_citations_weighted": int(sanity_row[6]),
        "pre_asof_unique_citing_family_count": int(sanity_row[7]),
        "pre_asof_citing_assignee_diversity_out_of_range": int(sanity_row[8]),
    }
    return audit


def _build_dense_pit_audit(
    con: duckdb.DuckDBPyConnection,
    pit_table: Path,
    family_summary: Path,
    snapshot_date: str,
) -> dict[str, object]:
    snapshot_year = int(snapshot_date[:4])
    audit: dict[str, object] = {
        "snapshot_date": snapshot_date,
        "snapshot_year": snapshot_year,
        "pit_table": str(pit_table),
    }
    row = con.execute(
        f"""
        with base as (
            select
                p.docdb_family_id,
                p.as_of_year,
                cast(g.family_priority_year as integer) as family_priority_year,
                cast(g.family_earliest_priority_date as date) as priority_date,
                cast(p.as_of_date as date) as as_of_date,
                p.is_partial_snapshot_year
            from read_parquet('{pit_table}') p
            join read_parquet('{family_summary}') g using (docdb_family_id)
        )
        select
            count(*) as rows,
            count(distinct (docdb_family_id, as_of_year)) as distinct_keys,
            count(*) - count(distinct (docdb_family_id, as_of_year)) as duplicate_keys,
            min(as_of_year) as min_year,
            max(as_of_year) as max_year,
            sum(case when as_of_year < family_priority_year then 1 else 0 end) as before_priority_year_rows,
            sum(case when is_partial_snapshot_year then 1 else 0 end) as partial_snapshot_year_rows,
            count(distinct case when as_of_year = {snapshot_year} then docdb_family_id end) as families_in_current_partial_year
        from base
        """
    ).fetchone()
    audit["row_count"] = int(row[0])
    audit["distinct_family_year_keys"] = int(row[1])
    audit["duplicate_family_year_keys"] = int(row[2])
    audit["min_as_of_year"] = int(row[3]) if row[3] is not None else None
    audit["max_as_of_year"] = int(row[4]) if row[4] is not None else None
    audit["before_priority_year_rows"] = int(row[5])
    audit["partial_snapshot_year_rows"] = int(row[6])
    audit["families_in_current_partial_year"] = int(row[7])
    multi_year = con.execute(
        f"""
        select count(*)
        from (
            select docdb_family_id, count(distinct as_of_year) as year_count
            from read_parquet('{pit_table}')
            group by 1
            having year_count > 1
        )
        """
    ).fetchone()[0]
    audit["families_with_multiple_year_rows"] = int(multi_year)
    sanity_row = con.execute(
        f"""
        select
            sum(case when active_jurisdiction_count_asof < 0 then 1 else 0 end) as neg_active_j,
            sum(case when active_grant_branch_count_asof < 0 then 1 else 0 end) as neg_active_grant,
            sum(case when lapsed_jurisdiction_count_asof < 0 then 1 else 0 end) as neg_lapsed,
            sum(case when family_jurisdiction_count_asof < 0 then 1 else 0 end) as neg_family_jur,
            sum(case when family_coverage_stability_score_asof < 0 or family_coverage_stability_score_asof > 1 then 1 else 0 end) as bad_coverage,
            sum(case when pre_asof_forward_citations_clean < 0 then 1 else 0 end) as neg_cits,
            sum(case when pre_asof_forward_citations_weighted < 0 then 1 else 0 end) as neg_weighted,
            sum(case when pre_asof_unique_citing_family_count < 0 then 1 else 0 end) as neg_unique,
            sum(case when pre_asof_citing_assignee_diversity < 0 or pre_asof_citing_assignee_diversity > 1 then 1 else 0 end) as bad_diversity
        from read_parquet('{pit_table}')
        """
    ).fetchone()
    audit["negative_or_invalid_counts"] = {
        "active_jurisdiction": int(sanity_row[0]),
        "active_grant_branch": int(sanity_row[1]),
        "lapsed_jurisdiction": int(sanity_row[2]),
        "family_jurisdiction": int(sanity_row[3]),
        "coverage_stability_out_of_range": int(sanity_row[4]),
        "pre_asof_forward_citations_clean": int(sanity_row[5]),
        "pre_asof_forward_citations_weighted": int(sanity_row[6]),
        "pre_asof_unique_citing_family_count": int(sanity_row[7]),
        "pre_asof_citing_assignee_diversity_out_of_range": int(sanity_row[8]),
    }
    return audit


def build_silver_family_pit(settings: BuildSettings) -> StageResult:
    """Build silver_family_feature_snapshot_pit.parquet.

    Grain: (docdb_family_id, as_of_date) where as_of_date = family_earliest_priority_date + 2 years.
    Provides point-in-time safe legal state, citation, and blocking power features for Phase 03 ML.
    """
    result = StageResult(
        stage="silver-pit",
        status="success",
        summary=(
            "Built silver_family_feature_snapshot_pit.parquet with point-in-time safe features "
            "for each in-scope family at as_of_date = priority_date + 2 years."
        ),
        methods=[
            "Legal state (composite_status, active_jurisdiction_count, active_grant_branch_count, lapsed_jurisdiction_count) "
            "derived from silver_family_status_history at the nearest snapshot_year <= as_of_year.",
            "Pre-as_of citation metrics (forward_citations_clean, weighted, unique_citing_family_count, "
            "citing_assignee_diversity, attacker_density_score) derived from silver_enriched_citation_network "
            "filtering citation_date <= as_of_date.",
            "Blocking power (family_blocking_power_score_asof, family_enforceability_score_asof) "
            "derived from gold_family_blocking_power_timeseries at the nearest snapshot before as_of_year.",
            "Primary field contribution and WIPO breadth derived from gold_family_field_contributions_timeseries at the nearest snapshot_year <= as_of_year.",
            "family_size_docdb_asof derived from distinct appln_id values in silver_family_member_publications with publn_date <= as_of_date.",
            "family_jurisdiction_count_asof derived from silver_branch_status_history_dense at the nearest snapshot_year <= as_of_year.",
            "family_coverage_stability_score_asof = active_jurisdiction_count_asof / family_jurisdiction_count_asof.",
            "A persisted JSON audit is written beside the PIT parquet to validate anchor-date correctness, uniqueness, and basic value sanity.",
        ],
        calculations=[
            "as_of_date = CAST(family_earliest_priority_date AS DATE) + INTERVAL '2 years'.",
            "family_rcf_score_asof = pre_asof_forward_citations_weighted / cohort_average_pre_asof_forward_citations_weighted within the same as_of_year.",
            "data_completeness_pct_asof is the fraction of 12 tracked PIT columns that are non-null "
            "before COALESCE defaults are applied.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
            "docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md",
        ],
        downstream_impacts=[
            "ml-phase03-family-forecast: replaces current-state leakage features with PIT equivalents when this table is present.",
        ],
    )

    required = _required_inputs(settings)
    missing = [str(p) for p in required.values() if not p.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing required inputs for silver-pit: {missing}")
        return result

    ensure_dir(settings.silver_dir)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    audit_table = settings.silver_dir / AUDIT_TABLE
    temp_dir = ensure_dir(settings.silver_dir / "_duckdb_tmp_pit")
    chunk_dir = ensure_dir(settings.silver_dir / "_pit_chunks")

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET threads=2")
    con.execute("SET memory_limit='7GB'")
    con.execute(f"SET temp_directory='{temp_dir}'")

    year_rows = con.execute(
        f"""
        select distinct
            extract(year from cast(family_earliest_priority_date as date) + interval '2 years')::integer as as_of_year
        from read_parquet('{required["family_summary"]}')
        where coalesce(is_main_window_family, true) = true
          and family_earliest_priority_date is not null
        order by 1
        """
    ).fetchall()
    chunk_paths: list[Path] = []
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"silver_family_feature_snapshot_pit_{int(as_of_year)}.parquet"
        if chunk_path.exists():
            chunk_path.unlink()
        sql = _build_pit_sql(
            family_summary=required["family_summary"],
            status_history=required["status_history"],
            branch_history=required["branch_history"],
            enriched_network=required["enriched_network"],
            blocking_ts=required["blocking_ts"],
            field_ts=required["field_ts"],
            member_publications=required["member_publications"],
            snapshot_date=settings.snapshot_date,
            target_as_of_year=int(as_of_year),
        )
        con.execute(
            f"COPY ({sql}) TO '{chunk_path}' (FORMAT parquet, COMPRESSION zstd)"
        )
        chunk_paths.append(chunk_path)

    if pit_table.exists():
        pit_table.unlink()
    con.execute(
        f"COPY (SELECT * FROM read_parquet('{chunk_dir / 'silver_family_feature_snapshot_pit_*.parquet'}')) TO '{pit_table}' "
        "(FORMAT parquet, COMPRESSION zstd)"
    )
    audit_payload = _build_pit_audit(con, pit_table, required["family_summary"], settings.snapshot_date)
    if audit_table.exists():
        audit_table.unlink()
    write_text_json(audit_table, audit_payload)

    row_count = parquet_row_count(pit_table)
    result.outputs.append(str(pit_table))
    result.outputs.append(str(audit_table))
    result.metrics["silver_family_feature_snapshot_pit_rows"] = row_count
    result.metrics["silver_family_feature_snapshot_pit_future_anchor_rows"] = audit_payload["future_anchor_rows"]
    result.metrics["silver_family_feature_snapshot_pit_duplicate_family_year_keys"] = audit_payload["duplicate_family_year_keys"]
    return result


def build_silver_family_pit_dense(settings: BuildSettings) -> StageResult:
    """Build silver_family_feature_snapshot_pit_dense.parquet.

    Grain: (docdb_family_id, as_of_year) with one observed row per family-year from family_priority_year
    through the current snapshot year. This is the dense PIT layer for family over-time product behavior.
    """
    result = StageResult(
        stage="silver-pit-dense",
        status="success",
        summary=(
            "Built silver_family_feature_snapshot_pit_dense.parquet with observed family-year PIT rows "
            "for historical compare, reports, and portfolio-over-time product behavior."
        ),
        methods=[
            "Generated one observed PIT row per family and as_of_year from family_priority_year through snapshot_year.",
            "For each year, legal, blocking, field, citation, and coverage metrics are taken from the latest history or event evidence available at or before that year-end.",
            "The current snapshot year uses snapshot_date rather than synthetic year-end so current-year product views stay aligned with the actual ETL snapshot.",
            "A persisted JSON audit is written beside the dense PIT parquet to validate uniqueness, year range, multi-year family coverage, and value sanity.",
        ],
        calculations=[
            "as_of_date = MAKE_DATE(as_of_year, 12, 31) except for the current snapshot year where as_of_date = snapshot_date.",
            "family_rcf_score_asof is normalized within the same as_of_year and primary field cohort.",
            "data_completeness_pct_asof is the fraction of 12 tracked PIT columns that are non-null before COALESCE defaults are applied.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md",
            "docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md",
        ],
        downstream_impacts=[
            "gold-family-compare-pit: should use this dense PIT layer when present for current-vs-selected-year family comparisons.",
            "Historical compare and report flows can now use family-year rows rather than one anchored checkpoint per family.",
        ],
    )

    required = _required_inputs(settings)
    missing = [str(p) for p in required.values() if not p.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing required inputs for silver-pit-dense: {missing}")
        return result

    ensure_dir(settings.silver_dir)
    pit_table = settings.silver_dir / DENSE_OUTPUT_TABLE
    audit_table = settings.silver_dir / DENSE_AUDIT_TABLE
    temp_dir = ensure_dir(settings.silver_dir / "_duckdb_tmp_pit_dense")
    chunk_dir = ensure_dir(settings.silver_dir / "_pit_dense_chunks")

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET threads=2")
    con.execute("SET memory_limit='8GB'")
    con.execute(f"SET temp_directory='{temp_dir}'")

    min_year_row = con.execute(
        f"""
        select
            min(
                coalesce(
                    cast(family_priority_year as integer),
                    extract(year from cast(family_earliest_priority_date as date))::integer
                )
            ) as min_priority_year
        from read_parquet('{required["family_summary"]}')
        where coalesce(is_main_window_family, true) = true
          and family_earliest_priority_date is not null
        """
    ).fetchone()
    if min_year_row[0] is None:
        result.status = "failed"
        result.warnings.append("No eligible families found for silver-pit-dense.")
        return result

    snapshot_year = int(settings.snapshot_date[:4])
    start_year = max(settings.year_window_start, int(min_year_row[0]))
    chunk_paths: list[Path] = []
    for stale in chunk_dir.glob("silver_family_feature_snapshot_pit_dense_*.parquet"):
        stale.unlink()
    for as_of_year in range(start_year, snapshot_year + 1):
        for bucket_id in range(DENSE_BUCKET_COUNT):
            chunk_path = chunk_dir / f"silver_family_feature_snapshot_pit_dense_{int(as_of_year)}_bucket_{bucket_id:02d}.parquet"
            sql = _build_dense_pit_year_sql(
                family_summary=required["family_summary"],
                status_history=required["status_history"],
                branch_history=required["branch_history"],
                enriched_network=required["enriched_network"],
                blocking_ts=required["blocking_ts"],
                field_ts=required["field_ts"],
                member_publications=required["member_publications"],
                snapshot_date=settings.snapshot_date,
                target_as_of_year=int(as_of_year),
                bucket_id=bucket_id,
                bucket_count=DENSE_BUCKET_COUNT,
            )
            con.execute(f"COPY ({sql}) TO '{chunk_path}' (FORMAT parquet, COMPRESSION zstd)")
            chunk_paths.append(chunk_path)

    if pit_table.exists():
        pit_table.unlink()
    con.execute(
        f"COPY (SELECT * FROM read_parquet('{chunk_dir / 'silver_family_feature_snapshot_pit_dense_*_bucket_*.parquet'}')) TO '{pit_table}' "
        "(FORMAT parquet, COMPRESSION zstd)"
    )
    audit_payload = _build_dense_pit_audit(con, pit_table, required["family_summary"], settings.snapshot_date)
    if audit_table.exists():
        audit_table.unlink()
    write_text_json(audit_table, audit_payload)

    row_count = parquet_row_count(pit_table)
    result.outputs.append(str(pit_table))
    result.outputs.append(str(audit_table))
    result.metrics["silver_family_feature_snapshot_pit_dense_rows"] = row_count
    result.metrics["silver_family_feature_snapshot_pit_dense_duplicate_family_year_keys"] = audit_payload["duplicate_family_year_keys"]
    result.metrics["silver_family_feature_snapshot_pit_dense_families_with_multiple_year_rows"] = audit_payload["families_with_multiple_year_rows"]
    return result


def build_silver_family_classification_pit_dense(settings: BuildSettings) -> StageResult:
    """Build silver_family_classification_pit_dense.parquet.

    Grain: (docdb_family_id, as_of_year) mirroring dense family PIT.
    Prefers first-seen classification visibility when available, otherwise falls back to stable family replay.
    """
    result = StageResult(
        stage="silver-pit-classification-dense",
        status="success",
        summary=(
            "Built silver_family_classification_pit_dense.parquet with dense family-year WIPO/CPC "
            "classification membership for family, portfolio, and market chronology surfaces."
        ),
        methods=[
            "Uses silver_family_feature_snapshot_pit_dense as the family-year backbone so classification rows stay aligned with the existing PIT grain.",
            "Prefers silver_family_classification_visibility_timeline so WIPO/CPC membership appears only after its first visible member-publication year.",
            "Falls back to stable family-level WIPO and CPC replay when the visibility timeline is not yet available.",
            "Derives CPC sections, subclasses, and main groups from canonical family CPC symbols.",
            "Writes a persisted JSON audit beside the parquet to validate dense PIT parity, uniqueness, and classification coverage.",
        ],
        calculations=[
            "When the visibility timeline exists, covered_wipo_fields_asof and CPC arrays only include codes with first_seen_year <= as_of_year.",
            "Otherwise covered_wipo_fields_asof and primary_wipo_field_asof come from silver_family_wipo_fields and are replayed across PIT years.",
            "cpc_main_groups_asof normalizes CPC symbols to main-group form by replacing the subgroup suffix with '/00'.",
            "classification_visibility_policy is first_seen_classification_visibility when the timeline is used, otherwise stable_family_classification_replay.",
        ],
        doc_refs=[
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md",
            "docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md",
            "docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md",
        ],
        downstream_impacts=[
            "gold_family_classification_mix_pit can use this as the family-year classification basis.",
            "gold_portfolio_classification_mix_pit can aggregate this with explicit current-owner replay caveats.",
            "gold_market_cpc_trend_pit can use the same CPC/WIPO chronology for CPC-within-field trends and PIT importance views.",
        ],
    )

    required = _required_classification_inputs(settings)
    missing = [str(p) for p in required.values() if not p.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing required inputs for silver-pit-classification-dense: {missing}")
        return result
    visibility_timeline = settings.silver_dir / CLASSIFICATION_VISIBILITY_OUTPUT_TABLE

    ensure_dir(settings.silver_dir)
    classification_table = settings.silver_dir / CLASSIFICATION_DENSE_OUTPUT_TABLE
    audit_table = settings.silver_dir / CLASSIFICATION_DENSE_AUDIT_TABLE
    temp_dir = ensure_dir(settings.silver_dir / "_duckdb_tmp_pit_classification_dense")
    chunk_dir = ensure_dir(settings.silver_dir / "_pit_classification_dense_chunks")

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    # Classification PIT rebuild is memory-heavy once the first-seen timeline is applied.
    # Keep threads conservative and split by more family hash buckets to avoid OOM on later years.
    con.execute("SET threads=2")
    con.execute("SET memory_limit='8GB'")
    con.execute(f"SET temp_directory='{temp_dir}'")

    year_rows = con.execute(
        f"""
        SELECT DISTINCT as_of_year
        FROM read_parquet('{required["pit_dense"]}')
        ORDER BY 1
        """
    ).fetchall()
    chunk_paths: list[Path] = []
    for stale in chunk_dir.glob("silver_family_classification_pit_dense_*.parquet"):
        stale.unlink()
    for (as_of_year,) in year_rows:
        for bucket_id in range(CLASSIFICATION_DENSE_BUCKET_COUNT):
            chunk_path = (
                chunk_dir
                / f"silver_family_classification_pit_dense_{int(as_of_year)}_bucket_{bucket_id:02d}.parquet"
            )
            sql = _build_classification_dense_year_sql(
                pit_dense=required["pit_dense"],
                family_wipo_fields=required["family_wipo_fields"],
                family_ipc_cpc_canonical=required["family_ipc_cpc_canonical"],
                visibility_timeline=visibility_timeline if visibility_timeline.exists() else None,
                target_as_of_year=int(as_of_year),
                bucket_id=bucket_id,
                bucket_count=CLASSIFICATION_DENSE_BUCKET_COUNT,
            )
            con.execute(
                f"COPY ({sql}) TO '{chunk_path}' (FORMAT parquet, COMPRESSION zstd)"
            )
            chunk_paths.append(chunk_path)

    if classification_table.exists():
        classification_table.unlink()
    con.execute(
        f"COPY (SELECT * FROM read_parquet('{chunk_dir / 'silver_family_classification_pit_dense_*_bucket_*.parquet'}')) "
        f"TO '{classification_table}' (FORMAT parquet, COMPRESSION zstd)"
    )
    audit_payload = _build_classification_dense_audit(
        con,
        classification_table,
        required["pit_dense"],
    )
    if audit_table.exists():
        audit_table.unlink()
    write_text_json(audit_table, audit_payload)

    row_count = parquet_row_count(classification_table)
    result.outputs.append(str(classification_table))
    result.outputs.append(str(audit_table))
    result.metrics["silver_family_classification_pit_dense_rows"] = row_count
    result.metrics["silver_family_classification_pit_dense_duplicate_family_year_keys"] = audit_payload["duplicate_family_year_keys"]
    result.metrics["silver_family_classification_pit_dense_rows_with_cpc_main_groups"] = audit_payload["rows_with_cpc_main_groups"]
    result.metrics["silver_family_classification_pit_dense_visibility_timeline_used"] = visibility_timeline.exists()
    if not visibility_timeline.exists():
        result.warnings.append(
            "silver_family_classification_visibility_timeline.parquet not found; "
            "falling back to stable_family_classification_replay."
        )
    return result


def build_silver_family_classification_visibility_timeline(settings: BuildSettings) -> StageResult:
    """Build silver_family_classification_visibility_timeline.parquet."""
    result = StageResult(
        stage="silver-pit-classification-visibility",
        status="success",
        summary=(
            "Built silver_family_classification_visibility_timeline.parquet with first-seen WIPO/CPC/IPC "
            "classification visibility by family from member-publication chronology."
        ),
        methods=[
            "Uses silver_family_member_publications as the chronology backbone for first visible classification year.",
            "Joins bronze PATSTAT CPC, IPC, and techn-field inputs at appln_id grain before collapsing to family-level first-seen visibility.",
            "Produces one row per family and classification code with first_seen_date and first_seen_year.",
        ],
        calculations=[
            "WIPO_FIELD visibility comes from appln_techn_field joined through bronze_ref_techn_field_ipc.",
            "CPC_MAIN_GROUP visibility is normalized by replacing subgroup suffixes with /00.",
            "historical_classification_truth_supported remains false because this is first-seen visibility, not true code mutation lineage.",
        ],
        doc_refs=[
            "docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md",
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
        ],
        downstream_impacts=[
            "silver_family_classification_pit_dense can use this timeline to avoid showing late-visible codes too early.",
            "gold family, portfolio, and market classification PIT marts inherit more credible chronology from this timeline.",
        ],
    )

    required = _required_classification_visibility_inputs(settings)
    missing = [str(p) for p in required.values() if not p.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(
            f"Missing required inputs for silver-pit-classification-visibility: {missing}"
        )
        return result

    ensure_dir(settings.silver_dir)
    visibility_table = settings.silver_dir / CLASSIFICATION_VISIBILITY_OUTPUT_TABLE
    audit_table = settings.silver_dir / CLASSIFICATION_VISIBILITY_AUDIT_TABLE
    temp_dir = ensure_dir(settings.silver_dir / "_duckdb_tmp_pit_classification_visibility")
    chunk_dir = ensure_dir(settings.silver_dir / "_pit_classification_visibility_chunks")

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET threads=4")
    con.execute("SET memory_limit='8GB'")
    con.execute(f"SET temp_directory='{temp_dir}'")

    chunk_paths: list[Path] = []
    for stale in chunk_dir.glob("silver_family_classification_visibility_timeline_*.parquet"):
        stale.unlink()
    for bucket_id in range(DENSE_BUCKET_COUNT):
        chunk_path = chunk_dir / f"silver_family_classification_visibility_timeline_bucket_{bucket_id:02d}.parquet"
        sql = _build_classification_visibility_timeline_sql(
            member_publications=required["member_publications"],
            appln_cpc=required["appln_cpc"],
            appln_ipc=required["appln_ipc"],
            appln_techn_field=required["appln_techn_field"],
            ref_techn_field_ipc=required["ref_techn_field_ipc"],
            bucket_id=bucket_id,
            bucket_count=DENSE_BUCKET_COUNT,
        )
        con.execute(
            f"COPY ({sql}) TO '{chunk_path}' (FORMAT parquet, COMPRESSION zstd)"
        )
        chunk_paths.append(chunk_path)

    if visibility_table.exists():
        visibility_table.unlink()
    con.execute(
        f"COPY (SELECT * FROM read_parquet('{chunk_dir / 'silver_family_classification_visibility_timeline_bucket_*.parquet'}')) "
        f"TO '{visibility_table}' (FORMAT parquet, COMPRESSION zstd)"
    )

    audit_payload = _build_classification_visibility_audit(con, visibility_table)
    if audit_table.exists():
        audit_table.unlink()
    write_text_json(audit_table, audit_payload)

    row_count = parquet_row_count(visibility_table)
    result.outputs.append(str(visibility_table))
    result.outputs.append(str(audit_table))
    result.metrics["silver_family_classification_visibility_timeline_rows"] = row_count
    result.metrics["silver_family_classification_visibility_duplicate_family_classification_keys"] = audit_payload[
        "duplicate_family_classification_keys"
    ]
    return result
