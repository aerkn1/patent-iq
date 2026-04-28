from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
from lightgbm import LGBMClassifier

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.ml.phase_grant import _prepare_pending_grant_matrix, build_ml_pending_grant_pipeline, build_pending_grant_prediction_parquet
from patentiq_etl.ml.run import run_ml_pending_grant_pipeline


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


def test_ml_pending_grant_pipeline_stage_is_exposed() -> None:
    assert callable(build_ml_pending_grant_pipeline)
    assert callable(run_ml_pending_grant_pipeline)


def test_build_ml_pending_grant_pipeline_materializes_contracts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "family_priority_year": 2018,
                "family_earliest_priority_date": "2018-05-01",
                "primary_wipo_field": "Computer technology",
                "is_main_window_family": True,
            },
            {
                "docdb_family_id": 2,
                "family_priority_year": 2021,
                "family_earliest_priority_date": "2021-03-01",
                "primary_wipo_field": "Digital communication",
                "is_main_window_family": True,
            },
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2021,
                "snapshot_date": "2021-12-31",
                "last_pending_event_date": "2021-06-01",
                "replay_branch_state": "PENDING_ONLY",
                "pending_branch_flag": True,
                "active_branch_flag": False,
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2022,
                "snapshot_date": "2022-12-31",
                "last_pending_event_date": "2021-06-01",
                "replay_branch_state": "ACTIVE_GRANT",
                "pending_branch_flag": False,
                "active_branch_flag": True,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "EP",
                "snapshot_year": 2023,
                "snapshot_date": "2023-12-31",
                "last_pending_event_date": "2023-01-10",
                "replay_branch_state": "PENDING_ONLY",
                "pending_branch_flag": True,
                "active_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "EP",
                "snapshot_year": 2025,
                "snapshot_date": "2025-12-31",
                "last_pending_event_date": "2023-01-10",
                "replay_branch_state": "ACTIVE_GRANT",
                "pending_branch_flag": False,
                "active_branch_flag": True,
            },
        ],
        settings.silver_dir / "silver_branch_status_history_dense.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": "2021-12-31",
                "as_of_year": 2021,
                "family_composite_status_asof": "pending_emerging",
                "family_size_docdb_asof": 3.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_coverage_stability_score_asof": 0.8,
                "family_tech_breadth_wipo_count_asof": 2.0,
                "family_blocking_power_score_asof": 0.4,
                "family_enforceability_score_asof": 0.6,
                "family_rcf_score_asof": 0.5,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "data_completeness_pct_asof": 1.0,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": "2023-12-31",
                "as_of_year": 2023,
                "family_composite_status_asof": "pending_emerging",
                "family_size_docdb_asof": 2.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.7,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.5,
                "family_rcf_score_asof": 0.3,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.8,
                "data_completeness_pct_asof": 1.0,
            },
        ],
        settings.silver_dir / "silver_family_feature_snapshot_pit_dense.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "publn_auth": "US",
                "publn_nr": "100",
                "publn_kind": "A1",
                "publn_date": "2020-01-01",
                "is_application_stage": True,
                "is_grant_stage": False,
            },
            {
                "docdb_family_id": 1,
                "publn_auth": "US",
                "publn_nr": "101",
                "publn_kind": "B1",
                "publn_date": "2022-01-01",
                "is_application_stage": False,
                "is_grant_stage": True,
            },
            {
                "docdb_family_id": 2,
                "publn_auth": "EP",
                "publn_nr": "200",
                "publn_kind": "A1",
                "publn_date": "2023-01-01",
                "is_application_stage": True,
                "is_grant_stage": False,
            },
        ],
        settings.silver_dir / "silver_family_member_publications.parquet",
    )
    write_pylist_parquet(
        [
            {
                "snapshot_year": 2021,
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "local_family_filings": 10,
                "prior_period_local_family_filings": 8,
                "local_growth_rate": 0.25,
                "local_trend_coefficient": 1.4,
                "counting_unit": "family_count",
                "family_model": "mega_cluster_bounded",
                "method_version": "test_method_v1",
            },
            {
                "snapshot_year": 2023,
                "jurisdiction_code": "EP",
                "wipo_industry_code": "Digital communication",
                "local_family_filings": 6,
                "prior_period_local_family_filings": 4,
                "local_growth_rate": 0.5,
                "local_trend_coefficient": 1.6,
                "counting_unit": "family_count",
                "family_model": "mega_cluster_bounded",
                "method_version": "test_method_v1",
            },
        ],
        settings.silver_dir / "silver_local_tech_trends_timeseries.parquet",
    )

    result = build_ml_pending_grant_pipeline(settings)
    assert result.status == "success"

    label_path = settings.ml_dir / "ml_label_pending_grant_event.parquet"
    feature_path = settings.ml_dir / "ml_feature_pending_grant_pipeline.parquet"
    split_path = settings.ml_dir / "ml_split_registry_phase_grant.parquet"
    model_card_path = settings.ml_dir / "model_card_pending_grant_pipeline.json"

    assert label_path.exists()
    assert feature_path.exists()
    assert split_path.exists()
    assert model_card_path.exists()

    con = duckdb.connect()
    labels = con.execute(
        """
        select docdb_family_id, jurisdiction_code, as_of_year, grant_event_12m, grant_event_24m, observed_12m, observed_24m
        from read_parquet(?)
        order by docdb_family_id, jurisdiction_code, as_of_year
        """,
        [str(label_path)],
    ).fetchall()
    assert labels == [
        (1, "US", 2021, 1, 1, True, True),
        (2, "EP", 2023, 0, 1, True, True),
    ]

    features = con.execute(
        """
        select
            docdb_family_id,
            jurisdiction_code,
            primary_wipo_field,
            family_tech_breadth_wipo_count_asof,
            family_blocking_power_score_asof,
            family_enforceability_score_asof,
            application_stage_publication_count,
            grant_stage_publication_count,
            jurisdiction_field_grant_rate_prior_12m,
            jurisdiction_field_grant_rate_prior_24m,
            local_family_filings_asof,
            prior_period_local_family_filings_asof,
            local_growth_rate_asof,
            local_trend_coefficient_asof,
            jurisdiction_is_ep,
            jurisdiction_is_major_office
        from read_parquet(?)
        order by docdb_family_id, jurisdiction_code
        """,
        [str(feature_path)],
    ).fetchall()
    assert features == [
        (1, "US", "Computer technology", 2.0, 0.4, 0.6, 1.0, 0.0, 0.0, 0.0, 10.0, 8.0, 0.25, 1.4, False, True),
        (2, "EP", "Digital communication", 1.0, 0.2, 0.5, 1.0, 0.0, 1.0, 1.0, 6.0, 4.0, 0.5, 1.6, True, True),
    ]

    split_rows = con.execute(
        "select split_name from read_parquet(?) order by split_name",
        [str(split_path)],
    ).fetchall()
    assert split_rows == [("test",), ("train",)]

    model_card = json.loads(model_card_path.read_text(encoding="utf-8"))
    assert model_card["model_scope"] == "publication_or_subfamily_grant_probability"
    assert model_card["native_grain"] == "family_x_jurisdiction_asof_pending_branch_context"


def test_build_pending_grant_prediction_parquet_scores_current_pending_rows(tmp_path: Path) -> None:
    ml_dir = tmp_path / "etl/data/ml"
    silver_dir = tmp_path / "etl/data/silver"
    ensure_dir(ml_dir)
    ensure_dir(silver_dir)

    feature_path = ml_dir / "ml_feature_pending_grant_pipeline.parquet"
    branch_history_path = silver_dir / "silver_branch_status_history_dense.parquet"
    model_card_path = ml_dir / "model_card_pending_grant_pipeline.json"
    calibration_path = ml_dir / "pending_grant_pipeline_calibration.json"
    model_12m_path = ml_dir / "pending_grant_pipeline_12m_model.txt"
    model_24m_path = ml_dir / "pending_grant_pipeline_24m_model.txt"
    output_path = ml_dir / "ml_prediction_pending_grant_pipeline.parquet"

    def feature_row(
        family_id: int,
        office: str,
        as_of_date: str,
        *,
        field: str,
        family_age: float,
        pending_age: float,
        blocking: float,
        enforceability: float,
        citations: float,
        local_filings: float,
    ) -> dict[str, object]:
        return {
            "docdb_family_id": family_id,
            "jurisdiction_code": office,
            "as_of_date": as_of_date,
            "as_of_year": int(as_of_date[:4]),
            "family_priority_year": int(as_of_date[:4]) - int(round(family_age)),
            "primary_wipo_field": field,
            "family_age_years": family_age,
            "pending_age_years": pending_age,
            "family_composite_status_asof": "pending_emerging",
            "family_size_docdb_asof": 3.0 + family_id / 10.0,
            "family_jurisdiction_count_asof": 1.0 + (family_id % 3),
            "family_coverage_stability_score_asof": 0.6 + family_id / 100.0,
            "family_tech_breadth_wipo_count_asof": 1.0 + (family_id % 2),
            "family_blocking_power_score_asof": blocking,
            "family_enforceability_score_asof": enforceability,
            "family_rcf_score_asof": 0.3 + family_id / 20.0,
            "pre_asof_forward_citations_clean": citations,
            "pre_asof_forward_citations_weighted": citations * 0.8,
            "data_completeness_pct_asof": 0.9,
            "application_stage_publication_count": 2.0 + (family_id % 2),
            "grant_stage_publication_count": float(family_id % 2),
            "jurisdiction_field_grant_rate_prior_12m": 0.2 + family_id / 100.0,
            "jurisdiction_field_grant_rate_prior_24m": 0.3 + family_id / 100.0,
            "local_family_filings_asof": local_filings,
            "prior_period_local_family_filings_asof": max(local_filings - 1.0, 0.0),
            "local_growth_rate_asof": 0.1 + family_id / 200.0,
            "local_trend_coefficient_asof": 1.0 + family_id / 50.0,
            "jurisdiction_is_ep": office == "EP",
            "jurisdiction_is_us": office == "US",
            "jurisdiction_is_cn": office == "CN",
            "jurisdiction_is_jp": office == "JP",
            "jurisdiction_is_kr": office == "KR",
            "jurisdiction_is_major_office": office in {"EP", "US", "CN", "JP", "KR"},
        }

    scoring_rows = [
        feature_row(1, "US", "2026-03-15", field="Computer technology", family_age=6.0, pending_age=1.2, blocking=0.82, enforceability=0.76, citations=8.0, local_filings=14.0),
        feature_row(2, "EP", "2026-03-15", field="Digital communication", family_age=4.0, pending_age=0.9, blocking=0.44, enforceability=0.52, citations=4.0, local_filings=8.0),
        feature_row(4, "US", "2026-03-15", field="Computer technology", family_age=3.0, pending_age=0.6, blocking=0.31, enforceability=0.4, citations=2.0, local_filings=6.0),
        feature_row(3, "US", "2025-03-15", field="Computer technology", family_age=5.0, pending_age=1.5, blocking=0.55, enforceability=0.5, citations=5.0, local_filings=10.0),
    ]
    write_pylist_parquet(scoring_rows, feature_path)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "jurisdiction_code": "US", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": True},
            {"docdb_family_id": 2, "jurisdiction_code": "EP", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": True},
            {"docdb_family_id": 3, "jurisdiction_code": "US", "snapshot_year": 2025, "snapshot_date": "2025-03-15", "pending_branch_flag": True},
            {"docdb_family_id": 3, "jurisdiction_code": "US", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": False},
            {"docdb_family_id": 4, "jurisdiction_code": "US", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": True},
        ],
        branch_history_path,
    )

    training_rows = pd.DataFrame(
        [
            feature_row(11, "US", "2024-03-15", field="Computer technology", family_age=7.0, pending_age=1.4, blocking=0.9, enforceability=0.8, citations=9.0, local_filings=16.0),
            feature_row(12, "US", "2024-03-15", field="Computer technology", family_age=2.0, pending_age=0.4, blocking=0.18, enforceability=0.28, citations=1.0, local_filings=5.0),
            feature_row(13, "EP", "2024-03-15", field="Digital communication", family_age=5.0, pending_age=0.9, blocking=0.7, enforceability=0.67, citations=7.0, local_filings=11.0),
            feature_row(14, "EP", "2024-03-15", field="Digital communication", family_age=3.0, pending_age=0.3, blocking=0.21, enforceability=0.34, citations=2.0, local_filings=4.0),
            feature_row(15, "US", "2025-03-15", field="Computer technology", family_age=6.0, pending_age=1.1, blocking=0.78, enforceability=0.71, citations=6.0, local_filings=13.0),
            feature_row(16, "EP", "2025-03-15", field="Digital communication", family_age=2.0, pending_age=0.5, blocking=0.26, enforceability=0.38, citations=2.5, local_filings=5.0),
        ]
    )
    x_train, encoders = _prepare_pending_grant_matrix(training_rows)
    y_train_12m = [1, 0, 1, 0, 1, 0]
    y_train_24m = [1, 0, 1, 0, 1, 0]

    model_12m = LGBMClassifier(
        n_estimators=12,
        learning_rate=0.1,
        num_leaves=7,
        min_child_samples=1,
        random_state=42,
        verbosity=-1,
    )
    model_24m = LGBMClassifier(
        n_estimators=12,
        learning_rate=0.1,
        num_leaves=7,
        min_child_samples=1,
        random_state=43,
        verbosity=-1,
    )
    model_12m.fit(x_train, y_train_12m)
    model_24m.fit(x_train, y_train_24m)
    model_12m.booster_.save_model(str(model_12m_path))
    model_24m.booster_.save_model(str(model_24m_path))

    model_card_path.write_text(
        json.dumps(
            {
                "model_scope": "publication_or_subfamily_grant_probability",
                "feature_encoders": encoders,
                "baseline_results": {
                    "12m": {"test_metrics": {"office_subgroups": {"US": {"rows": 15000}, "EP": {"rows": 3000}}}},
                    "24m": {"test_metrics": {"office_subgroups": {"US": {"rows": 15000}, "EP": {"rows": 3000}}}},
                },
            }
        ),
        encoding="utf-8",
    )
    calibration_path.write_text(
        json.dumps(
            {
                "horizons": {
                    "12m": {"method": "identity", "params": {}},
                    "24m": {"method": "identity", "params": {}},
                }
            }
        ),
        encoding="utf-8",
    )

    metrics = build_pending_grant_prediction_parquet(
        feature_path=feature_path,
        branch_history_path=branch_history_path,
        model_card_path=model_card_path,
        calibration_path=calibration_path,
        model_12m_path=model_12m_path,
        model_24m_path=model_24m_path,
        output_path=output_path,
        chunk_row_limit=10,
        temp_dir=ml_dir / "_tmp_prediction_chunks",
    )

    assert metrics == {
        "current_pending_pair_count": 3,
        "scored_row_count": 3,
        "partition_count": 2,
        "chunk_count": 2,
    }
    assert output_path.exists()

    con = duckdb.connect()
    scored_ids = con.execute(
        "select docdb_family_id from read_parquet(?) order by jurisdiction_code, docdb_family_id",
        [str(output_path)],
    ).fetchall()
    assert scored_ids == [("2",), ("1",), ("4",)]

    us_rows = con.execute(
        """
        select
            docdb_family_id,
            grant_probability_calibrated_24m,
            pending_grant_rank_within_office_24m,
            pending_grant_percentile_within_office_24m,
            pending_grant_priority_tier_24m,
            office_support_level
        from read_parquet(?)
        where jurisdiction_code = 'US'
        order by pending_grant_rank_within_office_24m
        """,
        [str(output_path)],
    ).fetchall()
    assert len(us_rows) == 2
    assert us_rows[0][1] >= us_rows[1][1]
    assert us_rows[0][2:] == (1, 100.0, "top", "strong")
    assert us_rows[1][2:] == (2, 0.0, "monitor", "strong")

    ep_rows = con.execute(
        """
        select
            docdb_family_id,
            pending_grant_rank_within_office_24m,
            pending_grant_percentile_within_office_24m,
            pending_grant_priority_tier_24m,
            office_support_level
        from read_parquet(?)
        where jurisdiction_code = 'EP'
        """,
        [str(output_path)],
    ).fetchall()
    assert ep_rows == [("2", 1, 100.0, "top", "moderate")]
