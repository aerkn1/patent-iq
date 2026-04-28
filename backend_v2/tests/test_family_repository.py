from datetime import date
from pathlib import Path

import duckdb
import pytest

from config.settings import get_settings
from infrastructure.repositories.family_repository import FamilyRepository


def test_family_repository_prefers_core_serving_snapshot_for_compare_context(tmp_path: Path, monkeypatch) -> None:
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
              "tables": ["family_compare_current_serving"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table family_compare_current_serving as
            select
                123::bigint as docdb_family_id,
                'APPLE'::varchar as owner_name_harmonized,
                'Apple'::varchar as owner_name_display,
                'Computer technology'::varchar as primary_wipo_field,
                2018::integer as family_priority_year,
                'fully_active'::varchar as family_composite_status,
                3::integer as family_size_docdb,
                1::integer as family_tech_breadth_wipo_count,
                2.0::double as active_jurisdiction_count,
                81.0::double as family_fwd_cits7_percentile,
                0.72::double as family_quality_index_6_score,
                0.75::double as oecd_quality_percentile,
                0.74::double as oecd_quality_proxy_score,
                91.0::double as family_ui_blocking_power_score,
                4.2::double as family_overall_legal_enforceability_score,
                0.8::double as family_market_threat_score_raw,
                'Computer technology'::varchar as primary_wipo_field_current,
                'fully_active'::varchar as family_composite_status_asof,
                4.2::double as family_enforceability_score_asof,
                1.0::double as family_active_jurisdiction_share_asof,
                2.0::double as family_jurisdiction_count_asof,
                16.5::double as pre_asof_forward_citations_weighted,
                1.0::double as data_completeness_pct_asof,
                true as historical_compare_safe,
                true as historical_oecd_supported,
                false as current_owner_metadata_only,
                88.0::double as legal_durability_percentile,
                83.0::double as citation_heritage_percentile
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()

    repository = FamilyRepository()
    context = repository.get_family_compare_context("123")

    assert context["docdb_family_id"] == 123
    assert context["owner_name_harmonized"] == "APPLE"
    assert context["family_ui_blocking_power_score"] == 91.0
    assert context["legal_durability_percentile"] == 88.0
    assert context["citation_heritage_percentile"] == 83.0

    get_settings.cache_clear()


def test_family_repository_family_suggestions_use_core_serving_only(tmp_path: Path, monkeypatch) -> None:
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
              "tables": ["family_summary", "family_compare_current_serving"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table family_compare_current_serving as
            select
                123::bigint as docdb_family_id,
                'Computer technology'::varchar as primary_wipo_field_current,
                'fully_active'::varchar as family_composite_status_asof
            union all
            select
                123456::bigint as docdb_family_id,
                'Computer technology'::varchar as primary_wipo_field_current,
                'fully_active'::varchar as family_composite_status_asof
            union all
            select
                123499::bigint as docdb_family_id,
                'Computer technology'::varchar as primary_wipo_field_current,
                'fully_active'::varchar as family_composite_status_asof
            union all
            select
                456::bigint as docdb_family_id,
                'Medical technology'::varchar as primary_wipo_field_current,
                'pending_emerging'::varchar as family_composite_status_asof
            """
        )
        con.execute(
            """
            create table family_summary as
            select
                123::bigint as docdb_family_id,
                'Apple'::varchar as owner_name_display,
                'Computer technology'::varchar as primary_wipo_field,
                'fully_active'::varchar as family_composite_status
            union all
            select
                123456::bigint as docdb_family_id,
                'Apple'::varchar as owner_name_display,
                'Computer technology'::varchar as primary_wipo_field,
                'fully_active'::varchar as family_composite_status
            union all
            select
                123499::bigint as docdb_family_id,
                'Apple'::varchar as owner_name_display,
                'Computer technology'::varchar as primary_wipo_field,
                'fully_active'::varchar as family_composite_status
            union all
            select
                456::bigint as docdb_family_id,
                'Acme Labs'::varchar as owner_name_display,
                'Medical technology'::varchar as primary_wipo_field,
                'pending_emerging'::varchar as family_composite_status
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()

    repository = FamilyRepository()
    rows = repository.get_family_suggestions("Acme", limit=5)

    assert len(rows) == 1
    assert rows[0]["family_id"] == "456"
    assert rows[0]["owner_name_display"] == "Acme Labs"
    assert rows[0]["primary_field"] == "Medical technology"

    exact_rows = repository.get_family_suggestions("123456", limit=5)

    assert [row["family_id"] for row in exact_rows[:2]] == ["123456", "123499"]

    get_settings.cache_clear()


def test_family_repository_overview_context_keeps_serving_blocking_when_serving_snapshot_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir(parents=True)
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir(parents=True)
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
              "tables": ["family_summary", "family_blocking_power", "family_heritage_summary", "family_compare_current_serving"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table family_summary as
            select
                123::bigint as docdb_family_id,
                'APPLE'::varchar as owner_name_harmonized,
                'Apple'::varchar as owner_name_display,
                'Computer technology'::varchar as primary_wipo_field,
                2018::integer as family_priority_year,
                'fully_active'::varchar as family_composite_status,
                3::integer as family_size_docdb,
                1::integer as family_tech_breadth_wipo_count,
                2::integer as active_jurisdiction_count,
                81.0::double as family_fwd_cits7_percentile,
                0.72::double as family_quality_index_6_score,
                74.0::double as oecd_quality_percentile,
                0.74::double as oecd_quality_proxy_score
            """
        )
        con.execute(
            """
            create table family_blocking_power as
            select
                123::bigint as docdb_family_id,
                80.0::double as family_ui_blocking_power_score,
                1.0::double as family_overall_legal_enforceability_score,
                0.2::double as family_market_threat_score_raw,
                3.0::double as family_adjusted_citation_score_raw,
                0.4::double as family_raw_absolute_blocking_power
            """
        )
        con.execute(
            """
            create table family_heritage_summary as
            select
                123::bigint as docdb_family_id,
                13.5::double as family_heritage_score,
                12::bigint as raw_family_citation_count,
                0.1::double as out_of_bounds_citation_share
            """
        )
        con.execute(
            """
            create table family_compare_current_serving as
            select
                123::bigint as docdb_family_id,
                'Computer technology'::varchar as primary_wipo_field_current,
                'fully_active'::varchar as family_composite_status_asof,
                1.0::double as family_enforceability_score_asof,
                1.0::double as family_active_jurisdiction_share_asof,
                2.0::double as family_jurisdiction_count_asof,
                16.5::double as pre_asof_forward_citations_weighted,
                1.0::double as data_completeness_pct_asof,
                true as historical_compare_safe,
                true as historical_oecd_supported,
                false as current_owner_metadata_only,
                10.0::double as family_ui_blocking_power_score,
                50.0::double as legal_durability_percentile,
                60.0::double as citation_heritage_percentile
            """
        )

    with duckdb.connect() as con:
        con.execute(
            f"""
            copy (
                select * from (
                    values (
                        123::bigint,
                        'APPLE'::varchar,
                        'Apple'::varchar,
                        'Computer technology'::varchar,
                        2018::integer,
                        'fully_active'::varchar,
                        3::integer,
                        1::integer,
                        2::integer,
                        81.0::double,
                        0.72::double,
                        74.0::double,
                        0.74::double,
                        13.5::double,
                        date '2018-04-12'
                    )
                ) as t(
                    docdb_family_id,
                    owner_name_harmonized,
                    owner_name_display,
                    primary_wipo_field,
                    family_priority_year,
                    family_composite_status,
                    family_size_docdb,
                    family_tech_breadth_wipo_count,
                    active_jurisdiction_count,
                    family_fwd_cits7_percentile,
                    family_quality_index_6_score,
                    oecd_quality_percentile,
                    oecd_quality_proxy_score,
                    family_heritage_score,
                    family_earliest_priority_date
                )
            ) to '{gold_dir / "gold_family_summary.parquet"}' (format parquet)
            """
        )
        con.execute(
            f"""
            copy (
                select * from (
                    values (
                        123::bigint,
                        0.8::double,
                        3.7::double,
                        4.2::double,
                        2.1::double,
                        91.0::double
                    )
                ) as t(
                    docdb_family_id,
                    family_market_threat_score_raw,
                    family_adjusted_citation_score_raw,
                    family_overall_legal_enforceability_score,
                    family_raw_absolute_blocking_power,
                    family_ui_blocking_power_score
                )
            ) to '{gold_dir / "gold_family_blocking_power.parquet"}' (format parquet)
            """
        )
        con.execute(
            f"""
            copy (
                select * from (
                    values (
                        123::bigint,
                        date '2026-03-15',
                        2026::integer,
                        true,
                        true,
                        date '2026-03-15',
                        'APPLE'::varchar,
                        'Apple'::varchar,
                        'Computer technology'::varchar,
                        ['Computer technology']::varchar[],
                        74.0::double,
                        'fully_active'::varchar,
                        2.0::double,
                        2.0::double,
                        0.0::double,
                        2.0::double,
                        1.0::double,
                        0.84::double,
                        3.0::double,
                        1.0::double,
                        91.0::double,
                        4.2::double,
                        1.0::double,
                        16.5::double,
                        0.31::double,
                        5.0::double,
                        0.52::double,
                        0.33::double,
                        0.94::double,
                        true,
                        true,
                        false
                    )
                ) as t(
                    docdb_family_id,
                    as_of_date,
                    as_of_year,
                    is_observed_as_of_snapshot,
                    is_latest_observed_year,
                    current_snapshot_date,
                    owner_name_harmonized_current,
                    owner_name_display_current,
                    primary_wipo_field_current,
                    covered_wipo_fields_current,
                    oecd_quality_percentile_current,
                    family_composite_status_asof,
                    active_jurisdiction_count_asof,
                    active_grant_branch_count_asof,
                    lapsed_jurisdiction_count_asof,
                    family_jurisdiction_count_asof,
                    family_active_jurisdiction_share_asof,
                    family_coverage_stability_score_asof,
                    family_size_docdb_asof,
                    family_tech_breadth_wipo_count_asof,
                    family_blocking_power_score_asof,
                    family_enforceability_score_asof,
                    family_field_contribution_primary_asof,
                    pre_asof_forward_citations_weighted,
                    family_rcf_score_asof,
                    pre_asof_unique_citing_family_count,
                    pre_asof_citing_assignee_diversity,
                    pre_asof_attacker_density_score,
                    data_completeness_pct_asof,
                    historical_compare_safe,
                    historical_oecd_supported,
                    current_owner_metadata_only
                )
            ) to '{gold_dir / "gold_family_compare_pit.parquet"}' (format parquet)
            """
        )
        con.execute(
            f"""
            copy (
                select * from (
                    values (
                        123::bigint,
                        0.44::double
                    )
                ) as t(
                    docdb_family_id,
                    family_science_grounding_score
                )
            ) to '{silver_dir / "silver_family_citation_metrics.parquet"}' (format parquet)
            """
        )
        con.execute(
            f"""
            copy (
                select * from (
                    values (
                        123::bigint,
                        58.0::double
                    )
                ) as t(
                    docdb_family_id,
                    family_science_grounding_percentile
                )
            ) to '{silver_dir / "silver_family_oecd_quality.parquet"}' (format parquet)
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()

    repository = FamilyRepository()
    context = repository.get_family_overview_context("123")

    assert context["family_ui_blocking_power_score"] == 80.0
    assert context["family_overall_legal_enforceability_score"] == 1.0
    assert context["family_market_threat_score_raw"] == 0.2
    assert context["family_adjusted_citation_score_raw"] == 3.0

    get_settings.cache_clear()


def test_family_repository_prefers_analytics_serving_for_detail_views(tmp_path: Path, monkeypatch) -> None:
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
              "tables": ["family_status_history", "family_compare_pit"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(analytics_path)) as con:
        con.execute(
            """
            create table family_status_history as
            select
                123::bigint as docdb_family_id,
                2024::integer as snapshot_year,
                DATE '2024-12-31' as snapshot_date,
                'fully_active'::varchar as family_composite_status
            """
        )
        con.execute(
            """
            create table family_compare_pit as
            select * from (
                values
                    (123::bigint, 2025::integer, true, 1.0::double),
                    (123::bigint, 2024::integer, true, 1.0::double)
            ) as t(docdb_family_id, as_of_year, historical_compare_safe, family_enforceability_score_asof)
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path / "missing-etl-root"))
    get_settings.cache_clear()

    repository = FamilyRepository()

    status_rows = repository.get_family_status_history("123")
    compare_rows = repository.get_family_compare_timeslice("123", base_year=2025, compare_year=2024)

    assert [row["snapshot_year"] for row in status_rows] == [2024]
    assert [row["as_of_year"] for row in compare_rows] == [2025, 2024]

    get_settings.cache_clear()


def test_family_repository_computes_heritage_percentile_from_heritage_score(tmp_path: Path, monkeypatch) -> None:
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
              "tables": ["family_summary", "family_heritage_summary"]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    with duckdb.connect(str(core_path)) as con:
        con.execute(
            """
            create table family_summary as
            select * from (
                values
                    (111::bigint, 'Computer technology'::varchar, 2018::integer),
                    (123::bigint, 'Computer technology'::varchar, 2018::integer),
                    (222::bigint, 'Computer technology'::varchar, 2018::integer),
                    (333::bigint, 'Digital communication'::varchar, 2018::integer)
            ) as t(docdb_family_id, primary_wipo_field, family_priority_year)
            """
        )
        con.execute(
            """
            create table family_heritage_summary as
            select * from (
                values
                    (111::bigint, 1.0::double),
                    (123::bigint, 5.0::double),
                    (222::bigint, 9.0::double),
                    (333::bigint, 4.0::double)
            ) as t(docdb_family_id, family_heritage_score)
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()

    repository = FamilyRepository()

    assert repository.get_family_heritage_percentile("123") == 50.0

    get_settings.cache_clear()


def test_family_repository_field_timeseries_supports_aggregated_field_share_ordering(
    tmp_path: Path,
    monkeypatch,
) -> None:
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir(parents=True)
    timeseries_path = gold_dir / "gold_family_field_contributions_timeseries.parquet"

    with duckdb.connect() as con:
        con.execute(
            f"""
            copy (
                select * from (
                    values
                        (
                            123::bigint,
                            2024::integer,
                            date '2024-12-31',
                            'H04L'::varchar,
                            'Digital communication'::varchar,
                            0.5::double,
                            0.72::double,
                            'appln_weighted_field_share'::varchar,
                            0.72::double,
                            3::integer,
                            4::integer,
                            2.8::double,
                            1.6::double,
                            0.9::double,
                            'ACTIVE_GRANT'::varchar,
                            true
                        ),
                        (
                            123::bigint,
                            2024::integer,
                            date '2024-12-31',
                            'G06F'::varchar,
                            'Computer technology'::varchar,
                            0.5::double,
                            0.28::double,
                            'appln_weighted_field_share'::varchar,
                            0.28::double,
                            1::integer,
                            4::integer,
                            1.1::double,
                            0.7::double,
                            0.4::double,
                            'ACTIVE_GRANT'::varchar,
                            true
                        ),
                        (
                            123::bigint,
                            2024::integer,
                            date '2024-12-30',
                            'H04L'::varchar,
                            'Digital communication'::varchar,
                            0.5::double,
                            0.72::double,
                            'appln_weighted_field_share'::varchar,
                            0.72::double,
                            3::integer,
                            4::integer,
                            2.8::double,
                            1.6::double,
                            0.9::double,
                            'ACTIVE_GRANT'::varchar,
                            true
                        )
                ) as t(
                    docdb_family_id,
                    snapshot_year,
                    snapshot_date,
                    wipo_industry_code,
                    field_name,
                    base_fraction,
                    field_share_asof,
                    field_share_method,
                    field_evidence_weight_asof,
                    field_application_count_asof,
                    family_application_count_asof,
                    enforceability_contribution_score,
                    heritage_contribution_score,
                    active_market_weight,
                    max_active_stage,
                    is_active_on_snapshot
                )
            ) to '{timeseries_path}' (format parquet)
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(tmp_path / "missing-serving"))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(tmp_path / "missing-serving-manifest.json"))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()

    repository = FamilyRepository()
    rows = repository.get_family_field_timeseries("123")

    assert [row["wipo_industry_code"] for row in rows] == [
        "H04L",
        "G06F",
    ]
    assert rows[0]["field_share_asof"] == 0.72
    assert rows[0]["field_share_method"] == "appln_weighted_field_share"
    assert rows[0]["field_application_count_asof"] == 3.0
    assert rows[0]["family_application_count_asof"] == 4.0

    get_settings.cache_clear()


def test_family_repository_blocking_timeseries_exposes_blocking_citation_when_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir(parents=True)
    timeseries_path = gold_dir / "gold_family_blocking_power_timeseries.parquet"

    with duckdb.connect() as con:
        con.execute(
            f"""
            copy (
                select * from (
                    values
                        (
                            123::bigint,
                            date '2026-03-15',
                            91.0::double,
                            4.2::double,
                            1.5::double,
                            1.5::double
                        )
                ) as t(
                    docdb_family_id,
                    snapshot_date,
                    ui_blocking_power_score,
                    overall_legal_enforceability_score,
                    adjusted_citation_score_raw,
                    blocking_citation_score_raw
                )
            ) to '{timeseries_path}' (format parquet)
            """
        )

    monkeypatch.setenv("PATENTIQ_V2_ETL_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(tmp_path / "missing-serving"))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(tmp_path / "missing-serving-manifest.json"))
    monkeypatch.setenv("PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()

    repository = FamilyRepository()
    rows = repository.get_family_blocking_timeseries("123")

    assert rows == [
        {
            "snapshot_year": 2026,
            "snapshot_date": date(2026, 3, 15),
            "ui_blocking_power_score": 91.0,
            "overall_legal_enforceability_score": 4.2,
            "adjusted_citation_score_raw": 1.5,
            "blocking_citation_score_raw": 1.5,
        }
    ]

    get_settings.cache_clear()


def test_family_repository_raises_when_serving_table_is_missing_and_raw_fallback_disabled(
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
    get_settings.cache_clear()

    repository = FamilyRepository()

    with repository.duckdb_provider.connect() as con:
        with pytest.raises(RuntimeError, match="family_status_history"):
            repository._analytics_relation(con, repository.status_history_path)

    get_settings.cache_clear()
