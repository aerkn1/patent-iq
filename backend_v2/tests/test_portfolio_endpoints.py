import pytest
from fastapi.testclient import TestClient

from main import app
from api.v1 import portfolios as portfolio_api
from domain.schemas.portfolio import (
    PortfolioThreatResponse,
    PortfolioClassificationResponse,
    PortfolioOwnerSearchResponse,
    PortfolioOwnerSearchResult,
    PortfolioClassificationTimeseries,
    PortfolioClassificationTimeseriesPoint,
    PortfolioClassificationRow,
    PortfolioSectionResponse,
)
from domain.schemas.common import ResponseMeta
from domain.schemas.common import PaginationMetadata


def test_portfolio_threat_and_classification_routes_return_expected_shapes(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    threat_calls = {"owner_id": None, "limit": None, "offset": None, "wipo_field": None}
    classification_calls = {
        "owner_id": None,
        "as_of_year": None,
        "limit": None,
        "offset": None,
        "classification_type": None,
        "timeseries_fields": None,
        "wipo_field": None,
    }

    def fake_get_threats(
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
    ) -> PortfolioThreatResponse:
        threat_calls["owner_id"] = owner_id
        threat_calls["limit"] = limit
        threat_calls["offset"] = offset
        threat_calls["wipo_field"] = wipo_field
        return PortfolioThreatResponse(
            owner_id=owner_id,
            rows=[
                {
                    "citing_assignee": "Alpha Labs",
                    "wipo_field": "Semiconductors",
                    "citation_lethality": 0.27,
                    "collided_family_count": 3,
                }
            ],
            meta=ResponseMeta(
                page="portfolio.threats",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_get_classification(
        owner_id: str,
        as_of_year: int | None = None,
        limit: int = 10,
        offset: int = 0,
        classification_type: str = "CPC_MAIN_GROUP",
        timeseries_fields: int = 6,
        wipo_field: str | None = None,
    ) -> PortfolioClassificationResponse:
        classification_calls["owner_id"] = owner_id
        classification_calls["as_of_year"] = as_of_year
        classification_calls["limit"] = limit
        classification_calls["offset"] = offset
        classification_calls["classification_type"] = classification_type
        classification_calls["timeseries_fields"] = timeseries_fields
        classification_calls["wipo_field"] = wipo_field
        return PortfolioClassificationResponse(
            owner_id=owner_id,
            rows=[
                PortfolioClassificationRow(
                    segment="H01L",
                    classification_type="WIPO_FIELD",
                    wipo_field="Semiconductors",
                    family_share=0.42,
                    trajectory=0.08,
                    top_change="gain",
                )
            ],
            timeseries=[
                PortfolioClassificationTimeseries(
                    field="Semiconductors",
                    points=[
                        PortfolioClassificationTimeseriesPoint(
                            year=2024,
                            share=0.36,
                            portfolio=0.34,
                        ),
                    ],
                )
            ],
            meta=ResponseMeta(
                page="portfolio.classification",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    monkeypatch.setattr(portfolio_api.service, "get_threats", fake_get_threats)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_classification", fake_get_classification)  # type: ignore[method-assign]

    threats_response = client.get("/api/v1/portfolios/Acme%20Ltd/threats?limit=7")
    assert threats_response.status_code == 200
    threat_payload = threats_response.json()
    assert threat_payload["owner_id"] == "Acme Ltd"
    assert threat_payload["rows"][0]["citing_assignee"] == "Alpha Labs"
    assert threat_calls["owner_id"] == "Acme Ltd"
    assert threat_calls["limit"] == 7
    assert threat_calls["offset"] == 0

    classification_response = client.get(
        "/api/v1/portfolios/Acme%20Ltd/classification?as_of_year=2025&limit=10&offset=0&classification_type=WIPO_FIELD&timeseries_fields=0&wipo_field=Semiconductors"
    )
    assert classification_response.status_code == 200
    classification_payload = classification_response.json()
    assert classification_payload["owner_id"] == "Acme Ltd"
    assert classification_payload["rows"][0]["segment"] == "H01L"
    assert classification_payload["timeseries"][0]["field"] == "Semiconductors"
    assert classification_calls["owner_id"] == "Acme Ltd"
    assert classification_calls["as_of_year"] == 2025
    assert classification_calls["classification_type"] == "WIPO_FIELD"
    assert classification_calls["timeseries_fields"] == 0
    assert classification_calls["wipo_field"] == "Semiconductors"


def test_portfolio_search_route_returns_owner_suggestions(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    search_calls = {"query": None, "limit": None}

    def fake_search_owners(query: str, limit: int = 8) -> PortfolioOwnerSearchResponse:
        search_calls["query"] = query
        search_calls["limit"] = limit
        return PortfolioOwnerSearchResponse(
            query=query,
            rows=[
                PortfolioOwnerSearchResult(
                    owner_id="ACME_INDUSTRIES_HOLDINGS",
                    label="Acme Industries Holdings",
                    family_count=428,
                )
            ],
            meta=ResponseMeta(page="portfolio.search", artifact_sources=[]),
        )

    monkeypatch.setattr(portfolio_api.service, "search_owners", fake_search_owners)  # type: ignore[method-assign]

    response = client.get("/api/v1/portfolios/search?query=acme&limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "acme"
    assert payload["rows"][0]["owner_id"] == "ACME_INDUSTRIES_HOLDINGS"
    assert payload["rows"][0]["label"] == "Acme Industries Holdings"
    assert payload["rows"][0]["family_count"] == 428
    assert search_calls["query"] == "acme"
    assert search_calls["limit"] == 5


def test_portfolio_new_section_routes_forward_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls: dict[str, dict[str, object | None]] = {
        "field_timeseries": {"owner_id": None, "as_of_year": None, "limit_fields": None},
        "citation_summary": {"owner_id": None, "as_of_year": None},
        "citation_timeseries": {"owner_id": None, "year_from": None, "year_to": None},
        "citation_families": {"owner_id": None, "limit": None, "offset": None, "wipo_field": None, "status": None, "sort": None},
        "citation_attackers": {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "jurisdiction_code": None,
            "year_from": None,
            "year_to": None,
        },
        "citation_fields": {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "jurisdiction_code": None,
            "year_from": None,
            "year_to": None,
        },
        "citation_jurisdictions": {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "year_from": None,
            "year_to": None,
        },
        "citation_cpc_groups": {
            "owner_id": None,
            "limit": None,
            "offset": None,
            "wipo_field": None,
            "jurisdiction_code": None,
            "year_from": None,
            "year_to": None,
        },
        "filing_timeseries": {"owner_id": None, "year_from": None, "year_to": None},
        "status_timeseries": {"owner_id": None, "year_from": None, "year_to": None},
        "jurisdiction_unlocks": {
            "owner_id": None,
            "year_from": None,
            "year_to": None,
            "jurisdiction_limit": None,
        },
        "market_context": {"owner_id": None, "horizon": None, "as_of_year": None},
        "forecast_contributors": {"owner_id": None, "horizon": None, "contributor_scope": None, "limit": None, "offset": None},
        "compare_timeslice": {"owner_id": None, "base_year": None, "compare_year": None},
        "pending_grants": {
            "owner_id": None,
            "horizon": None,
            "branch_jurisdiction_code": None,
            "branch_wipo_field": None,
            "branch_limit": None,
        },
    }

    def fake_field_timeseries(owner_id: str, as_of_year: int | None = None, limit_fields: int = 8) -> PortfolioSectionResponse:
        calls["field_timeseries"] = {"owner_id": owner_id, "as_of_year": as_of_year, "limit_fields": limit_fields}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"wipo_field": "Computer technology"}],
            meta=ResponseMeta(page="portfolio.field_timeseries", artifact_sources=[]),
        )

    def fake_market_context(owner_id: str, horizon: str = "3y", as_of_year: int | None = None) -> PortfolioSectionResponse:
        calls["market_context"] = {"owner_id": owner_id, "horizon": horizon, "as_of_year": as_of_year}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"kind": "summary", "horizon": horizon}],
            meta=ResponseMeta(page="portfolio.market_context", artifact_sources=[]),
        )

    def fake_citation_summary(owner_id: str, as_of_year: int | None = None) -> PortfolioSectionResponse:
        calls["citation_summary"] = {"owner_id": owner_id, "as_of_year": as_of_year}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {
                    "family_count": 12,
                    "forward_citations_clean_total": 144.0,
                    "distinct_citing_family_count": 31,
                    "distinct_cited_family_count": 54,
                }
            ],
            meta=ResponseMeta(page="portfolio.citation_summary", artifact_sources=[]),
        )

    def fake_citation_timeseries(
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["citation_timeseries"] = {"owner_id": owner_id, "year_from": year_from, "year_to": year_to}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"as_of_year": 2024, "forward_citations_clean_total": 100.0}],
            meta=ResponseMeta(page="portfolio.citation_timeseries", artifact_sources=[]),
        )

    def fake_citation_families(
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ) -> PortfolioSectionResponse:
        calls["citation_families"] = {
            "owner_id": owner_id,
            "limit": limit,
            "offset": offset,
            "wipo_field": wipo_field,
            "status": status,
            "sort": sort,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"family_id": "12345", "forward_citations_clean": 82.0}],
            meta=ResponseMeta(
                page="portfolio.citation_families",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_citation_attackers(
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["citation_attackers"] = {
            "owner_id": owner_id,
            "limit": limit,
            "offset": offset,
            "wipo_field": wipo_field,
            "jurisdiction_code": jurisdiction_code,
            "year_from": year_from,
            "year_to": year_to,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"citing_assignee": "Alpha Labs"}],
            meta=ResponseMeta(
                page="portfolio.citation_attackers",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_filing_timeseries(
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["filing_timeseries"] = {"owner_id": owner_id, "year_from": year_from, "year_to": year_to}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"year": 2023, "family_filing_count": 7, "momentum_direction": "accelerating"}],
            meta=ResponseMeta(page="portfolio.filing_timeseries", artifact_sources=[]),
        )

    def fake_status_timeseries(
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["status_timeseries"] = {"owner_id": owner_id, "year_from": year_from, "year_to": year_to}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"as_of_year": 2024, "fully_active_family_count": 9, "dead_family_count": 2}],
            meta=ResponseMeta(page="portfolio.status_timeseries", artifact_sources=[]),
        )

    def fake_jurisdiction_unlocks(
        owner_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        jurisdiction_limit: int = 20,
    ) -> PortfolioSectionResponse:
        calls["jurisdiction_unlocks"] = {
            "owner_id": owner_id,
            "year_from": year_from,
            "year_to": year_to,
            "jurisdiction_limit": jurisdiction_limit,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[
                {"kind": "summary", "unlocked_jurisdiction_count": 4},
                {"kind": "year", "as_of_year": 2024, "unlocked_jurisdiction_count": 2},
            ],
            meta=ResponseMeta(page="portfolio.jurisdiction_unlock_history", artifact_sources=[]),
        )

    def fake_citation_fields(
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["citation_fields"] = {
            "owner_id": owner_id,
            "limit": limit,
            "offset": offset,
            "jurisdiction_code": jurisdiction_code,
            "year_from": year_from,
            "year_to": year_to,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"wipo_field": "Computer technology"}],
            meta=ResponseMeta(
                page="portfolio.citation_fields",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_citation_jurisdictions(
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["citation_jurisdictions"] = {
            "owner_id": owner_id,
            "limit": limit,
            "offset": offset,
            "wipo_field": wipo_field,
            "year_from": year_from,
            "year_to": year_to,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"jurisdiction_code": "US"}],
            meta=ResponseMeta(
                page="portfolio.citation_jurisdictions",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_citation_cpc_groups(
        owner_id: str,
        limit: int = 10,
        offset: int = 0,
        wipo_field: str | None = None,
        jurisdiction_code: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> PortfolioSectionResponse:
        calls["citation_cpc_groups"] = {
            "owner_id": owner_id,
            "limit": limit,
            "offset": offset,
            "wipo_field": wipo_field,
            "jurisdiction_code": jurisdiction_code,
            "year_from": year_from,
            "year_to": year_to,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"cpc_main_group": "H04L1/00"}],
            meta=ResponseMeta(
                page="portfolio.citation_cpc_groups",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_forecast_contributors(
        owner_id: str,
        horizon: str = "3y",
        contributor_scope: str = "phase03_future_citations",
        limit: int = 10,
        offset: int = 0,
    ) -> PortfolioSectionResponse:
        calls["forecast_contributors"] = {
            "owner_id": owner_id,
            "horizon": horizon,
            "contributor_scope": contributor_scope,
            "limit": limit,
            "offset": offset,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"contributor_entity_id": "12345"}],
            meta=ResponseMeta(
                page="portfolio.forecast_contributors",
                artifact_sources=[],
                pagination=PaginationMetadata(limit=limit, offset=offset, returned_count=1, total_count=1),
            ),
        )

    def fake_compare(owner_id: str, base_year: int | None = None, compare_year: int | None = None) -> PortfolioSectionResponse:
        calls["compare_timeslice"] = {"owner_id": owner_id, "base_year": base_year, "compare_year": compare_year}
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"metric": "blocking_strength"}],
            meta=ResponseMeta(page="portfolio.compare_timeslice", artifact_sources=[]),
        )

    def fake_pending(
        owner_id: str,
        horizon: str = "24m",
        branch_jurisdiction_code: str | None = None,
        branch_wipo_field: str | None = None,
        branch_limit: int = 25,
    ) -> PortfolioSectionResponse:
        calls["pending_grants"] = {
            "owner_id": owner_id,
            "horizon": horizon,
            "branch_jurisdiction_code": branch_jurisdiction_code,
            "branch_wipo_field": branch_wipo_field,
            "branch_limit": branch_limit,
        }
        return PortfolioSectionResponse(
            owner_id=owner_id,
            rows=[{"feature_status": "candidate_only"}],
            meta=ResponseMeta(page="portfolio.pending_grants", artifact_sources=[]),
        )

    monkeypatch.setattr(portfolio_api.service, "get_field_timeseries", fake_field_timeseries)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_summary", fake_citation_summary)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_timeseries", fake_citation_timeseries)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_families", fake_citation_families)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_attackers", fake_citation_attackers)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_fields", fake_citation_fields)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_jurisdictions", fake_citation_jurisdictions)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_citation_cpc_groups", fake_citation_cpc_groups)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_filing_timeseries", fake_filing_timeseries)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_status_timeseries", fake_status_timeseries)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_jurisdiction_unlock_history", fake_jurisdiction_unlocks)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_market_context", fake_market_context)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_forecast_contributors", fake_forecast_contributors)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_compare_timeslice", fake_compare)  # type: ignore[method-assign]
    monkeypatch.setattr(portfolio_api.service, "get_pending_grants", fake_pending)  # type: ignore[method-assign]

    response = client.get("/api/v1/portfolios/Acme%20Ltd/field-timeseries?as_of_year=2025&limit_fields=4")
    assert response.status_code == 200
    assert response.json()["rows"][0]["wipo_field"] == "Computer technology"
    assert calls["field_timeseries"]["limit_fields"] == 4

    response = client.get("/api/v1/portfolios/Acme%20Ltd/citation-summary?as_of_year=2026")
    assert response.status_code == 200
    assert response.json()["rows"][0]["family_count"] == 12
    assert calls["citation_summary"]["as_of_year"] == 2026

    response = client.get("/api/v1/portfolios/Acme%20Ltd/citation-timeseries?year_from=2020&year_to=2025")
    assert response.status_code == 200
    assert response.json()["rows"][0]["as_of_year"] == 2024
    assert calls["citation_timeseries"]["year_from"] == 2020

    response = client.get(
        "/api/v1/portfolios/Acme%20Ltd/citation-families?limit=4&offset=8&wipo_field=Computer%20technology&status=fully_active&sort=forward_clean"
    )
    assert response.status_code == 200
    assert response.json()["rows"][0]["family_id"] == "12345"
    assert calls["citation_families"]["limit"] == 4
    assert calls["citation_families"]["offset"] == 8
    assert calls["citation_families"]["wipo_field"] == "Computer technology"
    assert calls["citation_families"]["status"] == "fully_active"
    assert calls["citation_families"]["sort"] == "forward_clean"

    response = client.get(
        "/api/v1/portfolios/Acme%20Ltd/citation-attackers?limit=5&offset=5&wipo_field=Computer%20technology&jurisdiction_code=US&year_from=2020&year_to=2025"
    )
    assert response.status_code == 200
    assert response.json()["rows"][0]["citing_assignee"] == "Alpha Labs"
    assert calls["citation_attackers"]["limit"] == 5
    assert calls["citation_attackers"]["jurisdiction_code"] == "US"

    response = client.get("/api/v1/portfolios/Acme%20Ltd/citation-fields?limit=5&offset=0&jurisdiction_code=US&year_from=2020&year_to=2025")
    assert response.status_code == 200
    assert response.json()["rows"][0]["wipo_field"] == "Computer technology"
    assert calls["citation_fields"]["jurisdiction_code"] == "US"
    assert calls["citation_fields"]["year_from"] == 2020

    response = client.get("/api/v1/portfolios/Acme%20Ltd/citation-jurisdictions?limit=5&offset=0&wipo_field=Computer%20technology&year_from=2020&year_to=2025")
    assert response.status_code == 200
    assert response.json()["rows"][0]["jurisdiction_code"] == "US"
    assert calls["citation_jurisdictions"]["wipo_field"] == "Computer technology"
    assert calls["citation_jurisdictions"]["year_to"] == 2025

    response = client.get(
        "/api/v1/portfolios/Acme%20Ltd/citation-cpc-groups?limit=5&offset=10&wipo_field=Computer%20technology&jurisdiction_code=US&year_from=2020&year_to=2025"
    )
    assert response.status_code == 200
    assert response.json()["rows"][0]["cpc_main_group"] == "H04L1/00"
    assert calls["citation_cpc_groups"]["limit"] == 5
    assert calls["citation_cpc_groups"]["offset"] == 10
    assert calls["citation_cpc_groups"]["wipo_field"] == "Computer technology"
    assert calls["citation_cpc_groups"]["jurisdiction_code"] == "US"
    assert calls["citation_cpc_groups"]["year_from"] == 2020
    assert calls["citation_cpc_groups"]["year_to"] == 2025

    response = client.get("/api/v1/portfolios/Acme%20Ltd/filing-timeseries?year_from=2020&year_to=2025")
    assert response.status_code == 200
    assert response.json()["rows"][0]["year"] == 2023
    assert calls["filing_timeseries"]["year_from"] == 2020
    assert calls["filing_timeseries"]["year_to"] == 2025

    response = client.get("/api/v1/portfolios/Acme%20Ltd/status-timeseries?year_from=2020&year_to=2025")
    assert response.status_code == 200
    assert response.json()["rows"][0]["as_of_year"] == 2024
    assert calls["status_timeseries"]["year_from"] == 2020
    assert calls["status_timeseries"]["year_to"] == 2025

    response = client.get("/api/v1/portfolios/Acme%20Ltd/jurisdiction-unlocks?year_from=2020&year_to=2025&jurisdiction_limit=12")
    assert response.status_code == 200
    assert response.json()["rows"][0]["kind"] == "summary"
    assert calls["jurisdiction_unlocks"]["year_from"] == 2020
    assert calls["jurisdiction_unlocks"]["year_to"] == 2025
    assert calls["jurisdiction_unlocks"]["jurisdiction_limit"] == 12

    response = client.get("/api/v1/portfolios/Acme%20Ltd/market-context?horizon=5y&as_of_year=2025")
    assert response.status_code == 200
    assert response.json()["rows"][0]["horizon"] == "5y"
    assert calls["market_context"]["horizon"] == "5y"

    response = client.get(
        "/api/v1/portfolios/Acme%20Ltd/forecast-contributors?horizon=5y&contributor_scope=phase04_lapse_risk&limit=5&offset=5"
    )
    assert response.status_code == 200
    assert response.json()["rows"][0]["contributor_entity_id"] == "12345"
    assert calls["forecast_contributors"]["contributor_scope"] == "phase04_lapse_risk"
    assert calls["forecast_contributors"]["offset"] == 5

    response = client.get("/api/v1/portfolios/Acme%20Ltd/compare-timeslice?base_year=2026&compare_year=2024")
    assert response.status_code == 200
    assert response.json()["rows"][0]["metric"] == "blocking_strength"
    assert calls["compare_timeslice"]["base_year"] == 2026

    response = client.get(
        "/api/v1/portfolios/Acme%20Ltd/pending-grants?horizon=24m&branch_jurisdiction_code=EP&branch_wipo_field=Computer%20technology&branch_limit=25"
    )
    assert response.status_code == 200
    assert response.json()["rows"][0]["feature_status"] == "candidate_only"
    assert calls["pending_grants"]["horizon"] == "24m"
    assert calls["pending_grants"]["branch_jurisdiction_code"] == "EP"
    assert calls["pending_grants"]["branch_wipo_field"] == "Computer technology"
    assert calls["pending_grants"]["branch_limit"] == 25
