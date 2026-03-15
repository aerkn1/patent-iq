from __future__ import annotations

import json

import duckdb

from patentiq_etl.common.io import parquet_row_count, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


MODEL_SCOPES = [
    "family_future_citation_forecast",
    "publication_or_subfamily_grant_probability",
    "family_jurisdiction_lapse_risk",
    "family_friction_risk",
    "jurisdiction_field_trend_forecast",
    "ep_special_publication_grant_probability",
]


def run_ml(settings: BuildSettings) -> list[StageResult]:
    """Materialize MVP ML feature artifacts and placeholder registry metadata."""
    result = StageResult(
        stage="ml",
        status="success",
        summary="Materialized ML manifests, feature tables, and placeholder model registry artifacts for MVP training integration.",
        methods=[
            "Built feature-manifest and model-registry scaffolding from validated Silver and Gold inputs.",
            "Recorded model-scope metadata and release-safe placeholders where full training artifacts are not yet promoted.",
        ],
        calculations=[
            "Feature tables remain tied to the bounded family universe and carry the ETL method version.",
        ],
        doc_refs=[
            "docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    family_core = settings.silver_dir / "silver_family_core.parquet"
    cite = settings.silver_dir / "silver_family_citation_metrics.parquet"
    enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    market_seg = settings.silver_dir / "silver_market_intelligence_segments.parquet"
    model_registry = settings.ml_dir / "ml_model_registry.parquet"
    feature_table = settings.ml_dir / "ml_feature_family_future_citations.parquet"
    feature_manifest = settings.ml_dir / "ml_feature_manifest.json"
    model_card = settings.ml_dir / "model_card_family_future_citation_forecast.json"

    con = duckdb.connect()
    con.execute(
        f"""
        copy (
            select
                c.docdb_family_id,
                c.family_priority_year,
                coalesce(x.family_rcf_score, 0.0) as family_rcf_score,
                coalesce(e.branch_enforceability_contribution_raw, 0.0) as branch_enforceability_contribution_raw,
                '{settings.snapshot_date}' as as_of_date,
                '{settings.method_version}' as method_version
            from read_parquet('{family_core}') c
            left join read_parquet('{cite}') x using (docdb_family_id)
            left join read_parquet('{enforce}') e using (docdb_family_id)
        ) to '{feature_table}' (format parquet, compression zstd)
        """
    )
    con.execute(
        f"""
        copy (
            select
                scope as model_scope,
                'pending_real_training' as model_version,
                'not_trained' as promotion_status,
                '{settings.release_id}' as training_snapshot,
                '{settings.method_version}' as method_version
            from (
                select unnest([{", ".join([f"'{scope}'" for scope in MODEL_SCOPES])}]) as scope
            )
        ) to '{model_registry}' (format parquet, compression zstd)
        """
    )
    write_text_json(
        feature_manifest,
        {
            "model_scope": "family_future_citation_forecast",
            "feature_table": str(feature_table),
            "features": [
                "family_priority_year",
                "family_rcf_score",
                "branch_enforceability_contribution_raw",
            ],
            "method_version": settings.method_version,
            "governing_docs": [
                "docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md",
                "docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md",
            ],
        },
    )
    write_text_json(
        model_card,
        {
            "model_scope": "family_future_citation_forecast",
            "status": "pending_real_training",
            "reason": "ETL pipeline built the feature and registry scaffolding, but no promoted model artifact has been produced inside this implementation step.",
            "feature_table": str(feature_table),
            "method_version": settings.method_version,
        },
    )

    result.outputs.extend([str(feature_table), str(model_registry), str(feature_manifest), str(model_card)])
    result.metrics["ml_feature_family_future_citations_rows"] = parquet_row_count(feature_table)
    result.metrics["ml_model_registry_rows"] = parquet_row_count(model_registry)
    return [result]
