from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


def _parquet_fingerprint(path: Path) -> dict[str, object]:
    stat = path.stat()
    fingerprint = hashlib.sha256(
        f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{parquet_row_count(path)}".encode("utf-8")
    ).hexdigest()
    return {
        "path": str(path),
        "row_count": parquet_row_count(path),
        "size_bytes": stat.st_size,
        "modified_at_ns": stat.st_mtime_ns,
        "fingerprint": fingerprint,
    }


def build_ml_phase0_foundation(settings: BuildSettings) -> StageResult:
    """Materialize the reproducibility and evaluation scaffolding for semantic and forecast work."""
    result = StageResult(
        stage="ml-phase0-foundation",
        status="success",
        summary="Built a frozen training snapshot manifest, immediate family-forecast split registry, and semantic evaluation fixtures.",
        methods=[
            "Fingerprinted canonical Silver and Gold source marts with row counts, file size, and modified-time metadata for reproducibility.",
            "Built a deterministic family-first split registry for the immediate family citation forecast scope using priority-year time bands.",
            "Bootstrapped semantic evaluation fixtures and compare pairs from the live family semantic context while preserving legal-status expectations.",
        ],
        calculations=[
            "Family forecast split assignment uses main-window family rows from Gold family summary and places recent unlabeled cohorts into an explicit holdout bucket.",
            "Semantic fixtures intentionally cover claim-backed, abstract-backed, dead, pending, and partially-lapsed families to test both retrieval and legal gating behavior.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-implementation-runbook-backlog.md",
            "docs/new-feature-ideas/semantic-and-model-development/phases/phase-00-freeze-inputs-and-eval-fixtures.md",
            "docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md",
            "docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md",
        ],
    )

    ml_dir = ensure_dir(settings.ml_dir)
    split_registry = ml_dir / "ml_split_registry.parquet"
    semantic_fixtures = ml_dir / "semantic_eval_fixture_registry.parquet"
    semantic_pairs = ml_dir / "semantic_eval_pair_registry.parquet"
    snapshot_manifest = ml_dir / "training_snapshot_manifest.json"

    family_summary = settings.gold_dir / "gold_family_summary.parquet"
    semantic_context = settings.gold_dir / "gold_semantic_match_context.parquet"
    semantic_rep = settings.silver_dir / "silver_family_text_representative.parquet"
    citation_metrics = settings.silver_dir / "silver_family_citation_metrics.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_status_history = settings.silver_dir / "silver_family_status_history.parquet"
    family_oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"
    family_coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"

    required_inputs = [
        family_summary,
        semantic_context,
        semantic_rep,
        citation_metrics,
        family_status,
        family_status_history,
        family_oecd,
        family_coverage,
        enforce,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing required Phase 00 inputs: {missing}")
        return result

    con = duckdb.connect()
    snapshot_year = int(settings.snapshot_date[:4])
    family_forecast_cutoff_year = snapshot_year - 6
    split_cutoff = f"{family_forecast_cutoff_year}-12-31"

    con.execute(
        f"""
        copy (
            with family_base as (
                select
                    docdb_family_id,
                    family_priority_year,
                    primary_wipo_field
                from read_parquet('{family_summary}')
                where coalesce(is_main_window_family, false) = true
            )
            select
                'family_future_citation_forecast' as model_scope,
                cast(docdb_family_id as varchar) as entity_id,
                docdb_family_id as root_family_id,
                case
                    when family_priority_year <= {family_forecast_cutoff_year - 4} then 'train'
                    when family_priority_year between {family_forecast_cutoff_year - 3} and {family_forecast_cutoff_year - 2} then 'validation'
                    when family_priority_year between {family_forecast_cutoff_year - 1} and {family_forecast_cutoff_year} then 'test'
                    else 'unassigned_recent'
                end as split_name,
                'family_grouped_time_by_priority_year' as split_strategy,
                date '{split_cutoff}' as snapshot_cutoff,
                primary_wipo_field,
                family_priority_year as time_key_year
            from family_base
        ) to '{split_registry}' (format parquet, compression zstd)
        """
    )

    con.execute(
        f"""
        copy (
            with
            semantic_base as (
                select
                    c.docdb_family_id,
                    c.owner_name_harmonized,
                    c.representative_stage,
                    c.representative_source_type,
                    c.text_provenance,
                    c.is_abstract_fallback,
                    c.covered_wipo_fields,
                    list_extract(c.covered_wipo_fields, 1) as primary_wipo_field,
                    c.family_ui_blocking_power_score,
                    c.oecd_quality_percentile,
                    s.family_composite_status
                from read_parquet('{semantic_context}') c
                join read_parquet('{family_status}') s using (docdb_family_id)
                where coalesce(c.is_semantic_candidate, false) = true
            ),
            claim_active as (
                select
                    'claim_active_discovery' as fixture_group,
                    'text_to_family_semantic_search' as workflow_type,
                    docdb_family_id,
                    'vector_claims' as vector_space,
                    representative_source_type,
                    text_provenance,
                    is_abstract_fallback,
                    family_composite_status,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    'allow_current_strategic_display' as expected_behavior
                from semantic_base
                where family_composite_status = 'fully_active'
                  and coalesce(is_abstract_fallback, false) = false
                order by docdb_family_id
                limit 100
            ),
            abstract_active as (
                select
                    'abstract_active_discovery' as fixture_group,
                    'text_to_family_semantic_search' as workflow_type,
                    docdb_family_id,
                    'vector_abstract' as vector_space,
                    representative_source_type,
                    text_provenance,
                    is_abstract_fallback,
                    family_composite_status,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    'allow_current_strategic_display' as expected_behavior
                from semantic_base
                where family_composite_status = 'fully_active'
                  and coalesce(is_abstract_fallback, false) = true
                order by docdb_family_id
                limit 200
            ),
            dead_families as (
                select
                    'dead_family_suppression' as fixture_group,
                    'semantic_current_threat_gating' as workflow_type,
                    docdb_family_id,
                    'vector_abstract' as vector_space,
                    representative_source_type,
                    text_provenance,
                    is_abstract_fallback,
                    family_composite_status,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    'suppress_current_threat_display' as expected_behavior
                from semantic_base
                where family_composite_status = 'dead'
                order by docdb_family_id
                limit 100
            ),
            pending_families as (
                select
                    'pending_family_watch' as fixture_group,
                    'semantic_current_threat_gating' as workflow_type,
                    docdb_family_id,
                    'vector_abstract' as vector_space,
                    representative_source_type,
                    text_provenance,
                    is_abstract_fallback,
                    family_composite_status,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    'watch_not_current_threat' as expected_behavior
                from semantic_base
                where family_composite_status = 'pending_emerging'
                order by docdb_family_id
                limit 100
            ),
            partially_lapsed_families as (
                select
                    'partially_lapsed_watch' as fixture_group,
                    'semantic_current_threat_gating' as workflow_type,
                    docdb_family_id,
                    'vector_abstract' as vector_space,
                    representative_source_type,
                    text_provenance,
                    is_abstract_fallback,
                    family_composite_status,
                    primary_wipo_field,
                    owner_name_harmonized,
                    family_ui_blocking_power_score,
                    oecd_quality_percentile,
                    'caveat_partial_lapse' as expected_behavior
                from semantic_base
                where family_composite_status = 'partially_lapsed'
                order by docdb_family_id
                limit 100
            ),
            unioned as (
                select * from claim_active
                union all
                select * from abstract_active
                union all
                select * from dead_families
                union all
                select * from pending_families
                union all
                select * from partially_lapsed_families
            ),
            rep as (
                select
                    docdb_family_id,
                    representative_claim_1_en,
                    representative_abstract_en
                from read_parquet('{semantic_rep}')
            )
            select
                concat(fixture_group, '_', lpad(cast(row_number() over (partition by fixture_group order by docdb_family_id) as varchar), 4, '0')) as fixture_id,
                workflow_type,
                fixture_group,
                docdb_family_id,
                vector_space,
                coalesce(rep.representative_claim_1_en, rep.representative_abstract_en) as query_text,
                representative_source_type,
                text_provenance,
                is_abstract_fallback,
                family_composite_status,
                primary_wipo_field,
                owner_name_harmonized,
                family_ui_blocking_power_score,
                oecd_quality_percentile,
                expected_behavior,
                case when expected_behavior = 'allow_current_strategic_display' then true else false end as expected_current_threat_allowed
            from unioned
            left join rep using (docdb_family_id)
        ) to '{semantic_fixtures}' (format parquet, compression zstd)
        """
    )

    con.execute(
        f"""
        copy (
            with compare_base as (
                select
                    f.docdb_family_id,
                    f.vector_space,
                    f.primary_wipo_field,
                    f.family_composite_status,
                    row_number() over (
                        partition by f.vector_space, f.primary_wipo_field
                        order by f.docdb_family_id
                    ) as rn
                from read_parquet('{semantic_fixtures}') f
                where f.fixture_group in ('claim_active_discovery', 'abstract_active_discovery')
                  and f.primary_wipo_field is not null
                )
                select
                    concat('pair_', left_side.vector_space, '_', left_side.primary_wipo_field, '_', lpad(cast(left_side.rn as varchar), 4, '0')) as pair_fixture_id,
                    'family_to_family_semantic_compare' as workflow_type,
                    left_side.vector_space,
                    left_side.primary_wipo_field,
                left_side.docdb_family_id as anchor_family_id,
                right_side.docdb_family_id as target_family_id,
                left_side.family_composite_status as anchor_status,
                right_side.family_composite_status as target_status,
                'same_field_pair_compare' as pair_policy,
                'compare_overlap_with_legal_overlay' as expected_behavior
            from compare_base left_side
            join compare_base right_side
              on left_side.vector_space = right_side.vector_space
             and left_side.primary_wipo_field = right_side.primary_wipo_field
             and right_side.rn = left_side.rn + 1
            where mod(left_side.rn, 2) = 1
              and left_side.rn <= 400
        ) to '{semantic_pairs}' (format parquet, compression zstd)
        """
    )

    manifest_payload = {
        "training_snapshot_id": f"{settings.release_id}-{settings.snapshot_date}-phase0",
        "snapshot_cutoff_date": split_cutoff,
        "method_version": settings.method_version,
        "semantic_fixture_policy": {
            "vector_spaces": ["vector_claims", "vector_abstract"],
            "fixture_groups": [
                "claim_active_discovery",
                "abstract_active_discovery",
                "dead_family_suppression",
                "pending_family_watch",
                "partially_lapsed_watch",
            ],
            "pair_policy": "same_field_pair_compare",
        },
        "source_tables": [_parquet_fingerprint(path) for path in required_inputs],
        "generated_outputs": [str(split_registry), str(semantic_fixtures), str(semantic_pairs)],
    }
    write_text_json(snapshot_manifest, manifest_payload)

    result.inputs.extend([str(path) for path in required_inputs])
    result.outputs.extend([str(split_registry), str(semantic_fixtures), str(semantic_pairs), str(snapshot_manifest)])
    result.metrics["ml_split_registry_rows"] = parquet_row_count(split_registry)
    result.metrics["semantic_eval_fixture_registry_rows"] = parquet_row_count(semantic_fixtures)
    result.metrics["semantic_eval_pair_registry_rows"] = parquet_row_count(semantic_pairs)
    result.metrics["training_snapshot_source_table_count"] = len(required_inputs)
    result.artifacts["training_snapshot_manifest"] = str(snapshot_manifest)
    return result
