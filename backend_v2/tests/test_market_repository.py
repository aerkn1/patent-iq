from pathlib import Path

import duckdb
import pytest

from config.settings import get_settings
from infrastructure.repositories.market_intelligence_repository import MarketIntelligenceRepository


def test_market_repository_prefers_market_serving_snapshot_for_base_views(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    market_path = serving_dir / "market_serving.duckdb"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "market": {
              "filename": "market_serving.duckdb",
              "tables": [
                "market_intelligence_overview",
                "market_intelligence_segments",
                "market_intelligence_timeseries"
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(market_path)) as con:
        con.execute(
            """
            create table market_intelligence_overview as
            select
                2::bigint as segment_count,
                1::bigint as rising_segment_count,
                1::bigint as cooling_segment_count,
                42::bigint as total_family_count,
                21.0::double as avg_segment_family_count
            """
        )
        con.execute(
            """
            create table market_intelligence_segments as
            select * from (
                values
                    (
                        'segment-computing'::varchar,
                        'Computer technology'::varchar,
                        'rising'::varchar,
                        24::bigint,
                        2023::integer,
                        2022::integer,
                        false,
                        DATE '2026-03-15'
                    ),
                    (
                        'segment-digital'::varchar,
                        'Digital communication'::varchar,
                        'cooling'::varchar,
                        18::bigint,
                        2023::integer,
                        2022::integer,
                        true,
                        DATE '2026-03-15'
                    )
            ) as t(
                segment_id,
                wipo_industry_code,
                market_state,
                total_family_count,
                latest_year,
                latest_comparable_year,
                latest_year_incomplete,
                snapshot_date
            )
            """
        )
        con.execute(
            """
            create table market_intelligence_timeseries as
            select * from (
                values
                    (2021::integer, 'Computer technology'::varchar, 8::bigint, 6::bigint, 'rising'::varchar, false, 'rising'::varchar, 2021::integer, DATE '2026-03-15'),
                    (2022::integer, 'Computer technology'::varchar, 10::bigint, 8::bigint, 'rising'::varchar, false, 'rising'::varchar, 2022::integer, DATE '2026-03-15'),
                    (2021::integer, 'Digital communication'::varchar, 7::bigint, 9::bigint, 'cooling'::varchar, false, 'cooling'::varchar, 2021::integer, DATE '2026-03-15')
            ) as t(
                family_priority_year,
                wipo_industry_code,
                family_count,
                prior_family_count,
                market_state,
                is_recent_priority_year_incomplete,
                market_state_ui_safe,
                latest_comparable_year,
                snapshot_date
            )
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path / "missing-etl-root"))
    get_settings.cache_clear()

    repository = MarketIntelligenceRepository()

    overview = repository.get_overview_snapshot()
    scope = repository.get_scope_summary()
    segments = repository.get_segments()
    timeseries = repository.get_timeseries(segment_id="Computer technology")

    assert overview["segment_count"] == 2
    assert scope["covered_field_count"] == 2
    assert scope["latest_market_year"] == 2023
    assert scope["latest_comparable_market_year"] == 2022
    assert [row["wipo_industry_code"] for row in segments] == ["Computer technology", "Digital communication"]
    assert [row["family_priority_year"] for row in timeseries] == [2021, 2022]
    assert all(row["wipo_industry_code"] == "Computer technology" for row in timeseries)

    get_settings.cache_clear()


def test_market_repository_prefers_analytics_serving_for_deep_views(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    analytics_path = serving_dir / "analytics_serving.duckdb"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "analytics": {
              "filename": "analytics_serving.duckdb",
              "tables": [
                "market_leaderboard_pit",
                "family_compare_pit",
                "market_citation_trend_pit"
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(analytics_path)) as con:
        con.execute(
            """
            create table market_leaderboard_pit as
            select * from (
                values
                    ('Computer technology'::varchar, 'owner'::varchar, 2023::integer, 1::integer, 'APPLE'::varchar, 'Apple'::varchar, null::bigint, null::double, null::double, null::double, null::varchar),
                    ('Computer technology'::varchar, 'family'::varchar, 2023::integer, 1::integer, null::varchar, null::varchar, 123::bigint, 0.8::double, 1.1::double, 0.6::double, 'fully_active'::varchar)
            ) as t(
                segment_key,
                leaderboard_entity_type,
                as_of_year,
                leaderboard_rank,
                owner_name_harmonized,
                owner_name_display_current,
                docdb_family_id,
                avg_blocking_score_asof,
                total_blocking_score_asof,
                field_presence_weight_asof,
                family_composite_status_asof
            )
            """
        )
        con.execute(
            """
            create table family_compare_pit as
            select
                123::bigint as docdb_family_id,
                2023::integer as as_of_year,
                'APPLE'::varchar as owner_name_harmonized_current,
                'Computer technology'::varchar as primary_wipo_field_current
            """
        )
        con.execute(
            """
            create table market_citation_trend_pit as
            select
                2023::integer as as_of_year,
                'Computer technology'::varchar as wipo_industry_code,
                9.0::double as citation_lethality_sum_raw
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path / "missing-etl-root"))
    get_settings.cache_clear()

    repository = MarketIntelligenceRepository()

    owner_rows = repository.get_segment_owners("Computer technology", as_of_year=2023)
    family_rows = repository.get_segment_families("Computer technology", as_of_year=2023)
    citation_rows = repository.get_citation_trends(segment_id="Computer technology", as_of_year=2023)

    assert owner_rows[0]["owner_name_harmonized"] == "APPLE"
    assert family_rows[0]["docdb_family_id"] == 123
    assert citation_rows[0]["wipo_industry_code"] == "Computer technology"

    get_settings.cache_clear()


def test_market_repository_raises_when_serving_table_is_missing_and_raw_fallback_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {}
        }
        """.strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path / "missing-etl-root"))
    get_settings.cache_clear()

    repository = MarketIntelligenceRepository()

    from infrastructure.duckdb import DuckDbProvider

    with DuckDbProvider().connect() as con:
        with pytest.raises(RuntimeError, match="market_citation_trend_pit"):
            repository._relation_for_path(con, repository.citation_trend_path)

    get_settings.cache_clear()
