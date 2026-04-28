from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.silver.build_core import build_core_silver, build_history_refresh, build_owner_refresh
from patentiq_etl.silver.build_enrichment import (
    build_citation_and_market_layers,
    build_kindcode_legal_refresh_layers,
    build_kindcode_refresh_layers,
    build_legal_status_refresh_layers,
    build_semantic_representative_text,
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


def test_incremental_silver_refresh_stages_are_exposed() -> None:
    assert callable(build_kindcode_refresh_layers)
    assert callable(build_kindcode_legal_refresh_layers)
    assert callable(build_legal_status_refresh_layers)
    assert callable(build_history_refresh)
    assert callable(build_owner_refresh)


def test_semantic_representative_text_uses_epab_then_patstat(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_earliest_priority_date": date(2020, 1, 1)},
            {"docdb_family_id": 200, "family_earliest_priority_date": date(2021, 1, 1)},
        ],
        ensure_dir(settings.silver_dir) / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "appln_id": 10,
                "pat_publn_id": 1000,
                "publn_auth": "EP",
                "publn_kind": "B1",
                "publication_number_full": "EP123B1",
            },
            {
                "docdb_family_id": 200,
                "appln_id": 20,
                "pat_publn_id": 2000,
                "publn_auth": "US",
                "publn_kind": "B1",
                "publication_number_full": "US456B1",
            },
        ],
        settings.silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "appln_id": 10},
            {"docdb_family_id": 200, "appln_id": 20},
        ],
        settings.silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "EP", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True},
            {"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True},
        ],
        settings.silver_dir / "silver_kind_code_normalization.parquet",
    )
    write_pylist_parquet(
        [{"epab_doc_id": "doc-1", "publication_number_full": "EP123B1"}],
        ensure_dir(settings.bronze_dir) / "bronze_epab_document.parquet",
    )
    write_pylist_parquet(
        [{"epab_doc_id": "doc-1", "publication_number_full": "EP123B1", "language_code": "EN", "claim_sequence_no": 1, "claim_text_plain": "EP claim 1 text"}],
        settings.bronze_dir / "bronze_epab_claims.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 10, "appln_abstract": "EP abstract fallback", "appln_abstract_lg": "en"},
            {"appln_id": 20, "appln_abstract": "US abstract fallback", "appln_abstract_lg": "en"},
        ],
        settings.bronze_dir / "bronze_patstat_appln_abstr.parquet",
    )
    write_pylist_parquet(
        [{"publication_number_full": "US456B1", "claim_num": "1", "claim_text_plain": "USPTO claim text should be ignored"}],
        settings.bronze_dir / "bronze_uspto_ft_claims.parquet",
    )

    result = build_semantic_representative_text(settings).finish()

    assert result.status == "success"
    rep_path = settings.silver_dir / "silver_family_text_representative.parquet"
    con = duckdb.connect()
    rows = con.execute(
        """
        select
            docdb_family_id,
            representative_appln_id,
            representative_publn_id,
            representative_stage,
            representative_source_type,
            representative_claim_1_en,
            representative_abstract_en,
            text_provenance,
            is_abstract_fallback
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(rep_path)],
    ).fetchall()
    assert rows == [
        (100, 10, 1000, "STANDARD_GRANT", "EPAB_CLAIM", "EP claim 1 text", None, "EPAB_EP123B1", False),
        (200, 20, None, "PATSTAT_ABSTRACT_FALLBACK", "PATSTAT_ABSTRACT", None, "US abstract fallback", "PATSTAT_ABSTRACT", True),
    ]

    elig_rows = con.execute(
        "select docdb_family_id, has_ep_grant, is_semantic_candidate, is_in_vector_sample from read_parquet(?) order by docdb_family_id",
        [str(settings.silver_dir / "silver_semantic_sampling_eligibility.parquet")],
    ).fetchall()
    assert elig_rows == [(100, True, True, True), (200, False, True, True)]


def test_build_core_silver_materializes_multiyear_market_weighting(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "inpadoc_family_id": 900,
                "family_earliest_priority_date": date(2020, 1, 1),
                "scope_appln_count": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 1000,
                "appln_id": 10,
                "docdb_family_id": 100,
                "publn_auth": "US",
                "publn_nr": "123",
                "publn_kind": "B1",
                "publn_date": "2020-02-01",
                "publication_number_full": "US123B1",
                "scope_type": settings.scope_type,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
            [
                {
                    "appln_id": 10,
                    "docdb_family_id": 100,
                    "family_earliest_priority_date": date(2020, 1, 1),
                    "appln_auth": "US",
                    "wipo_industry_code": "Computer technology",
                }
            ],
            silver_dir / "silver_scope_appln_seed.parquet",
        )
    write_pylist_parquet(
        [
            {
                "appln_id": 10,
                "docdb_family_id": 100,
                "owner_name_harmonized": "Acme",
                "owner_name": "Acme",
                "owner_country": "US",
            }
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )

    write_pylist_parquet(
        [{"iso2": "US", "iso3": "USA", "country_name": "United States"}],
        bronze_dir / "bronze_ext_iso_country_map.parquet",
    )
    write_pylist_parquet(
        [
            {"iso3": "USA", "snapshot_year": 2023, "gdp_value": 1000000000000.0},
            {"iso3": "USA", "snapshot_year": 2024, "gdp_value": 6000000000000.0},
        ],
        bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet",
    )
    write_pylist_parquet(
        [
            {"iso2": "US", "snapshot_year": 2023, "ip_score": 40.0},
            {"iso2": "US", "snapshot_year": 2024, "ip_score": 50.0},
        ],
        bronze_dir / "bronze_ext_us_chamber_ip_index.parquet",
    )
    write_pylist_parquet(
        [{"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True}],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    weight_path = silver_dir / "silver_tiered_market_weighting.parquet"
    con = duckdb.connect()
    rows = con.execute(
        "select jurisdiction_code, snapshot_year, gdp_tier_weight, ip_score, final_market_multiplier from read_parquet(?) order by snapshot_year",
        [str(weight_path)],
    ).fetchall()
    assert rows == [
        ("US", 2023, 3.0, 40.0, 1.2),
        ("US", 2024, 5.0, 50.0, 2.5),
    ]


def test_build_owner_refresh_materializes_bridge_and_primary_owner(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "appln_id": 1, "owner_name_harmonized": "BETA", "owner_name": "Beta Ltd", "owner_country": "GB"},
            {"docdb_family_id": 100, "appln_id": 2, "owner_name_harmonized": "ALPHA", "owner_name": "Alpha Corp", "owner_country": "US"},
            {"docdb_family_id": 100, "appln_id": 3, "owner_name_harmonized": "ALPHA", "owner_name": "Alpha Corporation", "owner_country": "US"},
            {"docdb_family_id": 100, "appln_id": 4, "owner_name_harmonized": "UNKNOWN_OWNER", "owner_name": "Unknown Owner", "owner_country": None},
            {"docdb_family_id": 200, "appln_id": 5, "owner_name_harmonized": "UNKNOWN_OWNER", "owner_name": "Unknown Owner", "owner_country": None},
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )

    result = build_owner_refresh(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    primary_rows = con.execute(
        """
        select docdb_family_id, owner_name_harmonized, owner_name_display, owner_scope_appln_count, family_distinct_owner_count
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(silver_dir / "silver_assignee_harmonized.parquet")],
    ).fetchall()
    assert primary_rows == [
        (100, "ALPHA", "Alpha Corp", 2, 3),
        (200, "UNKNOWN_OWNER", "Unknown Owner", 1, 1),
    ]

    bridge_rows = con.execute(
        """
        select docdb_family_id, owner_name_harmonized, owner_scope_appln_count, owner_family_rank, is_primary_owner
        from read_parquet(?)
        order by docdb_family_id, owner_family_rank, owner_name_harmonized
        """,
        [str(silver_dir / "silver_family_owner_bridge.parquet")],
    ).fetchall()
    assert bridge_rows == [
        (100, "ALPHA", 2, 1, True),
        (100, "BETA", 1, 2, False),
        (100, "UNKNOWN_OWNER", 1, 3, False),
        (200, "UNKNOWN_OWNER", 1, 1, True),
    ]


def test_build_core_silver_uses_legal_publication_dates_for_negative_events(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "inpadoc_family_id": 900,
                "family_earliest_priority_date": date(2020, 1, 1),
                "scope_appln_count": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 1000,
                "appln_id": 10,
                "docdb_family_id": 100,
                "publn_auth": "US",
                "publn_nr": "123",
                "publn_kind": "B1",
                "publn_date": "2020-02-01",
                "publication_number_full": "US123B1",
                "scope_type": settings.scope_type,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 10,
                "docdb_family_id": 100,
                "family_earliest_priority_date": date(2020, 1, 1),
                "appln_auth": "US",
                "wipo_industry_code": "Computer technology",
            }
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 10,
                "docdb_family_id": 100,
                "owner_name_harmonized": "Acme",
                "owner_name": "Acme",
                "owner_country": "US",
            }
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )

    write_pylist_parquet(
        [{"iso2": "US", "iso3": "USA", "country_name": "United States"}],
        bronze_dir / "bronze_ext_iso_country_map.parquet",
    )
    write_pylist_parquet(
        [{"iso3": "USA", "snapshot_year": 2026, "gdp_value": 6000000000000.0}],
        bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "US", "snapshot_year": 2026, "ip_score": 50.0}],
        bronze_dir / "bronze_ext_us_chamber_ip_index.parquet",
    )
    write_pylist_parquet(
        [{"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True}],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "event_id": 1,
                "appln_id": 10,
                "event_seq_nr": 1,
                "event_type": "LEGAL_EVENT",
                "event_auth": "US",
                "event_code": "LAPS",
                "event_filing_date": date(9999, 12, 31),
                "event_publn_date": date(2022, 1, 17),
                "event_effective_date": date(9999, 12, 31),
                "lapse_date": date(9999, 12, 31),
                "event_text": "PATENT EXPIRED FOR FAILURE TO PAY MAINTENANCE FEES",
            }
        ],
        bronze_dir / "bronze_patstat_inpadoc_legal_event.parquet",
    )

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    legal_rows = con.execute(
        """
        select event_code, event_date, event_date_source, is_lapse_event, is_expiry_event
        from read_parquet(?)
        where appln_id = 10 and event_code = 'LAPS'
        """,
        [str(silver_dir / "silver_legal_status_event_ledger.parquet")],
    ).fetchall()
    assert legal_rows == [("LAPS", date(2022, 1, 17), "event_publn_date", True, False)]

    status_rows = con.execute(
        """
        select family_composite_status, active_jurisdiction_count, lapsed_jurisdiction_count, has_any_active_grant
        from read_parquet(?)
        where docdb_family_id = 100
        """,
        [str(silver_dir / "silver_family_status_pt.parquet")],
    ).fetchall()
    assert status_rows == [("dead", 0.0, 1.0, False)]


def test_build_citation_and_market_layers_materializes_localized_branch_rows(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)

    family_core_rows = []
    fields_rows = []
    status_rows = []
    jur_rows = []
    member_rows = []
    legal_rows = []
    appln_rows = []
    publn_rows = []
    for family_id in range(1, 27):
        priority_date = date(2020, 1, 1) if family_id == 1 else date(2021, 1, 1)
        appln_id = family_id * 10
        pat_publn_id = family_id * 100
        family_core_rows.append(
            {
                "docdb_family_id": family_id,
                "family_earliest_priority_date": priority_date,
                "family_priority_year": priority_date.year,
                "family_size_docdb": 1,
            }
        )
        fields_rows.append(
            {
                "docdb_family_id": family_id,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": priority_date,
                "in_scope_appln_count": 1,
            }
        )
        status_rows.append(
            {
                "docdb_family_id": family_id,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            }
        )
        jur_rows.append(
            {
                "docdb_family_id": family_id,
                "jurisdiction_code": "US",
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
            }
        )
        member_rows.append(
            {
                "pat_publn_id": pat_publn_id,
                "appln_id": appln_id,
                "docdb_family_id": family_id,
                "publn_auth": "US",
                "publn_nr": str(pat_publn_id),
                "publn_kind": "B1",
                "publn_date": priority_date,
                "publication_number_full": f"US{pat_publn_id}B1",
                "is_application_stage": False,
                "is_grant_stage": True,
                "is_modifier_stage": False,
                "scope_type": settings.scope_type,
                "snapshot_date": settings.snapshot_date,
            }
        )
        legal_rows.append(
            {
                "docdb_family_id": family_id,
                "appln_id": appln_id,
                "jurisdiction_code": "US",
                "event_date": priority_date,
                "event_code": "B1",
                "event_type": "STANDARD_GRANT",
                "event_severity": "active",
                "is_grant_event": True,
                "is_lapse_event": False,
                "is_opposition_event": False,
                "is_expiry_event": False,
                "is_up_event": False,
            }
        )
        appln_rows.append({"docdb_family_id": family_id, "appln_id": appln_id})
        publn_rows.append({"docdb_family_id": family_id, "pat_publn_id": pat_publn_id})

    write_pylist_parquet(family_core_rows, silver_dir / "silver_family_core.parquet")
    write_pylist_parquet(appln_rows, silver_dir / "silver_scope_appln_seed.parquet")
    write_pylist_parquet(publn_rows, silver_dir / "silver_scope_publn_seed.parquet")
    write_pylist_parquet(fields_rows, silver_dir / "silver_family_wipo_fields.parquet")
    write_pylist_parquet(status_rows, silver_dir / "silver_family_status_pt.parquet")
    write_pylist_parquet(jur_rows, silver_dir / "silver_family_jurisdiction_unrolled.parquet")
    write_pylist_parquet(member_rows, silver_dir / "silver_family_member_publications.parquet")
    write_pylist_parquet(legal_rows, silver_dir / "silver_legal_status_event_ledger.parquet")
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "US",
                "kind_code": "B1",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "is_application_stage": False,
                "is_post_grant_modifier": False,
                "legal_status_proxy": "grant",
                "method_version": settings.method_version,
            }
        ],
        silver_dir / "silver_kind_code_normalization.parquet",
    )
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "US",
                "snapshot_year": 2026,
                "gdp_value": 1_000_000_000_000.0,
                "ip_score": 50.0,
                "gdp_tier_weight": 3.0,
                "final_market_multiplier": 2.0,
            }
        ],
        silver_dir / "silver_tiered_market_weighting.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "has_up_registration": False, "up_detection_method": "none", "up_member_state_count": 0}
            for family_id in range(1, 27)
        ],
        silver_dir / "silver_up_status.parquet",
    )

    result = build_citation_and_market_layers(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    local_rows = con.execute(
        """
        select snapshot_year, jurisdiction_code, wipo_industry_code, local_family_filings, local_trend_coefficient
        from read_parquet(?)
        order by snapshot_year
        """,
        [str(silver_dir / "silver_local_tech_trends_timeseries.parquet")],
    ).fetchall()
    assert local_rows == [
        (2020, "US", "Computer technology", 1, 1.0),
        (2021, "US", "Computer technology", 25, 25.0),
    ]

    branch_stats = con.execute(
        """
        select
            count(*) as row_count,
            count(distinct branch_coefficient_mode) as mode_count,
            min(branch_enforceability_contribution_raw) as min_contrib,
            max(branch_enforceability_contribution_raw) as max_contrib
        from read_parquet(?)
        """,
        [str(silver_dir / "silver_family_enforceability_branches.parquet")],
    ).fetchone()
    branch_mode_rows = con.execute(
        "select distinct branch_coefficient_mode from read_parquet(?)",
        [str(silver_dir / "silver_family_enforceability_branches.parquet")],
    ).fetchall()
    assert branch_stats[0] == 26
    assert branch_stats[1] == 1
    assert branch_mode_rows == [("localized",)]
    assert float(branch_stats[2]) == 50.0
    assert float(branch_stats[3]) == 50.0

    field_rows = con.execute(
        """
        select
            count(*) as row_count,
            min(family_field_enforceability_contribution_score) as min_enforce,
            max(family_field_enforceability_contribution_score) as max_enforce,
            min(family_field_heritage_contribution_score) as min_heritage,
            max(family_field_heritage_contribution_score) as max_heritage
        from read_parquet(?)
        """,
        [str(silver_dir / "silver_family_field_contributions.parquet")],
    ).fetchone()
    assert field_rows[0] == 26
    assert float(field_rows[1]) == 50.0
    assert float(field_rows[2]) == 50.0
    assert float(field_rows[3]) == 0.0
    assert float(field_rows[4]) == 0.0


def test_build_core_silver_preserves_kind_code_curation_provenance(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "inpadoc_family_id": 900,
                "family_earliest_priority_date": date(2020, 1, 1),
                "scope_appln_count": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 1000,
                "appln_id": 10,
                "docdb_family_id": 100,
                "publn_auth": "UA",
                "publn_nr": "123",
                "publn_kind": "U",
                "publn_date": "2020-02-01",
                "publication_number_full": "UA123U",
                "scope_type": settings.scope_type,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 10,
                "docdb_family_id": 100,
                "family_earliest_priority_date": date(2020, 1, 1),
                "wipo_industry_code": "Computer technology",
            }
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 10,
                "docdb_family_id": 100,
                "owner_name_harmonized": "Acme",
                "owner_name": "Acme",
                "owner_country": "UA",
            }
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "UA",
                "kind_code": "U",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_curated",
                "source_reference": "WIPO Handbook 7.3.2",
            }
        ],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "UA", "iso3": "UKR", "country_name": "Ukraine"}],
        bronze_dir / "bronze_ext_iso_country_map.parquet",
    )
    write_pylist_parquet(
        [{"iso3": "UKR", "snapshot_year": 2024, "gdp_value": 1000000000.0}],
        bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "UA", "snapshot_year": 2024, "ip_score": 25.0}],
        bronze_dir / "bronze_ext_us_chamber_ip_index.parquet",
    )
    write_pylist_parquet(
        [{"member_state_code": "UA"}],
        bronze_dir / "bronze_ext_up_member_states.parquet",
    )
    write_pylist_parquet(
        [{"wipo_industry_code": "Computer technology", "snapshot_year": 2024, "family_count": 1, "global_trend_coefficient": 1.0}],
        bronze_dir / "bronze_ref_techn_field_ipc.parquet",
    )

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    row = con.execute(
        """
        select
            jurisdiction_code,
            kind_code,
            universal_stage,
            mapping_basis,
            review_status,
            source_reference
        from read_parquet(?)
        """,
        [str(silver_dir / "silver_kind_code_normalization.parquet")],
    ).fetchone()
    assert row == ("UA", "U", "STANDARD_GRANT", "MANUAL_OVERRIDE", "office_curated", "WIPO Handbook 7.3.2")


def test_build_core_silver_preserves_non_enforceable_stage_flags(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 200,
                "inpadoc_family_id": 901,
                "family_earliest_priority_date": date(2020, 1, 1),
                "scope_appln_count": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 2000,
                "appln_id": 20,
                "docdb_family_id": 200,
                "publn_auth": "GB",
                "publn_nr": "456",
                "publn_kind": "D0",
                "publn_date": "2020-02-01",
                "publication_number_full": "GB456D0",
                "scope_type": settings.scope_type,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 20,
                "docdb_family_id": 200,
                "family_earliest_priority_date": date(2020, 1, 1),
                "wipo_industry_code": "Computer technology",
            }
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 20,
                "docdb_family_id": 200,
                "owner_name_harmonized": "Acme",
                "owner_name": "Acme",
                "owner_country": "GB",
            }
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "GB",
                "kind_code": "D0",
                "universal_stage": "NON_ENFORCEABLE_PUBLICATION",
                "stage_multiplier": 0.0,
                "is_enforceable": False,
                "legal_status_proxy": "non_enforceable_publication",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "UK IPO + WIPO office inference",
            }
        ],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "GB", "iso3": "GBR", "country_name": "United Kingdom"}],
        bronze_dir / "bronze_ext_iso_country_map.parquet",
    )
    write_pylist_parquet(
        [{"iso3": "GBR", "snapshot_year": 2024, "gdp_value": 1000000000.0}],
        bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "GB", "snapshot_year": 2024, "ip_score": 25.0}],
        bronze_dir / "bronze_ext_us_chamber_ip_index.parquet",
    )
    write_pylist_parquet(
        [{"member_state_code": "GB"}],
        bronze_dir / "bronze_ext_up_member_states.parquet",
    )
    write_pylist_parquet(
        [{"wipo_industry_code": "Computer technology", "snapshot_year": 2024, "family_count": 1, "global_trend_coefficient": 1.0}],
        bronze_dir / "bronze_ref_techn_field_ipc.parquet",
    )

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    row = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, is_enforceable, is_application_stage, is_post_grant_modifier
        from read_parquet(?)
        """,
        [str(silver_dir / "silver_kind_code_normalization.parquet")],
    ).fetchone()
    assert row == ("GB", "D0", "NON_ENFORCEABLE_PUBLICATION", False, False, False)


def test_build_core_silver_preserves_pt_validation_and_fi_cz_kindcode_mappings(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "family_earliest_priority_date": date(2020, 1, 1),
                "scope_appln_count": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 1,
                "appln_id": 1,
                "docdb_family_id": 1,
                "publn_auth": "PT",
                "publn_nr": "123",
                "publn_kind": "T",
                "publn_date": "2024-01-01",
                "publication_number_full": "PT123T",
                "scope_type": settings.scope_type,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 1,
                "docdb_family_id": 1,
                "family_earliest_priority_date": date(2020, 1, 1),
                "wipo_industry_code": "Computer technology",
            }
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 1,
                "docdb_family_id": 1,
                "owner_name_harmonized": "Acme",
                "owner_name": "Acme",
                "owner_country": "PT",
            }
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "PT",
                "kind_code": "T",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "Portuguese INPI validation inference",
            },
            {
                "jurisdiction_code": "PT",
                "kind_code": "E",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_inferred",
                "source_reference": "Portuguese INPI validation inference",
            },
            {
                "jurisdiction_code": "FI",
                "kind_code": "L",
                "universal_stage": "PENDING_APPLICATION",
                "stage_multiplier": 0.2,
                "is_enforceable": False,
                "legal_status_proxy": "pending_application",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_curated",
                "source_reference": "WIPO Handbook 7.3.2",
            },
            {
                "jurisdiction_code": "CZ",
                "kind_code": "U1",
                "universal_stage": "STANDARD_GRANT",
                "stage_multiplier": 1.0,
                "is_enforceable": True,
                "legal_status_proxy": "active_grant",
                "mapping_basis": "MANUAL_OVERRIDE",
                "review_status": "office_curated",
                "source_reference": "Czech utility model publication examples",
            },
        ],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "PT", "iso3": "PRT", "country_name": "Portugal"}],
        bronze_dir / "bronze_ext_iso_country_map.parquet",
    )
    write_pylist_parquet(
        [{"iso3": "PRT", "snapshot_year": 2024, "gdp_value": 1000000000.0}],
        bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet",
    )
    write_pylist_parquet(
        [{"iso2": "PT", "snapshot_year": 2024, "ip_score": 25.0}],
        bronze_dir / "bronze_ext_us_chamber_ip_index.parquet",
    )
    write_pylist_parquet(
        [{"member_state_code": "PT"}],
        bronze_dir / "bronze_ext_up_member_states.parquet",
    )
    write_pylist_parquet(
        [{"wipo_industry_code": "Computer technology", "snapshot_year": 2024, "family_count": 1, "global_trend_coefficient": 1.0}],
        bronze_dir / "bronze_ref_techn_field_ipc.parquet",
    )

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(silver_dir / "silver_kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("CZ", "U1", "STANDARD_GRANT", "office_curated"),
        ("FI", "L", "PENDING_APPLICATION", "office_curated"),
        ("PT", "E", "STANDARD_GRANT", "office_inferred"),
        ("PT", "T", "STANDARD_GRANT", "office_inferred"),
    ]


def test_build_core_silver_preserves_utility_model_and_translation_stage_pairs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "inpadoc_family_id": 11, "family_earliest_priority_date": date(2020, 1, 1), "scope_appln_count": 1, "scope_type": settings.scope_type, "method_version": settings.method_version, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 1, "docdb_family_id": 1, "publn_auth": "PL", "publn_nr": "1", "publn_kind": "Y1", "publn_date": "2024-01-01", "publication_number_full": "PL1Y1", "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 1, "docdb_family_id": 1, "family_earliest_priority_date": date(2020, 1, 1), "wipo_industry_code": "Computer technology"},
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 1, "docdb_family_id": 1, "owner_name_harmonized": "Acme", "owner_name": "Acme", "owner_country": "PL"},
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "BR", "kind_code": "U2", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "Brazilian INPI utility-model application guidance"},
            {"jurisdiction_code": "BR", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "Brazilian INPI utility-model grant guidance"},
            {"jurisdiction_code": "DE", "kind_code": "T1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "DPMA T1 guidance"},
            {"jurisdiction_code": "PL", "kind_code": "U1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "UPRP bulletin inference"},
            {"jurisdiction_code": "PL", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "UPRP bulletin inference"},
            {"jurisdiction_code": "SI", "kind_code": "T1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Slovenian EP validation inference"},
        ],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet([{"iso2": "PL", "iso3": "POL", "country_name": "Poland"}], bronze_dir / "bronze_ext_iso_country_map.parquet")
    write_pylist_parquet([{"iso3": "POL", "snapshot_year": 2024, "gdp_value": 1000000000.0}], bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet")
    write_pylist_parquet([{"iso2": "PL", "snapshot_year": 2024, "ip_score": 25.0}], bronze_dir / "bronze_ext_us_chamber_ip_index.parquet")
    write_pylist_parquet([{"member_state_code": "PL"}], bronze_dir / "bronze_ext_up_member_states.parquet")
    write_pylist_parquet([{"wipo_industry_code": "Computer technology", "snapshot_year": 2024, "family_count": 1, "global_trend_coefficient": 1.0}], bronze_dir / "bronze_ref_techn_field_ipc.parquet")

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(silver_dir / "silver_kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("BR", "U2", "PENDING_APPLICATION", "office_curated"),
        ("BR", "Y1", "STANDARD_GRANT", "office_curated"),
        ("DE", "T1", "PENDING_APPLICATION", "office_curated"),
        ("PL", "U1", "PENDING_APPLICATION", "office_inferred"),
        ("PL", "Y1", "STANDARD_GRANT", "office_inferred"),
        ("SI", "T1", "STANDARD_GRANT", "office_inferred"),
    ]


def test_build_core_silver_preserves_ep_translation_and_followup_utility_pairs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "inpadoc_family_id": 11, "family_earliest_priority_date": date(2020, 1, 1), "scope_appln_count": 1, "scope_type": settings.scope_type, "method_version": settings.method_version, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 1, "docdb_family_id": 1, "publn_auth": "FI", "publn_nr": "1", "publn_kind": "T3", "publn_date": "2024-01-01", "publication_number_full": "FI1T3", "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 1, "docdb_family_id": 1, "family_earliest_priority_date": date(2020, 1, 1), "wipo_industry_code": "Computer technology"},
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 1, "docdb_family_id": 1, "owner_name_harmonized": "Acme", "owner_name": "Acme", "owner_country": "FI"},
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "FI", "kind_code": "T3", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "WIPO Handbook 7.3.2"},
            {"jurisdiction_code": "HR", "kind_code": "T1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Croatian EP validation inference"},
            {"jurisdiction_code": "CY", "kind_code": "T1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Cyprus EP validation inference"},
            {"jurisdiction_code": "LT", "kind_code": "T", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Lithuania EP validation inference"},
            {"jurisdiction_code": "SK", "kind_code": "U1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Slovak utility model inference"},
            {"jurisdiction_code": "SK", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Slovak utility model inference"},
            {"jurisdiction_code": "PH", "kind_code": "U1", "universal_stage": "PENDING_APPLICATION", "stage_multiplier": 0.2, "is_enforceable": False, "legal_status_proxy": "pending_application", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Philippine utility model inference"},
            {"jurisdiction_code": "PH", "kind_code": "Y1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Philippine utility model inference"},
        ],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet([{"iso2": "FI", "iso3": "FIN", "country_name": "Finland"}], bronze_dir / "bronze_ext_iso_country_map.parquet")
    write_pylist_parquet([{"iso3": "FIN", "snapshot_year": 2024, "gdp_value": 1000000000.0}], bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet")
    write_pylist_parquet([{"iso2": "FI", "snapshot_year": 2024, "ip_score": 25.0}], bronze_dir / "bronze_ext_us_chamber_ip_index.parquet")
    write_pylist_parquet([{"member_state_code": "FI"}], bronze_dir / "bronze_ext_up_member_states.parquet")
    write_pylist_parquet([{"wipo_industry_code": "Computer technology", "snapshot_year": 2024, "family_count": 1, "global_trend_coefficient": 1.0}], bronze_dir / "bronze_ref_techn_field_ipc.parquet")

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(silver_dir / "silver_kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("CY", "T1", "STANDARD_GRANT", "office_inferred"),
        ("FI", "T3", "STANDARD_GRANT", "office_curated"),
        ("HR", "T1", "STANDARD_GRANT", "office_inferred"),
        ("LT", "T", "STANDARD_GRANT", "office_inferred"),
        ("PH", "U1", "PENDING_APPLICATION", "office_inferred"),
        ("PH", "Y1", "STANDARD_GRANT", "office_inferred"),
        ("SK", "U1", "PENDING_APPLICATION", "office_inferred"),
        ("SK", "Y1", "STANDARD_GRANT", "office_inferred"),
    ]


def test_build_core_silver_preserves_at_u1_and_es_r1_stage_pairs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "inpadoc_family_id": 11, "family_earliest_priority_date": date(2020, 1, 1), "scope_appln_count": 1, "scope_type": settings.scope_type, "method_version": settings.method_version, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_scope_family_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 1, "appln_id": 1, "docdb_family_id": 1, "publn_auth": "AT", "publn_nr": "1", "publn_kind": "U1", "publn_date": "2024-01-01", "publication_number_full": "AT1U1", "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 1, "docdb_family_id": 1, "family_earliest_priority_date": date(2020, 1, 1), "wipo_industry_code": "Computer technology"},
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"appln_id": 1, "docdb_family_id": 1, "owner_name_harmonized": "Acme", "owner_name": "Acme", "owner_country": "AT"},
        ],
        silver_dir / "silver_scope_owner_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "AT", "kind_code": "U1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "legal_status_proxy": "active_grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_inferred", "source_reference": "Austrian utility-model registration inference"},
            {"jurisdiction_code": "ES", "kind_code": "R1", "universal_stage": "NON_ENFORCEABLE_PUBLICATION", "stage_multiplier": 0.0, "is_enforceable": False, "legal_status_proxy": "non_enforceable_publication", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "office_curated", "source_reference": "OEPM kind-code table"},
        ],
        bronze_dir / "bronze_ext_kind_code_normalization_seed.parquet",
    )
    write_pylist_parquet([{"iso2": "AT", "iso3": "AUT", "country_name": "Austria"}], bronze_dir / "bronze_ext_iso_country_map.parquet")
    write_pylist_parquet([{"iso3": "AUT", "snapshot_year": 2024, "gdp_value": 1000000000.0}], bronze_dir / "bronze_ext_world_bank_gdp_ppp.parquet")
    write_pylist_parquet([{"iso2": "AT", "snapshot_year": 2024, "ip_score": 25.0}], bronze_dir / "bronze_ext_us_chamber_ip_index.parquet")
    write_pylist_parquet([{"member_state_code": "AT"}], bronze_dir / "bronze_ext_up_member_states.parquet")
    write_pylist_parquet([{"wipo_industry_code": "Computer technology", "snapshot_year": 2024, "family_count": 1, "global_trend_coefficient": 1.0}], bronze_dir / "bronze_ref_techn_field_ipc.parquet")

    result = build_core_silver(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    rows = con.execute(
        """
        select jurisdiction_code, kind_code, universal_stage, review_status
        from read_parquet(?)
        order by jurisdiction_code, kind_code
        """,
        [str(silver_dir / "silver_kind_code_normalization.parquet")],
    ).fetchall()
    assert rows == [
        ("AT", "U1", "STANDARD_GRANT", "office_inferred"),
        ("ES", "R1", "NON_ENFORCEABLE_PUBLICATION", "office_curated"),
    ]


def test_build_citation_and_market_layers_materializes_windowed_citation_metrics(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "family_earliest_priority_date": date(2020, 1, 1), "family_priority_year": 2020, "family_size_docdb": 1},
            {"docdb_family_id": 2, "family_earliest_priority_date": date(2024, 1, 1), "family_priority_year": 2024, "family_size_docdb": 1},
            {"docdb_family_id": 3, "family_earliest_priority_date": date(2026, 1, 1), "family_priority_year": 2026, "family_size_docdb": 1},
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": anchor_date,
                "in_scope_appln_count": 1,
            }
            for family_id, anchor_date in (
                (1, date(2020, 1, 1)),
                (2, date(2024, 1, 1)),
                (3, date(2026, 1, 1)),
            )
        ],
        silver_dir / "silver_family_wipo_fields.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            }
            for family_id in (1, 2, 3)
        ],
        silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "jurisdiction_code": "US", "source_auth": "US", "is_up_unrolled": False, "is_classic_validation": False, "is_global_member": False}
            for family_id in (1, 2, 3)
        ],
        silver_dir / "silver_family_jurisdiction_unrolled.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ALPHA", "owner_name_display": "Alpha", "owner_country": "US", "owner_scope_appln_count": 1},
            {"docdb_family_id": 2, "owner_name_harmonized": "BETA", "owner_name_display": "Beta", "owner_country": "US", "owner_scope_appln_count": 1},
            {"docdb_family_id": 3, "owner_name_harmonized": "GAMMA", "owner_name_display": "Gamma", "owner_country": "US", "owner_scope_appln_count": 1},
        ],
        silver_dir / "silver_assignee_harmonized.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "appln_id": 10},
            {"docdb_family_id": 2, "appln_id": 20},
            {"docdb_family_id": 3, "appln_id": 30},
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "pat_publn_id": 100},
            {"docdb_family_id": 2, "pat_publn_id": 200},
            {"docdb_family_id": 3, "pat_publn_id": 300},
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 100, "appln_id": 10, "docdb_family_id": 1, "publn_auth": "US", "publn_nr": "100", "publn_kind": "B1", "publn_date": date(2020, 1, 1), "publication_number_full": "US100B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
            {"pat_publn_id": 200, "appln_id": 20, "docdb_family_id": 2, "publn_auth": "US", "publn_nr": "200", "publn_kind": "B1", "publn_date": date(2024, 1, 1), "publication_number_full": "US200B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
            {"pat_publn_id": 300, "appln_id": 30, "docdb_family_id": 3, "publn_auth": "US", "publn_nr": "300", "publn_kind": "B1", "publn_date": date(2026, 1, 1), "publication_number_full": "US300B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_family_member_publications.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "appln_id": family_id * 10, "jurisdiction_code": "US", "event_date": anchor_date, "event_code": "B1", "event_type": "STANDARD_GRANT", "event_severity": "active", "is_grant_event": True, "is_lapse_event": False, "is_opposition_event": False, "is_expiry_event": False, "is_up_event": False}
            for family_id, anchor_date in (
                (1, date(2020, 1, 1)),
                (2, date(2024, 1, 1)),
                (3, date(2026, 1, 1)),
            )
        ],
        silver_dir / "silver_legal_status_event_ledger.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "is_application_stage": False, "is_post_grant_modifier": False, "legal_status_proxy": "grant", "method_version": settings.method_version},
        ],
        silver_dir / "silver_kind_code_normalization.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "snapshot_year": 2020, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
            {"jurisdiction_code": "US", "snapshot_year": 2024, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
            {"jurisdiction_code": "US", "snapshot_year": 2026, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
        ],
        silver_dir / "silver_tiered_market_weighting.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "has_up_registration": False, "up_detection_method": "none", "up_member_state_count": 0}
            for family_id in (1, 2, 3)
        ],
        silver_dir / "silver_up_status.parquet",
    )

    write_pylist_parquet(
        [
            {"docdb_family_id": 2, "cited_docdb_family_id": 1},
            {"docdb_family_id": 3, "cited_docdb_family_id": 1},
        ],
        bronze_dir / "bronze_patstat_docdb_fam_citn.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 200, "citn_replenished": 0, "citn_id": 1, "citn_origin": "SEA", "cited_pat_publn_id": 100, "cited_appln_id": None, "pat_citn_seq_nr": 1, "cited_npl_publn_id": None, "npl_citn_seq_nr": None, "citn_gener_auth": "US"},
            {"pat_publn_id": 300, "citn_replenished": 0, "citn_id": 2, "citn_origin": "SEA", "cited_pat_publn_id": 100, "cited_appln_id": None, "pat_citn_seq_nr": 1, "cited_npl_publn_id": None, "npl_citn_seq_nr": None, "citn_gener_auth": "US"},
        ],
        bronze_dir / "bronze_patstat_citation.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 100, "publn_auth": "US", "publn_nr": "100", "publn_nr_original": "100", "publn_kind": "B1", "appln_id": 10, "publn_date": date(2020, 1, 1), "publn_lg": "en", "publn_first_grant": "Y", "publn_claims": 10},
            {"pat_publn_id": 200, "publn_auth": "US", "publn_nr": "200", "publn_nr_original": "200", "publn_kind": "B1", "appln_id": 20, "publn_date": date(2024, 1, 1), "publn_lg": "en", "publn_first_grant": "Y", "publn_claims": 10},
            {"pat_publn_id": 300, "publn_auth": "US", "publn_nr": "300", "publn_nr_original": "300", "publn_kind": "B1", "appln_id": 30, "publn_date": date(2026, 1, 1), "publn_lg": "en", "publn_first_grant": "Y", "publn_claims": 10},
        ],
        bronze_dir / "bronze_patstat_pat_publn.parquet",
    )
    write_pylist_parquet(
        [{"npl_publn_id": "NPL-1"}],
        bronze_dir / "bronze_patstat_npl_publn.parquet",
    )

    result = build_citation_and_market_layers(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    network_rows = con.execute(
        """
        select
            source_docdb_family_id,
            cited_docdb_family_id,
            citation_date,
            citing_jurisdiction_code,
            clean_edge_weight,
            citing_stage_multiplier,
            citing_market_multiplier,
            clipped_trend_coefficient,
            citation_lethality_score
        from read_parquet(?)
        order by citation_date
        """,
        [str(silver_dir / "silver_enriched_citation_network.parquet")],
    ).fetchall()
    assert len(network_rows) == 2
    assert network_rows[0][:4] == (2, 1, date(2024, 1, 1), "US")
    assert network_rows[1][:4] == (3, 1, date(2026, 1, 1), "US")
    assert float(network_rows[0][4]) == 1.0
    assert float(network_rows[0][5]) == 1.0
    assert float(network_rows[0][6]) == 2.0
    assert float(network_rows[0][7]) >= 0.5
    assert float(network_rows[0][8]) > 0.0

    metric_row = con.execute(
        """
        select
            family_forward_citations_raw,
            family_forward_citations_clean,
            family_forward_citations_weighted,
            family_fwd_cits5,
            family_fwd_cits7,
            family_adjusted_citation_score_raw
        from read_parquet(?)
        where docdb_family_id = 1
        """,
        [str(silver_dir / "silver_family_citation_metrics.parquet")],
    ).fetchone()
    assert metric_row[0] == 2
    assert metric_row[1] == 2
    assert float(metric_row[2]) > 0.0
    assert metric_row[3] == 1
    assert metric_row[4] == 2
    assert float(metric_row[5]) > 0.0


def test_kindcode_refresh_rebuilds_only_dependent_silver_outputs(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "family_earliest_priority_date": date(2020, 1, 1), "family_priority_year": 2020, "family_size_docdb": 1},
            {"docdb_family_id": 2, "family_earliest_priority_date": date(2024, 1, 1), "family_priority_year": 2024, "family_size_docdb": 1},
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": anchor_date,
                "in_scope_appln_count": 1,
            }
            for family_id, anchor_date in ((1, date(2020, 1, 1)), (2, date(2024, 1, 1)))
        ],
        silver_dir / "silver_family_wipo_fields.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            }
            for family_id in (1, 2)
        ],
        silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "jurisdiction_code": "US", "source_auth": "US", "is_up_unrolled": False, "is_classic_validation": False, "is_global_member": False}
            for family_id in (1, 2)
        ],
        silver_dir / "silver_family_jurisdiction_unrolled.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ALPHA", "owner_name_display": "Alpha", "owner_country": "US", "owner_scope_appln_count": 1},
            {"docdb_family_id": 2, "owner_name_harmonized": "BETA", "owner_name_display": "Beta", "owner_country": "US", "owner_scope_appln_count": 1},
        ],
        silver_dir / "silver_assignee_harmonized.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "appln_id": 10},
            {"docdb_family_id": 2, "appln_id": 20},
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "pat_publn_id": 100},
            {"docdb_family_id": 2, "pat_publn_id": 200},
        ],
        silver_dir / "silver_scope_publn_seed.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 100, "appln_id": 10, "docdb_family_id": 1, "publn_auth": "US", "publn_nr": "100", "publn_kind": "B1", "publn_date": date(2020, 1, 1), "publication_number_full": "US100B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
            {"pat_publn_id": 200, "appln_id": 20, "docdb_family_id": 2, "publn_auth": "US", "publn_nr": "200", "publn_kind": "B1", "publn_date": date(2024, 1, 1), "publication_number_full": "US200B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_family_member_publications.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "appln_id": family_id * 10, "jurisdiction_code": "US", "event_date": anchor_date, "event_code": "B1", "event_type": "STANDARD_GRANT", "event_severity": "active", "is_grant_event": True, "is_lapse_event": False, "is_opposition_event": False, "is_expiry_event": False, "is_up_event": False}
            for family_id, anchor_date in ((1, date(2020, 1, 1)), (2, date(2024, 1, 1)))
        ],
        silver_dir / "silver_legal_status_event_ledger.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 1.0, "is_enforceable": True, "is_application_stage": False, "is_post_grant_modifier": False, "legal_status_proxy": "grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "docdb_curated", "source_reference": "seed", "method_version": settings.method_version},
        ],
        silver_dir / "silver_kind_code_normalization.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "snapshot_year": 2020, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
            {"jurisdiction_code": "US", "snapshot_year": 2024, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
            {"jurisdiction_code": "US", "snapshot_year": 2026, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
        ],
        silver_dir / "silver_tiered_market_weighting.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "has_up_registration": False, "up_detection_method": "none", "up_member_state_count": 0}
            for family_id in (1, 2)
        ],
        silver_dir / "silver_up_status.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 2, "cited_docdb_family_id": 1}],
        bronze_dir / "bronze_patstat_docdb_fam_citn.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 200, "citn_replenished": 0, "citn_id": 1, "citn_origin": "SEA", "cited_pat_publn_id": 100, "cited_appln_id": None, "pat_citn_seq_nr": 1, "cited_npl_publn_id": None, "npl_citn_seq_nr": None, "citn_gener_auth": "US"},
        ],
        bronze_dir / "bronze_patstat_citation.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 100, "publn_auth": "US", "publn_nr": "100", "publn_nr_original": "100", "publn_kind": "B1", "appln_id": 10, "publn_date": date(2020, 1, 1), "publn_lg": "en", "publn_first_grant": "Y", "publn_claims": 10},
            {"pat_publn_id": 200, "publn_auth": "US", "publn_nr": "200", "publn_nr_original": "200", "publn_kind": "B1", "appln_id": 20, "publn_date": date(2024, 1, 1), "publn_lg": "en", "publn_first_grant": "Y", "publn_claims": 10},
        ],
        bronze_dir / "bronze_patstat_pat_publn.parquet",
    )
    write_pylist_parquet(
        [{"npl_publn_id": "NPL-1"}],
        bronze_dir / "bronze_patstat_npl_publn.parquet",
    )

    initial = build_citation_and_market_layers(settings).finish()
    assert initial.status == "success"

    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 0.5, "is_enforceable": True, "is_application_stage": False, "is_post_grant_modifier": False, "legal_status_proxy": "grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "docdb_curated", "source_reference": "seed", "method_version": settings.method_version},
        ],
        silver_dir / "silver_kind_code_normalization.parquet",
    )

    refreshed = build_kindcode_refresh_layers(settings).finish()
    assert refreshed.status == "success"

    con = duckdb.connect()
    network_row = con.execute(
        """
        select citing_stage_multiplier
        from read_parquet(?)
        where source_docdb_family_id = 2 and cited_docdb_family_id = 1
        """,
        [str(silver_dir / "silver_enriched_citation_network.parquet")],
    ).fetchone()
    assert float(network_row[0]) == 0.5


def test_kindcode_legal_refresh_rebuilds_branch_outputs_from_refreshed_citation_metrics(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    bronze_dir = ensure_dir(settings.bronze_dir)

    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "family_earliest_priority_date": date(2020, 1, 1), "family_priority_year": 2020, "family_size_docdb": 1},
            {"docdb_family_id": 2, "family_earliest_priority_date": date(2024, 1, 1), "family_priority_year": 2024, "family_size_docdb": 1},
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": anchor_date,
                "in_scope_appln_count": 1,
            }
            for family_id, anchor_date in ((1, date(2020, 1, 1)), (2, date(2024, 1, 1)))
        ],
        silver_dir / "silver_family_wipo_fields.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            }
            for family_id in (1, 2)
        ],
        silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "jurisdiction_code": "US", "source_auth": "US", "is_up_unrolled": False, "is_classic_validation": False, "is_global_member": False}
            for family_id in (1, 2)
        ],
        silver_dir / "silver_family_jurisdiction_unrolled.parquet",
    )
    write_pylist_parquet(
        [
            {"pat_publn_id": 100, "appln_id": 10, "docdb_family_id": 1, "publn_auth": "US", "publn_nr": "100", "publn_kind": "B1", "publn_date": date(2020, 1, 1), "publication_number_full": "US100B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
            {"pat_publn_id": 200, "appln_id": 20, "docdb_family_id": 2, "publn_auth": "US", "publn_nr": "200", "publn_kind": "B1", "publn_date": date(2024, 1, 1), "publication_number_full": "US200B1", "is_application_stage": False, "is_grant_stage": True, "is_modifier_stage": False, "scope_type": settings.scope_type, "snapshot_date": settings.snapshot_date},
        ],
        silver_dir / "silver_family_member_publications.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "appln_id": family_id * 10, "jurisdiction_code": "US", "event_date": anchor_date, "event_code": "B1", "event_type": "STANDARD_GRANT", "event_severity": "active", "is_grant_event": True, "is_lapse_event": False, "is_opposition_event": False, "is_expiry_event": False, "is_up_event": False}
            for family_id, anchor_date in ((1, date(2020, 1, 1)), (2, date(2024, 1, 1)))
        ],
        silver_dir / "silver_legal_status_event_ledger.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "kind_code": "B1", "universal_stage": "STANDARD_GRANT", "stage_multiplier": 0.5, "is_enforceable": True, "is_application_stage": False, "is_post_grant_modifier": False, "legal_status_proxy": "grant", "mapping_basis": "MANUAL_OVERRIDE", "review_status": "docdb_curated", "source_reference": "seed", "method_version": settings.method_version},
        ],
        silver_dir / "silver_kind_code_normalization.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "snapshot_year": 2020, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
            {"jurisdiction_code": "US", "snapshot_year": 2024, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
            {"jurisdiction_code": "US", "snapshot_year": 2026, "gdp_value": 1_000_000_000_000.0, "ip_score": 50.0, "gdp_tier_weight": 3.0, "final_market_multiplier": 2.0},
        ],
        silver_dir / "silver_tiered_market_weighting.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": family_id, "has_up_registration": False, "up_detection_method": "none", "up_member_state_count": 0}
            for family_id in (1, 2)
        ],
        silver_dir / "silver_up_status.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": family_id,
                "family_adjusted_citation_score_raw": 1.0 if family_id == 1 else 2.0,
            }
            for family_id in (1, 2)
        ],
        silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {
                "snapshot_year": 2024,
                "wipo_industry_code": "Computer technology",
                "global_family_filings": 100,
                "prior_period_global_family_filings": 90,
                "global_growth_rate": 0.1111111111,
                "global_trend_coefficient": 1.1111111111,
                "counting_unit": "family_count",
                "family_model": settings.scope_type,
                "method_version": settings.method_version,
            },
        ],
        silver_dir / "silver_global_tech_trends_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "snapshot_year": 2024,
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "local_family_filings": 30,
                "prior_period_local_family_filings": 20,
                "local_growth_rate": 0.5,
                "local_trend_coefficient": 1.5,
                "counting_unit": "family_count",
                "family_model": settings.scope_type,
                "method_version": settings.method_version,
            },
        ],
        silver_dir / "silver_local_tech_trends_timeseries.parquet",
    )

    refreshed = build_kindcode_legal_refresh_layers(settings).finish()
    assert refreshed.status == "success"

    con = duckdb.connect()
    branch_row = con.execute(
        """
        select branch_stage_multiplier
        from read_parquet(?)
        where docdb_family_id = 1 and jurisdiction_code = 'US' and wipo_industry_code = 'Computer technology'
        """,
        [str(silver_dir / "silver_family_enforceability_branches.parquet")],
    ).fetchone()
    assert float(branch_row[0]) == 0.5
