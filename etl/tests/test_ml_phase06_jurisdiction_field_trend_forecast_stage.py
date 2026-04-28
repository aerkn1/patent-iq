from __future__ import annotations

import json
from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.ml.phase06 import build_ml_phase06_jurisdiction_field_trend_forecast
from patentiq_etl.ml.run import run_ml_phase06_jurisdiction_field_trend_forecast


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


def test_ml_phase06_jurisdiction_field_trend_forecast_stage_is_exposed() -> None:
    assert callable(build_ml_phase06_jurisdiction_field_trend_forecast)
    assert callable(run_ml_phase06_jurisdiction_field_trend_forecast)


def test_build_ml_phase06_jurisdiction_field_trend_forecast_materializes_contracts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    jurisdictions = ["US", "JP", "CN", "KR", "EP", "DE", "FR", "GB", "TW", "CA"]
    fields = [
        "Computer technology",
        "Digital communication",
        "Semiconductors",
        "Measurement",
        "Audio-visual technology",
    ]
    local_rows: list[dict[str, object]] = []
    global_rows: list[dict[str, object]] = []
    market_rows: list[dict[str, object]] = []
    for year in range(1996, 2026):
        for field_idx, field in enumerate(fields, start=1):
            global_value = (year - 1990) * field_idx + 10
            global_rows.append(
                {
                    "snapshot_year": year,
                    "wipo_industry_code": field,
                    "global_family_filings": global_value,
                    "prior_period_global_family_filings": max(global_value - field_idx, 0),
                    "global_growth_rate": float(field_idx),
                    "global_trend_coefficient": float(field_idx) * 1.2,
                    "counting_unit": "family_count",
                    "family_model": "test_model",
                    "method_version": "test_method_v1",
                }
            )
            market_rows.append(
                {
                    "segment_key": field,
                    "wipo_industry_code": field,
                    "as_of_year": year,
                    "current_snapshot_date": None,
                    "segment_heat_state_asof": "heating" if year % 3 == 0 else "stable",
                    "segment_priority_year_family_count_asof": float(global_value),
                    "segment_family_count_asof": float(global_value),
                    "segment_prior_family_count_asof": float(max(global_value - field_idx, 0)),
                    "segment_growth_index_asof": float(field_idx) / 10.0,
                    "segment_owner_count_hist_proxy_asof": 0,
                    "segment_blocking_density_asof": 0.0,
                    "segment_field_balance_asof": 0.0,
                    "segment_active_family_count_asof": 0,
                    "segment_active_weight_asof": 0.0,
                    "segment_active_jurisdiction_share_asof": 0.0,
                    "segment_enforceability_density_asof": 0.0,
                    "segment_top_owner_share_hist_proxy": 0.0,
                    "historical_compare_safe": True,
                    "historical_owner_truth_supported": False,
                    "current_owner_bridge_replayed_to_history": True,
                    "historical_oecd_supported": False,
                }
            )
            for jur_idx, jurisdiction in enumerate(jurisdictions, start=1):
                local_value = max((year - 1994) * field_idx + jur_idx % 4 + (year % 2), 0)
                local_rows.append(
                    {
                        "snapshot_year": year,
                        "jurisdiction_code": jurisdiction,
                        "wipo_industry_code": field,
                        "local_family_filings": local_value,
                        "prior_period_local_family_filings": max(local_value - field_idx, 0),
                        "local_growth_rate": float(field_idx) / 2.0,
                        "local_trend_coefficient": float(field_idx) + jur_idx / 20.0,
                        "counting_unit": "family_count",
                        "family_model": "test_model",
                        "method_version": "test_method_v1",
                    }
                )

    write_pylist_parquet(local_rows, settings.silver_dir / "silver_local_tech_trends_timeseries.parquet")
    write_pylist_parquet(global_rows, settings.silver_dir / "silver_global_tech_trends_timeseries.parquet")
    write_pylist_parquet(market_rows, settings.gold_dir / "gold_market_summary_pit.parquet")

    result = build_ml_phase06_jurisdiction_field_trend_forecast(settings)

    label_path = settings.ml_dir / "ml_label_jurisdiction_field_trend_future.parquet"
    feature_path = settings.ml_dir / "ml_feature_jurisdiction_field_trend_forecast.parquet"
    prediction_path = settings.ml_dir / "ml_prediction_jurisdiction_field_trend_forecast.parquet"
    split_path = settings.ml_dir / "ml_split_registry_phase06.parquet"
    model_card_path = settings.ml_dir / "model_card_jurisdiction_field_trend_forecast.json"

    assert result.status == "success"
    assert label_path.exists()
    assert feature_path.exists()
    assert prediction_path.exists()
    assert split_path.exists()
    assert model_card_path.exists()

    con = duckdb.connect()
    assert con.execute(f"select count(*) from read_parquet('{label_path}')").fetchone()[0] > 0
    assert con.execute(f"select count(*) from read_parquet('{feature_path}')").fetchone()[0] > 0
    assert con.execute(f"select count(*) from read_parquet('{prediction_path}')").fetchone()[0] > 0
    assert con.execute(f"select count(*) from read_parquet('{split_path}') where model_scope = 'jurisdiction_field_trend_forecast'").fetchone()[0] > 0

    payload = json.loads(model_card_path.read_text(encoding="utf-8"))
    assert payload["model_scope"] == "jurisdiction_field_trend_forecast"
    assert payload["status"] == "candidate_trained"
    assert payload["horizons"]["3y"]["status"] == "baseline_trained"
    assert payload["horizons"]["5y"]["status"] == "baseline_trained"
