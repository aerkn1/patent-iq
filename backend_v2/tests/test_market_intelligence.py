import pytest
from fastapi.testclient import TestClient

from api.v1 import market_intelligence as market_api
from application.services.market_intelligence import MarketIntelligenceService
from domain.schemas.common import PaginationMetadata, ResponseMeta
from domain.schemas.market_intelligence import MarketSectionResponse, MarketWorkspaceResponse
from main import app


class FakeMarketRepository:
    def artifacts(self) -> list:
        return []

    def get_scope_summary(self):
        return {
            "covered_field_count": 3,
            "start_year": 2018,
            "end_year": 2023,
            "latest_market_year": 2023,
            "latest_comparable_market_year": 2023,
            "latest_cpc_year": 2023,
            "snapshot_date": "2026-03-15",
        }

    def get_overview_snapshot(self):
        return {
            "segment_count": 3,
            "rising_segment_count": 1,
            "cooling_segment_count": 1,
            "total_family_count": 156000,
            "avg_segment_family_count": 52000.0,
        }

    def get_segments(self, as_of_year: int | None = None):
        return [
            {
                "segment_id": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "market_state": "cooling",
                "total_family_count": 64000,
                "latest_year": 2025,
                "latest_comparable_year": 2023,
                "latest_year_incomplete": True,
                "latest_market_year": 2023,
                "snapshot_date": "2026-03-15",
                "segment_heat_state_asof": None,
                "segment_market_state_ui_safe_asof": False,
                "segment_priority_year_incomplete_asof": True,
                "segment_latest_comparable_year": 2023,
                "segment_family_count_stock_asof": 32000,
                "segment_priority_year_family_count_asof": 18000,
                "segment_prior_priority_year_family_count_asof": 22000,
                "segment_growth_index_asof": -0.18,
                "segment_owner_count_hist_proxy_asof": 220000,
                "segment_blocking_density_asof": 31.5,
                "segment_field_balance_asof": 0.82,
                "segment_active_family_count_asof": 27000,
                "segment_active_weight_asof": 0.81,
                "segment_active_jurisdiction_share_asof": 0.73,
                "segment_enforceability_density_asof": 0.61,
                "segment_top_owner_share_hist_proxy": 0.031,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_oecd_supported": False,
            },
            {
                "segment_id": "Digital communication",
                "wipo_industry_code": "Digital communication",
                "market_state": "rising",
                "total_family_count": 52000,
                "latest_year": 2025,
                "latest_comparable_year": 2023,
                "latest_year_incomplete": True,
                "latest_market_year": 2023,
                "snapshot_date": "2026-03-15",
                "segment_heat_state_asof": None,
                "segment_market_state_ui_safe_asof": False,
                "segment_priority_year_incomplete_asof": True,
                "segment_latest_comparable_year": 2023,
                "segment_family_count_stock_asof": 36000,
                "segment_priority_year_family_count_asof": 21000,
                "segment_prior_priority_year_family_count_asof": 17000,
                "segment_growth_index_asof": 0.24,
                "segment_owner_count_hist_proxy_asof": 128000,
                "segment_blocking_density_asof": 44.5,
                "segment_field_balance_asof": 0.76,
                "segment_active_family_count_asof": 31000,
                "segment_active_weight_asof": 0.88,
                "segment_active_jurisdiction_share_asof": 0.79,
                "segment_enforceability_density_asof": 0.69,
                "segment_top_owner_share_hist_proxy": 0.047,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_oecd_supported": False,
            },
        ]

    def get_market_overview_history(self):
        return [
            {
                "as_of_year": 2023,
                "current_snapshot_date": "2026-03-15",
                "market_family_count_asof": 148000,
                "pending_family_count_asof": 39000,
                "fully_active_family_count_asof": 93000,
                "partially_lapsed_family_count_asof": 4200,
                "dead_family_count_asof": 11800,
                "owner_count_asof": 301000,
                "avg_blocking_power_score_asof": 38.6,
                "avg_enforceability_score_asof": 0.64,
                "avg_forward_citations_clean_asof": 2.8,
                "total_forward_citations_clean_asof": 414400.0,
                "top_owner_share_asof": 0.021,
            },
        ]

    def get_timeseries(self, segment_id: str | None = None):
        rows = [
            {
                "family_priority_year": 2021,
                "wipo_industry_code": "Computer technology",
                "family_count": 26000,
                "prior_family_count": 24000,
                "market_state": "stable",
                "market_state_ui_safe": True,
                "is_recent_priority_year_incomplete": False,
                "latest_comparable_year": 2023,
            },
            {
                "family_priority_year": 2022,
                "wipo_industry_code": "Computer technology",
                "family_count": 24000,
                "prior_family_count": 26000,
                "market_state": "cooling",
                "market_state_ui_safe": True,
                "is_recent_priority_year_incomplete": False,
                "latest_comparable_year": 2023,
            },
            {
                "family_priority_year": 2023,
                "wipo_industry_code": "Computer technology",
                "family_count": 22000,
                "prior_family_count": 24000,
                "market_state": "cooling",
                "market_state_ui_safe": True,
                "is_recent_priority_year_incomplete": False,
                "latest_comparable_year": 2023,
            },
            {
                "family_priority_year": 2024,
                "wipo_industry_code": "Digital communication",
                "family_count": 19000,
                "prior_family_count": 16500,
                "market_state": "rising",
                "market_state_ui_safe": False,
                "is_recent_priority_year_incomplete": True,
                "latest_comparable_year": 2023,
            },
            {
                "family_priority_year": 2025,
                "wipo_industry_code": "Digital communication",
                "family_count": 21000,
                "prior_family_count": 19000,
                "market_state": "rising",
                "market_state_ui_safe": False,
                "is_recent_priority_year_incomplete": True,
                "latest_comparable_year": 2023,
            },
        ]
        if segment_id:
            return [row for row in rows if row["wipo_industry_code"] == segment_id]
        return rows

    def get_segment_owners(self, segment_id: str, as_of_year: int | None = None, limit: int = 20, offset: int = 0):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "leaderboard_rank": 1,
                "owner_name_display_current": "Acme Holdings",
                "owner_name_harmonized": "ACME_HOLDINGS",
                "in_segment_family_count_hist_proxy": 420,
                "in_segment_family_share_hist_proxy": 0.043,
                "avg_blocking_score_asof": 88.4,
                "total_blocking_score_asof": 37128.0,
                "field_presence_weight_asof": 0.92,
                "family_composite_status_asof": "fully_active",
                "total_count": 1,
            }
        ]

    def get_segment_families(self, segment_id: str, as_of_year: int | None = None, limit: int = 20, offset: int = 0):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "leaderboard_rank": 1,
                "docdb_family_id": 43381800,
                "owner_name_harmonized_current": "ACME_HOLDINGS",
                "avg_blocking_score_asof": 99.4,
                "total_blocking_score_asof": 99.4,
                "field_presence_weight_asof": 0.33,
                "family_composite_status_asof": "fully_active",
                "total_count": 1,
            }
        ]

    def get_cpc_trends(self, segment_id: str | None = None, as_of_year: int | None = None, limit: int = 20, offset: int = 0):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "current_snapshot_date": "2026-03-15",
                "wipo_industry_code": segment_id or "Computer technology",
                "cpc_main_group": "G06F17/00",
                "cpc_main_group_label": "G06F17/00",
                "cpc_family_count_asof": 1200,
                "cpc_active_family_count_asof": 880,
                "cpc_family_share_within_segment_asof": 0.082,
                "cpc_active_family_share_within_segment_asof": 0.091,
                "cpc_blocking_density_asof": 57.0,
                "cpc_enforceability_density_asof": 0.71,
                "cpc_pre_asof_forward_citations_clean_avg_asof": 0.52,
                "cpc_avg_rcf_score_asof": 1.83,
                "cpc_prior_family_count_asof": 950,
                "cpc_growth_index_asof": 0.263,
                "cpc_heat_state_asof": "heating",
                "cpc_rank_within_segment_year": 1,
                "total_count": 1,
            }
        ]

    def get_segment_field_jurisdictions(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_field": segment_id,
                "jurisdiction_code": "US",
                "jurisdiction_family_count_asof": 4200,
                "jurisdiction_active_family_count_asof": 3100,
                "jurisdiction_family_share_within_segment_asof": 0.19,
                "jurisdiction_active_family_share_within_segment_asof": 0.22,
                "cpc_group_count": 214,
                "total_count": 1,
            }
        ]

    def get_segment_cpc_jurisdictions(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        cpc_main_group: str | None = None,
        jurisdiction_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "current_snapshot_date": "2026-03-15",
                "wipo_field": segment_id,
                "cpc_main_group": cpc_main_group or "G06F17/00",
                "jurisdiction_code": jurisdiction_code or "US",
                "family_count_asof": 1200,
                "active_family_count_asof": 880,
                "family_share_within_slice_asof": 0.082,
                "citation_pressure_index_asof": 0.54,
                "growth_index_asof": 0.263,
                "blocking_density_asof": 57.0,
                "enforceability_density_asof": 0.71,
                "slice_rank_within_year": 1,
                "total_count": 1,
            }
        ]

    def get_segment_cpc_owners(
        self,
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_field": segment_id,
                "cpc_main_group": cpc_main_group,
                "leaderboard_rank": 1,
                "owner_name_harmonized": "ACME_HOLDINGS",
                "owner_name_display_current": "Acme Holdings",
                "owner_family_count_in_cpc_asof": 182,
                "owner_active_family_count_in_cpc_asof": 144,
                "owner_family_share_within_cpc_asof": 0.143,
                "owner_active_family_share_within_cpc_asof": 0.158,
                "avg_blocking_score_asof": 61.4,
                "avg_enforceability_score_asof": 0.73,
                "total_count": 1,
            }
        ]

    def get_segment_cpc_citing_owners(
        self,
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_field": segment_id,
                "cpc_main_group": cpc_main_group,
                "leaderboard_rank": 1,
                "citing_assignee_name": "QUALCOMM",
                "latest_citation_year": as_of_year or 2023,
                "citation_event_count": 96,
                "clean_citation_count": 94.5,
                "citation_lethality_sum": 88.2,
                "distinct_citing_jurisdiction_count": 4,
                "cited_family_count": 31,
                "citation_event_share_within_cpc_asof": 0.214,
                "total_count": 1,
            }
        ]

    def get_leading_jurisdictions(self, as_of_year: int | None = None, limit_per_field: int = 5):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_field": "Computer technology",
                "field_rank_within_year": 1,
                "jurisdiction_code": "US",
                "jurisdiction_family_count_asof": 5100,
                "jurisdiction_active_family_count_asof": 4100,
                "jurisdiction_family_share_within_field_asof": 0.159,
                "total_count": 1,
            }
        ]

    def get_segment_applications_grants(
        self,
        segment_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 12,
    ):
        return [
            {
                "as_of_year": year_to or 2023,
                "wipo_field": segment_id,
                "jurisdiction_code": "EP",
                "application_count": 420,
                "grant_count": 190,
                "total_event_count": 610,
            }
        ]

    def get_segment_grant_mix(
        self,
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 12,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_field": segment_id,
                "jurisdiction_code": "US",
                "application_count": 560,
                "grant_count": 340,
                "total_event_count": 900,
                "grant_share_of_events": 0.3778,
                "total_count": 1,
            }
        ]

    def get_segment_unitary_patent_summary(
        self,
        segment_id: str,
        jurisdiction_limit: int = 18,
    ):
        return [
            {
                "row_kind": "summary",
                "wipo_field": segment_id,
                "as_of_year": 2023,
                "jurisdiction_code": None,
                "register_confirmed_family_count": 2,
                "heuristic_family_count": 42,
                "unrolled_member_state_count": 18,
                "jurisdiction_family_count": None,
                "ep_grant_event_count": 120,
                "ep_grant_event_count_on_heuristic_up": 18,
            },
            {
                "row_kind": "jurisdiction",
                "wipo_field": segment_id,
                "as_of_year": 2023,
                "jurisdiction_code": "DE",
                "register_confirmed_family_count": None,
                "heuristic_family_count": 42,
                "unrolled_member_state_count": None,
                "jurisdiction_family_count": 42,
                "ep_grant_event_count": None,
                "ep_grant_event_count_on_heuristic_up": None,
            },
        ]

    def get_citation_trends(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_industry_code": segment_id or "Computer technology",
                "citation_event_count": 12,
                "citation_count": 11.5,
                "citation_lethality_sum_raw": 9.2,
                "distinct_citing_assignee_count": 4,
                "distinct_citing_jurisdiction_count": 2,
                "citation_pressure_index": 87.0,
                "market_citation_state": "heating",
                "market_state_reference": "rising",
                "total_count": 1,
            }
        ]

    def get_citation_jurisdictions(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_industry_code": segment_id or "Computer technology",
                "jurisdiction_code": "US",
                "citation_event_count": 8,
                "distinct_citing_assignee_count": 3,
                "citation_count": 8.0,
                "citation_lethality_sum_raw": 5.4,
                "citation_pressure_index": 77.0,
                "total_count": 1,
            }
        ]

    def get_citation_attackers(
        self,
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return [
            {
                "as_of_year": as_of_year or 2023,
                "wipo_industry_code": segment_id or "Computer technology",
                "citing_assignee_name": "QUALCOMM",
                "citation_event_count": 6,
                "distinct_citing_jurisdiction_count": 2,
                "citation_count": 6.0,
                "citation_lethality_sum_raw": 4.8,
                "attacker_pressure_index": 91.0,
                "total_count": 1,
            }
        ]


def test_market_citation_service_maps_rows() -> None:
    service = MarketIntelligenceService(FakeMarketRepository())

    trend = service.get_citation_trends(segment_id="Computer technology", as_of_year=2025, limit=5, offset=0)
    assert trend.rows[0]["wipo_field"] == "Computer technology"
    assert trend.rows[0]["market_citation_state"] == "heating"
    assert trend.meta.page == "market_intelligence.citation_trends"
    assert trend.meta.pagination == PaginationMetadata(limit=5, offset=0, returned_count=1, total_count=1)

    jurisdiction = service.get_citation_jurisdictions(segment_id="Computer technology", as_of_year=2025, limit=5, offset=0)
    assert jurisdiction.rows[0]["jurisdiction_code"] == "US"
    assert jurisdiction.meta.page == "market_intelligence.citation_jurisdictions"

    attacker = service.get_citation_attackers(segment_id="Computer technology", as_of_year=2025, limit=5, offset=0)
    assert attacker.rows[0]["citing_assignee"] == "QUALCOMM"
    assert attacker.meta.page == "market_intelligence.citation_attackers"


def test_market_cpc_service_maps_rows() -> None:
    service = MarketIntelligenceService(FakeMarketRepository())

    cpc_trends = service.get_cpc_trends(segment_id="Computer technology", as_of_year=2022, limit=7, offset=2)
    assert cpc_trends.section_key == "cpc_trends"
    assert cpc_trends.rows[0]["as_of_year"] == 2022
    assert cpc_trends.rows[0]["cpc_main_group"] == "G06F17/00"
    assert cpc_trends.meta.pagination == PaginationMetadata(limit=7, offset=2, returned_count=1, total_count=1)

    cpc_jurisdictions = service.get_segment_cpc_jurisdictions(
        segment_id="Computer technology",
        as_of_year=2022,
        cpc_main_group="G06F3/00",
        jurisdiction_code="EP",
        limit=9,
        offset=1,
    )
    assert cpc_jurisdictions.section_key == "cpc_jurisdictions"
    assert cpc_jurisdictions.rows[0]["cpc_main_group"] == "G06F3/00"
    assert cpc_jurisdictions.rows[0]["jurisdiction_code"] == "EP"
    assert cpc_jurisdictions.meta.pagination == PaginationMetadata(limit=9, offset=1, returned_count=1, total_count=1)

    cpc_owners = service.get_segment_cpc_owners(
        segment_id="Computer technology",
        cpc_main_group="G06F3/00",
        as_of_year=2022,
        limit=8,
        offset=1,
    )
    assert cpc_owners.section_key == "cpc_owners"
    assert cpc_owners.rows[0]["cpc_main_group"] == "G06F3/00"
    assert cpc_owners.rows[0]["owner_name"] == "Acme Holdings"
    assert cpc_owners.meta.pagination == PaginationMetadata(limit=8, offset=1, returned_count=1, total_count=1)

    cpc_citing_owners = service.get_segment_cpc_citing_owners(
        segment_id="Computer technology",
        cpc_main_group="G06F3/00",
        as_of_year=2022,
        limit=6,
        offset=2,
    )
    assert cpc_citing_owners.section_key == "cpc_citing_owners"
    assert cpc_citing_owners.rows[0]["cpc_main_group"] == "G06F3/00"
    assert cpc_citing_owners.rows[0]["citing_owner_name"] == "QUALCOMM"
    assert cpc_citing_owners.rows[0]["citation_event_share_within_cpc_asof"] == 0.214
    assert cpc_citing_owners.meta.pagination == PaginationMetadata(limit=6, offset=2, returned_count=1, total_count=1)


def test_market_grants_and_jurisdictions_service_maps_rows() -> None:
    service = MarketIntelligenceService(FakeMarketRepository())

    leading = service.get_leading_jurisdictions(as_of_year=2023, limit_per_field=5)
    assert leading.section_key == "leading_jurisdictions"
    assert leading.metric_basis == "Unique DOCDB families"
    assert leading.rows[0]["field_rank_within_year"] == 1
    assert leading.rows[0]["jurisdiction_family_share_within_field_asof"] == 0.159

    applications_grants = service.get_segment_applications_grants(
        segment_id="Computer technology",
        year_from=2020,
        year_to=2023,
        jurisdiction_limit=12,
    )
    assert applications_grants.section_key == "applications_grants"
    assert applications_grants.scope_basis == "Selected field using primary-field family replay"
    assert applications_grants.rows[0]["application_count"] == 420

    grant_mix = service.get_segment_grant_mix(
        segment_id="Computer technology",
        as_of_year=2023,
        limit=6,
        offset=1,
    )
    assert grant_mix.section_key == "grant_mix"
    assert grant_mix.rows[0]["grant_share_of_events"] == 0.3778
    assert grant_mix.meta.pagination == PaginationMetadata(limit=6, offset=1, returned_count=1, total_count=1)

    unitary = service.get_segment_unitary_patent_summary(segment_id="Computer technology", jurisdiction_limit=10)
    assert unitary.section_key == "unitary_patent"
    assert unitary.rows[0]["row_kind"] == "summary"
    assert unitary.rows[0]["ep_grant_event_count"] == 120
    assert unitary.rows[0]["ep_grant_event_count_on_heuristic_up"] == 18
    assert unitary.rows[1]["jurisdiction_code"] == "DE"


def test_market_workspace_service_maps_rows() -> None:
    service = MarketIntelligenceService(FakeMarketRepository())

    workspace = service.get_workspace(market_state="all", segment_id="Digital communication", as_of_year=2025)

    assert workspace.identity.page_kind == "market_intelligence"
    assert workspace.overview["segment_count"] == 3
    assert workspace.scope["scope_type"] == "mega_cluster_bounded"
    assert workspace.scope["latest_market_year"] == 2023
    assert workspace.scope["latest_comparable_market_year"] == 2023
    assert workspace.identity.selected_year == 2023
    assert workspace.overview.get("latest_market_summary") is None
    assert workspace.overview.get("market_overview_history") is None
    assert workspace.filters["selected_segment"] == "Digital communication"
    assert workspace.segments[0]["wipo_industry_code"] == "Computer technology"
    assert workspace.selected_segment is not None
    assert workspace.selected_segment["summary"]["segment_heat_state_asof"] == "provisional"
    assert workspace.selected_segment["summary"]["crowding_label"] == "concentrated"
    assert workspace.selected_segment["top_owners"][0]["owner_name"] == "Acme Holdings"
    assert workspace.selected_segment["top_owners"][0]["as_of_year"] == 2023
    assert workspace.selected_segment["top_families"][0]["docdb_family_id"] == 43381800
    assert workspace.selected_segment["top_families"][0]["owner_name"] == "ACME HOLDINGS"
    assert workspace.selected_segment["field_jurisdictions"][0]["jurisdiction_code"] == "US"
    assert workspace.selected_segment["top_cpcs"][0]["cpc_main_group"] == "G06F17/00"
    assert workspace.selected_segment["cpc_jurisdictions"][0]["cpc_main_group"] == "G06F17/00"
    assert workspace.meta.page == "market_intelligence.workspace"


def test_market_overview_history_service_maps_rows() -> None:
    service = MarketIntelligenceService(FakeMarketRepository())

    history = service.get_market_overview_history()

    assert history.meta.page == "market_intelligence.market_overview_history"
    assert history.rows[-1]["as_of_year"] == 2023
    assert history.rows[-1]["crowding_label"] == "balanced"


def test_market_citation_routes_forward_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls = {
        "trend": {"segment_id": None, "as_of_year": None, "limit": None, "offset": None},
        "jurisdiction": {"segment_id": None, "as_of_year": None, "limit": None, "offset": None},
        "attacker": {"segment_id": None, "as_of_year": None, "limit": None, "offset": None},
    }

    def fake_trends(
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["trend"] = {"segment_id": segment_id, "as_of_year": as_of_year, "limit": limit, "offset": offset}
        return MarketSectionResponse(
            segment_id=segment_id,
            rows=[{"wipo_field": segment_id or "Computer technology"}],
            meta=ResponseMeta(
                page="market_intelligence.citation_trends",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_jurisdictions(
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["jurisdiction"] = {"segment_id": segment_id, "as_of_year": as_of_year, "limit": limit, "offset": offset}
        return MarketSectionResponse(
            segment_id=segment_id,
            rows=[{"jurisdiction_code": "US"}],
            meta=ResponseMeta(
                page="market_intelligence.citation_jurisdictions",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_attackers(
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["attacker"] = {"segment_id": segment_id, "as_of_year": as_of_year, "limit": limit, "offset": offset}
        return MarketSectionResponse(
            segment_id=segment_id,
            rows=[{"citing_assignee": "QUALCOMM"}],
            meta=ResponseMeta(
                page="market_intelligence.citation_attackers",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    monkeypatch.setattr(market_api.service, "get_citation_trends", fake_trends)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_citation_jurisdictions", fake_jurisdictions)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_citation_attackers", fake_attackers)  # type: ignore[method-assign]

    response = client.get("/api/v1/market-intelligence/citation-trends?segment_id=Computer%20technology&as_of_year=2025&limit=5&offset=10")
    assert response.status_code == 200
    assert calls["trend"] == {"segment_id": "Computer technology", "as_of_year": 2025, "limit": 5, "offset": 10}

    response = client.get("/api/v1/market-intelligence/citation-jurisdictions?segment_id=Computer%20technology&as_of_year=2025&limit=7&offset=1")
    assert response.status_code == 200
    assert calls["jurisdiction"] == {"segment_id": "Computer technology", "as_of_year": 2025, "limit": 7, "offset": 1}

    response = client.get("/api/v1/market-intelligence/citation-attackers?segment_id=Computer%20technology&as_of_year=2025&limit=9&offset=2")
    assert response.status_code == 200
    assert calls["attacker"] == {"segment_id": "Computer technology", "as_of_year": 2025, "limit": 9, "offset": 2}


def test_market_cpc_routes_forward_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls = {
        "trends": {"segment_id": None, "as_of_year": None, "limit": None, "offset": None},
        "jurisdictions": {
            "segment_id": None,
            "as_of_year": None,
            "cpc_main_group": None,
            "jurisdiction_code": None,
            "limit": None,
            "offset": None,
        },
        "owners": {
            "segment_id": None,
            "cpc_main_group": None,
            "as_of_year": None,
            "limit": None,
            "offset": None,
        },
        "citing_owners": {
            "segment_id": None,
            "cpc_main_group": None,
            "as_of_year": None,
            "limit": None,
            "offset": None,
        },
    }

    def fake_trends(
        segment_id: str | None = None,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["trends"] = {"segment_id": segment_id, "as_of_year": as_of_year, "limit": limit, "offset": offset}
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="cpc_trends",
            rows=[{"cpc_main_group": "G06F17/00"}],
            meta=ResponseMeta(page="market_intelligence.cpc_trends", artifact_sources=[]),
        )

    def fake_jurisdictions(
        segment_id: str,
        as_of_year: int | None = None,
        cpc_main_group: str | None = None,
        jurisdiction_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["jurisdictions"] = {
            "segment_id": segment_id,
            "as_of_year": as_of_year,
            "cpc_main_group": cpc_main_group,
            "jurisdiction_code": jurisdiction_code,
            "limit": limit,
            "offset": offset,
        }
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="cpc_jurisdictions",
            rows=[{"cpc_main_group": cpc_main_group or "G06F17/00", "jurisdiction_code": jurisdiction_code or "US"}],
            meta=ResponseMeta(page="market_intelligence.segment_cpc_jurisdictions", artifact_sources=[]),
        )

    def fake_owners(
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["owners"] = {
            "segment_id": segment_id,
            "cpc_main_group": cpc_main_group,
            "as_of_year": as_of_year,
            "limit": limit,
            "offset": offset,
        }
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="cpc_owners",
            rows=[{"cpc_main_group": cpc_main_group, "owner_name": "Acme Holdings"}],
            meta=ResponseMeta(page="market_intelligence.segment_cpc_owners", artifact_sources=[]),
        )

    def fake_citing_owners(
        segment_id: str,
        cpc_main_group: str,
        as_of_year: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["citing_owners"] = {
            "segment_id": segment_id,
            "cpc_main_group": cpc_main_group,
            "as_of_year": as_of_year,
            "limit": limit,
            "offset": offset,
        }
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="cpc_citing_owners",
            rows=[{"cpc_main_group": cpc_main_group, "citing_owner_name": "Qualcomm"}],
            meta=ResponseMeta(page="market_intelligence.segment_cpc_citing_owners", artifact_sources=[]),
        )

    monkeypatch.setattr(market_api.service, "get_cpc_trends", fake_trends)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_segment_cpc_jurisdictions", fake_jurisdictions)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_segment_cpc_owners", fake_owners)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_segment_cpc_citing_owners", fake_citing_owners)  # type: ignore[method-assign]

    response = client.get("/api/v1/market-intelligence/cpc-trends?segment_id=Computer%20technology&as_of_year=2022&limit=7&offset=2")
    assert response.status_code == 200
    assert calls["trends"] == {"segment_id": "Computer technology", "as_of_year": 2022, "limit": 7, "offset": 2}

    response = client.get(
        "/api/v1/market-intelligence/segments/Computer%20technology/cpc-jurisdictions"
        "?as_of_year=2022&cpc_main_group=G06F3%2F00&jurisdiction_code=EP&limit=9&offset=1"
    )
    assert response.status_code == 200
    assert calls["jurisdictions"] == {
        "segment_id": "Computer technology",
        "as_of_year": 2022,
        "cpc_main_group": "G06F3/00",
        "jurisdiction_code": "EP",
        "limit": 9,
        "offset": 1,
    }

    response = client.get(
        "/api/v1/market-intelligence/segments/Computer%20technology/cpc-owners"
        "?cpc_main_group=G06F3%2F00&as_of_year=2022&limit=8&offset=1"
    )
    assert response.status_code == 200
    assert calls["owners"] == {
        "segment_id": "Computer technology",
        "cpc_main_group": "G06F3/00",
        "as_of_year": 2022,
        "limit": 8,
        "offset": 1,
    }

    response = client.get(
        "/api/v1/market-intelligence/segments/Computer%20technology/cpc-citing-owners"
        "?cpc_main_group=G06F3%2F00&as_of_year=2022&limit=6&offset=2"
    )
    assert response.status_code == 200
    assert calls["citing_owners"] == {
        "segment_id": "Computer technology",
        "cpc_main_group": "G06F3/00",
        "as_of_year": 2022,
        "limit": 6,
        "offset": 2,
    }


def test_market_grant_routes_forward_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls = {
        "leading": {"as_of_year": None, "limit_per_field": None},
        "applications_grants": {"segment_id": None, "year_from": None, "year_to": None, "jurisdiction_limit": None},
        "grant_mix": {"segment_id": None, "as_of_year": None, "limit": None, "offset": None},
        "unitary": {"segment_id": None, "jurisdiction_limit": None},
    }

    def fake_leading(as_of_year: int | None = None, limit_per_field: int = 5) -> MarketSectionResponse:
        calls["leading"] = {"as_of_year": as_of_year, "limit_per_field": limit_per_field}
        return MarketSectionResponse(
            section_key="leading_jurisdictions",
            rows=[{"wipo_field": "Computer technology", "jurisdiction_code": "US"}],
            meta=ResponseMeta(page="market_intelligence.leading_jurisdictions", artifact_sources=[]),
        )

    def fake_applications_grants(
        segment_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 12,
    ) -> MarketSectionResponse:
        calls["applications_grants"] = {
            "segment_id": segment_id,
            "year_from": year_from,
            "year_to": year_to,
            "jurisdiction_limit": jurisdiction_limit,
        }
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="applications_grants",
            rows=[{"jurisdiction_code": "EP", "application_count": 420}],
            meta=ResponseMeta(page="market_intelligence.segment_applications_grants", artifact_sources=[]),
        )

    def fake_grant_mix(
        segment_id: str,
        as_of_year: int | None = None,
        limit: int = 12,
        offset: int = 0,
    ) -> MarketSectionResponse:
        calls["grant_mix"] = {
            "segment_id": segment_id,
            "as_of_year": as_of_year,
            "limit": limit,
            "offset": offset,
        }
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="grant_mix",
            rows=[{"jurisdiction_code": "US", "grant_count": 340}],
            meta=ResponseMeta(page="market_intelligence.segment_grant_mix", artifact_sources=[]),
        )

    def fake_unitary(segment_id: str, jurisdiction_limit: int = 18) -> MarketSectionResponse:
        calls["unitary"] = {"segment_id": segment_id, "jurisdiction_limit": jurisdiction_limit}
        return MarketSectionResponse(
            segment_id=segment_id,
            section_key="unitary_patent",
            rows=[{"row_kind": "summary", "heuristic_family_count": 42}],
            meta=ResponseMeta(page="market_intelligence.segment_unitary_patent", artifact_sources=[]),
        )

    monkeypatch.setattr(market_api.service, "get_leading_jurisdictions", fake_leading)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_segment_applications_grants", fake_applications_grants)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_segment_grant_mix", fake_grant_mix)  # type: ignore[method-assign]
    monkeypatch.setattr(market_api.service, "get_segment_unitary_patent_summary", fake_unitary)  # type: ignore[method-assign]

    response = client.get("/api/v1/market-intelligence/leading-jurisdictions?as_of_year=2023&limit_per_field=4")
    assert response.status_code == 200
    assert calls["leading"] == {"as_of_year": 2023, "limit_per_field": 4}

    response = client.get(
        "/api/v1/market-intelligence/segments/Computer%20technology/applications-grants?year_from=2020&year_to=2023&jurisdiction_limit=8"
    )
    assert response.status_code == 200
    assert calls["applications_grants"] == {
        "segment_id": "Computer technology",
        "year_from": 2020,
        "year_to": 2023,
        "jurisdiction_limit": 8,
    }

    response = client.get("/api/v1/market-intelligence/segments/Computer%20technology/grant-mix?as_of_year=2023&limit=6&offset=2")
    assert response.status_code == 200
    assert calls["grant_mix"] == {"segment_id": "Computer technology", "as_of_year": 2023, "limit": 6, "offset": 2}

    response = client.get("/api/v1/market-intelligence/segments/Computer%20technology/unitary-patent?jurisdiction_limit=10")
    assert response.status_code == 200
    assert calls["unitary"] == {"segment_id": "Computer technology", "jurisdiction_limit": 10}


def test_market_workspace_route_forwards_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls = {"market_state": None, "segment_id": None, "as_of_year": None}

    def fake_workspace(
        market_state: str = "all",
        segment_id: str | None = None,
        as_of_year: int | None = None,
    ) -> MarketWorkspaceResponse:
        calls["market_state"] = market_state
        calls["segment_id"] = segment_id
        calls["as_of_year"] = as_of_year
        return MarketWorkspaceResponse(
            identity={"id": "market-intelligence", "label": "Market Intelligence", "page_kind": "market_intelligence"},
            scope={"scope_type": "mega_cluster_bounded"},
            overview={"segment_count": 3},
            filters={"market_state": market_state, "selected_segment": segment_id},
            segments=[],
            selected_segment=None,
            methodology=[],
            meta=ResponseMeta(page="market_intelligence.workspace", artifact_sources=[]),
        )

    monkeypatch.setattr(market_api.service, "get_workspace", fake_workspace)  # type: ignore[method-assign]

    response = client.get("/api/v1/market-intelligence/workspace?market_state=cooling&segment_id=Computer%20technology&as_of_year=2025")
    assert response.status_code == 200
    assert calls == {"market_state": "cooling", "segment_id": "Computer technology", "as_of_year": 2025}


def test_market_overview_history_route(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)

    def fake_history() -> MarketSectionResponse:
        return MarketSectionResponse(
            segment_id=None,
            rows=[{"as_of_year": 2023, "market_family_count_asof": 148000}],
            meta=ResponseMeta(page="market_intelligence.market_overview_history", artifact_sources=[]),
        )

    monkeypatch.setattr(market_api.service, "get_market_overview_history", fake_history)  # type: ignore[method-assign]

    response = client.get("/api/v1/market-intelligence/overview-history")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"][0]["as_of_year"] == 2023
