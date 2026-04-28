from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from config.settings import get_settings
from infrastructure.repositories.portfolio_repository import PortfolioRepository


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0]}
    table = pa.table(columns)
    pq.write_table(table, path)


def _patch_test_settings(
    monkeypatch,
    tmp_path: Path,
    manifest_path: Path,
    *,
    raw_fallback_enabled: bool = True,
) -> None:
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(tmp_path / "missing-serving"))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    monkeypatch.setenv(
        "PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED",
        "true" if raw_fallback_enabled else "false",
    )
    get_settings.cache_clear()


def test_gold_citation_views_exclude_self_owner_rows_only_for_owner_leaderboard(tmp_path: Path) -> None:
    get_settings.cache_clear()
    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    attacker = tmp_path / "gold_portfolio_attacker_momentum.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch
    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        owner_bridge,
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "is_primary_owner": True,
            }
        ],
    )
    _write_parquet(
        attacker,
        [
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2025,
                "citing_assignee_name": "APPLE",
                "wipo_field": "Digital communication",
                "jurisdiction_code": "US",
                "citation_event_count": 10,
                "clean_citation_count": 10.0,
                "citation_lethality_sum_raw": 100.0,
                "attacker_pressure_index": 99.0,
                "momentum_direction": "heating",
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2025,
                "citing_assignee_name": "QUALCOMM",
                "wipo_field": "Digital communication",
                "jurisdiction_code": "US",
                "citation_event_count": 7,
                "clean_citation_count": 7.0,
                "citation_lethality_sum_raw": 50.0,
                "attacker_pressure_index": 80.0,
                "momentum_direction": "heating",
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2025,
                "citing_assignee_name": "UNKNOWN_OWNER",
                "wipo_field": "Digital communication",
                "jurisdiction_code": "US",
                "citation_event_count": 4,
                "clean_citation_count": 4.0,
                "citation_lethality_sum_raw": 25.0,
                "attacker_pressure_index": 40.0,
                "momentum_direction": "flat",
                "method_version": "test",
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.portfolio_citation_attacker_path = attacker

    attackers = repository.get_owner_citation_attackers("APPLE", limit=10, offset=0)
    assert len(attackers) == 1
    assert attackers[0]["citing_assignee_name"] == "QUALCOMM"

    fields = repository.get_owner_citation_fields("APPLE", limit=10, offset=0)
    assert len(fields) == 1
    assert fields[0]["wipo_field"] == "Digital communication"
    assert fields[0]["citation_event_count"] == 21

    jurisdictions = repository.get_owner_citation_jurisdictions("APPLE", limit=10, offset=0)
    assert len(jurisdictions) == 1
    assert jurisdictions[0]["jurisdiction_code"] == "US"
    assert jurisdictions[0]["citation_event_count"] == 21
    monkeypatch.undo()
    get_settings.cache_clear()


def test_citation_year_slice_with_cross_filter_uses_attacker_grain(tmp_path: Path) -> None:
    get_settings.cache_clear()
    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    attacker = tmp_path / "gold_portfolio_attacker_momentum.parquet"
    field = tmp_path / "gold_portfolio_citation_pressure_by_field.parquet"
    jurisdiction = tmp_path / "gold_portfolio_citation_pressure_by_jurisdiction.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        owner_bridge,
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "is_primary_owner": True,
            }
        ],
    )
    _write_parquet(
        attacker,
        [
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "citing_assignee_name": "QUALCOMM",
                "wipo_field": "Computer technology",
                "jurisdiction_code": "US",
                "citation_event_count": 5,
                "clean_citation_count": 5.0,
                "citation_lethality_sum_raw": 5.0,
                "attacker_pressure_index": 50.0,
                "momentum_direction": "flat",
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "citing_assignee_name": "QUALCOMM",
                "wipo_field": "Computer technology",
                "jurisdiction_code": "EP",
                "citation_event_count": 7,
                "clean_citation_count": 7.0,
                "citation_lethality_sum_raw": 7.0,
                "attacker_pressure_index": 70.0,
                "momentum_direction": "flat",
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "citing_assignee_name": "APPLE",
                "wipo_field": "Computer technology",
                "jurisdiction_code": "EP",
                "citation_event_count": 3,
                "clean_citation_count": 3.0,
                "citation_lethality_sum_raw": 3.0,
                "attacker_pressure_index": 30.0,
                "momentum_direction": "flat",
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "citing_assignee_name": "_",
                "wipo_field": "Digital communication",
                "jurisdiction_code": "EP",
                "citation_event_count": 2,
                "clean_citation_count": 2.0,
                "citation_lethality_sum_raw": 2.0,
                "attacker_pressure_index": 20.0,
                "momentum_direction": "flat",
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "citing_assignee_name": "ERICSSON",
                "wipo_field": "Digital communication",
                "jurisdiction_code": "EP",
                "citation_event_count": 11,
                "clean_citation_count": 11.0,
                "citation_lethality_sum_raw": 11.0,
                "attacker_pressure_index": 90.0,
                "momentum_direction": "flat",
                "method_version": "test",
            },
        ],
    )
    _write_parquet(
        field,
        [
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "wipo_field": "Computer technology",
                "citing_assignee_count": 1,
                "citation_event_count": 15.0,
                "clean_citation_count": 15.0,
                "citation_lethality_sum_raw": 15.0,
                "citation_pressure_index": 60.0,
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "wipo_field": "Digital communication",
                "citing_assignee_count": 2,
                "citation_event_count": 13.0,
                "clean_citation_count": 13.0,
                "citation_lethality_sum_raw": 13.0,
                "citation_pressure_index": 50.0,
                "method_version": "test",
            },
        ],
    )
    _write_parquet(
        jurisdiction,
        [
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "jurisdiction_code": "US",
                "citing_assignee_count": 1,
                "wipo_field_count": 1,
                "citation_event_count": 5.0,
                "clean_citation_count": 5.0,
                "citation_lethality_sum_raw": 5.0,
                "citation_pressure_index": 40.0,
                "method_version": "test",
            },
            {
                "owner_name_harmonized": "APPLE",
                "current_snapshot_date": "2026-03-15",
                "year": 2024,
                "jurisdiction_code": "EP",
                "citing_assignee_count": 4,
                "wipo_field_count": 2,
                "citation_event_count": 23.0,
                "clean_citation_count": 23.0,
                "citation_lethality_sum_raw": 23.0,
                "citation_pressure_index": 80.0,
                "method_version": "test",
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.portfolio_citation_attacker_path = attacker
    repository.portfolio_citation_field_path = field
    repository.portfolio_citation_jurisdiction_path = jurisdiction

    fields = repository.get_owner_citation_fields(
        "APPLE",
        limit=10,
        offset=0,
        jurisdiction_code="US",
        year_from=2024,
        year_to=2024,
    )
    assert len(fields) == 1
    assert fields[0]["wipo_field"] == "Computer technology"
    assert fields[0]["citation_event_count"] == 5

    ep_fields = repository.get_owner_citation_fields(
        "APPLE",
        limit=10,
        offset=0,
        jurisdiction_code="EP",
        year_from=2024,
        year_to=2024,
    )
    assert len(ep_fields) == 2
    assert sum(float(row["clean_citation_count"]) for row in ep_fields) == 23.0

    jurisdictions = repository.get_owner_citation_jurisdictions(
        "APPLE",
        limit=10,
        offset=0,
        wipo_field="Computer technology",
        year_from=2024,
        year_to=2024,
    )
    assert len(jurisdictions) == 2
    assert jurisdictions[0]["jurisdiction_code"] == "EP"
    assert jurisdictions[0]["citation_event_count"] == 10
    assert jurisdictions[1]["jurisdiction_code"] == "US"
    assert jurisdictions[1]["citation_event_count"] == 5

    monkeypatch.undo()
    get_settings.cache_clear()


def test_owner_filing_timeseries_prefers_core_serving_snapshot(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    core_path = serving_dir / "core_serving.duckdb"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "core": {
              "filename": "core_serving.duckdb",
              "tables": ["portfolio_filing_timeseries"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table portfolio_filing_timeseries as
            select * from (
                values
                    (
                        'APPLE'::varchar,
                        'Apple'::varchar,
                        2022::integer,
                        DATE '2026-03-15',
                        4::bigint,
                        4::bigint,
                        4::bigint,
                        0::bigint,
                        1.0::double,
                        'accelerating'::varchar,
                        'test'::varchar
                    ),
                    (
                        'APPLE'::varchar,
                        'Apple'::varchar,
                        2023::integer,
                        DATE '2026-03-15',
                        5::bigint,
                        9::bigint,
                        9::bigint,
                        4::bigint,
                        1.25::double,
                        'accelerating'::varchar,
                        'test'::varchar
                    )
            ) as t(
                owner_name_harmonized,
                owner_name_display,
                filing_year,
                current_snapshot_date,
                family_filing_count,
                cumulative_family_count,
                rolling_3y_family_filing_count,
                prior_3y_family_filing_count,
                rolling_3y_change_pct,
                momentum_direction,
                method_version
            )
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    _patch_test_settings(monkeypatch, tmp_path, manifest_path, raw_fallback_enabled=False)

    repository = PortfolioRepository()
    rows = repository.get_owner_filing_timeseries("APPLE", year_from=2022, year_to=2023)

    assert [row["filing_year"] for row in rows] == [2022, 2023]
    assert rows[0]["family_filing_count"] == 4
    assert rows[1]["cumulative_family_count"] == 9
    assert rows[1]["momentum_direction"] == "accelerating"

    get_settings.cache_clear()


def test_portfolio_repository_prefers_analytics_serving_for_detail_views(tmp_path: Path, monkeypatch) -> None:
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
                    "family_owner_bridge",
                    "portfolio_field_timeseries",
                    "portfolio_compare_pit",
                    "portfolio_attacker_momentum",
                    "enriched_citation_network"
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
            create table family_owner_bridge as
            select
                101::bigint as docdb_family_id,
                'APPLE'::varchar as owner_name_harmonized,
                'Apple'::varchar as owner_name_display,
                true as is_primary_owner
            """
        )
        con.execute(
            """
            create table portfolio_field_timeseries as
            select
                'APPLE'::varchar as owner_name_harmonized,
                DATE '2026-03-15' as snapshot_date,
                'Computer technology'::varchar as wipo_field,
                2::bigint as active_family_count,
                0.8::double as enforceability_score,
                0.7::double as heritage_score
            """
        )
        con.execute(
            """
            create table portfolio_compare_pit as
            select * from (
                values
                    ('APPLE'::varchar, 2025::integer, true, 1.0::double),
                    ('APPLE'::varchar, 2024::integer, true, 1.0::double)
            ) as t(owner_name_harmonized, as_of_year, historical_compare_safe, portfolio_avg_enforceability_score_asof)
            """
        )
        con.execute(
            """
            create table portfolio_attacker_momentum as
            select
                'APPLE'::varchar as owner_name_harmonized,
                2025::integer as year,
                'QUALCOMM'::varchar as citing_assignee_name,
                'Computer technology'::varchar as wipo_field,
                'US'::varchar as jurisdiction_code,
                5::bigint as citation_event_count,
                5.0::double as clean_citation_count,
                9.0::double as citation_lethality_sum_raw
            """
        )
        con.execute("create table enriched_citation_network(dummy integer)")

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path / "missing-etl-root"))
    get_settings.cache_clear()

    repository = PortfolioRepository()

    field_rows = repository.get_owner_field_timeseries("APPLE")
    compare_rows = repository.get_owner_compare_timeslice("APPLE", base_year=2025, compare_year=2024)
    attacker_rows = repository.get_owner_citation_attackers("APPLE")

    assert [row["wipo_field"] for row in field_rows] == ["Computer technology"]
    assert [row["as_of_year"] for row in compare_rows] == [2025, 2024]
    assert attacker_rows[0]["citing_assignee_name"] == "QUALCOMM"

    get_settings.cache_clear()


def test_portfolio_repository_prefers_analytics_serving_for_current_views_and_pending_grants(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
                    "portfolio_summary",
                    "portfolio_forecast_summary",
                    "portfolio_forecast_segments",
                    "portfolio_forecast_contributors",
                    "portfolio_field_timeseries",
                    "family_owner_bridge",
                    "family_summary",
                    "family_blocking_power",
                    "branch_status_history_dense",
                    "pending_grant_prediction_pipeline"
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
            create table portfolio_summary as
            select * from (
                values
                    (
                        'APPLE'::varchar,
                        'Apple'::varchar,
                        DATE '2026-03-15',
                        1.2::double,
                        0.8::double,
                        0.7::double,
                        0.9::double,
                        0.6::double,
                        0.5::double,
                        1::bigint
                    ),
                    (
                        'QUALCOMM'::varchar,
                        'Qualcomm'::varchar,
                        DATE '2026-03-15',
                        1.0::double,
                        0.6::double,
                        0.5::double,
                        0.7::double,
                        0.4::double,
                        0.3::double,
                        3::bigint
                    )
            ) as t(
                owner_name_harmonized,
                owner_name_display,
                snapshot_date,
                portfolio_total_mass_score,
                portfolio_current_threat_score,
                portfolio_heritage_score,
                portfolio_avg_blocking_power_within_mega_cluster,
                portfolio_hit_rate_top_decile,
                portfolio_crown_jewel_index,
                portfolio_family_count_within_mega_cluster
            )
            """
        )
        con.execute(
            """
            create table portfolio_forecast_summary as
            select
                'APPLE'::varchar as owner_name_harmonized,
                'Apple'::varchar as owner_name_display,
                DATE '2026-03-15' as snapshot_date,
                0.42::double as portfolio_predicted_growth_rate_reference
            """
        )
        con.execute(
            """
            create table portfolio_forecast_segments as
            select * from (
                values
                    (
                        'APPLE'::varchar,
                        DATE '2026-03-15',
                        '3y'::varchar,
                        'Computer technology'::varchar,
                        2::bigint,
                        'heating'::varchar,
                        0.25::double,
                        'strong'::varchar
                    ),
                    (
                        'APPLE'::varchar,
                        DATE '2026-03-15',
                        '3y'::varchar,
                        'Digital communication'::varchar,
                        1::bigint,
                        'stable'::varchar,
                        0.05::double,
                        'moderate'::varchar
                    )
            ) as t(
                owner_name_harmonized,
                snapshot_date,
                horizon,
                wipo_field,
                portfolio_active_family_count_in_field,
                predicted_direction_band,
                predicted_growth_rate_reference,
                support_level
            )
            """
        )
        con.execute(
            """
            create table portfolio_forecast_contributors as
            select
                'APPLE'::varchar as owner_name_harmonized,
                'phase03_future_citations'::varchar as contributor_scope,
                '3y'::varchar as horizon,
                '101'::varchar as contributor_entity_id,
                1.0::double as contribution_share,
                12.0::double as contribution_value
            """
        )
        con.execute(
            """
            create table portfolio_field_timeseries as
            select
                'APPLE'::varchar as owner_name_harmonized,
                DATE '2026-03-15' as snapshot_date,
                'Computer technology'::varchar as wipo_field,
                1::bigint as active_family_count,
                0.5::double as enforceability_score,
                0.4::double as heritage_score
            """
        )
        con.execute(
            """
            create table family_owner_bridge as
            select
                101::bigint as docdb_family_id,
                'APPLE'::varchar as owner_name_harmonized,
                'Apple'::varchar as owner_name_display,
                true as is_primary_owner
            """
        )
        con.execute(
            """
            create table family_summary as
            select
                101::bigint as docdb_family_id,
                'fully_active'::varchar as family_composite_status,
                2022::integer as family_priority_year,
                'Computer technology'::varchar as primary_wipo_field
            """
        )
        con.execute(
            """
            create table family_blocking_power as
            select
                101::bigint as docdb_family_id,
                77.0::double as family_ui_blocking_power_score
            """
        )
        con.execute(
            """
            create table branch_status_history_dense as
            select
                101::bigint as docdb_family_id,
                'US'::varchar as jurisdiction_code,
                DATE '2026-03-15' as snapshot_date,
                2026::integer as snapshot_year,
                true as pending_branch_flag
            """
        )
        con.execute(
            """
            create table pending_grant_prediction_pipeline as
            select
                101::bigint as docdb_family_id,
                'US'::varchar as jurisdiction_code,
                DATE '2026-03-15' as as_of_date,
                'Computer technology'::varchar as primary_wipo_field,
                1.5::double as pending_age_years,
                4.0::double as family_age_years,
                77.0::double as family_blocking_power_score_asof,
                0.72::double as family_enforceability_score_asof,
                0.64::double as family_rcf_score_asof,
                0.95::double as data_completeness_pct_asof,
                0.61::double as grant_probability_calibrated_12m,
                0.83::double as grant_probability_calibrated_24m,
                3::bigint as pending_grant_rank_within_office_12m,
                88.0::double as pending_grant_percentile_within_office_12m,
                1::bigint as pending_grant_rank_within_office_24m,
                97.0::double as pending_grant_percentile_within_office_24m,
                'strong'::varchar as office_support_level
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path / "missing-etl-root"))
    get_settings.cache_clear()

    repository = PortfolioRepository()

    summary = repository.get_owner_summary("APPLE")
    peer_context = repository.get_owner_summary_peer_context("APPLE")
    search_rows = repository.search_owners("Apple")
    forecast_summary = repository.get_owner_forecast_summary("APPLE")
    family_status = repository.get_owner_family_status_counts("APPLE")
    in_scope_status = repository.get_owner_in_scope_family_status_counts("APPLE")
    forecast_sections = repository.get_owner_forecast_sections("APPLE")
    families = repository.get_owner_families("APPLE")
    fields = repository.get_owner_fields("APPLE")
    filings = repository.get_owner_filing_timeseries("APPLE", year_from=2022, year_to=2022)
    pending_grants = repository.get_owner_pending_grant_sections("APPLE")
    latest_year = repository.get_latest_snapshot_year()

    assert summary["owner_name_harmonized"] == "APPLE"
    assert peer_context["owner_name_harmonized"] == "APPLE"
    assert search_rows[0]["owner_name_harmonized"] == "APPLE"
    assert forecast_summary["owner_name_harmonized"] == "APPLE"
    assert family_status["family_count"] == 1
    assert family_status["active_family_count"] == 1
    assert in_scope_status["family_count"] == 1
    assert forecast_sections[0]["wipo_field"] == "Computer technology"
    assert families[0]["family_id"] == "101"
    assert float(families[0]["blocking_score"]) == 77.0
    assert fields[0]["field"] == "Computer technology"
    assert filings[0]["filing_year"] == 2022
    assert pending_grants["serving_ready"] is True
    assert pending_grants["summary"]["pending_pipeline_branch_count"] == 1
    assert pending_grants["branches"][0]["priority_tier"] == "top"
    assert latest_year == 2026

    get_settings.cache_clear()


def test_citation_cpc_groups_replays_cited_family_cpc_with_citation_slice_filters(tmp_path: Path) -> None:
    get_settings.cache_clear()
    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_classification_mix = tmp_path / "gold_family_classification_mix_pit.parquet"
    enriched_citation_network = tmp_path / "silver_enriched_citation_network.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        owner_bridge,
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "is_primary_owner": True,
            },
            {
                "docdb_family_id": 2,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "is_primary_owner": True,
            },
        ],
    )
    _write_parquet(
        family_classification_mix,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2025,
                "as_of_date": "2025-12-31",
                "cpc_main_groups_asof": ["H04L1/00", "H04W72/00"],
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2025,
                "as_of_date": "2025-12-31",
                "cpc_main_groups_asof": ["G06F3/00"],
            },
        ],
    )
    _write_parquet(
        enriched_citation_network,
        [
            {
                "cited_docdb_family_id": 1,
                "citation_year": 2024,
                "citing_primary_wipo_field": "Computer technology",
                "citing_jurisdiction_code": "US",
                "clean_edge_weight": 1.0,
                "citation_lethality_score": 2.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "cited_docdb_family_id": 1,
                "citation_year": 2025,
                "citing_primary_wipo_field": "Digital communication",
                "citing_jurisdiction_code": "EP",
                "clean_edge_weight": 2.0,
                "citation_lethality_score": 3.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "cited_docdb_family_id": 2,
                "citation_year": 2025,
                "citing_primary_wipo_field": "Digital communication",
                "citing_jurisdiction_code": "EP",
                "clean_edge_weight": 4.0,
                "citation_lethality_score": 5.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_classification_mix_path = family_classification_mix
    repository.enriched_citation_network_path = enriched_citation_network

    all_rows = repository.get_owner_citation_cpc_groups("APPLE", limit=10, offset=0)
    assert [row["cpc_main_group"] for row in all_rows] == ["G06F3/00", "H04L1/00", "H04W72/00"]
    assert all_rows[0]["citation_event_count"] == 1
    assert all_rows[0]["clean_citation_count"] == 4.0
    assert all_rows[0]["citation_lethality_sum"] == 5.0
    assert all_rows[0]["cited_family_count"] == 1

    filtered_rows = repository.get_owner_citation_cpc_groups(
        "APPLE",
        limit=10,
        offset=0,
        wipo_field="Digital communication",
        jurisdiction_code="EP",
        year_from=2025,
        year_to=2025,
    )
    assert [row["cpc_main_group"] for row in filtered_rows] == ["G06F3/00", "H04L1/00", "H04W72/00"]
    assert filtered_rows[0]["latest_citation_year"] == 2025
    assert filtered_rows[0]["citation_event_count"] == 1
    assert filtered_rows[0]["clean_citation_count"] == 4.0
    assert filtered_rows[0]["citation_lethality_sum"] == 5.0
    assert filtered_rows[0]["cited_family_count"] == 1
    assert filtered_rows[0]["latest_citation_year"] == 2025
    assert filtered_rows[1]["citation_event_count"] == 1
    assert filtered_rows[1]["clean_citation_count"] == 2.0
    assert filtered_rows[2]["citation_event_count"] == 1
    assert filtered_rows[2]["clean_citation_count"] == 2.0

    monkeypatch.undo()
    get_settings.cache_clear()


def test_search_and_summary_skip_placeholder_owner_rows(tmp_path: Path) -> None:
    get_settings.cache_clear()
    summary = tmp_path / "gold_portfolio_summary.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch
    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        summary,
        [
            {
                "owner_name_harmonized": "UNKNOWN_OWNER",
                "owner_name_display": "Unknown Owner",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 999,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 42,
            },
            {
                "owner_name_harmonized": "SAM",
                "owner_name_display": "Sam",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 1,
            },
            {
                "owner_name_harmonized": "SAMSUNG_ELECTRONICS_COMPANY",
                "owner_name_display": "Samsung Electronics Company",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 4200,
            },
            {
                "owner_name_harmonized": "TESLA",
                "owner_name_display": "Tesla",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 356,
            },
            {
                "owner_name_harmonized": "TES_COMPANY",
                "owner_name_display": "Tes Company",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 502,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.summary_path = summary

    assert repository.search_owners("unknown", limit=10) == []
    assert repository.search_owners("sam", limit=10)[0]["owner_name_harmonized"] == "SAMSUNG_ELECTRONICS_COMPANY"
    assert repository.search_owners("tes", limit=10)[0]["owner_name_harmonized"] == "TESLA"
    apple_summary = repository.get_owner_summary("APPLE")
    assert apple_summary["owner_name_harmonized"] == "APPLE"
    assert repository.get_owner_summary("UNKNOWN_OWNER") == {}
    monkeypatch.undo()
    get_settings.cache_clear()


def test_get_owner_classification_uses_selected_and_previous_year_for_trajectory(tmp_path: Path) -> None:
    get_settings.cache_clear()
    classification_mix = tmp_path / "gold_portfolio_classification_mix_pit.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        classification_mix,
        [
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "classification_type": "CPC_MAIN_GROUP",
                "as_of_year": 2024,
                "classification_code": "H01L",
                "classification_label": "Semiconductors",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 0.30,
                "portfolio_family_count_in_classification_asof": 3,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "classification_type": "CPC_MAIN_GROUP",
                "as_of_year": 2024,
                "classification_code": "G06F",
                "classification_label": "Computing",
                "classification_rank_within_owner_year": 2,
                "portfolio_family_share_asof": 0.20,
                "portfolio_family_count_in_classification_asof": 2,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "classification_type": "CPC_MAIN_GROUP",
                "as_of_year": 2025,
                "classification_code": "H01L",
                "classification_label": "Semiconductors",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 0.40,
                "portfolio_family_count_in_classification_asof": 4,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "classification_type": "CPC_MAIN_GROUP",
                "as_of_year": 2025,
                "classification_code": "G06F",
                "classification_label": "Computing",
                "classification_rank_within_owner_year": 2,
                "portfolio_family_share_asof": 0.10,
                "portfolio_family_count_in_classification_asof": 1,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.classification_mix_path = classification_mix

    rows = repository.get_owner_classification("APPLE", limit=10, offset=0, classification_type="CPC_MAIN_GROUP")

    assert len(rows) == 2
    assert rows[0]["segment"] == "H01L"
    assert rows[0]["rank"] == 1
    assert rows[0]["family_share"] == pytest.approx(0.40)
    assert rows[0]["trajectory"] == pytest.approx(0.10)
    assert rows[0]["active_family_count"] == 4
    assert rows[0]["total_count"] == 2
    assert rows[1]["segment"] == "G06F"
    assert rows[1]["trajectory"] == pytest.approx(-0.10)

    monkeypatch.undo()
    get_settings.cache_clear()


def test_get_owner_classification_field_scoped_cpc_uses_selected_and_previous_year(tmp_path: Path) -> None:
    get_settings.cache_clear()
    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_classification_mix = tmp_path / "gold_family_classification_mix_pit.parquet"
    classification_mix = tmp_path / "gold_portfolio_classification_mix_pit.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        classification_mix,
        [
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "classification_type": "CPC_MAIN_GROUP",
                "as_of_year": 2025,
                "classification_code": "H01L",
                "classification_label": "Semiconductors",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 0.40,
                "portfolio_family_count_in_classification_asof": 4,
            }
        ],
    )
    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 3, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_classification_mix,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2024,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["H01L"],
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2024,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["G06F"],
            },
            {
                "docdb_family_id": 1,
                "as_of_year": 2025,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["H01L"],
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2025,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["G06F"],
            },
            {
                "docdb_family_id": 3,
                "as_of_year": 2025,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["H01L"],
            },
        ],
    )

    repository = PortfolioRepository()
    repository.classification_mix_path = classification_mix
    repository.owner_bridge_path = owner_bridge
    repository.family_classification_mix_path = family_classification_mix

    rows = repository.get_owner_classification(
        "APPLE",
        limit=10,
        offset=0,
        classification_type="CPC_MAIN_GROUP",
        wipo_field="Computer technology",
    )

    assert len(rows) == 2
    assert rows[0]["segment"] == "H01L"
    assert rows[0]["classification_type"] == "CPC_MAIN_GROUP"
    assert rows[0]["classification_label"] == "Computer technology"
    assert rows[0]["family_share"] == pytest.approx(2 / 3)
    assert rows[0]["trajectory"] == pytest.approx((2 / 3) - 0.5)
    assert rows[0]["total_count"] == 2
    assert rows[1]["segment"] == "G06F"
    assert rows[1]["family_share"] == pytest.approx(1 / 3)
    assert rows[1]["trajectory"] == pytest.approx((1 / 3) - 0.5)

    monkeypatch.undo()
    get_settings.cache_clear()


def test_get_owner_threats_handles_parquet_without_owner_display(tmp_path: Path) -> None:
    get_settings.cache_clear()
    threat = tmp_path / "gold_portfolio_threat_matrix.parquet"
    manifest_path = tmp_path / "missing-serving-manifest.json"

    from pytest import MonkeyPatch
    monkeypatch = MonkeyPatch()
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    _write_parquet(
        threat,
        [
            {
                "owner_name_harmonized": "APPLE",
                "snapshot_date": "2026-03-15",
                "citing_assignee_name": "QUALCOMM",
                "wipo_field": "Digital communication",
                "citation_lethality_sum": 55.0,
                "collided_family_count": 3,
            }
        ],
    )

    repository = PortfolioRepository()
    repository.threat_path = threat

    assert repository.get_owner_threats("APPLE", limit=10, offset=0)
    assert repository.get_owner_threats("Apple Inc.", limit=10, offset=0) == []
    monkeypatch.undo()
    get_settings.cache_clear()


def test_attach_core_serving_is_idempotent(tmp_path: Path) -> None:
    core_path = tmp_path / "core_serving.duckdb"
    with duckdb.connect(str(core_path)) as con:
        con.execute("create table portfolio_summary(owner_name_harmonized varchar)")

    repository = PortfolioRepository()
    with duckdb.connect() as con:
        repository._attach_core_serving(con, core_path)
        repository._attach_core_serving(con, core_path)
        attached_names = [row[1] for row in con.execute("pragma database_list").fetchall()]

    assert attached_names.count("core_db") == 1


def test_portfolio_repository_prefers_core_serving_snapshot_for_hot_methods(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    core_path = serving_dir / "core_serving.duckdb"
    manifest_path.write_text(
        """
        {
          "serving_release": "test-serving",
          "contract_version": "1",
          "snapshots": {
            "core": {
              "filename": "core_serving.duckdb",
              "tables": [
                "portfolio_summary",
                "portfolio_compare_current_serving",
                "portfolio_classification_current_serving",
                "portfolio_forecast_summary",
                "portfolio_forecast_segments",
                "portfolio_forecast_contributors",
                "family_owner_bridge",
                "family_summary",
                "family_blocking_power",
                "portfolio_threat_matrix"
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table portfolio_summary as
            select * from (
                values
                    ('APPLE', 'Apple', DATE '2026-03-15', 2, 80.0, 30.0, 50.0, 75.0, 0.6, 12.0),
                    ('SAM', 'Sam', DATE '2026-03-15', 1, 5.0, 1.0, 1.0, 10.0, 0.1, 1.0),
                    ('SAMSUNG_ELECTRONICS_COMPANY', 'Samsung Electronics Company', DATE '2026-03-15', 3000, 120.0, 40.0, 80.0, 78.0, 0.5, 10.0),
                    ('TESLA', 'Tesla', DATE '2026-03-15', 356, 90.0, 14.0, 60.0, 55.0, 0.4, 8.0),
                    ('TES_COMPANY', 'Tes Company', DATE '2026-03-15', 502, 17.0, 7.0, 12.0, 28.0, 0.1, 2.0),
                    ('BETA', 'Beta', DATE '2026-03-15', 2, 40.0, 10.0, 20.0, 35.0, 0.2, 5.0)
            ) as t(
                owner_name_harmonized,
                owner_name_display,
                snapshot_date,
                portfolio_family_count_within_mega_cluster,
                portfolio_total_mass_score,
                portfolio_current_threat_score,
                portfolio_heritage_score,
                portfolio_avg_blocking_power_within_mega_cluster,
                portfolio_hit_rate_top_decile,
                portfolio_crown_jewel_index
            )
            """
        )
        con.execute(
            """
            create table portfolio_compare_current_serving as
            select * from (
                values
                    ('APPLE', 'Apple', DATE '2026-03-15', '2_5', 2, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0),
                    ('BETA', 'Beta', DATE '2026-03-15', '2_5', 2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            ) as t(
                owner_name_harmonized,
                owner_name_display,
                snapshot_date,
                peer_bucket,
                peer_bucket_size,
                portfolio_total_mass_score_percentile,
                portfolio_current_threat_score_percentile,
                portfolio_heritage_score_percentile,
                portfolio_avg_blocking_power_percentile,
                portfolio_hit_rate_top_decile_percentile,
                portfolio_crown_jewel_index_percentile
            )
            """
        )
        con.execute(
            """
            create table portfolio_classification_current_serving as
            select * from (
                values
                    ('APPLE', 'Apple', 2025, 'Computer technology', 'Computer technology', 'WIPO_FIELD', 1, 0.7, 4, 0.1),
                    ('APPLE', 'Apple', 2025, 'Digital communication', 'Digital communication', 'WIPO_FIELD', 2, 0.3, 2, -0.1),
                    ('APPLE', 'Apple', 2025, 'H04L', 'H04L', 'CPC_MAIN_GROUP', 1, 1.0, 2, 0.5)
            ) as t(
                owner_name_harmonized,
                owner_name_display,
                as_of_year,
                segment,
                classification_label,
                classification_type,
                rank,
                family_share,
                active_family_count,
                trajectory
            )
            """
        )
        con.execute(
            """
            create table portfolio_forecast_summary as
            select * from (
                values
                    ('APPLE', 'Apple', DATE '2026-03-15', 10.0)
            ) as t(owner_name_harmonized, owner_name_display, snapshot_date, citation_forecast_3y_total)
            """
        )
        con.execute(
            """
            create table portfolio_forecast_segments as
            select * from (
                values
                    ('APPLE', 'Apple', DATE '2026-03-15', '3y', 'Computer technology', 2, 'heating', 0.15, 'high')
            ) as t(
                owner_name_harmonized,
                owner_name_display,
                snapshot_date,
                horizon,
                wipo_field,
                portfolio_active_family_count_in_field,
                predicted_direction_band,
                predicted_growth_rate_reference,
                support_level
            )
            """
        )
        con.execute(
            """
            create table portfolio_forecast_contributors as
            select * from (
                values
                    ('APPLE', 'phase03_future_citations', '3y', '101', 0.7, 2.5)
            ) as t(
                owner_name_harmonized,
                contributor_scope,
                horizon,
                contributor_entity_id,
                contribution_share,
                contribution_value
            )
            """
        )
        con.execute(
            """
            create table family_owner_bridge as
            select * from (
                values
                    (101, 'APPLE', 'Apple', true),
                    (202, 'APPLE', 'Apple', true),
                    (301, 'SAM', 'Sam', true),
                    (302, 'SAMSUNG_ELECTRONICS_COMPANY', 'Samsung Electronics Company', true),
                    (303, 'TESLA', 'Tesla', true),
                    (304, 'TES_COMPANY', 'Tes Company', true),
                    (305, 'BETA', 'Beta', true)
            ) as t(docdb_family_id, owner_name_harmonized, owner_name_display, is_primary_owner)
            """
        )
        con.execute(
            """
            create table family_summary as
            select * from (
                values
                    (101, 'fully_active', 2018, 'Computer technology'),
                    (202, 'pending_emerging', 2020, 'Computer technology'),
                    (303, 'dead', 2012, 'Digital communication'),
                    (404, 'partially_lapsed', 2016, 'Digital communication')
            ) as t(docdb_family_id, family_composite_status, family_priority_year, primary_wipo_field)
            """
        )
        con.execute(
            """
            create table family_blocking_power as
            select * from (
                values
                    (101, 91.0),
                    (202, 63.0),
                    (404, 88.0)
            ) as t(docdb_family_id, family_ui_blocking_power_score)
            """
        )
        con.execute(
            """
            insert into family_owner_bridge values (404, 'APPLE', 'Apple', true)
            """
        )
        con.execute(
            """
            create table portfolio_threat_matrix as
            select * from (
                values
                    ('APPLE', 'QUALCOMM', 'Computer technology', 30.0, 2)
            ) as t(owner_name_harmonized, citing_assignee_name, wipo_field, citation_lethality_sum, collided_family_count)
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_DUCKDB_PATH", str(tmp_path / "repository-test.duckdb"))
    get_settings.cache_clear()

    repository = PortfolioRepository()
    repository.classification_mix_path = tmp_path / "missing_portfolio_classification_mix.parquet"

    search_rows = repository.search_owners("app", limit=10)
    assert search_rows[0]["owner_name_harmonized"] == "APPLE"
    assert repository.search_owners("sam", limit=10)[0]["owner_name_harmonized"] == "SAMSUNG_ELECTRONICS_COMPANY"
    assert repository.search_owners("tes", limit=10)[0]["owner_name_harmonized"] == "TESLA"

    summary = repository.get_owner_summary("APPLE")
    assert summary["owner_name_harmonized"] == "APPLE"
    assert summary["portfolio_total_mass_score"] == 80.0

    peer_context = repository.get_owner_summary_peer_context("APPLE")
    assert peer_context["peer_bucket"] == "2_5"
    assert peer_context["portfolio_total_mass_score_percentile"] == 100.0

    forecast_summary = repository.get_owner_forecast_summary("APPLE")
    assert forecast_summary["citation_forecast_3y_total"] == 10.0

    status_counts = repository.get_owner_family_status_counts("APPLE")
    assert status_counts["family_count"] == 3
    assert status_counts["active_family_count"] == 1
    assert status_counts["pending_family_count"] == 1

    family_rows = repository.get_owner_families("APPLE", limit=10, offset=0)
    assert family_rows[0]["family_id"] == "101"
    assert family_rows[0]["forecast_contributor"] == 2.5
    filtered_family_rows = repository.get_owner_families("APPLE", limit=10, offset=0, exclude_inactive=True)
    assert [row["family_id"] for row in filtered_family_rows[:3]] == ["101", "404", "202"]

    contributor_path = tmp_path / "portfolio_forecast_contributors.parquet"
    _write_parquet(
        contributor_path,
        [
            {
                "owner_name_harmonized": "APPLE",
                "contributor_scope": "phase03_future_citations",
                "horizon": "3y",
                "contributor_entity_id": "101",
                "jurisdiction_code": "US",
                "contribution_share": 0.7,
                "contribution_value": 2.5,
                "contributor_rank": 1,
            },
            {
                "owner_name_harmonized": "APPLE",
                "contributor_scope": "phase03_future_citations",
                "horizon": "3y",
                "contributor_entity_id": "404",
                "jurisdiction_code": "JP",
                "contribution_share": 0.6,
                "contribution_value": 3.8,
                "contributor_rank": 2,
            },
            {
                "owner_name_harmonized": "APPLE",
                "contributor_scope": "phase03_future_citations",
                "horizon": "3y",
                "contributor_entity_id": "303",
                "jurisdiction_code": "EP",
                "contribution_share": 0.9,
                "contribution_value": 4.2,
                "contributor_rank": 3,
            },
        ],
    )
    repository.forecast_contributors_path = contributor_path
    filtered_contributors = repository.get_owner_forecast_contributors("APPLE", current_state_only=True)
    assert [row["contributor_entity_id"] for row in filtered_contributors] == ["101", "404"]
    assert filtered_contributors[0]["status"] == "fully_active"
    assert filtered_contributors[1]["status"] == "partially_lapsed"

    forecast_sections = repository.get_owner_forecast_sections("APPLE")
    assert forecast_sections[0]["wipo_field"] == "Computer technology"

    field_rows = repository.get_owner_fields("APPLE", limit=10)
    assert field_rows[0]["field"] == "Computer technology"
    assert field_rows[0]["hotspot_direction"] == "gains"

    classification_rows = repository.get_owner_classification("APPLE", classification_type="WIPO_FIELD", limit=10, offset=0)
    assert classification_rows[0]["segment"] == "Computer technology"
    assert float(classification_rows[0]["trajectory"]) == pytest.approx(0.1)

    threat_rows = repository.get_owner_threats("APPLE", limit=10, offset=0)
    assert threat_rows[0]["citing_assignee_name"] == "QUALCOMM"

    assert repository.get_latest_snapshot_year() == 2026

    get_settings.cache_clear()


def test_pending_grant_sections_filter_to_current_pending_pairs_and_report_coverage(tmp_path: Path, monkeypatch) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    branch_history = tmp_path / "silver_branch_status_history_dense.parquet"
    prediction = tmp_path / "ml_prediction_pending_grant_pipeline.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 3, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        branch_history,
        [
            {"docdb_family_id": 1, "jurisdiction_code": "EP", "snapshot_year": 2025, "snapshot_date": "2025-03-15", "pending_branch_flag": True},
            {"docdb_family_id": 1, "jurisdiction_code": "EP", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": False},
            {"docdb_family_id": 2, "jurisdiction_code": "US", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": True},
            {"docdb_family_id": 3, "jurisdiction_code": "JP", "snapshot_year": 2026, "snapshot_date": "2026-03-15", "pending_branch_flag": True},
        ],
    )
    _write_parquet(
        prediction,
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "EP",
                "as_of_date": "2025-03-15",
                "as_of_year": 2025,
                "primary_wipo_field": "Computer technology",
                "office_support_level": "strong",
                "grant_probability_calibrated_12m": 0.55,
                "grant_probability_calibrated_24m": 0.8,
                "pending_grant_rank_within_office_24m": 1,
                "pending_grant_percentile_within_office_24m": 100.0,
                "pending_age_years": 1.2,
                "family_age_years": 4.0,
                "family_blocking_power_score_asof": 55.0,
                "family_enforceability_score_asof": 61.0,
                "family_rcf_score_asof": 48.0,
                "data_completeness_pct_asof": 0.88,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "US",
                "as_of_date": "2026-03-15",
                "as_of_year": 2026,
                "primary_wipo_field": "Audio-visual technology",
                "office_support_level": "moderate",
                "grant_probability_calibrated_12m": 0.31,
                "grant_probability_calibrated_24m": 0.67,
                "pending_grant_rank_within_office_24m": 1,
                "pending_grant_percentile_within_office_24m": 95.0,
                "pending_age_years": 0.8,
                "family_age_years": 3.0,
                "family_blocking_power_score_asof": 42.0,
                "family_enforceability_score_asof": 51.0,
                "family_rcf_score_asof": 39.0,
                "data_completeness_pct_asof": 0.91,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.branch_history_dense_path = branch_history
    repository.pending_grant_prediction_path = prediction

    result = repository.get_owner_pending_grant_sections("ACME")

    assert result["serving_ready"] is True
    assert result["reason"] == "Pending-grant is served from current scored pending branches and should remain rank/percentile-first in the UI."
    assert result["summary"]["current_pending_branch_count"] == 2
    assert result["summary"]["current_pending_family_count"] == 2
    assert result["summary"]["pending_pipeline_branch_count"] == 1
    assert result["summary"]["pending_pipeline_family_count"] == 1
    assert result["summary"]["top_branch_family_id"] == "2"
    assert [row["jurisdiction_code"] for row in result["jurisdictions"]] == ["US"]
    assert [row["docdb_family_id"] for row in result["branches"]] == ["2"]

    get_settings.cache_clear()


def test_owner_status_timeseries_aggregates_counts_and_audit_fields(tmp_path: Path, monkeypatch) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_summary = tmp_path / "gold_family_summary.parquet"
    family_blocking = tmp_path / "gold_family_blocking_power.parquet"
    family_compare = tmp_path / "gold_family_compare_pit.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 9, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": False},
        ],
    )
    _write_parquet(
        family_summary,
        [
            {"docdb_family_id": 1, "family_composite_status": "dead"},
            {"docdb_family_id": 2, "family_composite_status": "partially_lapsed"},
            {"docdb_family_id": 9, "family_composite_status": "fully_active"},
        ],
    )
    _write_parquet(
        family_blocking,
        [
            {"docdb_family_id": 1},
            {"docdb_family_id": 2},
            {"docdb_family_id": 9},
        ],
    )
    _write_parquet(
        family_compare,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2024,
                "current_snapshot_date": "2026-03-15",
                "owner_name_harmonized_current": "ACME",
                "owner_name_display_current": "Acme",
                "family_composite_status_asof": "fully_active",
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
                "data_completeness_pct_asof": 0.9,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2024,
                "current_snapshot_date": "2026-03-15",
                "owner_name_harmonized_current": "ACME",
                "owner_name_display_current": "Acme",
                "family_composite_status_asof": "dead",
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
                "data_completeness_pct_asof": 0.8,
            },
            {
                "docdb_family_id": 1,
                "as_of_year": 2025,
                "current_snapshot_date": "2026-03-15",
                "owner_name_harmonized_current": "ACME",
                "owner_name_display_current": "Acme",
                "family_composite_status_asof": "fully_active",
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
                "data_completeness_pct_asof": 0.95,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2025,
                "current_snapshot_date": "2026-03-15",
                "owner_name_harmonized_current": "ACME",
                "owner_name_display_current": "Acme",
                "family_composite_status_asof": "partially_lapsed",
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
                "data_completeness_pct_asof": 0.85,
            },
            {
                "docdb_family_id": 9,
                "as_of_year": 2025,
                "current_snapshot_date": "2026-03-15",
                "owner_name_harmonized_current": "OTHER",
                "owner_name_display_current": "Other",
                "family_composite_status_asof": "fully_active",
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
                "data_completeness_pct_asof": 0.5,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_summary_path = family_summary
    repository.family_blocking_path = family_blocking
    repository.family_compare_path = family_compare

    rows = repository.get_owner_status_timeseries("ACME", year_from=2024, year_to=2025)

    assert [row["as_of_year"] for row in rows] == [2024, 2025]
    assert rows[0]["family_count"] == 2
    assert rows[0]["fully_active_family_count"] == 1
    assert rows[0]["dead_family_count"] == 1
    assert rows[1]["family_count"] == 3
    assert rows[1]["fully_active_family_count"] == 2
    assert rows[1]["partially_lapsed_family_count"] == 1
    assert rows[1]["dead_family_count"] == 0
    assert rows[1]["status_coverage_pct"] == pytest.approx(1.0)
    assert rows[1]["current_owner_metadata_only_pct"] == pytest.approx(1.0)

    get_settings.cache_clear()


def test_owner_jurisdiction_unlock_history_returns_summary_years_and_detail_rows(tmp_path: Path, monkeypatch) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_summary = tmp_path / "gold_family_summary.parquet"
    family_blocking = tmp_path / "gold_family_blocking_power.parquet"
    branch_history = tmp_path / "silver_branch_status_history_dense.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_summary,
        [
            {"docdb_family_id": 1},
            {"docdb_family_id": 2},
        ],
    )
    _write_parquet(
        family_blocking,
        [
            {"docdb_family_id": 1},
            {"docdb_family_id": 2},
        ],
    )
    _write_parquet(
        branch_history,
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "EP",
                "snapshot_year": 2020,
                "pending_branch_flag": True,
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "EP",
                "snapshot_year": 2021,
                "pending_branch_flag": False,
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "US",
                "snapshot_year": 2024,
                "pending_branch_flag": False,
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "CN",
                "snapshot_year": 2024,
                "pending_branch_flag": True,
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "CN",
                "snapshot_year": 2025,
                "pending_branch_flag": False,
                "active_branch_flag": False,
                "lapsed_or_expired_flag": True,
                "opposed_branch_flag": False,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_summary_path = family_summary
    repository.family_blocking_path = family_blocking
    repository.branch_history_dense_path = branch_history

    result = repository.get_owner_jurisdiction_unlock_history(
        "ACME",
        year_from=2020,
        year_to=2025,
        jurisdiction_limit=10,
    )

    assert result["summary"]["unlocked_jurisdiction_count"] == 3
    assert result["summary"]["first_unlock_year"] == 2020
    assert result["summary"]["latest_unlock_year"] == 2024
    assert result["summary"]["latest_presence_year"] == 2025
    assert [row["as_of_year"] for row in result["years"]] == [2020, 2021, 2024, 2025]
    assert result["years"][1]["unlocked_jurisdiction_count"] == 0
    assert result["years"][1]["active_jurisdiction_count"] == 1
    assert result["years"][2]["cumulative_unlocked_jurisdiction_count"] == 3
    assert result["years"][3]["unlocked_jurisdiction_count"] == 0
    assert result["years"][3]["lapsed_jurisdiction_count"] == 1
    assert [row["jurisdiction_code"] for row in result["jurisdictions"]] == ["EP", "CN", "US"]
    assert result["jurisdictions"][0]["first_unlock_basis"] == "pending"

    get_settings.cache_clear()


def test_owner_jurisdiction_unlock_history_uses_exclusive_state_and_unlock_buckets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_summary = tmp_path / "gold_family_summary.parquet"
    family_blocking = tmp_path / "gold_family_blocking_power.parquet"
    branch_history = tmp_path / "silver_branch_status_history_dense.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
            {"docdb_family_id": 3, "owner_name_harmonized": "ACME", "owner_name_display": "Acme", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_summary,
        [
            {"docdb_family_id": 1},
            {"docdb_family_id": 2},
            {"docdb_family_id": 3},
        ],
    )
    _write_parquet(
        family_blocking,
        [
            {"docdb_family_id": 1},
            {"docdb_family_id": 2},
            {"docdb_family_id": 3},
        ],
    )
    _write_parquet(
        branch_history,
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "EP",
                "snapshot_year": 2020,
                "pending_branch_flag": True,
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "EP",
                "snapshot_year": 2020,
                "pending_branch_flag": False,
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 3,
                "jurisdiction_code": "CN",
                "snapshot_year": 2020,
                "pending_branch_flag": True,
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 3,
                "jurisdiction_code": "CN",
                "snapshot_year": 2021,
                "pending_branch_flag": False,
                "active_branch_flag": False,
                "lapsed_or_expired_flag": True,
                "opposed_branch_flag": False,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_summary_path = family_summary
    repository.family_blocking_path = family_blocking
    repository.branch_history_dense_path = branch_history

    result = repository.get_owner_jurisdiction_unlock_history(
        "ACME",
        year_from=2020,
        year_to=2021,
        jurisdiction_limit=10,
    )

    assert [row["as_of_year"] for row in result["years"]] == [2020, 2021]
    assert result["years"][0]["unlocked_jurisdiction_count"] == 2
    assert result["years"][0]["active_unlock_count"] == 1
    assert result["years"][0]["pending_unlock_count"] == 1
    assert result["years"][0]["lapsed_only_unlock_count"] == 0
    assert result["years"][0]["active_jurisdiction_count"] == 1
    assert result["years"][0]["pending_jurisdiction_count"] == 1
    assert result["years"][0]["lapsed_jurisdiction_count"] == 0
    assert result["jurisdictions"][0]["jurisdiction_code"] == "EP"
    assert result["jurisdictions"][0]["first_unlock_basis"] == "active"

    get_settings.cache_clear()


def test_owner_citation_summary_uses_selected_year_scope_and_exact_edge_counts(tmp_path: Path, monkeypatch) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_pit = tmp_path / "silver_family_feature_snapshot_pit.parquet"
    citation_network = tmp_path / "silver_enriched_citation_network.parquet"
    family_citation_metrics = tmp_path / "silver_family_citation_metrics.parquet"
    family_summary = tmp_path / "gold_family_summary.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 3, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_pit,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.2,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.8,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.7,
                "pre_asof_attacker_density_score": 0.4,
            },
            {
                "docdb_family_id": 3,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": False,
                "pre_asof_forward_citations_weighted": 9.0,
                "pre_asof_unique_citing_family_count": 9.0,
                "pre_asof_citing_assignee_diversity": 0.9,
                "pre_asof_attacker_density_score": 0.9,
            },
        ],
    )
    _write_parquet(
        citation_network,
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 2,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 11,
                "cited_docdb_family_id": 2,
                "citation_year": 2026,
                "clean_edge_weight": 0.8,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 12,
                "cited_docdb_family_id": 3,
                "citation_year": 2026,
                "clean_edge_weight": 1.1,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 1,
                "cited_docdb_family_id": 200,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 1,
                "cited_docdb_family_id": 201,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 2,
                "cited_docdb_family_id": 201,
                "citation_year": 2026,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 2,
                "cited_docdb_family_id": 999,
                "citation_year": 2026,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": True,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
        ],
    )
    _write_parquet(
        family_citation_metrics,
        [
            {
                "docdb_family_id": 1,
                "family_backward_npl_citation_count": 4.0,
                "family_science_grounding_score": 0.2,
                "out_of_bounds_citation_share": 0.1,
            },
            {
                "docdb_family_id": 2,
                "family_backward_npl_citation_count": 6.0,
                "family_science_grounding_score": 0.6,
                "out_of_bounds_citation_share": 0.3,
            },
            {
                "docdb_family_id": 3,
                "family_backward_npl_citation_count": 99.0,
                "family_science_grounding_score": 0.9,
                "out_of_bounds_citation_share": 0.9,
            },
        ],
    )
    _write_parquet(
        family_summary,
        [
            {"docdb_family_id": 1, "family_generality_percentile": 0.4, "family_originality_percentile": 0.2},
            {"docdb_family_id": 2, "family_generality_percentile": 0.8, "family_originality_percentile": 0.6},
            {"docdb_family_id": 3, "family_generality_percentile": 0.9, "family_originality_percentile": 0.9},
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_feature_snapshot_pit_path = family_pit
    repository.family_citation_timeseries_path = tmp_path / "missing_gold_family_citation_timeseries_pit.parquet"
    repository.portfolio_citation_summary_path = tmp_path / "missing_gold_portfolio_citation_summary.parquet"
    repository.enriched_citation_network_path = citation_network
    repository.family_citation_metrics_path = family_citation_metrics
    repository.family_summary_path = family_summary

    result = repository.get_owner_citation_summary("APPLE", as_of_year=2026)

    assert result["family_count"] == 2
    assert result["forward_citations_clean_total"] == pytest.approx(3.0)
    assert result["forward_citations_weighted_total"] == pytest.approx(2.8)
    assert result["distinct_citing_family_count"] == 2
    assert result["backward_citations_clean_total"] == pytest.approx(3.0)
    assert result["distinct_cited_family_count"] == 2
    assert result["backward_npl_citation_total"] == pytest.approx(10.0)
    assert result["avg_science_grounding_score"] == pytest.approx(0.4)
    assert result["avg_generality_percentile"] == pytest.approx(0.6)
    assert result["avg_originality_percentile"] == pytest.approx(0.4)
    assert result["avg_unique_citing_family_count"] == pytest.approx(1.5)
    assert result["avg_citing_assignee_diversity"] == pytest.approx(0.6)
    assert result["avg_attacker_density_score"] == pytest.approx(0.3)
    assert result["avg_out_of_bounds_citation_share"] == pytest.approx(0.2)

    get_settings.cache_clear()


def test_owner_citation_summary_ignores_old_schema_fast_path_and_uses_exact_edge_counts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_pit = tmp_path / "silver_family_feature_snapshot_pit.parquet"
    citation_network = tmp_path / "silver_enriched_citation_network.parquet"
    family_citation_metrics = tmp_path / "silver_family_citation_metrics.parquet"
    family_summary = tmp_path / "gold_family_summary.parquet"
    portfolio_citation_summary = tmp_path / "gold_portfolio_citation_summary.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 3, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_pit,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.2,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.8,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.7,
                "pre_asof_attacker_density_score": 0.4,
            },
            {
                "docdb_family_id": 3,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": False,
                "pre_asof_forward_citations_weighted": 9.0,
                "pre_asof_unique_citing_family_count": 9.0,
                "pre_asof_citing_assignee_diversity": 0.9,
                "pre_asof_attacker_density_score": 0.9,
            },
        ],
    )
    _write_parquet(
        citation_network,
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 2,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 11,
                "cited_docdb_family_id": 2,
                "citation_year": 2026,
                "clean_edge_weight": 0.8,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 12,
                "cited_docdb_family_id": 3,
                "citation_year": 2026,
                "clean_edge_weight": 1.1,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 1,
                "cited_docdb_family_id": 200,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 1,
                "cited_docdb_family_id": 201,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 2,
                "cited_docdb_family_id": 201,
                "citation_year": 2026,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
        ],
    )
    _write_parquet(
        family_citation_metrics,
        [
            {
                "docdb_family_id": 1,
                "family_backward_npl_citation_count": 4.0,
                "family_science_grounding_score": 0.2,
                "out_of_bounds_citation_share": 0.1,
            },
            {
                "docdb_family_id": 2,
                "family_backward_npl_citation_count": 6.0,
                "family_science_grounding_score": 0.6,
                "out_of_bounds_citation_share": 0.3,
            },
        ],
    )
    _write_parquet(
        family_summary,
        [
            {"docdb_family_id": 1, "family_generality_percentile": 0.4, "family_originality_percentile": 0.2},
            {"docdb_family_id": 2, "family_generality_percentile": 0.8, "family_originality_percentile": 0.6},
        ],
    )
    _write_parquet(
        portfolio_citation_summary,
        [
            {
                "owner_name_harmonized": "APPLE",
                "as_of_year": 2026,
                "current_snapshot_date": "2026-04-10",
                "family_count": 999,
                "forward_citations_clean_total": 999.0,
                "forward_citations_weighted_total": 999.0,
                "backward_citations_clean_total": 999.0,
                "backward_npl_citation_total": 999.0,
                "avg_science_grounding_score": 9.9,
                "avg_generality_percentile": 9.9,
                "avg_originality_percentile": 9.9,
                "avg_unique_citing_family_count": 9.9,
                "avg_citing_assignee_diversity": 9.9,
                "avg_attacker_density_score": 9.9,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_feature_snapshot_pit_path = family_pit
    repository.family_citation_timeseries_path = tmp_path / "missing_gold_family_citation_timeseries_pit.parquet"
    repository.enriched_citation_network_path = citation_network
    repository.family_citation_metrics_path = family_citation_metrics
    repository.family_summary_path = family_summary
    repository.portfolio_citation_summary_path = portfolio_citation_summary

    result = repository.get_owner_citation_summary("APPLE", as_of_year=2026)

    assert result["family_count"] == 2
    assert result["forward_citations_clean_total"] == pytest.approx(3.0)
    assert result["forward_citations_weighted_total"] == pytest.approx(2.8)
    assert result["distinct_citing_family_count"] == 2
    assert result["backward_citations_clean_total"] == pytest.approx(3.0)
    assert result["distinct_cited_family_count"] == 2
    assert result["backward_npl_citation_total"] == pytest.approx(10.0)
    assert result["avg_science_grounding_score"] == pytest.approx(0.4)
    assert result["avg_generality_percentile"] == pytest.approx(0.6)
    assert result["avg_originality_percentile"] == pytest.approx(0.4)
    assert result["avg_unique_citing_family_count"] == pytest.approx(1.5)
    assert result["avg_citing_assignee_diversity"] == pytest.approx(0.6)
    assert result["avg_attacker_density_score"] == pytest.approx(0.3)
    assert result["avg_out_of_bounds_citation_share"] == pytest.approx(0.2)

    get_settings.cache_clear()


def test_owner_citation_timeseries_uses_exact_forward_edge_counts(tmp_path: Path, monkeypatch) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_pit = tmp_path / "silver_family_feature_snapshot_pit.parquet"
    citation_network = tmp_path / "silver_enriched_citation_network.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_pit,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2025,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.0,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
            },
            {
                "docdb_family_id": 1,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.5,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.6,
                "pre_asof_attacker_density_score": 0.3,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 0.7,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.8,
                "pre_asof_attacker_density_score": 0.4,
            },
        ],
    )
    _write_parquet(
        citation_network,
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 11,
                "cited_docdb_family_id": 2,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 12,
                "cited_docdb_family_id": 2,
                "citation_year": 2026,
                "clean_edge_weight": 0.8,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 13,
                "cited_docdb_family_id": 1,
                "citation_year": 2026,
                "clean_edge_weight": 0.9,
                "is_out_of_bounds": True,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_feature_snapshot_pit_path = family_pit
    repository.family_citation_timeseries_path = tmp_path / "missing_gold_family_citation_timeseries_pit.parquet"
    repository.portfolio_citation_timeseries_path = tmp_path / "missing_gold_portfolio_citation_timeseries.parquet"
    repository.enriched_citation_network_path = citation_network

    rows = repository.get_owner_citation_timeseries("APPLE", year_from=2025, year_to=2026)

    assert [row["as_of_year"] for row in rows] == [2025, 2026]
    assert rows[0]["family_count"] == 1
    assert rows[0]["forward_citations_clean_total"] == pytest.approx(1.0)
    assert rows[0]["forward_citations_weighted_total"] == pytest.approx(1.0)
    assert rows[1]["family_count"] == 2
    assert rows[1]["forward_citations_clean_total"] == pytest.approx(3.0)
    assert rows[1]["forward_citations_weighted_total"] == pytest.approx(2.2)

    get_settings.cache_clear()


def test_owner_citation_timeseries_ignores_old_schema_fast_path_and_uses_exact_forward_edge_counts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    family_pit = tmp_path / "silver_family_feature_snapshot_pit.parquet"
    citation_network = tmp_path / "silver_enriched_citation_network.parquet"
    portfolio_citation_timeseries = tmp_path / "gold_portfolio_citation_timeseries.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        family_pit,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2025,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.0,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
            },
            {
                "docdb_family_id": 1,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.5,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.6,
                "pre_asof_attacker_density_score": 0.3,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 0.7,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.8,
                "pre_asof_attacker_density_score": 0.4,
            },
        ],
    )
    _write_parquet(
        citation_network,
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 11,
                "cited_docdb_family_id": 2,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 12,
                "cited_docdb_family_id": 2,
                "citation_year": 2026,
                "clean_edge_weight": 0.8,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 13,
                "cited_docdb_family_id": 1,
                "citation_year": 2026,
                "clean_edge_weight": 0.9,
                "is_out_of_bounds": True,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
        ],
    )
    _write_parquet(
        portfolio_citation_timeseries,
        [
            {
                "owner_name_harmonized": "APPLE",
                "as_of_year": 2025,
                "current_snapshot_date": "2026-04-10",
                "family_count": 999,
                "forward_citations_clean_total": 999.0,
                "forward_citations_weighted_total": 999.0,
                "avg_unique_citing_family_count": 9.9,
                "avg_citing_assignee_diversity": 9.9,
                "avg_attacker_density_score": 9.9,
            },
            {
                "owner_name_harmonized": "APPLE",
                "as_of_year": 2026,
                "current_snapshot_date": "2026-04-10",
                "family_count": 999,
                "forward_citations_clean_total": 999.0,
                "forward_citations_weighted_total": 999.0,
                "avg_unique_citing_family_count": 9.9,
                "avg_citing_assignee_diversity": 9.9,
                "avg_attacker_density_score": 9.9,
            },
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_feature_snapshot_pit_path = family_pit
    repository.family_citation_timeseries_path = tmp_path / "missing_gold_family_citation_timeseries_pit.parquet"
    repository.enriched_citation_network_path = citation_network
    repository.portfolio_citation_timeseries_path = portfolio_citation_timeseries

    rows = repository.get_owner_citation_timeseries("APPLE", year_from=2025, year_to=2026)

    assert [row["as_of_year"] for row in rows] == [2025, 2026]
    assert rows[0]["family_count"] == 1
    assert rows[0]["forward_citations_clean_total"] == pytest.approx(1.0)
    assert rows[0]["forward_citations_weighted_total"] == pytest.approx(1.0)
    assert rows[1]["family_count"] == 2
    assert rows[1]["forward_citations_clean_total"] == pytest.approx(3.0)
    assert rows[1]["forward_citations_weighted_total"] == pytest.approx(2.2)

    get_settings.cache_clear()


def test_owner_citation_summary_prefers_gold_citation_timeseries_scope_when_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    get_settings.cache_clear()
    manifest_path = tmp_path / "missing-serving-manifest.json"
    _patch_test_settings(monkeypatch, tmp_path, manifest_path)

    owner_bridge = tmp_path / "silver_family_owner_bridge.parquet"
    silver_family_pit = tmp_path / "silver_family_feature_snapshot_pit.parquet"
    gold_citation_pit = tmp_path / "gold_family_citation_timeseries_pit.parquet"
    citation_network = tmp_path / "silver_enriched_citation_network.parquet"
    family_citation_metrics = tmp_path / "silver_family_citation_metrics.parquet"
    family_summary = tmp_path / "gold_family_summary.parquet"

    _write_parquet(
        owner_bridge,
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
            {"docdb_family_id": 2, "owner_name_harmonized": "APPLE", "owner_name_display": "Apple", "is_primary_owner": True},
        ],
    )
    _write_parquet(
        silver_family_pit,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "pre_asof_forward_citations_weighted": 1.2,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
            },
        ],
    )
    _write_parquet(
        gold_citation_pit,
        [
            {
                "docdb_family_id": 1,
                "as_of_year": 2026,
                "pre_asof_forward_citations_weighted": 1.2,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
            },
            {
                "docdb_family_id": 2,
                "as_of_year": 2026,
                "pre_asof_forward_citations_weighted": 1.8,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.7,
                "pre_asof_attacker_density_score": 0.4,
            },
        ],
    )
    _write_parquet(
        citation_network,
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 11,
                "cited_docdb_family_id": 2,
                "citation_year": 2026,
                "clean_edge_weight": 0.8,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 1,
                "cited_docdb_family_id": 200,
                "citation_year": 2025,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
            {
                "source_docdb_family_id": 2,
                "cited_docdb_family_id": 201,
                "citation_year": 2026,
                "clean_edge_weight": 1.0,
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
            },
        ],
    )
    _write_parquet(
        family_citation_metrics,
        [
            {
                "docdb_family_id": 1,
                "family_backward_npl_citation_count": 4.0,
                "family_science_grounding_score": 0.2,
                "out_of_bounds_citation_share": 0.1,
            },
            {
                "docdb_family_id": 2,
                "family_backward_npl_citation_count": 6.0,
                "family_science_grounding_score": 0.6,
                "out_of_bounds_citation_share": 0.3,
            },
        ],
    )
    _write_parquet(
        family_summary,
        [
            {"docdb_family_id": 1, "family_generality_percentile": 0.4, "family_originality_percentile": 0.2},
            {"docdb_family_id": 2, "family_generality_percentile": 0.8, "family_originality_percentile": 0.6},
        ],
    )

    repository = PortfolioRepository()
    repository.owner_bridge_path = owner_bridge
    repository.family_feature_snapshot_pit_path = silver_family_pit
    repository.family_citation_timeseries_path = gold_citation_pit
    repository.enriched_citation_network_path = citation_network
    repository.family_citation_metrics_path = family_citation_metrics
    repository.family_summary_path = family_summary
    repository.portfolio_citation_summary_path = tmp_path / "missing_portfolio_citation_summary.parquet"

    result = repository.get_owner_citation_summary("APPLE", as_of_year=2026)

    assert result["family_count"] == 2
    assert result["forward_citations_clean_total"] == pytest.approx(2.0)
    assert result["distinct_citing_family_count"] == 2
    assert result["backward_citations_clean_total"] == pytest.approx(2.0)
    assert result["distinct_cited_family_count"] == 2
    assert result["avg_unique_citing_family_count"] == pytest.approx(1.5)
    assert result["avg_citing_assignee_diversity"] == pytest.approx(0.6)
    assert result["avg_attacker_density_score"] == pytest.approx(0.3)

    get_settings.cache_clear()


def test_portfolio_repository_raises_when_serving_table_is_missing_and_raw_fallback_disabled(
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
    _patch_test_settings(monkeypatch, tmp_path, manifest_path, raw_fallback_enabled=False)

    repository = PortfolioRepository()

    with repository.duckdb_provider.connect() as con:
        with pytest.raises(RuntimeError, match="portfolio_field_timeseries"):
            repository._analytics_relation(con, repository.field_timeseries_path)

    get_settings.cache_clear()
