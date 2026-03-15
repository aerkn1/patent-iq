from __future__ import annotations

from patentiq_etl.bronze.source_registry import PATSTAT_TABLES, REFERENCE_TABLES, REGISTER_TABLES, REQUIRED_SOURCE_COLUMNS


def test_source_registry_includes_core_market_weighting_inputs() -> None:
    assert "bronze_ext_iso_country_map" in REFERENCE_TABLES
    assert "bronze_ext_world_bank_gdp_ppp" in REFERENCE_TABLES
    assert "bronze_ext_us_chamber_ip_index" in REFERENCE_TABLES
    assert "bronze_ext_up_member_states" in REFERENCE_TABLES
    assert "bronze_ext_kind_code_normalization_seed" in REFERENCE_TABLES
    assert "bronze_ext_oecd_indicator_seed" in REFERENCE_TABLES


def test_source_registry_includes_patstat_and_register_anchor_tables() -> None:
    assert "bronze_patstat_appln" in PATSTAT_TABLES
    assert "bronze_patstat_pat_publn" in PATSTAT_TABLES
    assert "bronze_patstat_inpadoc_legal_event" in PATSTAT_TABLES
    assert "bronze_reg101_appln" in REGISTER_TABLES
    assert "bronze_reg403_appln_status" in REGISTER_TABLES
    assert "bronze_reg301_event_data" in REGISTER_TABLES


def test_required_source_columns_cover_scope_and_semantic_anchors() -> None:
    assert REQUIRED_SOURCE_COLUMNS["bronze_patstat_appln"] == ["appln_id", "docdb_family_id", "appln_auth"]
    assert "ipc_class_symbol" in REQUIRED_SOURCE_COLUMNS["bronze_patstat_appln_ipc"]
    assert "cpc_class_symbol" in REQUIRED_SOURCE_COLUMNS["bronze_patstat_appln_cpc"]
    assert "jurisdiction_code" in REQUIRED_SOURCE_COLUMNS["bronze_ext_kind_code_normalization_seed"]
    assert "indicator_name" in REQUIRED_SOURCE_COLUMNS["bronze_ext_oecd_indicator_seed"]
