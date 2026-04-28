from application.services.compare import CompareService


class FakePortfolioRepository:
    def __init__(self) -> None:
        self.family_calls: list[dict[str, object]] = []
        self.forecast_contributor_calls: list[dict[str, object]] = []

    def artifacts(self) -> list:
        return []

    def get_owner_summary(self, owner_id: str, as_of_year: int | None = None):
        rows = {
            "ALPHA": {
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha Corp",
                "portfolio_family_count_within_mega_cluster": 18,
                "portfolio_total_mass_score": 95.0,
                "portfolio_hit_rate_top_decile": 0.42,
                "portfolio_crown_jewel_index": 12.0,
                "portfolio_current_threat_score": 8.0,
                "portfolio_heritage_score": 42.0,
            },
            "BETA": {
                "owner_name_harmonized": "BETA",
                "owner_name_display": "Beta Labs",
                "portfolio_family_count_within_mega_cluster": 12,
                "portfolio_total_mass_score": 65.0,
                "portfolio_hit_rate_top_decile": 0.31,
                "portfolio_crown_jewel_index": 8.5,
                "portfolio_current_threat_score": 5.0,
                "portfolio_heritage_score": 31.0,
            },
            "TINY": {
                "owner_name_harmonized": "TINY",
                "owner_name_display": "Tiny IP",
                "portfolio_family_count_within_mega_cluster": 3,
                "portfolio_total_mass_score": 11.0,
                "portfolio_hit_rate_top_decile": 0.9,
                "portfolio_crown_jewel_index": 4.0,
                "portfolio_current_threat_score": 1.0,
                "portfolio_heritage_score": 7.0,
            },
        }
        return rows.get(owner_id, {})

    def get_owner_summary_peer_context(self, owner_id: str, as_of_year: int | None = None):
        rows = {
            "ALPHA": {
                "peer_bucket": "6_20",
                "portfolio_total_mass_score_percentile": 84.0,
                "portfolio_hit_rate_top_decile_percentile": 78.0,
                "portfolio_crown_jewel_index_percentile": 81.0,
                "portfolio_current_threat_score_percentile": 73.0,
                "portfolio_heritage_score_percentile": 69.0,
            },
            "BETA": {
                "peer_bucket": "6_20",
                "portfolio_total_mass_score_percentile": 63.0,
                "portfolio_hit_rate_top_decile_percentile": 55.0,
                "portfolio_crown_jewel_index_percentile": 58.0,
                "portfolio_current_threat_score_percentile": 52.0,
                "portfolio_heritage_score_percentile": 48.0,
            },
            "TINY": {
                "peer_bucket": "2_5",
                "portfolio_total_mass_score_percentile": 72.0,
                "portfolio_hit_rate_top_decile_percentile": 93.0,
                "portfolio_crown_jewel_index_percentile": 88.0,
                "portfolio_current_threat_score_percentile": 44.0,
                "portfolio_heritage_score_percentile": 39.0,
            },
        }
        return rows.get(owner_id, {})

    def get_owner_families(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        q: str | None = None,
        status: str | None = None,
        primary_field: str | None = None,
        sort: str | None = None,
        exclude_inactive: bool = False,
    ):
        self.family_calls.append(
            {
                "owner_id": owner_id,
                "as_of_year": as_of_year,
                "limit": limit,
                "offset": offset,
                "q": q,
                "status": status,
                "primary_field": primary_field,
                "sort": sort,
                "exclude_inactive": exclude_inactive,
            }
        )
        rows = {
            "ALPHA": [
                {
                    "family_id": "1001",
                    "blocking_score": 87.2,
                    "forecast_contributor": 3.1,
                    "primary_field": "Computer technology",
                    "status": "fully_active",
                },
                {
                    "family_id": "1002",
                    "blocking_score": 74.0,
                    "forecast_contributor": 2.2,
                    "primary_field": "Digital communication",
                    "status": "fully_active",
                },
            ],
            "BETA": [
                {
                    "family_id": "2001",
                    "blocking_score": 79.3,
                    "forecast_contributor": 2.8,
                    "primary_field": "Computer technology",
                    "status": "fully_active",
                },
            ],
            "TINY": [
                {
                    "family_id": "3001",
                    "blocking_score": 96.4,
                    "forecast_contributor": 1.1,
                    "primary_field": "Semiconductors",
                    "status": "pending_emerging",
                },
            ],
        }
        return rows.get(owner_id, [])[:limit]

    def get_owner_family_status_counts(self, owner_id: str):
        rows = {
            "ALPHA": {"active_family_count": 11, "pending_family_count": 3, "abandoned_family_count": 2},
            "BETA": {"active_family_count": 7, "pending_family_count": 2, "abandoned_family_count": 3},
            "TINY": {"active_family_count": 1, "pending_family_count": 1, "abandoned_family_count": 1},
        }
        return rows.get(owner_id, {})

    def get_owner_fields(self, owner_id: str, as_of_year: int | None = None, limit: int = 30):
        rows = {
            "ALPHA": [
                {"field": "Computer technology", "active_share": 0.52, "hotspot_direction": "gains"},
                {"field": "Digital communication", "active_share": 0.28, "hotspot_direction": "stable"},
            ],
            "BETA": [
                {"field": "Computer technology", "active_share": 0.41, "hotspot_direction": "stable"},
                {"field": "Semiconductors", "active_share": 0.24, "hotspot_direction": "gains"},
            ],
            "TINY": [{"field": "Semiconductors", "active_share": 0.88, "hotspot_direction": "gains"}],
        }
        return rows.get(owner_id, [])[:limit]

    def get_owner_forecast_summary(self, owner_id: str, as_of_year: int | None = None):
        rows = {
            "ALPHA": {
                "phase03_family_coverage_pct": 0.82,
                "portfolio_expected_future_citations_total_3y": 18.0,
                "portfolio_expected_future_citations_lower_3y": 15.0,
                "portfolio_expected_future_citations_upper_3y": 22.0,
                "portfolio_phase03_feature_completeness_pct_3y": 0.91,
                "portfolio_expected_future_citations_total_5y": 31.0,
                "portfolio_expected_future_citations_lower_5y": 27.0,
                "portfolio_expected_future_citations_upper_5y": 36.0,
                "portfolio_phase03_feature_completeness_pct_5y": 0.91,
                "portfolio_prediction_coverage_status": "moderate",
            },
            "BETA": {
                "phase03_family_coverage_pct": 0.77,
                "portfolio_expected_future_citations_total_3y": 13.0,
                "portfolio_expected_future_citations_lower_3y": 11.0,
                "portfolio_expected_future_citations_upper_3y": 17.0,
                "portfolio_phase03_feature_completeness_pct_3y": 0.86,
                "portfolio_expected_future_citations_total_5y": 24.0,
                "portfolio_expected_future_citations_lower_5y": 20.0,
                "portfolio_expected_future_citations_upper_5y": 28.0,
                "portfolio_phase03_feature_completeness_pct_5y": 0.86,
                "portfolio_prediction_coverage_status": "moderate",
            },
            "TINY": {
                "phase03_family_coverage_pct": 0.33,
                "portfolio_expected_future_citations_total_3y": 2.0,
                "portfolio_expected_future_citations_lower_3y": 0.5,
                "portfolio_expected_future_citations_upper_3y": 4.0,
                "portfolio_phase03_feature_completeness_pct_3y": 0.41,
                "portfolio_expected_future_citations_total_5y": 3.0,
                "portfolio_expected_future_citations_lower_5y": 1.0,
                "portfolio_expected_future_citations_upper_5y": 6.0,
                "portfolio_phase03_feature_completeness_pct_5y": 0.41,
                "portfolio_prediction_coverage_status": "low",
            },
        }
        return rows.get(owner_id, {})

    def get_owner_forecast_contributors(
        self,
        owner_id: str,
        horizon: str = "3y",
        contributor_scope: str = "phase03_future_citations",
        limit: int = 10,
        offset: int = 0,
        current_state_only: bool = False,
    ):
        self.forecast_contributor_calls.append(
            {
                "owner_id": owner_id,
                "horizon": horizon,
                "contributor_scope": contributor_scope,
                "limit": limit,
                "offset": offset,
                "current_state_only": current_state_only,
            }
        )
        rows = {
            "ALPHA": [
                {
                    "contributor_entity_id": "1001",
                    "jurisdiction_code": "US",
                    "horizon": "3y",
                    "contribution_share": 0.34,
                    "contribution_value": 3.1,
                    "status": "fully_active",
                },
            ],
            "BETA": [
                {
                    "contributor_entity_id": "2001",
                    "jurisdiction_code": "EP",
                    "horizon": "3y",
                    "contribution_share": 0.29,
                    "contribution_value": 2.4,
                    "status": "fully_active",
                },
            ],
            "TINY": [
                {
                    "contributor_entity_id": "3001",
                    "jurisdiction_code": "US",
                    "horizon": "3y",
                    "contribution_share": 0.81,
                    "contribution_value": 1.1,
                    "status": "pending_emerging",
                },
            ],
        }
        return rows.get(owner_id, [])[:limit]

    def get_owner_compare_timeslice(self, owner_id: str, base_year: int | None = None, compare_year: int | None = None):
        rows = {
            "ALPHA": [
                {
                    "owner_name_harmonized": "ALPHA",
                    "owner_name_display_current": "Alpha Corp",
                    "as_of_year": 2026,
                    "portfolio_family_count_hist_proxy": 18,
                    "portfolio_active_family_count_asof": 11,
                    "portfolio_active_jurisdiction_count_asof": 24,
                    "portfolio_lapsed_jurisdiction_count_asof": 3,
                    "portfolio_avg_blocking_power_score_asof": 8.2,
                    "portfolio_total_blocking_power_score_asof": 95.0,
                    "portfolio_avg_enforceability_score_asof": 2.4,
                    "portfolio_total_rcf_score_asof": 31.2,
                    "portfolio_data_completeness_pct_asof": 0.91,
                    "portfolio_top_family_blocking_share_asof": 0.18,
                    "portfolio_legal_durability_index_asof": 0.71,
                    "portfolio_field_breadth_asof": 6,
                    "portfolio_field_concentration_hhi_asof": 0.29,
                    "portfolio_top_field_share_asof": 0.36,
                    "historical_compare_safe": True,
                    "historical_owner_truth_supported": False,
                    "current_owner_bridge_replayed_to_history": True,
                    "historical_field_mix_supported": True,
                },
                {
                    "owner_name_harmonized": "ALPHA",
                    "owner_name_display_current": "Alpha Corp",
                    "as_of_year": 2024,
                    "portfolio_family_count_hist_proxy": 15,
                    "portfolio_active_family_count_asof": 9,
                    "portfolio_active_jurisdiction_count_asof": 18,
                    "portfolio_lapsed_jurisdiction_count_asof": 2,
                    "portfolio_avg_blocking_power_score_asof": 6.7,
                    "portfolio_total_blocking_power_score_asof": 72.0,
                    "portfolio_avg_enforceability_score_asof": 1.9,
                    "portfolio_total_rcf_score_asof": 24.5,
                    "portfolio_data_completeness_pct_asof": 0.86,
                    "portfolio_top_family_blocking_share_asof": 0.24,
                    "portfolio_legal_durability_index_asof": 0.63,
                    "portfolio_field_breadth_asof": 5,
                    "portfolio_field_concentration_hhi_asof": 0.34,
                    "portfolio_top_field_share_asof": 0.42,
                    "historical_compare_safe": True,
                    "historical_owner_truth_supported": False,
                    "current_owner_bridge_replayed_to_history": True,
                    "historical_field_mix_supported": True,
                },
            ],
        }
        return rows.get(owner_id, [])

    def get_owner_compare_timeslice_options(self, owner_id: str):
        rows = {
            "ALPHA": {
                "entity_id": "ALPHA",
                "available_years": [2026, 2024],
                "compare_safe_years": [2026, 2024],
                "default_base_year": 2026,
                "default_compare_year": 2024,
            }
        }
        return rows.get(owner_id, {"entity_id": str(owner_id), "available_years": [], "compare_safe_years": [], "default_base_year": None, "default_compare_year": None})


class FakeFamilyRepository:
    def artifacts(self) -> list:
        return []

    def get_family_compare_contexts(self, family_ids: list[str | int | None]):
        rows = {
            "123": {
                "docdb_family_id": 123,
                "primary_wipo_field": "Computer technology",
                "primary_wipo_field_current": "Computer technology",
                "family_priority_year": 2018,
                "family_composite_status": "fully_active",
                "family_composite_status_asof": "fully_active",
                "family_ui_blocking_power_score": 91.0,
                "family_enforceability_score_asof": 4.2,
                "legal_durability_percentile": 88.0,
                "pre_asof_forward_citations_weighted": 16.5,
                "citation_heritage_percentile": 83.0,
                "oecd_quality_proxy_score": 0.74,
            },
            "456": {
                "docdb_family_id": 456,
                "primary_wipo_field": "Computer technology",
                "primary_wipo_field_current": "Computer technology",
                "family_priority_year": 2018,
                "family_composite_status": "fully_active",
                "family_composite_status_asof": "fully_active",
                "family_ui_blocking_power_score": 63.0,
                "family_enforceability_score_asof": 2.7,
                "legal_durability_percentile": 61.0,
                "pre_asof_forward_citations_weighted": 9.4,
                "citation_heritage_percentile": 59.0,
                "oecd_quality_proxy_score": 0.51,
            },
            "789": {
                "docdb_family_id": 789,
                "primary_wipo_field": "Semiconductors",
                "primary_wipo_field_current": "Semiconductors",
                "family_priority_year": 2021,
                "family_composite_status": "pending_emerging",
                "family_composite_status_asof": "pending_emerging",
                "family_ui_blocking_power_score": 77.0,
                "family_enforceability_score_asof": 1.1,
                "legal_durability_percentile": 42.0,
                "pre_asof_forward_citations_weighted": None,
                "citation_heritage_percentile": 72.0,
                "oecd_quality_proxy_score": 0.66,
            },
        }
        return {
            str(family_id): rows[str(family_id)]
            for family_id in family_ids
            if family_id is not None and str(family_id) in rows
        }

    def get_family_compare_context(self, family_id: str | int):
        return self.get_family_compare_contexts([family_id]).get(str(family_id), {})

    def get_family_compare_suggestions(self, query: str, limit: int = 8):
        rows = [
            {
                "family_id": "123",
                "label": "123",
                "owner_name_display": "Alpha Corp",
                "primary_field": "Computer technology",
                "status": "fully_active",
            },
            {
                "family_id": "456",
                "label": "456",
                "owner_name_display": "Beta Labs",
                "primary_field": "Computer technology",
                "status": "fully_active",
            },
        ]
        return rows[:limit] if query else []

    def get_family_field_rows(self, family_id: str | int, as_of_year: int | None = None):
        rows = {
            "123": [
                {"wipo_industry_code": "Computer technology", "base_fraction": 0.61, "heritage_contribution_score": 0.8},
                {"wipo_industry_code": "Digital communication", "base_fraction": 0.21, "heritage_contribution_score": 0.4},
            ],
            "456": [
                {"wipo_industry_code": "Computer technology", "base_fraction": 0.48, "heritage_contribution_score": 0.7},
                {"wipo_industry_code": "Semiconductors", "base_fraction": 0.19, "heritage_contribution_score": 0.5},
            ],
            "789": [
                {"wipo_industry_code": "Semiconductors", "base_fraction": 0.74, "heritage_contribution_score": 0.6},
            ],
        }
        return rows.get(str(family_id), [])

    def get_family_forecasts(self, family_id: str | int):
        rows = {
            "123": [{"horizon": "3y", "point_forecast": 0.72, "interval_lower": 0.61, "interval_upper": 0.84, "selected_variant": "baseline"}],
            "456": [{"horizon": "3y", "point_forecast": 0.43, "interval_lower": 0.34, "interval_upper": 0.58, "selected_variant": "baseline"}],
            "789": [{"horizon": "3y", "point_forecast": 0.66, "interval_lower": 0.51, "interval_upper": 0.78, "selected_variant": "baseline"}],
        }
        return rows.get(str(family_id), [])

    def get_family_jurisdiction_legal_rows(self, family_id: str | int, as_of_year: int | None = None):
        rows = {
            "123": [
                {"jurisdiction_code": "US", "dominant_wipo_field": "Computer technology", "jurisdiction_relative_enforceability_band": "dominant", "jurisdiction_enforceability_share_of_family": 0.48, "branch_state_label": "active"},
            ],
            "456": [
                {"jurisdiction_code": "EP", "dominant_wipo_field": "Computer technology", "jurisdiction_relative_enforceability_band": "strong", "jurisdiction_enforceability_share_of_family": 0.33, "branch_state_label": "active"},
            ],
            "789": [
                {"jurisdiction_code": "KR", "dominant_wipo_field": "Semiconductors", "jurisdiction_relative_enforceability_band": "supporting", "jurisdiction_enforceability_share_of_family": 0.25, "branch_state_label": "pending"},
            ],
        }
        return rows.get(str(family_id), [])

    def get_family_compare_timeslice(self, family_id: str | int, base_year: int | None = None, compare_year: int | None = None):
        rows = {
            "123": [
                {
                    "docdb_family_id": 123,
                    "as_of_year": 2026,
                    "primary_wipo_field_current": "Computer technology",
                    "family_composite_status_asof": "fully_active",
                    "active_jurisdiction_count_asof": 4,
                    "active_grant_branch_count_asof": 3,
                    "lapsed_jurisdiction_count_asof": 1,
                    "family_size_docdb_asof": 6,
                    "family_tech_breadth_wipo_count_asof": 3,
                    "family_blocking_power_score_asof": 91.0,
                    "family_enforceability_score_asof": 4.2,
                    "family_coverage_stability_score_asof": 0.78,
                    "pre_asof_forward_citations_weighted": 16.5,
                    "family_rcf_score_asof": 7.1,
                    "pre_asof_unique_citing_family_count": 12,
                    "pre_asof_attacker_density_score": 0.44,
                    "data_completeness_pct_asof": 0.94,
                    "historical_compare_safe": True,
                    "current_owner_metadata_only": False,
                },
                {
                    "docdb_family_id": 123,
                    "as_of_year": 2024,
                    "primary_wipo_field_current": "Computer technology",
                    "family_composite_status_asof": "fully_active",
                    "active_jurisdiction_count_asof": 3,
                    "active_grant_branch_count_asof": 2,
                    "lapsed_jurisdiction_count_asof": 0,
                    "family_size_docdb_asof": 5,
                    "family_tech_breadth_wipo_count_asof": 2,
                    "family_blocking_power_score_asof": 74.0,
                    "family_enforceability_score_asof": 3.1,
                    "family_coverage_stability_score_asof": 0.66,
                    "pre_asof_forward_citations_weighted": 9.8,
                    "family_rcf_score_asof": 5.3,
                    "pre_asof_unique_citing_family_count": 7,
                    "pre_asof_attacker_density_score": 0.31,
                    "data_completeness_pct_asof": 0.88,
                    "historical_compare_safe": True,
                    "current_owner_metadata_only": False,
                },
            ],
        }
        return rows.get(str(family_id), [])

    def get_family_compare_timeslice_options(self, family_id: str | int):
        rows = {
            "123": {
                "entity_id": "123",
                "available_years": [2026, 2024],
                "compare_safe_years": [2026, 2024],
                "default_base_year": 2026,
                "default_compare_year": 2024,
            }
        }
        return rows.get(str(family_id), {"entity_id": str(family_id), "available_years": [], "compare_safe_years": [], "default_base_year": None, "default_compare_year": None})


def test_portfolio_compare_returns_four_lenses_and_top_family_preview():
    portfolio_repository = FakePortfolioRepository()
    service = CompareService(
        portfolio_repository=portfolio_repository,
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_portfolio_compare("ALPHA", "BETA", top_family_limit=2)

    assert response.compare_kind == "portfolios"
    assert response.left_entity is not None
    assert response.left_entity.id == "ALPHA"
    assert response.right_entity is not None
    assert response.right_entity.id == "BETA"
    lens_rows = [row for row in response.rows if row.get("kind") == "lens"]
    assert [row["lens"] for row in lens_rows] == ["mass", "density", "crown_jewel", "current_threat"]
    assert lens_rows[0]["same_peer_bucket"] is True
    assert lens_rows[0]["winner"] == "left"
    assert lens_rows[0]["winner_basis"] == "peer_percentile"
    assert lens_rows[0]["left_band_label"] == "Outsize Footprint"
    assert lens_rows[1]["left_band_label"] == "Dense"
    assert lens_rows[3]["left_band_label"] == "High Pressure"
    assert lens_rows[3]["winner_basis"] == "peer_percentile"
    preview_rows = [row for row in response.rows if row.get("kind") == "top_family_preview"]
    assert len(preview_rows) == 3
    assert preview_rows[0]["side"] == "left"
    assert response.summary_cards[0]["key"] == "family_count"
    assert response.field_overlap_rows[0]["label"] == "Computer technology"
    assert response.forecast_rows[0]["label"] == "3y future citations"
    assert any(row["kind"] == "forecast_contributor" for row in response.support_rows)
    assert any(c.code == "forecast_current_state_support" for c in response.meta.caveats)
    assert portfolio_repository.family_calls[0]["sort"] == "blocking"
    assert portfolio_repository.family_calls[0]["exclude_inactive"] is True
    assert portfolio_repository.forecast_contributor_calls[0]["current_state_only"] is True
    forecast_support_rows = [row for row in response.support_rows if row["kind"] == "forecast_contributor"]
    assert forecast_support_rows[0]["badge"] in {"fully_active", "pending_emerging"}
    assert response.meta.page == "compare.portfolios"


def test_portfolio_compare_adds_cross_scale_and_density_suppression_caveats():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_portfolio_compare("ALPHA", "TINY", top_family_limit=1)

    lens_rows = [row for row in response.rows if row.get("kind") == "lens"]
    density_row = next(row for row in lens_rows if row["lens"] == "density")
    assert density_row["same_peer_bucket"] is False
    assert density_row["suppressed"] is True
    assert density_row["suppression_reason"] is not None
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "cross_scale_compare" in caveat_codes
    assert "density_small_sample" in caveat_codes


def test_family_compare_returns_three_lenses_for_same_cohort():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_compare("123", "456")

    assert response.compare_kind == "families"
    assert response.left_entity is not None
    assert response.left_entity.id == "123"
    assert response.right_entity is not None
    assert response.right_entity.id == "456"
    lens_rows = [row for row in response.rows if row.get("kind") == "lens"]
    assert [row["lens"] for row in lens_rows] == ["blocking_posture", "legal_durability", "citation_heritage"]
    assert lens_rows[0]["same_cohort"] is True
    assert lens_rows[0]["left_band_label"] == "Leading"
    assert lens_rows[1]["winner_basis"] == "peer_percentile"
    assert lens_rows[2]["right_band_label"] == "Deep"
    assert response.summary_cards[0]["key"] == "family_size"
    legal_card = next(card for card in response.summary_cards if card["key"] == "legal_durability")
    assert legal_card["left_value"] == 88.0
    assert legal_card["right_value"] == 61.0
    assert "percentile" in legal_card["note"].lower()
    assert response.field_overlap_rows[0]["presence"] == "shared"
    assert response.forecast_rows[0]["label"] == "3y citation outlook"
    assert response.support_rows[0]["kind"] == "jurisdiction_preview"
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "family_compare_lenses" in caveat_codes


def test_family_compare_adds_cross_cohort_and_citation_proxy_caveats():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_compare("123", "789")

    lens_rows = [row for row in response.rows if row.get("kind") == "lens"]
    citation_row = next(row for row in lens_rows if row["lens"] == "citation_heritage")
    assert citation_row["same_cohort"] is False
    assert citation_row["comparison_mode"] == "cross_cohort_band_first"
    caveat_codes = [c.code for c in response.meta.caveats]
    assert "cross_cohort_family_compare" in caveat_codes
    assert "citation_proxy_fallback" in caveat_codes


def test_family_timeslice_compare_returns_year_split_payload():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_timeslice_compare("123")

    assert response.compare_kind == "families"
    assert response.compare_mode == "timeslice"
    assert response.left_entity is not None
    assert response.left_entity.label.endswith("2026")
    assert response.right_entity is not None
    assert response.right_entity.label.endswith("2024")
    assert response.rows == []
    assert response.summary_cards[0]["key"] == "family_size_asof"
    assert response.field_overlap_rows[0]["label"] == "Computer technology"
    assert response.forecast_rows[0]["label"] == "Weighted citation trajectory"
    assert response.support_rows[0]["kind"] == "jurisdiction_preview"
    assert response.meta.page == "compare.families.timeslice"


def test_family_timeslice_options_returns_available_years():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_timeslice_options("123")

    assert response.entity_id == "123"
    assert response.available_years == [2026, 2024]
    assert response.compare_safe_years == [2026, 2024]
    assert response.default_base_year == 2026
    assert response.default_compare_year == 2024


def test_family_compare_lookup_returns_scope_status():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_compare_lookup("123")

    assert response.compare_kind == "families"
    assert response.entity_id == "123"
    assert response.in_scope is True
    assert response.primary_field == "Computer technology"
    assert response.status == "fully_active"
    assert response.timeslice_available is True
    assert response.default_base_year == 2026


def test_family_compare_lookup_returns_not_in_scope_note():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_compare_lookup("999")

    assert response.entity_id == "999"
    assert response.in_scope is False
    assert response.note is not None
    assert "not available" in response.note


def test_family_compare_suggestions_return_rows():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_family_compare_suggestions("12", limit=5)

    assert response.query == "12"
    assert len(response.rows) == 2
    assert response.rows[0].family_id == "123"
    assert response.rows[0].owner_label == "Alpha Corp"


def test_portfolio_timeslice_compare_returns_year_split_payload():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_portfolio_timeslice_compare("ALPHA")

    assert response.compare_kind == "portfolios"
    assert response.compare_mode == "timeslice"
    assert response.left_entity is not None
    assert response.left_entity.label.endswith("2026")
    assert response.right_entity is not None
    assert response.right_entity.label.endswith("2024")
    assert response.rows == []
    assert response.summary_cards[0]["key"] == "families_in_scope"
    assert response.field_overlap_rows[0]["label"] == "Computer technology"
    assert response.forecast_rows[0]["label"] == "Average blocking trajectory"
    assert response.support_rows[0]["kind"] == "timeslice_support"
    assert response.meta.page == "compare.portfolios.timeslice"


def test_portfolio_timeslice_options_returns_available_years():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_portfolio_timeslice_options("ALPHA")

    assert response.entity_id == "ALPHA"
    assert response.available_years == [2026, 2024]
    assert response.compare_safe_years == [2026, 2024]
    assert response.default_base_year == 2026
    assert response.default_compare_year == 2024


def test_portfolio_compare_lookup_returns_scope_status():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_portfolio_compare_lookup("ALPHA")

    assert response.compare_kind == "portfolios"
    assert response.entity_id == "ALPHA"
    assert response.label == "Alpha Corp"
    assert response.in_scope is True
    assert response.family_count == 18
    assert response.timeslice_available is True
    assert response.default_compare_year == 2024


def test_portfolio_compare_lookup_returns_not_in_scope_note():
    service = CompareService(
        portfolio_repository=FakePortfolioRepository(),
        family_repository=FakeFamilyRepository(),
    )

    response = service.get_portfolio_compare_lookup("UNKNOWN")

    assert response.entity_id == "UNKNOWN"
    assert response.in_scope is False
    assert response.note is not None
    assert "not available" in response.note
