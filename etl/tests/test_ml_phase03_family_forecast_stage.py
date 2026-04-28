from __future__ import annotations

import json
import math
from pathlib import Path

import duckdb
import numpy as np

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.ml.phase03 import (
    _choose_variant,
    _coverage_with_grouped_qhats,
    _fit_grouped_conformal_qhats,
    _forecast_metrics,
    _subgroup_coverage_with_grouped_qhats,
    build_ml_phase03_family_future_citation_forecast,
)
from patentiq_etl.ml.run import run_ml_phase03_family_forecast


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-15",
        year_window_start=2007,
        year_window_end=2026,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=1.0,
        active_grant_only_for_semantic=True,
        method_version="test_method_v1",
        semantic_embedding_method="stable_hash_embedding_mvp",
        semantic_ann_method="manifest_only_placeholder",
        patstat_source_mode="local_files",
        register_source_mode="local_files",
        epab_source_mode="local_files",
        uspto_source_mode="local_files",
        refs_source_mode="local_files",
        tip_env="PROD",
        raw_patstat_dir=root / "etl/data/raw/patstat",
        raw_register_dir=root / "etl/data/raw/register",
        raw_uspto_dir=root / "etl/data/raw/uspto",
        raw_epab_dir=root / "etl/data/raw/epab",
        raw_refs_dir=root / "etl/data/raw/refs",
        bounded_patstat_dir=root / "etl/data/raw-bounded/patstat",
        bounded_register_dir=root / "etl/data/raw-bounded/register",
        bounded_uspto_dir=root / "etl/data/raw-bounded/uspto",
        bounded_epab_dir=root / "etl/data/raw-bounded/epab",
        bounded_refs_dir=root / "etl/data/raw-bounded/refs",
        bounded_seed_dir=root / "etl/data/raw-bounded/_seeds",
        bronze_dir=root / "etl/data/bronze",
        silver_dir=root / "etl/data/silver",
        gold_dir=root / "etl/data/gold",
        ml_dir=root / "etl/data/ml",
        vectors_dir=root / "etl/data/vectors",
        releases_dir=root / "etl/data/releases",
        manifests_dir=root / "etl/manifests",
        journal_path=root / "etl/ETL_IMPLEMENTATION_LOG.md",
        ref_techn_field_ipc=root / "etl/data/raw/refs/wipo_techn_field_ipc.csv",
        scope_type="mega_cluster_bounded",
        field_source="wipo_industry_code",
        selected_wipo_fields=["Computer technology"],
        thresholds={},
        azure={},
        execution={},
    )


def test_ml_phase03_family_forecast_stage_is_exposed() -> None:
    assert callable(build_ml_phase03_family_future_citation_forecast)
    assert callable(run_ml_phase03_family_forecast)


def test_grouped_conformal_qhats_fall_back_globally_for_small_groups() -> None:
    frame = duckdb.sql(
        """
        select * from (
            values
                ('A'),
                ('A'),
                ('B')
        ) as t(primary_wipo_field)
        """
    ).df()
    y_true = duckdb.sql("select * from (values (0.10), (0.20), (0.80)) as t(v)").df()["v"]
    y_pred = np.array([0.10, 0.50, 0.20], dtype=float)

    global_qhat, qhat_by_group = _fit_grouped_conformal_qhats(
        frame,
        y_true,
        y_pred,
        target_coverage=0.8,
        group_col="primary_wipo_field",
        min_group_rows=10,
    )

    assert global_qhat > 0.0
    assert qhat_by_group == {}
    coverage = _coverage_with_grouped_qhats(
        frame.assign(target_log=y_true.to_numpy(dtype=float)),
        y_true,
        y_pred,
        global_qhat,
        group_col="primary_wipo_field",
        qhat_by_group=qhat_by_group,
    )
    subgroup = _subgroup_coverage_with_grouped_qhats(
        frame.assign(target_log=y_true.to_numpy(dtype=float)),
        y_pred,
        global_qhat,
        "primary_wipo_field",
        qhat_by_group=qhat_by_group,
    )
    assert coverage is not None
    assert subgroup["A"] <= 1.0
    assert subgroup["B"] <= 1.0


def test_grouped_conformal_qhats_can_tighten_subgroup_spread() -> None:
    frame = duckdb.sql(
        """
        select * from (
            values
                ('A'), ('A'), ('A'), ('A'),
                ('B'), ('B'), ('B'), ('B')
        ) as t(primary_wipo_field)
        """
    ).df()
    y_true = duckdb.sql(
        "select * from (values (0.10), (0.12), (0.11), (0.09), (0.50), (0.49), (0.52), (0.48)) as t(v)"
    ).df()["v"]
    y_pred = np.array([0.10, 0.11, 0.10, 0.10, 0.20, 0.20, 0.20, 0.20], dtype=float)

    global_qhat, qhat_by_group = _fit_grouped_conformal_qhats(
        frame,
        y_true,
        y_pred,
        target_coverage=0.8,
        group_col="primary_wipo_field",
        min_group_rows=4,
    )

    assert qhat_by_group["A"] < global_qhat
    assert qhat_by_group["B"] > qhat_by_group["A"]

    subgroup_global = _subgroup_coverage_with_grouped_qhats(
        frame.assign(target_log=y_true.to_numpy(dtype=float)),
        y_pred,
        global_qhat,
        "primary_wipo_field",
        qhat_by_group=None,
    )
    subgroup_grouped = _subgroup_coverage_with_grouped_qhats(
        frame.assign(target_log=y_true.to_numpy(dtype=float)),
        y_pred,
        global_qhat,
        "primary_wipo_field",
        qhat_by_group=qhat_by_group,
    )

    spread_global = max(subgroup_global.values()) - min(subgroup_global.values())
    spread_grouped = max(subgroup_grouped.values()) - min(subgroup_grouped.values())
    assert spread_grouped <= spread_global


def test_forecast_metrics_include_tail_mae_when_threshold_is_set() -> None:
    actual_raw = duckdb.sql("select * from (values (1.0), (2.0), (50.0), (80.0)) as t(v)").df()["v"]
    actual_log = np.log1p(actual_raw.to_numpy(dtype=float))
    pred_raw = np.array([1.5, 2.5, 25.0, 35.0], dtype=float)
    pred_log = np.log1p(pred_raw)

    metrics = _forecast_metrics(actual_raw, actual_log, pred_raw, pred_log, breakout_threshold=40.0)

    assert metrics["spearman"] is not None
    assert metrics["precision_at_1pct"] is not None
    assert metrics["breakout_tail_mae_raw"] is not None
    assert metrics["breakout_tail_mae_raw"] > 0.0


def test_choose_variant_prefers_two_stage_when_tail_improves_without_large_rank_drop() -> None:
    baseline_metrics = {
        "spearman": 0.50,
        "precision_at_1pct": 0.20,
        "breakout_tail_mae_raw": 100.0,
    }
    two_stage_metrics = {
        "spearman": 0.48,
        "precision_at_1pct": 0.30,
        "breakout_tail_mae_raw": 70.0,
    }

    assert _choose_variant(baseline_metrics, two_stage_metrics) == "two_stage"


def test_choose_variant_keeps_baseline_when_two_stage_hurts_rank_too_much() -> None:
    baseline_metrics = {
        "spearman": 0.50,
        "precision_at_1pct": 0.20,
        "breakout_tail_mae_raw": 100.0,
    }
    two_stage_metrics = {
        "spearman": 0.40,
        "precision_at_1pct": 0.35,
        "breakout_tail_mae_raw": 50.0,
    }

    assert _choose_variant(baseline_metrics, two_stage_metrics) == "baseline"


def test_build_ml_phase03_family_forecast_materializes_label_feature_and_registry_contracts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_priority_year": 2015,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology",
                "family_size_docdb": 5,
                "active_jurisdiction_count": 3,
                "family_distinct_owner_count": 1,
                "branch_enforceability_contribution_raw": 2.4,
                "family_overall_legal_enforceability_score": 0.87,
                "active_grant_branch_count": 2,
                "family_earliest_priority_date": "2015-02-10",
            },
            {
                "docdb_family_id": 200,
                "family_priority_year": 2017,
                "is_main_window_family": True,
                "primary_wipo_field": "Digital communication",
                "family_size_docdb": 4,
                "active_jurisdiction_count": 2,
                "family_distinct_owner_count": 2,
                "branch_enforceability_contribution_raw": 1.2,
                "family_overall_legal_enforceability_score": 0.62,
                "active_grant_branch_count": 1,
                "family_earliest_priority_date": "2017-05-01",
            },
            {
                "docdb_family_id": 300,
                "family_priority_year": 2019,
                "is_main_window_family": True,
                "primary_wipo_field": "Electrical machinery, apparatus, energy",
                "family_size_docdb": 8,
                "active_jurisdiction_count": 4,
                "family_distinct_owner_count": 1,
                "branch_enforceability_contribution_raw": 3.6,
                "family_overall_legal_enforceability_score": 0.91,
                "active_grant_branch_count": 3,
                "family_earliest_priority_date": "2019-01-20",
            },
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_forward_citations_clean": 12.0,
                "family_forward_citations_weighted_7y": 10.5,
                "family_rcf_score": 0.71,
                "fwd_cits5_raw": 14.0,
                "fwd_cits7_raw": 17.0,
                "future_forward_citations_3y_raw": 11.0,
                "future_forward_citations_5y_raw": 19.0,
            },
            {
                "docdb_family_id": 200,
                "family_forward_citations_clean": 5.0,
                "family_forward_citations_weighted_7y": 4.7,
                "family_rcf_score": 0.42,
                "fwd_cits5_raw": 6.0,
                "fwd_cits7_raw": 7.0,
                "future_forward_citations_3y_raw": 3.0,
                "future_forward_citations_5y_raw": 6.0,
            },
            {
                "docdb_family_id": 300,
                "family_forward_citations_clean": 21.0,
                "family_forward_citations_weighted_7y": 19.4,
                "family_rcf_score": 0.89,
                "fwd_cits5_raw": 25.0,
                "fwd_cits7_raw": 31.0,
                "future_forward_citations_3y_raw": 17.0,
                "future_forward_citations_5y_raw": 28.0,
            },
        ],
        settings.silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "unique_citing_family_count": 8.0,
                "citing_assignee_diversity": 0.61,
                "attacker_density_score": 0.22,
            },
            {
                "docdb_family_id": 200,
                "unique_citing_family_count": 3.0,
                "citing_assignee_diversity": 0.33,
                "attacker_density_score": 0.14,
            },
            {
                "docdb_family_id": 300,
                "unique_citing_family_count": 12.0,
                "citing_assignee_diversity": 0.73,
                "attacker_density_score": 0.28,
            },
        ],
        settings.silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "quality_index_4_percentile": 0.81,
                "quality_index_6_percentile": 0.84,
                "generality_percentile": 0.66,
                "radicalness_percentile": 0.44,
                "science_grounding_percentile": 0.51,
            },
            {
                "docdb_family_id": 200,
                "quality_index_4_percentile": 0.45,
                "quality_index_6_percentile": 0.47,
                "generality_percentile": 0.39,
                "radicalness_percentile": 0.27,
                "science_grounding_percentile": None,
            },
            {
                "docdb_family_id": 300,
                "quality_index_4_percentile": 0.93,
                "quality_index_6_percentile": 0.95,
                "generality_percentile": 0.78,
                "radicalness_percentile": 0.63,
                "science_grounding_percentile": 0.74,
            },
        ],
        settings.silver_dir / "silver_family_oecd_quality.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_coverage_stability_score": 0.76},
            {"docdb_family_id": 200, "family_coverage_stability_score": 0.51},
            {"docdb_family_id": 300, "family_coverage_stability_score": 0.88},
        ],
        settings.silver_dir / "silver_family_coverage_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_composite_status": "fully_active"},
            {"docdb_family_id": 200, "family_composite_status": "partially_lapsed"},
            {"docdb_family_id": 300, "family_composite_status": "fully_active"},
        ],
        settings.silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "primary_wipo_field": "Computer technology"},
            {"docdb_family_id": 200, "primary_wipo_field": "Digital communication"},
            {"docdb_family_id": 300, "primary_wipo_field": "Electrical machinery, apparatus, energy"},
        ],
        settings.silver_dir / "silver_family_wipo_fields.parquet",
    )

    result = build_ml_phase03_family_future_citation_forecast(settings).finish()
    assert result.status == "success"

    label_table = settings.ml_dir / "ml_label_family_future_citations.parquet"
    feature_table = settings.ml_dir / "ml_feature_family_future_citations.parquet"
    split_table = settings.ml_dir / "ml_split_registry.parquet"
    phase_split_table = settings.ml_dir / "ml_split_registry_phase03.parquet"
    experiment_registry = settings.ml_dir / "ml_experiment_registry.parquet"
    model_registry = settings.ml_dir / "ml_model_registry.parquet"
    calibration_registry = settings.ml_dir / "ml_calibration_registry.parquet"
    feature_manifest = settings.ml_dir / "ml_feature_manifest.parquet"
    model_card = settings.ml_dir / "model_card_family_future_citation_forecast.json"

    for path in [
        label_table,
        feature_table,
        split_table,
        phase_split_table,
        experiment_registry,
        model_registry,
        calibration_registry,
        feature_manifest,
        model_card,
    ]:
        assert path.exists()

    con = duckdb.connect()
    label_rows = con.execute(
        """
        select
            docdb_family_id,
            future_forward_citations_3y_raw,
            future_forward_citations_5y_raw,
            round(future_forward_citations_3y_log1p, 6),
            round(future_forward_citations_5y_log1p, 6)
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(label_table)],
    ).fetchall()
    assert label_rows == [
        (100, 11.0, 19.0, round(math.log1p(11.0), 6), round(math.log1p(19.0), 6)),
        (200, 3.0, 6.0, round(math.log1p(3.0), 6), round(math.log1p(6.0), 6)),
        (300, 17.0, 28.0, round(math.log1p(17.0), 6), round(math.log1p(28.0), 6)),
    ]

    feature_columns = [row[0] for row in con.execute("describe select * from read_parquet(?)", [str(feature_table)]).fetchall()]
    assert feature_columns == [
        "docdb_family_id",
        "as_of_date",
        "as_of_year",
        "is_observed_as_of_snapshot",
        "family_priority_year",
        "primary_wipo_field",
        "family_forward_citations_clean",
        "family_forward_citations_weighted_7y",
        "family_rcf_score",
        "family_size_docdb",
        "active_jurisdiction_count",
        "family_distinct_owner_count",
        "family_composite_status",
        "branch_enforceability_contribution_raw",
        "family_overall_legal_enforceability_score",
        "active_grant_branch_count",
        "quality_index_4_percentile",
        "quality_index_6_percentile",
        "generality_percentile",
        "radicalness_percentile",
        "science_grounding_percentile",
        "family_earliest_priority_date",
        "family_age_years",
        "family_coverage_stability_score",
        "training_snapshot_id",
        "method_version",
        "unique_citing_family_count",
        "citing_assignee_diversity",
        "attacker_density_score",
        "data_completeness_pct",
    ]

    completeness_rows = con.execute(
        """
        select docdb_family_id, science_grounding_percentile, data_completeness_pct
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(feature_table)],
    ).fetchall()
    assert completeness_rows[0][2] == 1.0
    assert completeness_rows[1][1] is None
    assert completeness_rows[1][2] < 1.0
    assert completeness_rows[2][2] == 1.0

    split_rows = con.execute(
        "select entity_id, split_name from read_parquet(?) where model_scope = ? order by entity_id",
        [str(split_table), "family_future_citation_forecast"],
    ).fetchall()
    assert split_rows == [("100", "train"), ("200", "validation"), ("300", "test")]
    phase_split_rows = con.execute(
        "select entity_id, split_name from read_parquet(?) order by entity_id",
        [str(phase_split_table)],
    ).fetchall()
    assert phase_split_rows == split_rows

    assert con.execute("select count(*) from read_parquet(?)", [str(experiment_registry)]).fetchone()[0] == 6
    assert con.execute("select count(*) from read_parquet(?)", [str(model_registry)]).fetchone()[0] == 2
    assert con.execute("select count(*) from read_parquet(?)", [str(calibration_registry)]).fetchone()[0] == 2

    manifest_rows = con.execute(
        "select count(*) from read_parquet(?) where model_scope = ?",
        [str(feature_manifest), "family_future_citation_forecast"],
    ).fetchone()[0]
    assert manifest_rows == 22

    payload = json.loads(model_card.read_text(encoding="utf-8"))
    assert payload["prediction_unit"] == "docdb_family_id"
    assert payload["status"] == "pending_real_training"
    assert payload["baseline_model_planned"]["objective"] == "regression_log1p"
    assert payload["split_registry"] == str(phase_split_table)
    assert payload["split_registry_shared"] == str(split_table)


def test_build_ml_phase03_family_forecast_trains_baseline_when_split_sizes_are_sufficient(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    families = []
    citation_rows = []
    network_rows = []
    oecd_rows = []
    coverage_rows = []
    status_rows = []
    wipo_rows = []

    priority_years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    for idx, priority_year in enumerate(priority_years, start=1):
        family_id = idx * 100
        base_signal = float(idx)
        families.append(
            {
                "docdb_family_id": family_id,
                "family_priority_year": priority_year,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology" if idx % 2 else "Digital communication",
                "family_size_docdb": 3 + idx,
                "active_jurisdiction_count": 1 + (idx % 4),
                "family_distinct_owner_count": 1 + (idx % 2),
                "branch_enforceability_contribution_raw": 0.5 + base_signal,
                "family_overall_legal_enforceability_score": 0.3 + (base_signal / 20.0),
                "active_grant_branch_count": 1 + (idx % 3),
                "family_earliest_priority_date": f"{priority_year}-01-15",
            }
        )
        citation_rows.append(
            {
                "docdb_family_id": family_id,
                "family_forward_citations_clean": base_signal * 2.0,
                "family_forward_citations_weighted_7y": base_signal * 1.8,
                "family_rcf_score": 0.1 * base_signal,
                "fwd_cits5_raw": base_signal * 2.5,
                "fwd_cits7_raw": base_signal * 3.0,
                "future_forward_citations_3y_raw": base_signal * 2.2,
                "future_forward_citations_5y_raw": base_signal * 3.4,
            }
        )
        network_rows.append(
            {
                "docdb_family_id": family_id,
                "unique_citing_family_count": 2.0 + base_signal,
                "citing_assignee_diversity": 0.2 + (base_signal / 20.0),
                "attacker_density_score": 0.1 + (base_signal / 30.0),
            }
        )
        oecd_rows.append(
            {
                "docdb_family_id": family_id,
                "quality_index_4_percentile": 0.25 + (base_signal / 20.0),
                "quality_index_6_percentile": 0.3 + (base_signal / 20.0),
                "generality_percentile": 0.2 + (base_signal / 25.0),
                "radicalness_percentile": 0.15 + (base_signal / 30.0),
                "science_grounding_percentile": 0.1 + (base_signal / 35.0),
            }
        )
        coverage_rows.append({"docdb_family_id": family_id, "family_coverage_stability_score": 0.4 + (base_signal / 20.0)})
        status_rows.append(
            {
                "docdb_family_id": family_id,
                "family_composite_status": "fully_active" if idx % 3 else "partially_lapsed",
            }
        )
        wipo_rows.append(
            {
                "docdb_family_id": family_id,
                "primary_wipo_field": "Computer technology" if idx % 2 else "Digital communication",
            }
        )

    write_pylist_parquet(families, settings.gold_dir / "gold_family_summary.parquet")
    write_pylist_parquet(citation_rows, settings.silver_dir / "silver_family_citation_metrics.parquet")
    write_pylist_parquet(network_rows, settings.silver_dir / "silver_enriched_citation_network.parquet")
    write_pylist_parquet(oecd_rows, settings.silver_dir / "silver_family_oecd_quality.parquet")
    write_pylist_parquet(coverage_rows, settings.silver_dir / "silver_family_coverage_metrics.parquet")
    write_pylist_parquet(status_rows, settings.silver_dir / "silver_family_status_pt.parquet")
    write_pylist_parquet(wipo_rows, settings.silver_dir / "silver_family_wipo_fields.parquet")

    result = build_ml_phase03_family_future_citation_forecast(settings).finish()
    assert result.status == "success"

    model_3y = settings.ml_dir / "family_future_citation_forecast_3y_model.txt"
    model_5y = settings.ml_dir / "family_future_citation_forecast_5y_model.txt"
    bundle_3y = settings.ml_dir / "family_future_citation_forecast_3y_bundle.json"
    bundle_5y = settings.ml_dir / "family_future_citation_forecast_5y_bundle.json"
    calibration_json = settings.ml_dir / "family_future_citation_forecast_calibration.json"
    assert model_3y.exists()
    assert model_5y.exists()
    assert bundle_3y.exists()
    assert bundle_5y.exists()
    assert calibration_json.exists()

    con = duckdb.connect()
    model_rows = con.execute(
        "select horizon, promotion_status, artifact_uri from read_parquet(?) order by horizon",
        [str(settings.ml_dir / "ml_model_registry.parquet")],
    ).fetchall()
    assert model_rows[0][1] == "candidate_trained"
    assert model_rows[1][1] == "candidate_trained"
    assert model_rows[0][2] == str(bundle_3y)
    assert model_rows[1][2] == str(bundle_5y)

    experiment_rows = con.execute(
        """
        select horizon, objective, primary_metric_value, interval_coverage_80pct
        from read_parquet(?)
        where notes = 'baseline_trained'
        order by horizon
        """,
        [str(settings.ml_dir / "ml_experiment_registry.parquet")],
    ).fetchall()
    assert len(experiment_rows) == 2
    assert experiment_rows[0][2] is not None
    assert experiment_rows[1][2] is not None
    assert experiment_rows[0][3] is not None
    assert experiment_rows[1][3] is not None

    calibration_rows = con.execute(
        "select horizon, status, coverage_overall from read_parquet(?) order by horizon",
        [str(settings.ml_dir / "ml_calibration_registry.parquet")],
    ).fetchall()
    assert calibration_rows[0][0] == "3y"
    assert calibration_rows[1][0] == "5y"
    assert calibration_rows[0][1] == "calibrated"
    assert calibration_rows[1][1] == "calibrated"
    assert calibration_rows[0][2] is not None
    assert calibration_rows[1][2] is not None

    payload = json.loads((settings.ml_dir / "model_card_family_future_citation_forecast.json").read_text(encoding="utf-8"))
    assert payload["status"] == "baseline_trained_candidate"
    assert payload["training_status"] == "baseline_lightgbm_trained"
    assert "3y" in payload["baseline_results"]
    assert "5y" in payload["baseline_results"]


def test_build_ml_phase03_family_forecast_uses_pit_safe_overrides_when_available(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_priority_year": 2015,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology",
                "family_size_docdb": 5,
                "active_jurisdiction_count": 3,
                "family_distinct_owner_count": 1,
                "branch_enforceability_contribution_raw": 2.0,
                "family_overall_legal_enforceability_score": 0.8,
                "active_grant_branch_count": 2,
                "family_earliest_priority_date": "2015-02-10",
            }
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_forward_citations_clean": 12.0,
                "family_forward_citations_weighted_7y": 10.5,
                "family_rcf_score": 0.71,
                "future_forward_citations_3y_raw": 11.0,
                "future_forward_citations_5y_raw": 19.0,
            }
        ],
        settings.silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "unique_citing_family_count": 8.0, "citing_assignee_diversity": 0.61, "attacker_density_score": 0.22}],
        settings.silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "quality_index_4_percentile": 0.81, "quality_index_6_percentile": 0.84, "generality_percentile": 0.66, "radicalness_percentile": 0.44, "science_grounding_percentile": 0.51}],
        settings.silver_dir / "silver_family_oecd_quality.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "family_coverage_stability_score": 0.76}],
        settings.silver_dir / "silver_family_coverage_metrics.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "family_composite_status": "fully_active"}],
        settings.silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "primary_wipo_field": "Computer technology"}],
        settings.silver_dir / "silver_family_wipo_fields.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "as_of_date": "2017-02-10",
                "as_of_year": 2017,
                    "is_observed_as_of_snapshot": False,
                "family_composite_status_asof": "partially_lapsed",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_coverage_stability_score_asof": 0.5,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.3,
                "family_blocking_power_score_asof": 0.4,
                "family_enforceability_score_asof": 0.45,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.9,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 1.0,
                "pre_asof_attacker_density_score": 0.9,
                "data_completeness_pct_asof": 1.0,
            }
        ],
        settings.silver_dir / "silver_family_feature_snapshot_pit.parquet",
    )

    result = build_ml_phase03_family_future_citation_forecast(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    row = con.execute(
        """
        select
            as_of_year,
            is_observed_as_of_snapshot,
            family_forward_citations_clean,
            family_forward_citations_weighted_7y,
            family_rcf_score,
            family_size_docdb,
            active_jurisdiction_count,
            family_composite_status,
            family_overall_legal_enforceability_score,
            active_grant_branch_count,
            family_coverage_stability_score,
            unique_citing_family_count,
            citing_assignee_diversity,
            attacker_density_score
        from read_parquet(?)
        """,
        [str(settings.ml_dir / "ml_feature_family_future_citations.parquet")],
    ).fetchone()
    assert row == (2017, False, 1.0, 0.9, 0.2, 2.0, 1.0, "partially_lapsed", 0.45, 1.0, 0.5, 1.0, 1.0, 0.9)

    payload = json.loads((settings.ml_dir / "model_card_family_future_citation_forecast.json").read_text(encoding="utf-8"))
    assert payload["pit_features_applied"] is True
    assert payload["observed_snapshot_filter_applied"] is True
    assert payload["observed_snapshot_rows_excluded"] == 1


def test_build_ml_phase03_family_forecast_derives_labels_from_citation_events_when_explicit_targets_are_absent(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.execution["phase03_allow_current_state_fallback"] = True
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_priority_year": 2015,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology",
                "family_size_docdb": 5,
                "active_jurisdiction_count": 3,
                "family_distinct_owner_count": 1,
                "active_grant_branch_count": 2,
                "family_earliest_priority_date": "2015-02-10",
            },
            {
                "docdb_family_id": 200,
                "family_priority_year": 2017,
                "is_main_window_family": True,
                "primary_wipo_field": "Digital communication",
                "family_size_docdb": 4,
                "active_jurisdiction_count": 2,
                "family_distinct_owner_count": 1,
                "active_grant_branch_count": 1,
                "family_earliest_priority_date": "2017-03-20",
            },
            {
                "docdb_family_id": 300,
                "family_priority_year": 2019,
                "is_main_window_family": True,
                "primary_wipo_field": "Electrical machinery, apparatus, energy",
                "family_size_docdb": 3,
                "active_jurisdiction_count": 1,
                "family_distinct_owner_count": 1,
                "active_grant_branch_count": 1,
                "family_earliest_priority_date": "2019-01-15",
            },
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_forward_citations_clean": 12.0,
                "family_forward_citations_weighted": 10.0,
                "family_rcf_score": 0.7,
                "family_fwd_cits5": 14.0,
                "family_fwd_cits7": 20.0,
            },
            {
                "docdb_family_id": 200,
                "family_forward_citations_clean": 6.0,
                "family_forward_citations_weighted": 5.0,
                "family_rcf_score": 0.4,
                "family_fwd_cits5": 8.0,
                "family_fwd_cits7": 12.0,
            },
            {
                "docdb_family_id": 300,
                "family_forward_citations_clean": 3.0,
                "family_forward_citations_weighted": 2.0,
                "family_rcf_score": 0.2,
                "family_fwd_cits5": 4.0,
                "family_fwd_cits7": 6.0,
            },
        ],
        settings.silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {
                "source_docdb_family_id": 9001,
                "cited_docdb_family_id": 100,
                "citation_date": "2016-01-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "A",
                "clean_edge_weight": 0.2,
            },
            {
                "source_docdb_family_id": 9002,
                "cited_docdb_family_id": 100,
                "citation_date": "2018-06-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "B",
                "clean_edge_weight": 0.3,
            },
            {
                "source_docdb_family_id": 9003,
                "cited_docdb_family_id": 100,
                "citation_date": "2021-01-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "C",
                "clean_edge_weight": 0.5,
            },
            {
                "source_docdb_family_id": 9004,
                "cited_docdb_family_id": 200,
                "citation_date": "2020-08-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "D",
                "clean_edge_weight": 0.4,
            },
            {
                "source_docdb_family_id": 9005,
                "cited_docdb_family_id": 200,
                "citation_date": "2023-04-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "E",
                "clean_edge_weight": 0.7,
            },
            {
                "source_docdb_family_id": 9006,
                "cited_docdb_family_id": 300,
                "citation_date": "2022-03-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "F",
                "clean_edge_weight": 0.6,
            },
            {
                "source_docdb_family_id": 9006,
                "cited_docdb_family_id": 300,
                "citation_date": "2024-03-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "F",
                "clean_edge_weight": 0.8,
            },
        ],
        settings.silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_quality_index_4_score": 0.8, "family_quality_index_6_score": 0.82, "family_generality_percentile": 0.7, "family_radicalness_percentile": 0.5, "family_science_grounding_percentile": 0.45},
            {"docdb_family_id": 200, "family_quality_index_4_score": 0.55, "family_quality_index_6_score": 0.58, "family_generality_percentile": 0.4, "family_radicalness_percentile": 0.3, "family_science_grounding_percentile": 0.25},
            {"docdb_family_id": 300, "family_quality_index_4_score": 0.6, "family_quality_index_6_score": 0.63, "family_generality_percentile": 0.42, "family_radicalness_percentile": 0.31, "family_science_grounding_percentile": 0.28},
        ],
        settings.silver_dir / "silver_family_oecd_quality.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_coverage_stability_score": 0.76},
            {"docdb_family_id": 200, "family_coverage_stability_score": 0.55},
            {"docdb_family_id": 300, "family_coverage_stability_score": 0.52},
        ],
        settings.silver_dir / "silver_family_coverage_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_composite_status": "fully_active"},
            {"docdb_family_id": 200, "family_composite_status": "fully_active"},
            {"docdb_family_id": 300, "family_composite_status": "partially_lapsed"},
        ],
        settings.silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "primary_wipo_field": "Computer technology"},
            {"docdb_family_id": 200, "primary_wipo_field": "Digital communication"},
            {"docdb_family_id": 300, "primary_wipo_field": "Electrical machinery, apparatus, energy"},
        ],
        settings.silver_dir / "silver_family_wipo_fields.parquet",
    )

    result = build_ml_phase03_family_future_citation_forecast(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    label_rows = con.execute(
        """
        select docdb_family_id, future_forward_citations_3y_raw, future_forward_citations_5y_raw
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(settings.ml_dir / "ml_label_family_future_citations.parquet")],
    ).fetchall()
    assert label_rows == [
        (100, 1.0, 2.0),
        (200, 1.0, 2.0),
        (300, 1.0, 1.0),
    ]

    payload = json.loads((settings.ml_dir / "model_card_family_future_citation_forecast.json").read_text(encoding="utf-8"))
    assert payload["label_source"] == "derived_from_citation_event_network"


def test_build_ml_phase03_family_forecast_fails_without_pit_for_derived_labels_by_default(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_priority_year": 2015,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology",
                "family_size_docdb": 5,
                "active_jurisdiction_count": 3,
                "family_distinct_owner_count": 1,
                "active_grant_branch_count": 2,
                "family_earliest_priority_date": "2015-02-10",
            }
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_forward_citations_clean": 12.0,
                "family_forward_citations_weighted": 10.0,
                "family_rcf_score": 0.7,
                "family_fwd_cits5": 14.0,
                "family_fwd_cits7": 20.0,
            }
        ],
        settings.silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {
                "source_docdb_family_id": 9001,
                "cited_docdb_family_id": 100,
                "citation_date": "2016-01-01",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "citing_assignee_name": "A",
                "clean_edge_weight": 0.2,
            }
        ],
        settings.silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_quality_index_4_score": 0.8, "family_quality_index_6_score": 0.82, "family_generality_percentile": 0.7, "family_radicalness_percentile": 0.5, "family_science_grounding_percentile": 0.45},
        ],
        settings.silver_dir / "silver_family_oecd_quality.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "family_coverage_stability_score": 0.76}],
        settings.silver_dir / "silver_family_coverage_metrics.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "family_composite_status": "fully_active"}],
        settings.silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100, "primary_wipo_field": "Computer technology"}],
        settings.silver_dir / "silver_family_wipo_fields.parquet",
    )

    result = build_ml_phase03_family_future_citation_forecast(settings).finish()
    assert result.status == "failed"
    assert any("Promotion-safe Phase 03 requires `silver_family_feature_snapshot_pit.parquet`" in warning for warning in result.warnings)
