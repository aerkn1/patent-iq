from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.services.market_intelligence_service import MarketIntelligenceService


class FakeMarketRepo:
    def get_overview(self):
        return {
            "segment_count": 1,
            "rising_segment_count": 1,
            "cooling_segment_count": 0,
            "total_family_count": 1200,
            "avg_segment_family_count": 1200,
        }

    def get_scope(self):
        return {
            "covered_field_count": 1,
            "start_year": 2022,
            "end_year": 2025,
            "latest_comparable_market_year": 2024,
            "latest_market_year": 2025,
            "latest_cpc_year": 2025,
            "snapshot_date": "2026-03-15",
        }

    def get_segments(self):
        return [
            {
                "segment_id": "Digital communication",
                "wipo_industry_code": "Digital communication",
                "market_state": "rising",
                "total_family_count": 1200,
                "latest_year": 2025,
                "latest_market_year": 2025,
                "snapshot_date": "2026-03-15",
                "segment_heat_state_asof": "rising",
                "segment_market_state_ui_safe_asof": True,
                "segment_priority_year_incomplete_asof": False,
                "segment_latest_comparable_year": 2024,
                "segment_family_count_stock_asof": 980,
                "segment_family_count_asof": 420,
                "segment_prior_family_count_asof": 360,
                "segment_growth_index_asof": 0.1667,
                "segment_owner_count_hist_proxy_asof": 120,
                "segment_blocking_density_asof": 29.5,
                "segment_field_balance_asof": 0.74,
                "segment_active_family_count_asof": 710,
                "segment_active_weight_asof": 0.83,
                "segment_active_jurisdiction_share_asof": 0.68,
                "segment_enforceability_density_asof": 0.61,
                "segment_top_owner_share_hist_proxy": 0.031,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_oecd_supported": False,
            }
        ]

    def get_timeseries(self):
        return [
            {
                "family_priority_year": 2023,
                "wipo_industry_code": "Digital communication",
                "family_count": 360,
                "prior_family_count": 310,
                "market_state": "rising",
                "market_state_ui_safe": True,
                "is_recent_priority_year_incomplete": False,
                "latest_comparable_year": 2024,
            },
            {
                "family_priority_year": 2024,
                "wipo_industry_code": "Digital communication",
                "family_count": 420,
                "prior_family_count": 360,
                "market_state": "rising",
                "market_state_ui_safe": True,
                "is_recent_priority_year_incomplete": False,
                "latest_comparable_year": 2024,
            },
        ]

    def get_segment_citation_trend(self, segment):
        assert segment == "Digital communication"
        return [
            {
                "as_of_year": 2024,
                "wipo_industry_code": segment,
                "citation_event_count": 25,
                "citation_count": 22.5,
                "citation_lethality_sum_raw": 19.1,
                "distinct_citing_assignee_count": 7,
                "distinct_citing_jurisdiction_count": 3,
                "citation_pressure_index": 17.4,
                "market_citation_state": "heating",
                "market_state_reference": "rising",
            }
        ]

    def get_segment_top_jurisdictions(self, segment):
        return [
            {
                "as_of_year": 2024,
                "wipo_industry_code": segment,
                "jurisdiction_code": "US",
                "citation_event_count": 12,
                "distinct_citing_assignee_count": 4,
                "citation_count": 10.0,
                "citation_lethality_sum_raw": 8.0,
                "citation_pressure_index": 7.5,
            }
        ]

    def get_segment_top_attackers(self, segment):
        return [
            {
                "as_of_year": 2024,
                "wipo_industry_code": segment,
                "citing_assignee_name": "ACME_INC",
                "citation_event_count": 6,
                "distinct_citing_jurisdiction_count": 2,
                "citation_count": 5.4,
                "citation_lethality_sum_raw": 4.1,
                "attacker_pressure_index": 3.2,
            }
        ]

    def get_segment_top_owners(self, segment):
        return [
            {
                "as_of_year": 2024,
                "leaderboard_rank": 1,
                "owner_name_harmonized": "ACME_HOLDINGS",
                "owner_name_display_current": "Acme Holdings",
                "in_segment_family_count_hist_proxy": 44,
                "in_segment_family_share_hist_proxy": 0.031,
                "avg_blocking_score_asof": 72.4,
                "total_blocking_score_asof": 3185.0,
                "field_presence_weight_asof": 0.71,
                "family_composite_status_asof": "fully_active",
            }
        ]

    def get_segment_top_cpcs(self, segment):
        return []

    def get_global_cpc_importance(self):
        return []

    def get_segment_forecasts(self, segment):
        return [
            {
                "horizon": 3,
                "as_of_year": 2024,
                "jurisdiction_code": "US",
                "wipo_industry_code": segment,
                "local_family_filings_asof": 100,
                "predicted_direction_band": "heating",
                "trend_strength_band": "measured",
                "support_level": "moderate",
                "predicted_direction_probability": 0.63,
                "predicted_margin": 0.18,
                "predicted_growth_rate_reference": 0.12,
                "predicted_count_reference": 112,
            },
            {
                "horizon": 5,
                "as_of_year": 2024,
                "jurisdiction_code": "EP",
                "wipo_industry_code": segment,
                "local_family_filings_asof": 75,
                "predicted_direction_band": "heating",
                "trend_strength_band": "measured",
                "support_level": "limited",
                "predicted_direction_probability": 0.57,
                "predicted_margin": 0.1,
                "predicted_growth_rate_reference": 0.08,
                "predicted_count_reference": 81,
            },
        ]


def test_market_workspace_contract_includes_runtime_fields():
    service = MarketIntelligenceService(repo=FakeMarketRepo())
    service._serving_release_id = lambda: "test-release"  # type: ignore[method-assign]
    service._reduced_context_mode = lambda: False  # type: ignore[method-assign]

    payload = service.get_workspace(market_state="all", segment="Digital communication")

    assert payload["identity"]["id"] == "market-intelligence"
    assert payload["scope"]["latest_comparable_market_year"] == 2024
    assert payload["meta"]["release_id"] == "test-release"
    assert payload["meta"]["support_level"] == "limited"
    assert payload["selected_segment"]["summary"]["concentration_role"] == "present"
    assert payload["selected_segment"]["summary"]["whitespace_candidate"] is True
    assert payload["selected_segment"]["forecast"][0]["predicted_direction_band"] == "heating"
    assert payload["selected_segment"]["linked_portfolios"][0]["owner_id"] == "ACME_HOLDINGS"
