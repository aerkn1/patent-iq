from datetime import date

import pytest

from application.services.portfolios import PortfolioService
from domain.schemas.portfolio import (
    PortfolioThreatResponse,
    PortfolioClassificationResponse,
    PortfolioOwnerSearchResponse,
    PortfolioSectionResponse,
)


class FakePortfolioRepository:
    def __init__(self) -> None:
        self.threat_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
        }
        self.classification_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "as_of_year": None,
            "timeseries_fields": None,
            "limit": None,
            "offset": None,
            "classification_type": None,
            "wipo_field": None,
        }
        self.contributor_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "horizon": None,
            "contributor_scope": None,
            "limit": None,
            "offset": None,
        }
        self.compare_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "base_year": None,
            "compare_year": None,
        }
        self.citation_summary_calls: dict[str, int | str | None] = {"owner_id": None, "as_of_year": None}
        self.citation_timeseries_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "year_from": None,
            "year_to": None,
        }
        self.citation_family_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "status": None,
            "sort": None,
        }
        self.citation_attacker_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "jurisdiction_code": None,
            "year_from": None,
            "year_to": None,
        }
        self.citation_field_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "jurisdiction_code": None,
            "year_from": None,
            "year_to": None,
        }
        self.citation_jurisdiction_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "year_from": None,
            "year_to": None,
        }
        self.citation_cpc_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "jurisdiction_code": None,
            "year_from": None,
            "year_to": None,
        }
        self.filing_timeseries_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "year_from": None,
            "year_to": None,
        }
        self.pending_grants_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "horizon": None,
            "branch_jurisdiction_code": None,
            "branch_wipo_field": None,
            "branch_limit": None,
        }
        self.status_timeseries_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "year_from": None,
            "year_to": None,
        }
        self.jurisdiction_unlock_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "year_from": None,
            "year_to": None,
            "jurisdiction_limit": None,
        }
        self.family_calls: dict[str, int | str | None] = {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "q": None,
            "status": None,
            "primary_field": None,
            "sort": None,
        }

    def artifacts(self) -> list:
        return []

    def get_owner_summary(self, owner_id: str, as_of_year: int | None = None):
        return {
            "owner_name_harmonized": "ACME_LTD",
            "owner_name_display": "Acme Ltd",
            "snapshot_date": "2026-03-15",
            "portfolio_family_count_within_mega_cluster": 12,
            "portfolio_active_grant_family_count": 7,
            "semantic_candidate_family_count": 10,
            "portfolio_avg_blocking_power_within_mega_cluster": 54.3,
            "portfolio_heritage_score": 2270.41,
            "portfolio_total_mass_score": 685.4,
            "portfolio_hit_rate_top_decile": 0.22,
            "portfolio_crown_jewel_index": 2.8,
            "portfolio_current_threat_score": 14.0,
        }

    def get_owner_summary_peer_context(self, owner_id: str, as_of_year: int | None = None):
        return {
            "peer_bucket": "6_20",
            "peer_bucket_size": 351660,
            "portfolio_total_mass_score_percentile": 81.0,
            "portfolio_current_threat_score_percentile": 62.0,
            "portfolio_heritage_score_percentile": 58.0,
        }

    def get_owner_forecast_summary(self, owner_id: str, as_of_year: int | None = None):
        return {
            "portfolio_prediction_coverage_status": "high",
            "phase03_family_coverage_pct": 0.82,
            "phase03_family_covered_count": 9,
            "phase03_family_denominator_count": 11,
            "portfolio_phase04_family_coverage_pct": 0.71,
            "portfolio_phase06_family_coverage_pct": 0.77,
            "coverage_caveat_text": "Coverage is good for modeled families only.",
        }

    def get_owner_family_status_counts(self, owner_id: str):
        return {
            "family_count": 9,
            "pending_family_count": 3,
            "active_family_count": 4,
            "under_fire_family_count": 1,
            "partially_lapsed_family_count": 0,
            "dead_family_count": 0,
            "abandoned_family_count": 0,
        }

    def get_owner_in_scope_family_status_counts(self, owner_id: str):
        return {
            "family_count": 12,
            "pending_family_count": 5,
            "active_family_count": 4,
            "under_fire_family_count": 1,
            "partially_lapsed_family_count": 1,
            "dead_family_count": 1,
        }

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
        self.family_calls["owner_id"] = owner_id
        self.family_calls["limit"] = limit
        self.family_calls["offset"] = offset
        self.family_calls["q"] = q
        self.family_calls["status"] = status
        self.family_calls["primary_field"] = primary_field
        self.family_calls["sort"] = sort
        return [
            {
                "family_id": "12345",
                "owner_weight": 0.22,
                "blocking_score": 81.4,
                "status": "fully_active",
                "heritage": "2019",
                "priority_year": "2019",
                "primary_field": "Computer technology",
                "forecast_contributor": 3.1,
            }
        ]

    def get_owner_threats(self, owner_id: str, limit: int = 10, offset: int = 0, wipo_field: str | None = None):
        self.threat_calls["owner_id"] = owner_id
        self.threat_calls["limit"] = limit
        self.threat_calls["offset"] = offset
        self.threat_calls["wipo_field"] = wipo_field
        return [
            {
                "citing_assignee_name": "Acme Labs",
                "wipo_field": "Semiconductors",
                "citation_lethality_sum": 0.27,
                "collided_family_count": 3,
                "total_count": 2,
            },
            {
                "citing_assignee_name": None,
                "wipo_field": None,
                "citation_lethality_sum": None,
                "collided_family_count": "12",
                "total_count": 2,
            },
        ]

    def get_owner_classification(
        self,
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        classification_type: str = "CPC_MAIN_GROUP",
        wipo_field: str | None = None,
    ):
        self.classification_calls["owner_id"] = owner_id
        self.classification_calls["as_of_year"] = as_of_year
        self.classification_calls["limit"] = limit
        self.classification_calls["offset"] = offset
        self.classification_calls["classification_type"] = classification_type
        self.classification_calls["wipo_field"] = wipo_field
        return [
            {
                "segment": "H01L",
                "classification_label": "Semiconductors",
                "classification_type": "WIPO_FIELD",
                "classification_rank_within_owner_year": 1,
                "family_share": 0.21,
                "trajectory": 0.08,
                "total_count": 2,
            },
            {
                "segment": "G06F",
                "classification_label": wipo_field or "Computing",
                "classification_type": "CPC_MAIN_GROUP",
                "wipo_field": wipo_field,
                "family_share": 0.12,
                "trajectory": -0.04,
                "total_count": 2,
            },
        ]

    def get_owner_classification_timeseries(self, owner_id: str, as_of_year: int | None = None, limit_fields: int = 6):
        self.classification_calls["owner_id"] = owner_id
        self.classification_calls["as_of_year"] = as_of_year
        self.classification_calls["timeseries_fields"] = limit_fields
        return [
            {"wipo_field": "H01L", "year": 2024, "share": 0.21, "portfolio": 0.24},
            {"wipo_field": "H01L", "year": 2025, "share": 0.19, "portfolio": 0.2},
            {"wipo_field": None, "year": 2025, "share": 0.07, "portfolio": 0.09},
        ]

    def get_owner_field_timeseries(self, owner_id: str, as_of_year: int | None = None, limit_fields: int = 8):
        return [
            {
                "snapshot_date": "2026-03-15",
                "wipo_field": "Computer technology",
                "active_family_count": 25,
                "active_share": 0.41,
                "enforceability_score": 7.2,
                "heritage_score": 91.5,
            }
        ]

    def get_owner_forecast_contributors(
        self,
        owner_id: str,
        horizon: str = "3y",
        contributor_scope: str = "phase03_future_citations",
        limit: int = 10,
        offset: int = 0,
        current_state_only: bool = False,
    ):
        self.contributor_calls["owner_id"] = owner_id
        self.contributor_calls["horizon"] = horizon
        self.contributor_calls["contributor_scope"] = contributor_scope
        self.contributor_calls["limit"] = limit
        self.contributor_calls["offset"] = offset
        self.contributor_calls["current_state_only"] = current_state_only
        return [
            {
                "contributor_scope": contributor_scope,
                "horizon": horizon,
                "contributor_entity_id": "12345",
                "jurisdiction_code": "US",
                "contribution_value": 18.4,
                "contribution_share": 0.21,
                "contributor_rank": 1,
                "status": "fully_active",
                "total_count": 1,
            }
        ]

    def get_owner_market_context(self, owner_id: str, horizon: str = "3y", as_of_year: int | None = None):
        return (
            {
                f"portfolio_heating_market_exposure_count_{horizon}": 12.0,
                f"portfolio_cooling_market_exposure_count_{horizon}": 3.0,
                f"portfolio_hotspot_coverage_pct_{horizon}": 0.84,
            },
            [
                {
                    "horizon": horizon,
                    "wipo_field": "Computer technology",
                    "predicted_direction_band": "heating",
                    "support_level": "moderate",
                    "predicted_growth_rate_reference": 0.11,
                    "predicted_count_reference": 42.0,
                    "portfolio_active_family_count_in_field": 25,
                }
            ],
        )

    def get_owner_forecast_sections(self, owner_id: str, as_of_year: int | None = None):
        return [
            {
                "horizon": "3y",
                "wipo_field": "Computer technology",
                "predicted_direction_band": "heating",
                "support_level": "moderate",
                "predicted_growth_rate_reference": 0.11,
                "portfolio_active_family_count_in_field": 25,
            }
        ]

    def get_owner_risk_distribution(self, owner_id: str, horizon: str = "12m", as_of_year: int | None = None):
        return [{"risk_band": "low", "family_count": 9, "share": 1.0}]

    def get_owner_compare_timeslice(
        self,
        owner_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ):
        self.compare_calls["owner_id"] = owner_id
        self.compare_calls["base_year"] = base_year
        self.compare_calls["compare_year"] = compare_year
        return [
            {
                "as_of_year": 2026,
                "portfolio_avg_blocking_power_score_asof": 61.0,
                "portfolio_legal_durability_index_asof": 0.72,
                "portfolio_field_breadth_asof": 8.0,
                "portfolio_field_concentration_hhi_asof": 0.18,
                "portfolio_data_completeness_pct_asof": 0.91,
            },
            {
                "as_of_year": 2024,
                "portfolio_avg_blocking_power_score_asof": 58.0,
                "portfolio_legal_durability_index_asof": 0.64,
                "portfolio_field_breadth_asof": 7.0,
                "portfolio_field_concentration_hhi_asof": 0.22,
                "portfolio_data_completeness_pct_asof": 0.86,
            },
        ]

    def get_owner_pending_grant_sections(
        self,
        owner_id: str,
        horizon: str = "24m",
        branch_jurisdiction_code: str | None = None,
        branch_wipo_field: str | None = None,
        branch_limit: int = 25,
    ):
        self.pending_grants_calls["owner_id"] = owner_id
        self.pending_grants_calls["horizon"] = horizon
        self.pending_grants_calls["branch_jurisdiction_code"] = branch_jurisdiction_code
        self.pending_grants_calls["branch_wipo_field"] = branch_wipo_field
        self.pending_grants_calls["branch_limit"] = branch_limit
        return {
            "serving_ready": True,
            "metrics": {"roc_auc": 0.61, "pr_auc": 0.32},
            "summary": {
                "pending_pipeline_branch_count": 6,
                "pending_pipeline_family_count": 4,
                "current_pending_branch_count": 8,
                "current_pending_family_count": 5,
                "pending_pipeline_avg_probability_12m": 0.18,
                "pending_pipeline_avg_probability_24m": 0.34,
                "pending_pipeline_expected_likely_grants_12m": 1.1,
                "pending_pipeline_expected_likely_grants_24m": 2.0,
                "pending_pipeline_percentile": 84.0,
                "pending_pipeline_support_level": "moderate",
                "pending_pipeline_top_jurisdiction": "EP",
                "pending_pipeline_top_field": "Computer technology",
                "top_branch_family_id": "12345",
                "top_branch_jurisdiction": "EP",
                "top_branch_field": "Computer technology",
                "top_branch_probability": 0.67,
                "top_branch_percentile": 97.0,
            },
            "jurisdictions": [
                {
                    "jurisdiction_code": "EP",
                    "office_support_level": "moderate",
                    "branch_count": 3,
                    "family_count": 2,
                    "avg_probability_12m": 0.21,
                    "avg_probability_24m": 0.42,
                    "expected_likely_grants_12m": 0.63,
                    "expected_likely_grants_24m": 1.26,
                    "avg_percentile": 88.0,
                }
            ],
            "fields": [
                {
                    "primary_wipo_field": "Computer technology",
                    "branch_count": 4,
                    "family_count": 3,
                    "avg_probability_12m": 0.19,
                    "avg_probability_24m": 0.36,
                    "expected_likely_grants_12m": 0.77,
                    "expected_likely_grants_24m": 1.44,
                    "avg_percentile": 82.0,
                }
            ],
            "branches": [
                {
                    "docdb_family_id": "12345",
                    "jurisdiction_code": "EP",
                    "primary_wipo_field": "Computer technology",
                    "pending_age_years": 2.1,
                    "family_age_years": 4.0,
                    "family_blocking_power_score_asof": 72.0,
                    "family_enforceability_score_asof": 0.61,
                    "family_rcf_score_asof": 0.28,
                    "data_completeness_pct_asof": 0.93,
                    "probability_12m": 0.29,
                    "probability_24m": 0.67,
                    "selected_probability": 0.67,
                    "rank_within_office_horizon": 1,
                    "percentile_within_office_horizon": 97.0,
                    "office_support_level": "moderate",
                    "priority_tier": "top",
                }
            ],
            "reason": "Pending-grant is served from owner-scoped current pending branch scoring and should remain rank/percentile-first in the UI.",
        }

    def get_owner_citation_summary(self, owner_id: str, as_of_year: int | None = None):
        self.citation_summary_calls["owner_id"] = owner_id
        self.citation_summary_calls["as_of_year"] = as_of_year
        return {
            "as_of_year": 2026,
            "family_count": 12,
            "forward_citations_clean_total": 144.0,
            "forward_citations_weighted_total": 183.5,
            "backward_citations_clean_total": 76.0,
            "backward_npl_citation_total": 14.0,
            "distinct_citing_family_count": 31,
            "distinct_cited_family_count": 54,
            "avg_science_grounding_score": 0.41,
            "avg_generality_percentile": 0.66,
            "avg_originality_percentile": 0.59,
            "avg_unique_citing_family_count": 5.4,
            "avg_citing_assignee_diversity": 0.72,
            "avg_attacker_density_score": 0.27,
            "avg_out_of_bounds_citation_share": 0.08,
        }

    def get_owner_citation_timeseries(self, owner_id: str, year_from: int | None = None, year_to: int | None = None):
        self.citation_timeseries_calls["owner_id"] = owner_id
        self.citation_timeseries_calls["year_from"] = year_from
        self.citation_timeseries_calls["year_to"] = year_to
        return [
            {
                "as_of_year": 2024,
                "family_count": 11,
                "forward_citations_clean_total": 102.0,
                "forward_citations_weighted_total": 128.0,
                "avg_unique_citing_family_count": 4.2,
                "avg_citing_assignee_diversity": 0.61,
                "avg_attacker_density_score": 0.19,
            },
            {
                "as_of_year": 2025,
                "family_count": 12,
                "forward_citations_clean_total": 121.0,
                "forward_citations_weighted_total": 157.0,
                "avg_unique_citing_family_count": 4.9,
                "avg_citing_assignee_diversity": 0.67,
                "avg_attacker_density_score": 0.24,
            },
        ]

    def get_owner_citation_attackers(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ):
        self.citation_attacker_calls["owner_id"] = owner_id
        self.citation_attacker_calls["limit"] = limit
        self.citation_attacker_calls["offset"] = offset
        self.citation_attacker_calls["wipo_field"] = wipo_field
        self.citation_attacker_calls["jurisdiction_code"] = jurisdiction_code
        self.citation_attacker_calls["year_from"] = year_from
        self.citation_attacker_calls["year_to"] = year_to
        return [
            {
                "citing_assignee_name": "Alpha Labs",
                "wipo_field": "Computer technology",
                "jurisdiction_code": "US",
                "latest_citation_year": 2025,
                "citation_event_count": 8,
                "clean_citation_count": 8.0,
                "citation_lethality_sum": 2.6,
                "total_count": 1,
            }
        ]

    def get_owner_citation_families(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ):
        self.citation_family_calls["owner_id"] = owner_id
        self.citation_family_calls["limit"] = limit
        self.citation_family_calls["offset"] = offset
        self.citation_family_calls["wipo_field"] = wipo_field
        self.citation_family_calls["status"] = status
        self.citation_family_calls["sort"] = sort
        return [
            {
                "family_id": "12345",
                "family_priority_year": 2018,
                "primary_field": "Computer technology",
                "status": "fully_active",
                "forward_citations_clean": 82.0,
                "forward_citations_weighted": 94.6,
                "early_citations_5y": 31.0,
                "early_citations_7y": 44.0,
                "unique_citing_family_count": 18.0,
                "citing_assignee_diversity": 0.74,
                "blocking_score": 72.4,
                "total_count": 1,
            }
        ]

    def get_owner_citation_fields(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ):
        self.citation_field_calls["owner_id"] = owner_id
        self.citation_field_calls["limit"] = limit
        self.citation_field_calls["offset"] = offset
        self.citation_field_calls["jurisdiction_code"] = jurisdiction_code
        self.citation_field_calls["year_from"] = year_from
        self.citation_field_calls["year_to"] = year_to
        return [
            {
                "wipo_field": "Computer technology",
                "latest_citation_year": 2025,
                "citation_event_count": 14,
                "citing_assignee_count": 6,
                "clean_citation_count": 13.0,
                "citation_lethality_sum": 4.8,
                "total_count": 1,
            }
        ]

    def get_owner_filing_timeseries(self, owner_id: str, year_from: int | None = None, year_to: int | None = None):
        self.filing_timeseries_calls["owner_id"] = owner_id
        self.filing_timeseries_calls["year_from"] = year_from
        self.filing_timeseries_calls["year_to"] = year_to
        return [
            {
                "filing_year": 2022,
                "family_filing_count": 6,
                "cumulative_family_count": 18,
                "rolling_3y_family_filing_count": 14,
                "prior_3y_family_filing_count": 11,
                "rolling_3y_change_pct": 0.27,
                "momentum_direction": "accelerating",
            },
            {
                "filing_year": 2023,
                "family_filing_count": 7,
                "cumulative_family_count": 25,
                "rolling_3y_family_filing_count": 17,
                "prior_3y_family_filing_count": 12,
                "rolling_3y_change_pct": 0.42,
                "momentum_direction": "accelerating",
            },
            {
                "filing_year": 2025,
                "family_filing_count": 2,
                "cumulative_family_count": 27,
                "rolling_3y_family_filing_count": 9,
                "prior_3y_family_filing_count": 18,
                "rolling_3y_change_pct": -0.5,
                "momentum_direction": "cooling",
            },
        ]

    def get_owner_status_timeseries(self, owner_id: str, year_from: int | None = None, year_to: int | None = None):
        self.status_timeseries_calls["owner_id"] = owner_id
        self.status_timeseries_calls["year_from"] = year_from
        self.status_timeseries_calls["year_to"] = year_to
        return [
            {
                "as_of_year": 2024,
                "current_snapshot_date": "2026-03-15",
                "family_count": 12,
                "pending_family_count": 3,
                "fully_active_family_count": 6,
                "under_fire_family_count": 1,
                "partially_lapsed_family_count": 1,
                "dead_family_count": 1,
                "status_coverage_pct": 1.0,
                "owner_identity_coverage_pct": 0.98,
                "historical_owner_truth_supported_pct": 0.0,
                "current_owner_metadata_only_pct": 1.0,
                "avg_data_completeness_pct_asof": 0.91,
            },
            {
                "as_of_year": 2025,
                "current_snapshot_date": "2026-03-15",
                "family_count": 12,
                "pending_family_count": 2,
                "fully_active_family_count": 7,
                "under_fire_family_count": 1,
                "partially_lapsed_family_count": 1,
                "dead_family_count": 1,
                "status_coverage_pct": 1.0,
                "owner_identity_coverage_pct": 0.98,
                "historical_owner_truth_supported_pct": 0.0,
                "current_owner_metadata_only_pct": 1.0,
                "avg_data_completeness_pct_asof": 0.93,
            },
        ]

    def get_owner_jurisdiction_unlock_history(
        self,
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 20,
    ):
        self.jurisdiction_unlock_calls["owner_id"] = owner_id
        self.jurisdiction_unlock_calls["year_from"] = year_from
        self.jurisdiction_unlock_calls["year_to"] = year_to
        self.jurisdiction_unlock_calls["jurisdiction_limit"] = jurisdiction_limit
        return {
            "summary": {
                "unlocked_jurisdiction_count": 3,
                "first_unlock_year": 2020,
                "latest_unlock_year": 2024,
                "latest_presence_year": 2025,
                "latest_active_jurisdiction_count": 3,
                "latest_pending_jurisdiction_count": 1,
                "latest_lapsed_jurisdiction_count": 1,
                "ever_active_jurisdiction_count": 3,
                "active_family_observations": 7,
                "pending_family_observations": 2,
                "lapsed_family_observations": 1,
            },
            "years": [
                {
                    "as_of_year": 2020,
                    "unlocked_jurisdiction_count": 1,
                    "cumulative_unlocked_jurisdiction_count": 1,
                    "active_unlock_count": 0,
                    "pending_unlock_count": 1,
                    "lapsed_only_unlock_count": 0,
                    "active_jurisdiction_count": 0,
                    "pending_jurisdiction_count": 1,
                    "lapsed_jurisdiction_count": 0,
                    "unlocked_jurisdictions": ["EP"],
                },
                {
                    "as_of_year": 2021,
                    "unlocked_jurisdiction_count": 0,
                    "cumulative_unlocked_jurisdiction_count": 1,
                    "active_unlock_count": 0,
                    "pending_unlock_count": 0,
                    "lapsed_only_unlock_count": 0,
                    "active_jurisdiction_count": 1,
                    "pending_jurisdiction_count": 0,
                    "lapsed_jurisdiction_count": 0,
                    "unlocked_jurisdictions": [],
                },
                {
                    "as_of_year": 2024,
                    "unlocked_jurisdiction_count": 2,
                    "cumulative_unlocked_jurisdiction_count": 3,
                    "active_unlock_count": 1,
                    "pending_unlock_count": 1,
                    "lapsed_only_unlock_count": 0,
                    "active_jurisdiction_count": 3,
                    "pending_jurisdiction_count": 1,
                    "lapsed_jurisdiction_count": 1,
                    "unlocked_jurisdictions": ["CN", "US"],
                },
                {
                    "as_of_year": 2025,
                    "unlocked_jurisdiction_count": 0,
                    "cumulative_unlocked_jurisdiction_count": 3,
                    "active_unlock_count": 0,
                    "pending_unlock_count": 0,
                    "lapsed_only_unlock_count": 0,
                    "active_jurisdiction_count": 3,
                    "pending_jurisdiction_count": 1,
                    "lapsed_jurisdiction_count": 1,
                    "unlocked_jurisdictions": [],
                },
            ],
            "jurisdictions": [
                {
                    "jurisdiction_code": "EP",
                    "first_unlock_year": 2020,
                    "first_unlock_basis": "pending",
                    "first_active_year": 2021,
                    "first_pending_year": 2020,
                    "first_lapsed_year": 0,
                    "tracked_family_count": 2,
                    "active_family_count": 2,
                    "pending_family_count": 1,
                    "lapsed_family_count": 0,
                },
                {
                    "jurisdiction_code": "US",
                    "first_unlock_year": 2024,
                    "first_unlock_basis": "active",
                    "first_active_year": 2024,
                    "first_pending_year": 0,
                    "first_lapsed_year": 0,
                    "tracked_family_count": 3,
                    "active_family_count": 3,
                    "pending_family_count": 0,
                    "lapsed_family_count": 0,
                },
            ],
        }

    def get_owner_citation_jurisdictions(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ):
        self.citation_jurisdiction_calls["owner_id"] = owner_id
        self.citation_jurisdiction_calls["limit"] = limit
        self.citation_jurisdiction_calls["offset"] = offset
        self.citation_jurisdiction_calls["wipo_field"] = wipo_field
        self.citation_jurisdiction_calls["year_from"] = year_from
        self.citation_jurisdiction_calls["year_to"] = year_to
        return [
            {
                "jurisdiction_code": "US",
                "latest_citation_year": 2025,
                "citation_event_count": 19,
                "citing_assignee_count": 7,
                "wipo_field_count": 4,
                "clean_citation_count": 18.0,
                "citation_lethality_sum": 5.4,
                "total_count": 1,
            }
        ]

    def get_owner_citation_cpc_groups(
        self,
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ):
        self.citation_cpc_calls["owner_id"] = owner_id
        self.citation_cpc_calls["limit"] = limit
        self.citation_cpc_calls["offset"] = offset
        self.citation_cpc_calls["wipo_field"] = wipo_field
        self.citation_cpc_calls["jurisdiction_code"] = jurisdiction_code
        self.citation_cpc_calls["year_from"] = year_from
        self.citation_cpc_calls["year_to"] = year_to
        return [
            {
                "cpc_main_group": "H04L1/00",
                "latest_citation_year": 2025,
                "citation_event_count": 16,
                "clean_citation_count": 16.0,
                "citation_lethality_sum": 4.1,
                "cited_family_count": 3,
                "total_count": 1,
            }
        ]

    def search_owners(self, query: str, limit: int = 8):
        self.search_calls = {"query": query, "limit": limit}
        return [
            {
                "owner_name_harmonized": "UNKNOWN_OWNER",
                "owner_name_display": "Unknown Owner",
                "family_count": 999,
            },
            {
                "owner_name_harmonized": "ACME_INDUSTRIES_HOLDINGS",
                "owner_name_display": "Acme Industries Holdings",
                "family_count": 428,
            },
            {
                "owner_name_harmonized": "ACME_LABS",
                "owner_name_display": "Acme Labs",
                "family_count": 112,
            },
        ]


def test_get_threats_maps_rows_with_defaults_and_forwards_limit():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.get_threats("Acme%20Ltd", limit=7)

    assert isinstance(response, PortfolioThreatResponse)
    assert response.owner_id == "Acme%20Ltd"
    assert len(response.rows) == 2
    assert response.rows[0]["citing_assignee"] == "Acme Labs"
    assert response.rows[0]["wipo_field"] == "Semiconductors"
    assert response.rows[0]["citation_lethality"] == 0.27
    assert response.rows[0]["collided_family_count"] == 3
    assert response.rows[1]["citing_assignee"] == ""
    assert response.rows[1]["wipo_field"] == ""
    assert response.rows[1]["citation_lethality"] == 0.0
    assert response.rows[1]["collided_family_count"] == 12
    assert response.meta.page == "portfolio.threats"
    assert response.meta.pagination.limit == 7
    assert response.meta.pagination.total_count == 2
    assert repository.threat_calls["owner_id"] == "Acme%20Ltd"
    assert repository.threat_calls["limit"] == 7


def test_get_classification_maps_wipo_and_cpc_rows_and_timeseries():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.get_classification("Acme Ltd", as_of_year=2025, timeseries_fields=4)

    assert isinstance(response, PortfolioClassificationResponse)
    assert response.owner_id == "Acme Ltd"
    assert len(response.rows) == 2
    assert response.rows[0].segment == "H01L"
    assert response.rows[0].wipo_field == "Semiconductors"
    assert response.rows[0].top_change == "gain"
    assert response.rows[0].classification_type == "WIPO_FIELD"
    assert response.rows[1].segment == "G06F"
    assert response.rows[1].top_change == "loss"
    assert response.rows[1].wipo_field == "Computing"
    assert len(response.timeseries) == 1
    assert response.timeseries[0].field == "H01L"
    assert len(response.timeseries[0].points) == 2
    assert response.timeseries[0].points[0].year == 2024
    assert response.timeseries[0].points[1].share == 0.19
    assert response.meta.page == "portfolio.classification"
    assert response.meta.caveats[0].code == "classification_visibility"
    assert response.meta.pagination.limit == 10
    assert response.meta.pagination.total_count == 2
    assert repository.classification_calls["as_of_year"] == 2025
    assert repository.classification_calls["timeseries_fields"] == 4


def test_get_classification_forwards_selected_wipo_field_for_cpc_mix():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.get_classification(
        "Acme Ltd",
        as_of_year=2025,
        classification_type="CPC_MAIN_GROUP",
        wipo_field="Computer technology",
    )

    assert isinstance(response, PortfolioClassificationResponse)
    assert response.rows[1].classification_type == "CPC_MAIN_GROUP"
    assert response.rows[1].wipo_field == "Computer technology"
    assert repository.classification_calls["wipo_field"] == "Computer technology"


def test_get_classification_skips_timeseries_when_disabled():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.get_classification("Acme Ltd", as_of_year=2025, timeseries_fields=0)

    assert isinstance(response, PortfolioClassificationResponse)
    assert response.rows[0].segment == "H01L"
    assert response.timeseries == []
    assert repository.classification_calls["owner_id"] == "Acme Ltd"
    assert repository.classification_calls["as_of_year"] == 2025
    assert repository.classification_calls["timeseries_fields"] is None


def test_search_owners_returns_harmonized_owner_rows():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.search_owners("acme", limit=5)

    assert isinstance(response, PortfolioOwnerSearchResponse)
    assert response.query == "acme"
    assert len(response.rows) == 2
    assert all(row.owner_id != "UNKNOWN_OWNER" for row in response.rows)
    assert response.rows[0].owner_id == "ACME_INDUSTRIES_HOLDINGS"
    assert response.rows[0].label == "Acme Industries Holdings"
    assert response.rows[0].family_count == 428
    assert response.meta.page == "portfolio.search"
    assert repository.search_calls["query"] == "acme"
    assert repository.search_calls["limit"] == 5


def test_get_overview_includes_family_status_ratio_cards_and_tooltips():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.get_overview("Acme Ltd")

    cards_by_key = {card.key: card for card in response.summary_cards}
    assert response.family_count == 12
    assert response.count_scopes is not None
    assert response.count_scopes.in_scope_family_count == 12
    assert response.count_scopes.primary_owner_family_count == 9
    assert response.count_scopes.active_grant_family_count == 7
    assert response.count_scopes.semantic_candidate_family_count == 10
    assert response.count_scopes.pending_family_count == 5
    assert response.count_scopes.unclassified_family_count == 0
    assert response.active_grant_family_count == 7
    assert cards_by_key["portfolio_primary_owner_family_count"].value == "9"
    assert cards_by_key["semantic_candidate_family_count"].value == "10 (83.3%)"
    assert [slice.key for slice in response.status_mix] == ["pending_emerging", "fully_active", "under_fire", "partially_lapsed", "dead"]
    assert [slice.count for slice in response.status_mix] == [5, 4, 1, 1, 1]
    assert [round(slice.share, 3) for slice in response.status_mix] == [0.417, 0.333, 0.083, 0.083, 0.083]
    assert cards_by_key["portfolio_primary_owner_family_count"].tooltip is not None
    assert cards_by_key["portfolio_total_mass_score"].caveat == "Peer-relative percentile"
    assert cards_by_key["portfolio_total_mass_score"].band_code == "very_high"
    assert cards_by_key["portfolio_total_mass_score"].band_label == "Outsize Footprint"
    assert cards_by_key["portfolio_total_mass_score"].peer_bucket == "6_20"
    assert cards_by_key["portfolio_total_mass_score"].peer_bucket_label == "6-20 families"
    assert cards_by_key["portfolio_total_mass_score"].peer_percentile == 81.0
    assert cards_by_key["portfolio_current_threat_score"].band_label == "High Pressure"
    assert cards_by_key["portfolio_heritage_score"].band_label == "Deep Heritage"
    assert "Current band: Outsize Footprint" in (cards_by_key["portfolio_total_mass_score"].tooltip or "")
    assert "executive_metric_audit" in [c.code for c in response.meta.caveats]
    assert "count_scope_split" in [c.code for c in response.meta.caveats]
    assert "peer_relative_bands" in [c.code for c in response.meta.caveats]
    assert response.meta.coverage is not None
    assert response.meta.coverage.pct == 0.82
    assert response.meta.coverage.covered_count == 9
    assert response.meta.coverage.denominator_count == 11


def test_get_forecast_maps_phase03_family_coverage_pct() -> None:
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    response = service.get_forecast("Acme Ltd", horizon="3y")

    assert response.coverage is not None
    assert response.coverage.pct == 0.82
    assert response.coverage.covered_count == 9
    assert response.coverage.denominator_count == 11
    assert response.meta.support_level == "strong"


def test_section_endpoints_map_field_timeseries_contributors_market_compare_and_pending_grants():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    field_timeseries = service.get_field_timeseries("Acme Ltd", limit_fields=4)
    assert isinstance(field_timeseries, PortfolioSectionResponse)
    assert field_timeseries.rows[0]["wipo_field"] == "Computer technology"
    assert field_timeseries.meta.page == "portfolio.field_timeseries"

    contributors = service.get_forecast_contributors(
        "Acme Ltd",
        horizon="5y",
        contributor_scope="phase04_lapse_risk",
        limit=5,
        offset=5,
    )
    assert contributors.rows[0]["contributor_entity_id"] == "12345"
    assert contributors.meta.pagination.limit == 5
    assert contributors.meta.pagination.offset == 5
    assert repository.contributor_calls["horizon"] == "5y"
    assert repository.contributor_calls["contributor_scope"] == "phase04_lapse_risk"

    market_context = service.get_market_context("Acme Ltd", horizon="3y")
    assert market_context.rows[0]["kind"] == "summary"
    assert market_context.rows[1]["predicted_direction_band"] == "heating"
    assert market_context.meta.page == "portfolio.market_context"

    compare = service.get_compare_timeslice("Acme Ltd", base_year=2026, compare_year=2024)
    assert compare.rows[0]["metric"] == "blocking_strength"
    assert compare.rows[0]["current_year"] == 2026
    assert compare.rows[0]["compare_year"] == 2024
    assert compare.meta.page == "portfolio.compare_timeslice"

    pending = service.get_pending_grants(
        "Acme Ltd",
        horizon="24m",
        branch_jurisdiction_code="EP",
        branch_wipo_field="Computer technology",
        branch_limit=25,
    )
    assert pending.rows[0]["kind"] == "summary"
    assert pending.rows[0]["feature_status"] == "candidate_only"
    assert pending.rows[0]["pending_pipeline_family_count"] == 4
    assert pending.rows[0]["current_pending_family_count"] == 5
    assert pending.rows[0]["pending_pipeline_family_coverage_pct"] == pytest.approx(0.8)
    assert pending.rows[0]["pending_pipeline_branch_coverage_pct"] == pytest.approx(0.75)
    assert pending.rows[0]["pending_pipeline_priority_tier"] == "high"
    assert pending.rows[1]["kind"] == "jurisdiction"
    assert pending.rows[2]["kind"] == "field"
    assert pending.rows[3]["kind"] == "branch"
    assert pending.rows[3]["priority_tier"] == "top"
    assert pending.meta.support_level == "moderate"
    assert repository.pending_grants_calls["branch_jurisdiction_code"] == "EP"
    assert repository.pending_grants_calls["branch_wipo_field"] == "Computer technology"
    assert repository.pending_grants_calls["branch_limit"] == 25


def test_citation_section_endpoints_map_summary_timeseries_and_attackers():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    summary = service.get_citation_summary("Acme Ltd", as_of_year=2026)
    assert isinstance(summary, PortfolioSectionResponse)
    assert summary.rows[0]["forward_citations_clean_total"] == 144.0
    assert summary.rows[0]["distinct_citing_family_count"] == 31
    assert summary.rows[0]["distinct_cited_family_count"] == 54
    assert summary.rows[0]["avg_originality_percentile"] == 0.59
    assert summary.meta.page == "portfolio.citation_summary"
    assert repository.citation_summary_calls["as_of_year"] == 2026

    timeseries = service.get_citation_timeseries("Acme Ltd", year_from=2024, year_to=2025)
    assert timeseries.rows[0]["as_of_year"] == 2024
    assert timeseries.rows[1]["forward_citations_weighted_total"] == 157.0
    assert timeseries.meta.page == "portfolio.citation_timeseries"
    assert repository.citation_timeseries_calls["year_from"] == 2024
    assert repository.citation_timeseries_calls["year_to"] == 2025

    citation_families = service.get_citation_families(
        "Acme Ltd",
        limit=5,
        offset=5,
        wipo_field="Computer technology",
        status="fully_active",
        sort="forward_clean",
    )
    assert citation_families.rows[0]["family_id"] == "12345"
    assert citation_families.rows[0]["early_citations_5y"] == 31.0
    assert citation_families.rows[0]["blocking_score"] == 72.4
    assert citation_families.meta.page == "portfolio.citation_families"
    assert citation_families.meta.pagination.limit == 5
    assert repository.citation_family_calls["offset"] == 5
    assert repository.citation_family_calls["wipo_field"] == "Computer technology"
    assert repository.citation_family_calls["status"] == "fully_active"

    attackers = service.get_citation_attackers(
        "Acme Ltd",
        limit=5,
        offset=5,
        wipo_field="Computer technology",
        jurisdiction_code="US",
        year_from=2020,
        year_to=2025,
    )
    assert attackers.rows[0]["citing_assignee"] == "Alpha Labs"
    assert attackers.rows[0]["citation_lethality_sum"] == 2.6
    assert attackers.meta.page == "portfolio.citation_attackers"
    assert attackers.meta.pagination.limit == 5
    assert repository.citation_attacker_calls["offset"] == 5
    assert repository.citation_attacker_calls["wipo_field"] == "Computer technology"

    fields = service.get_citation_fields("Acme Ltd", limit=5, offset=0, jurisdiction_code="US")
    assert fields.rows[0]["wipo_field"] == "Computer technology"
    assert fields.rows[0]["citing_assignee_count"] == 6
    assert fields.meta.page == "portfolio.citation_fields"
    assert repository.citation_field_calls["jurisdiction_code"] == "US"

    jurisdictions = service.get_citation_jurisdictions(
        "Acme Ltd",
        limit=5,
        offset=0,
        wipo_field="Computer technology",
    )
    assert jurisdictions.rows[0]["jurisdiction_code"] == "US"
    assert jurisdictions.rows[0]["wipo_field_count"] == 4
    assert jurisdictions.meta.page == "portfolio.citation_jurisdictions"
    assert repository.citation_jurisdiction_calls["wipo_field"] == "Computer technology"

    cpc_groups = service.get_citation_cpc_groups(
        "Acme Ltd",
        limit=5,
        offset=5,
        wipo_field="Computer technology",
        jurisdiction_code="US",
        year_from=2020,
        year_to=2025,
    )
    assert cpc_groups.rows[0]["cpc_main_group"] == "H04L1/00"
    assert cpc_groups.rows[0]["citation_event_count"] == 16
    assert cpc_groups.rows[0]["cited_family_count"] == 3
    assert cpc_groups.meta.page == "portfolio.citation_cpc_groups"
    assert cpc_groups.meta.pagination.limit == 5
    assert repository.citation_cpc_calls["offset"] == 5
    assert repository.citation_cpc_calls["wipo_field"] == "Computer technology"
    assert repository.citation_cpc_calls["jurisdiction_code"] == "US"
    assert repository.citation_cpc_calls["year_from"] == 2020
    assert repository.citation_cpc_calls["year_to"] == 2025

    families = service.get_families(
        "Acme Ltd",
        limit=5,
        offset=10,
        q="123",
        status="fully_active",
        primary_field="Computer technology",
        sort="priority_year",
    )
    assert families.rows[0]["priority_year"] == "2019"
    assert families.rows[0]["primary_field"] == "Computer technology"
    assert repository.family_calls["sort"] == "priority_year"
    assert repository.family_calls["q"] == "123"
    assert repository.family_calls["status"] == "fully_active"
    assert repository.family_calls["primary_field"] == "Computer technology"

    filing_timeseries = service.get_filing_timeseries("Acme Ltd", year_from=2022, year_to=2023)
    assert filing_timeseries.rows[0]["year"] == 2022
    assert filing_timeseries.rows[1]["family_filing_count"] == 7
    assert filing_timeseries.rows[1]["momentum_direction"] == "accelerating"
    assert filing_timeseries.meta.page == "portfolio.filing_timeseries"
    assert repository.filing_timeseries_calls["year_from"] == 2022
    assert repository.filing_timeseries_calls["year_to"] == 2023


def test_get_filing_timeseries_caps_latest_incomplete_year():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    filing_timeseries = service.get_filing_timeseries("Acme Ltd")

    assert [row["year"] for row in filing_timeseries.rows] == [2022, 2023]
    assert repository.filing_timeseries_calls["year_to"] == date.today().year - 2


def test_get_status_timeseries_maps_counts_shares_and_audit_meta():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    status_timeseries = service.get_status_timeseries("Acme Ltd", year_from=2024, year_to=2025)

    assert [row["as_of_year"] for row in status_timeseries.rows] == [2024, 2025]
    assert status_timeseries.rows[0]["fully_active_share"] == pytest.approx(0.5)
    assert status_timeseries.rows[1]["dead_family_count"] == 1
    assert status_timeseries.meta.page == "portfolio.status_timeseries"
    assert status_timeseries.meta.coverage is not None
    assert status_timeseries.meta.coverage.status == "high"
    assert status_timeseries.meta.coverage.covered_count == 2
    assert status_timeseries.meta.support_level.value == "moderate"
    assert repository.status_timeseries_calls["year_from"] == 2024
    assert repository.status_timeseries_calls["year_to"] == 2025


def test_get_jurisdiction_unlock_history_maps_summary_year_and_jurisdiction_rows():
    repository = FakePortfolioRepository()
    service = PortfolioService(repository=repository)

    unlock_history = service.get_jurisdiction_unlock_history(
        "Acme Ltd",
        year_from=2020,
        year_to=2025,
        jurisdiction_limit=10,
    )

    assert unlock_history.meta.page == "portfolio.jurisdiction_unlock_history"
    assert unlock_history.meta.coverage is not None
    assert unlock_history.meta.coverage.status == "high"
    assert unlock_history.meta.support_level.value == "moderate"
    assert unlock_history.rows[0]["kind"] == "summary"
    assert unlock_history.rows[0]["unlocked_jurisdiction_count"] == 3
    assert unlock_history.rows[1]["kind"] == "year"
    assert unlock_history.rows[1]["unlocked_jurisdictions"] == ["EP"]
    assert unlock_history.rows[2]["kind"] == "year"
    assert unlock_history.rows[2]["as_of_year"] == 2021
    assert unlock_history.rows[2]["unlocked_jurisdiction_count"] == 0
    assert unlock_history.rows[-1]["kind"] == "jurisdiction"
    assert unlock_history.rows[-1]["jurisdiction_code"] == "US"
    assert repository.jurisdiction_unlock_calls["jurisdiction_limit"] == 10
