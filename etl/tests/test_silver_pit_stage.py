from __future__ import annotations

from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.silver.build_pit import (
    AUDIT_TABLE,
    CLASSIFICATION_DENSE_AUDIT_TABLE,
    CLASSIFICATION_DENSE_OUTPUT_TABLE,
    CLASSIFICATION_VISIBILITY_AUDIT_TABLE,
    CLASSIFICATION_VISIBILITY_OUTPUT_TABLE,
    DENSE_AUDIT_TABLE,
    DENSE_OUTPUT_TABLE,
    OUTPUT_TABLE,
    build_silver_family_classification_visibility_timeline,
    build_silver_family_classification_pit_dense,
    build_silver_family_pit,
    build_silver_family_pit_dense,
)
from patentiq_etl.silver.run import (
    run_silver_pit,
    run_silver_pit_classification_dense,
    run_silver_pit_classification_visibility,
    run_silver_pit_dense,
)


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


def _write_minimal_inputs(settings: BuildSettings) -> None:
    """Write the minimal set of parquet fixtures needed to run silver-pit."""
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.bronze_dir)

    # gold_family_summary — family anchor (as_of_date = priority_date + 2 years)
    # family 100: priority 2015-03-01, as_of_date 2017-03-01, as_of_year 2017
    # family 200: priority 2018-06-15, as_of_date 2020-06-15, as_of_year 2020
    # family 300: priority 2020-01-01, as_of_date 2022-01-01, as_of_year 2022
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_earliest_priority_date": "2015-03-01", "family_size_docdb": 5, "is_main_window_family": True, "family_priority_year": 2015, "primary_wipo_field": "Computer technology"},
            {"docdb_family_id": 200, "family_earliest_priority_date": "2018-06-15", "family_size_docdb": 3, "is_main_window_family": True, "family_priority_year": 2018, "primary_wipo_field": "Digital communication"},
            {"docdb_family_id": 300, "family_earliest_priority_date": "2020-01-01", "family_size_docdb": 7, "is_main_window_family": True, "family_priority_year": 2020, "primary_wipo_field": "Computer technology"},
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )

    # silver_family_status_history — legal state snapshots by year
    # family 100: has history at 2016 and 2018 → as_of_year 2017 → uses 2016 entry
    # family 200: has history at 2019 → as_of_year 2020 → uses 2019 entry
    # family 300: no history before 2022 → as_of_year 2022 → no match (all nulls)
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "snapshot_year": 2016, "snapshot_date": "2016-12-31", "family_composite_status": "fully_active", "active_jurisdiction_count": 3, "active_grant_branch_count": 2, "lapsed_jurisdiction_count": 0},
            {"docdb_family_id": 100, "snapshot_year": 2018, "snapshot_date": "2018-12-31", "family_composite_status": "partially_lapsed", "active_jurisdiction_count": 2, "active_grant_branch_count": 1, "lapsed_jurisdiction_count": 1},
            {"docdb_family_id": 200, "snapshot_year": 2019, "snapshot_date": "2019-12-31", "family_composite_status": "fully_active", "active_jurisdiction_count": 4, "active_grant_branch_count": 3, "lapsed_jurisdiction_count": 0},
        ],
        settings.silver_dir / "silver_family_status_history.parquet",
    )

    # silver_enriched_citation_network — citation edges with dates
    # family 100 cited by 9001 on 2016-05-01 (before as_of 2017-03-01) → counts
    # family 100 cited by 9002 on 2019-01-01 (after as_of 2017-03-01) → excluded
    # family 200 cited by 9003 on 2019-12-01 (before as_of 2020-06-15) → counts
    # family 200 cited by 9004 on 2021-01-01 (after as_of 2020-06-15) → excluded
    # family 300: no citations before as_of 2022-01-01
    write_pylist_parquet(
        [
            {"cited_docdb_family_id": 100, "source_docdb_family_id": 9001, "citation_date": "2016-05-01", "is_out_of_bounds": False, "is_intra_family_citation": False, "is_self_citation": False, "citing_assignee_name": "Acme", "clean_edge_weight": 0.4},
            {"cited_docdb_family_id": 100, "source_docdb_family_id": 9002, "citation_date": "2019-01-01", "is_out_of_bounds": False, "is_intra_family_citation": False, "is_self_citation": False, "citing_assignee_name": "Beta", "clean_edge_weight": 0.6},
            {"cited_docdb_family_id": 200, "source_docdb_family_id": 9003, "citation_date": "2019-12-01", "is_out_of_bounds": False, "is_intra_family_citation": False, "is_self_citation": False, "citing_assignee_name": "Gamma", "clean_edge_weight": 0.5},
            {"cited_docdb_family_id": 200, "source_docdb_family_id": 9004, "citation_date": "2021-01-01", "is_out_of_bounds": False, "is_intra_family_citation": False, "is_self_citation": False, "citing_assignee_name": "Delta", "clean_edge_weight": 0.3},
        ],
        settings.silver_dir / "silver_enriched_citation_network.parquet",
    )

    # gold_family_blocking_power_timeseries — blocking power by snapshot_date
    # family 100: entry at 2016 → as_of_year 2017 → uses 2016 entry
    # family 200: entry at 2020 → as_of_year 2020 → uses 2020 entry
    # family 300: entry at 2023 → as_of_year 2022 → no match
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "snapshot_date": "2016-12-31", "ui_blocking_power_score": 0.72, "overall_legal_enforceability_score": 0.65, "adjusted_citation_score_raw": 1.2},
            {"docdb_family_id": 200, "snapshot_date": "2020-12-31", "ui_blocking_power_score": 0.55, "overall_legal_enforceability_score": 0.50, "adjusted_citation_score_raw": 0.9},
            {"docdb_family_id": 300, "snapshot_date": "2023-12-31", "ui_blocking_power_score": 0.81, "overall_legal_enforceability_score": 0.78, "adjusted_citation_score_raw": 1.8},
        ],
        settings.gold_dir / "gold_family_blocking_power_timeseries.parquet",
    )

    # gold_family_field_contributions_timeseries — field contribution by year and field breadth
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "snapshot_year": 2016, "snapshot_date": "2016-12-31", "wipo_industry_code": "Computer technology", "enforceability_contribution_score": 0.45, "base_fraction": 0.6, "heritage_contribution_score": 0.3, "active_market_weight": 1.0, "max_active_stage": "grant", "is_active_on_snapshot": True},
            {"docdb_family_id": 100, "snapshot_year": 2016, "snapshot_date": "2016-12-31", "wipo_industry_code": "Digital communication", "enforceability_contribution_score": 0.25, "base_fraction": 0.4, "heritage_contribution_score": 0.2, "active_market_weight": 0.8, "max_active_stage": "grant", "is_active_on_snapshot": True},
            {"docdb_family_id": 200, "snapshot_year": 2020, "snapshot_date": "2020-12-31", "wipo_industry_code": "Digital communication", "enforceability_contribution_score": 0.38, "base_fraction": 0.8, "heritage_contribution_score": 0.2, "active_market_weight": 0.9, "max_active_stage": "grant", "is_active_on_snapshot": True},
            {"docdb_family_id": 300, "snapshot_year": 2022, "snapshot_date": "2022-12-31", "wipo_industry_code": "Computer technology", "enforceability_contribution_score": 0.22, "base_fraction": 0.4, "heritage_contribution_score": 0.1, "active_market_weight": 0.3, "max_active_stage": "application", "is_active_on_snapshot": True},
            {"docdb_family_id": 300, "snapshot_year": 2022, "snapshot_date": "2022-12-31", "wipo_industry_code": "Semiconductors", "enforceability_contribution_score": 0.18, "base_fraction": 0.3, "heritage_contribution_score": 0.1, "active_market_weight": 0.2, "max_active_stage": "application", "is_active_on_snapshot": True},
            {"docdb_family_id": 300, "snapshot_year": 2022, "snapshot_date": "2022-12-31", "wipo_industry_code": "Electrical machinery, apparatus, energy", "enforceability_contribution_score": 0.12, "base_fraction": 0.3, "heritage_contribution_score": 0.1, "active_market_weight": 0.2, "max_active_stage": "application", "is_active_on_snapshot": True},
        ],
        settings.gold_dir / "gold_family_field_contributions_timeseries.parquet",
    )

    # silver_branch_status_history_dense — jurisdiction breadth by year
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "jurisdiction_code": "US", "snapshot_year": 2016, "snapshot_date": "2016-12-31", "active_branch_flag": True},
            {"docdb_family_id": 100, "jurisdiction_code": "EP", "snapshot_year": 2016, "snapshot_date": "2016-12-31", "active_branch_flag": True},
            {"docdb_family_id": 100, "jurisdiction_code": "JP", "snapshot_year": 2016, "snapshot_date": "2016-12-31", "active_branch_flag": False},
            {"docdb_family_id": 200, "jurisdiction_code": "US", "snapshot_year": 2019, "snapshot_date": "2019-12-31", "active_branch_flag": True},
            {"docdb_family_id": 200, "jurisdiction_code": "EP", "snapshot_year": 2019, "snapshot_date": "2019-12-31", "active_branch_flag": True},
            {"docdb_family_id": 200, "jurisdiction_code": "JP", "snapshot_year": 2019, "snapshot_date": "2019-12-31", "active_branch_flag": True},
            {"docdb_family_id": 200, "jurisdiction_code": "CN", "snapshot_year": 2019, "snapshot_date": "2019-12-31", "active_branch_flag": True},
            {"docdb_family_id": 300, "jurisdiction_code": "US", "snapshot_year": 2022, "snapshot_date": "2022-12-31", "active_branch_flag": True},
            {"docdb_family_id": 300, "jurisdiction_code": "EP", "snapshot_year": 2022, "snapshot_date": "2022-12-31", "active_branch_flag": False},
        ],
        settings.silver_dir / "silver_branch_status_history_dense.parquet",
    )

    # silver_family_member_publications — safer family_size_docdb_asof from publication-dated members
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "appln_id": 1, "publn_date": "2016-01-01"},
            {"docdb_family_id": 100, "appln_id": 2, "publn_date": "2017-02-01"},
            {"docdb_family_id": 100, "appln_id": 3, "publn_date": "2018-01-01"},
            {"docdb_family_id": 200, "appln_id": 4, "publn_date": "2019-01-01"},
            {"docdb_family_id": 200, "appln_id": 5, "publn_date": "2020-03-01"},
            {"docdb_family_id": 200, "appln_id": 6, "publn_date": "2021-01-01"},
            {"docdb_family_id": 300, "appln_id": 7, "publn_date": "2020-06-01"},
            {"docdb_family_id": 300, "appln_id": 8, "publn_date": "2021-05-01"},
            {"docdb_family_id": 300, "appln_id": 9, "publn_date": "2022-06-01"},
        ],
        settings.silver_dir / "silver_family_member_publications.parquet",
    )

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "covered_wipo_fields": ["Computer technology", "Digital communication"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 2,
                "family_field_fraction": 0.5,
                "family_earliest_priority_date": "2015-03-01",
                "in_scope_appln_count": 3,
            },
            {
                "docdb_family_id": 200,
                "covered_wipo_fields": ["Digital communication"],
                "primary_wipo_field": "Digital communication",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": "2018-06-15",
                "in_scope_appln_count": 2,
            },
            {
                "docdb_family_id": 300,
                "covered_wipo_fields": ["Computer technology", "Semiconductors"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 2,
                "family_field_fraction": 0.5,
                "family_earliest_priority_date": "2020-01-01",
                "in_scope_appln_count": 3,
            },
        ],
        settings.silver_dir / "silver_family_wipo_fields.parquet",
    )

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "ipc_symbols": ["H04W4/029", "H04W40/20"],
                "cpc_symbols": ["H04L45/122", "H04W4/023", "H04W4/029"],
            },
            {
                "docdb_family_id": 200,
                "ipc_symbols": ["G06F3/048"],
                "cpc_symbols": ["G06F3/0481"],
            },
            {
                "docdb_family_id": 300,
                "ipc_symbols": ["H01L21/8242", "Y02E10/541"],
                "cpc_symbols": ["H01L21/8242", "Y02E10/541"],
            },
        ],
        settings.silver_dir / "silver_family_ipc_cpc_canonical.parquet",
    )

    write_pylist_parquet(
        [
            {"appln_id": 1, "cpc_class_symbol": "H04L45/122"},
            {"appln_id": 3, "cpc_class_symbol": "H04W4/023"},
            {"appln_id": 4, "cpc_class_symbol": "G06F3/0481"},
            {"appln_id": 8, "cpc_class_symbol": "H01L21/8242"},
            {"appln_id": 9, "cpc_class_symbol": "Y02E10/541"},
        ],
        settings.bronze_dir / "bronze_patstat_appln_cpc.parquet",
    )

    write_pylist_parquet(
        [
            {"appln_id": 1, "ipc_class_symbol": "H04L45/00", "ipc_version": "2015.01"},
            {"appln_id": 3, "ipc_class_symbol": "H04W4/00", "ipc_version": "2017.01"},
            {"appln_id": 4, "ipc_class_symbol": "G06F3/00", "ipc_version": "2018.01"},
            {"appln_id": 8, "ipc_class_symbol": "H01L21/00", "ipc_version": "2021.01"},
            {"appln_id": 9, "ipc_class_symbol": "Y02E10/00", "ipc_version": "2022.01"},
        ],
        settings.bronze_dir / "bronze_patstat_appln_ipc.parquet",
    )

    write_pylist_parquet(
        [
            {"appln_id": 1, "techn_field_nr": 1, "weight": 1.0},
            {"appln_id": 3, "techn_field_nr": 2, "weight": 1.0},
            {"appln_id": 4, "techn_field_nr": 2, "weight": 1.0},
            {"appln_id": 8, "techn_field_nr": 3, "weight": 1.0},
            {"appln_id": 9, "techn_field_nr": 4, "weight": 1.0},
        ],
        settings.bronze_dir / "bronze_patstat_appln_techn_field.parquet",
    )

    write_pylist_parquet(
        [
            {
                "ipc_subclass": "H04L",
                "ipc_maingroup_symbol": "H04L45/00",
                "techn_field_nr": 1,
                "techn_sector": "Electrical engineering",
                "techn_field": "Computer technology",
                "wipo_industry_code": "Computer technology",
            },
            {
                "ipc_subclass": "H04W",
                "ipc_maingroup_symbol": "H04W4/00",
                "techn_field_nr": 2,
                "techn_sector": "Electrical engineering",
                "techn_field": "Digital communication",
                "wipo_industry_code": "Digital communication",
            },
            {
                "ipc_subclass": "H01L",
                "ipc_maingroup_symbol": "H01L21/00",
                "techn_field_nr": 3,
                "techn_sector": "Electrical engineering",
                "techn_field": "Semiconductors",
                "wipo_industry_code": "Semiconductors",
            },
            {
                "ipc_subclass": "Y02E",
                "ipc_maingroup_symbol": "Y02E10/00",
                "techn_field_nr": 4,
                "techn_sector": "Instruments",
                "techn_field": "Electrical machinery, apparatus, energy",
                "wipo_industry_code": "Electrical machinery, apparatus, energy",
            },
        ],
        settings.bronze_dir / "bronze_ref_techn_field_ipc.parquet",
    )


def test_silver_pit_stage_is_exposed() -> None:
    assert callable(build_silver_family_pit)
    assert callable(build_silver_family_pit_dense)
    assert callable(build_silver_family_classification_visibility_timeline)
    assert callable(build_silver_family_classification_pit_dense)
    assert callable(run_silver_pit)
    assert callable(run_silver_pit_dense)
    assert callable(run_silver_pit_classification_visibility)
    assert callable(run_silver_pit_classification_dense)


def test_silver_pit_fails_when_inputs_are_missing(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    result = build_silver_family_pit(settings).finish()
    assert result.status == "failed"
    assert result.warnings


def test_silver_pit_produces_output_parquet(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    result = build_silver_family_pit(settings).finish()
    assert result.status == "success", result.warnings
    pit_table = settings.silver_dir / OUTPUT_TABLE
    audit_table = settings.silver_dir / AUDIT_TABLE
    assert pit_table.exists()
    assert audit_table.exists()
    assert result.metrics.get("silver_family_feature_snapshot_pit_rows", 0) == 3


def test_silver_pit_dense_produces_multi_year_output_parquet(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    result = build_silver_family_pit_dense(settings).finish()
    assert result.status == "success", result.warnings
    pit_table = settings.silver_dir / DENSE_OUTPUT_TABLE
    audit_table = settings.silver_dir / DENSE_AUDIT_TABLE
    assert pit_table.exists()
    assert audit_table.exists()
    assert result.metrics.get("silver_family_feature_snapshot_pit_dense_rows", 0) > 3


def test_silver_pit_schema_is_correct(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    cols = {row[0] for row in con.execute(f"describe select * from read_parquet('{pit_table}')").fetchall()}
    expected = {
        "docdb_family_id", "as_of_date", "as_of_year",
        "family_composite_status_asof", "active_jurisdiction_count_asof",
        "active_grant_branch_count_asof", "lapsed_jurisdiction_count_asof",
        "is_observed_as_of_snapshot", "family_size_docdb_asof", "family_jurisdiction_count_asof",
        "family_coverage_stability_score_asof", "family_tech_breadth_wipo_count_asof",
        "family_field_contribution_primary_asof", "family_blocking_power_score_asof",
        "family_enforceability_score_asof", "family_rcf_score_asof",
        "pre_asof_forward_citations_clean", "pre_asof_forward_citations_weighted",
        "pre_asof_unique_citing_family_count", "pre_asof_citing_assignee_diversity",
        "pre_asof_attacker_density_score", "data_completeness_pct_asof",
    }
    assert expected <= cols


def test_silver_pit_dense_schema_is_correct(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    pit_table = settings.silver_dir / DENSE_OUTPUT_TABLE
    con = duckdb.connect()
    cols = {row[0] for row in con.execute(f"describe select * from read_parquet('{pit_table}')").fetchall()}
    expected = {
        "docdb_family_id", "as_of_date", "as_of_year", "is_observed_as_of_snapshot", "is_partial_snapshot_year",
        "family_composite_status_asof", "active_jurisdiction_count_asof", "active_grant_branch_count_asof",
        "lapsed_jurisdiction_count_asof", "family_size_docdb_asof", "family_jurisdiction_count_asof",
        "family_coverage_stability_score_asof", "family_tech_breadth_wipo_count_asof",
        "family_field_contribution_primary_asof", "family_blocking_power_score_asof",
        "family_enforceability_score_asof", "family_rcf_score_asof",
        "pre_asof_forward_citations_clean", "pre_asof_forward_citations_weighted",
        "pre_asof_unique_citing_family_count", "pre_asof_citing_assignee_diversity",
        "pre_asof_attacker_density_score", "data_completeness_pct_asof",
    }
    assert expected <= cols


def test_silver_pit_as_of_dates_are_priority_plus_2_years(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"select docdb_family_id, as_of_date, as_of_year from read_parquet('{pit_table}') order by docdb_family_id"
    ).fetchall()
    # as_of_date may come back as date or datetime depending on DuckDB version
    assert rows[0][0] == 100 and rows[0][2] == 2017
    assert str(rows[0][1])[:10] == "2017-03-01"
    assert str(rows[1][1])[:10] == "2020-06-15"
    assert str(rows[2][1])[:10] == "2022-01-01"


def test_silver_pit_dense_generates_multiple_years_and_partial_current_year(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    pit_table = settings.silver_dir / DENSE_OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select docdb_family_id, as_of_year, cast(as_of_date as varchar), is_partial_snapshot_year
        from read_parquet('{pit_table}')
        where docdb_family_id = 100 and as_of_year in (2015, 2017, 2026)
        order by as_of_year
        """
    ).fetchall()
    assert rows == [
        (100, 2015, "2015-12-31", False),
        (100, 2017, "2017-12-31", False),
        (100, 2026, "2026-03-15", True),
    ]


def test_silver_pit_dense_citation_counts_change_across_years(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    pit_table = settings.silver_dir / DENSE_OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select as_of_year, pre_asof_forward_citations_clean
        from read_parquet('{pit_table}')
        where docdb_family_id = 100 and as_of_year in (2016, 2018, 2019)
        order by as_of_year
        """
    ).fetchall()
    assert rows == [
        (2016, 1.0),
        (2018, 1.0),
        (2019, 2.0),
    ]


def test_silver_pit_dense_audit_reports_multi_year_families(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    audit_table = settings.silver_dir / DENSE_AUDIT_TABLE
    import json
    data = json.loads(audit_table.read_text(encoding="utf-8"))
    assert data["duplicate_family_year_keys"] == 0
    assert data["families_with_multiple_year_rows"] == 3
    assert data["partial_snapshot_year_rows"] == 3


def test_silver_pit_citation_counts_bounded_by_as_of_date(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select
            docdb_family_id,
            pre_asof_forward_citations_clean,
            pre_asof_unique_citing_family_count
        from read_parquet('{pit_table}')
        order by docdb_family_id
        """
    ).fetchall()
    # family 100: only 9001 cited before 2017-03-01 → 1 citing family
    assert rows[0][0] == 100
    assert rows[0][1] == 1.0
    assert rows[0][2] == 1.0
    # family 200: only 9003 cited before 2020-06-15 → 1 citing family
    assert rows[1][0] == 200
    assert rows[1][1] == 1.0
    # family 300: no citations before 2022-01-01 → 0
    assert rows[2][0] == 300
    assert rows[2][1] == 0.0


def test_silver_pit_legal_state_is_nearest_history_at_or_before_as_of_year(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select docdb_family_id, family_composite_status_asof, active_jurisdiction_count_asof, active_grant_branch_count_asof
        from read_parquet('{pit_table}')
        order by docdb_family_id
        """
    ).fetchall()
    # family 100: as_of_year=2017, nearest ≤ 2017 is snapshot_year=2016 → fully_active, 3, 2
    assert rows[0] == (100, "fully_active", 3.0, 2.0)
    # family 200: as_of_year=2020, nearest ≤ 2020 is snapshot_year=2019 → fully_active, 4, 3
    assert rows[1] == (200, "fully_active", 4.0, 3.0)
    # family 300: no history before as_of_year=2022 → defaults to 'unknown', 0.0, 0.0
    assert rows[2][1] == "unknown"
    assert rows[2][2] == 0.0


def test_silver_pit_wipo_breadth_counts_distinct_fields(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"select docdb_family_id, family_tech_breadth_wipo_count_asof from read_parquet('{pit_table}') order by docdb_family_id"
    ).fetchall()
    assert rows[0] == (100, 2.0)   # Computer technology + Digital communication
    assert rows[1] == (200, 1.0)   # Digital communication only
    assert rows[2] == (300, 3.0)   # 3 distinct fields


def test_silver_pit_coverage_and_family_size_are_time_safe(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select
            docdb_family_id,
            family_size_docdb_asof,
            family_jurisdiction_count_asof,
            family_coverage_stability_score_asof
        from read_parquet('{pit_table}')
        order by docdb_family_id
        """
    ).fetchall()
    assert rows[0] == (100, 2.0, 3.0, 1.0)
    assert rows[1] == (200, 2.0, 4.0, 1.0)
    assert rows[2] == (300, 2.0, 2.0, 0.0)


def test_silver_pit_completeness_reflects_data_availability(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit(settings)
    pit_table = settings.silver_dir / OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"select docdb_family_id, data_completeness_pct_asof from read_parquet('{pit_table}') order by docdb_family_id"
    ).fetchall()
    # family 100 has legal history, citations, blocking power, field contributions → high completeness
    assert rows[0][1] > 0.5
    # family 300 has no history / no citations / no blocking power before as_of → lower completeness
    assert rows[2][1] < rows[0][1]


def test_silver_pit_run_wrapper_returns_stage_result_list(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    results = run_silver_pit(settings)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].stage == "silver-pit"


def test_silver_pit_writes_audit_json(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    result = build_silver_family_pit(settings).finish()
    assert result.status == "success"
    audit_path = settings.silver_dir / AUDIT_TABLE
    assert audit_path.exists()
    payload = audit_path.read_text(encoding="utf-8")
    assert '"duplicate_family_year_keys": 0' in payload
    assert '"anchor_date_mismatches": 0' in payload


def test_silver_pit_classification_dense_produces_output_parquet(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    build_silver_family_classification_visibility_timeline(settings)
    result = build_silver_family_classification_pit_dense(settings).finish()
    assert result.status == "success", result.warnings
    classification_table = settings.silver_dir / CLASSIFICATION_DENSE_OUTPUT_TABLE
    audit_table = settings.silver_dir / CLASSIFICATION_DENSE_AUDIT_TABLE
    assert classification_table.exists()
    assert audit_table.exists()
    assert result.metrics.get("silver_family_classification_pit_dense_rows", 0) > 3


def test_silver_pit_classification_dense_schema_is_correct(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    build_silver_family_classification_visibility_timeline(settings)
    build_silver_family_classification_pit_dense(settings)
    classification_table = settings.silver_dir / CLASSIFICATION_DENSE_OUTPUT_TABLE
    con = duckdb.connect()
    cols = {
        row[0]
        for row in con.execute(
            f"describe select * from read_parquet('{classification_table}')"
        ).fetchall()
    }
    expected = {
        "docdb_family_id",
        "as_of_date",
        "as_of_year",
        "is_observed_as_of_snapshot",
        "is_partial_snapshot_year",
        "covered_wipo_fields_asof",
        "primary_wipo_field_asof",
        "wipo_field_count_asof",
        "ipc_subclasses_asof",
        "cpc_sections_asof",
        "cpc_subclasses_asof",
        "cpc_main_groups_asof",
        "ipc_subclass_count_asof",
        "cpc_section_count_asof",
        "cpc_subclass_count_asof",
        "cpc_main_group_count_asof",
        "classification_visibility_policy",
        "classification_membership_replayed_to_history",
        "historical_classification_truth_supported",
    }
    assert expected <= cols


def test_silver_pit_classification_dense_uses_first_seen_visibility_across_years(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    build_silver_family_classification_visibility_timeline(settings)
    build_silver_family_classification_pit_dense(settings)
    classification_table = settings.silver_dir / CLASSIFICATION_DENSE_OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select
            as_of_year,
            covered_wipo_fields_asof,
            cpc_main_groups_asof,
            classification_visibility_policy,
            historical_classification_truth_supported
        from read_parquet('{classification_table}')
        where docdb_family_id = 100 and as_of_year in (2015, 2017, 2018, 2026)
        order by as_of_year
        """
    ).fetchall()
    assert rows == [
        (
            2015,
            [],
            [],
            "first_seen_classification_visibility",
            False,
        ),
        (
            2017,
            ["Computer technology"],
            ["H04L45/00"],
            "first_seen_classification_visibility",
            False,
        ),
        (
            2018,
            ["Computer technology", "Digital communication"],
            ["H04L45/00", "H04W4/00"],
            "first_seen_classification_visibility",
            False,
        ),
        (
            2026,
            ["Computer technology", "Digital communication"],
            ["H04L45/00", "H04W4/00"],
            "first_seen_classification_visibility",
            False,
        ),
    ]


def test_silver_pit_classification_dense_writes_audit_json(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    build_silver_family_classification_visibility_timeline(settings)
    result = build_silver_family_classification_pit_dense(settings).finish()
    assert result.status == "success"
    audit_path = settings.silver_dir / CLASSIFICATION_DENSE_AUDIT_TABLE
    payload = audit_path.read_text(encoding="utf-8")
    assert '"duplicate_family_year_keys": 0' in payload
    assert '"classification_visibility_policy": "first_seen_classification_visibility"' in payload


def test_silver_pit_classification_visibility_timeline_produces_output_parquet(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    result = build_silver_family_classification_visibility_timeline(settings).finish()
    assert result.status == "success", result.warnings
    visibility_table = settings.silver_dir / CLASSIFICATION_VISIBILITY_OUTPUT_TABLE
    audit_table = settings.silver_dir / CLASSIFICATION_VISIBILITY_AUDIT_TABLE
    assert visibility_table.exists()
    assert audit_table.exists()
    assert result.metrics.get("silver_family_classification_visibility_timeline_rows", 0) > 0


def test_silver_pit_classification_visibility_timeline_records_first_seen_years(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_classification_visibility_timeline(settings)
    visibility_table = settings.silver_dir / CLASSIFICATION_VISIBILITY_OUTPUT_TABLE
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select classification_type, classification_code, first_seen_year
        from read_parquet('{visibility_table}')
        where docdb_family_id = 100 and classification_type in ('WIPO_FIELD', 'CPC_MAIN_GROUP')
        order by classification_type, classification_code
        """
    ).fetchall()
    assert rows == [
        ("CPC_MAIN_GROUP", "H04L45/00", 2016),
        ("CPC_MAIN_GROUP", "H04W4/00", 2018),
        ("WIPO_FIELD", "Computer technology", 2016),
        ("WIPO_FIELD", "Digital communication", 2018),
    ]


def test_silver_pit_classification_dense_falls_back_without_visibility_timeline(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_minimal_inputs(settings)
    build_silver_family_pit_dense(settings)
    result = build_silver_family_classification_pit_dense(settings).finish()
    assert result.status == "success", result.warnings
    assert result.metrics["silver_family_classification_pit_dense_visibility_timeline_used"] is False
    assert any("stable_family_classification_replay" in warning for warning in result.warnings)
