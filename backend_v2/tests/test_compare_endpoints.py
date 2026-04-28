from fastapi.testclient import TestClient

from api.v1 import compare as compare_api
from domain.schemas.common import PageIdentity, ResponseMeta
from domain.schemas.compare import CompareResponse
from main import app

client = TestClient(app)


def test_compare_portfolios_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"left_owner_id": None, "right_owner_id": None, "top_family_limit": None}

    def fake_get_portfolio_compare(left_owner_id: str, right_owner_id: str, top_family_limit: int = 5) -> CompareResponse:
        calls["left_owner_id"] = left_owner_id
        calls["right_owner_id"] = right_owner_id
        calls["top_family_limit"] = top_family_limit
        return CompareResponse(
            compare_kind="portfolios",
            left_entity=PageIdentity(id=left_owner_id, label="Left Co", page_kind="portfolio"),
            right_entity=PageIdentity(id=right_owner_id, label="Right Co", page_kind="portfolio"),
            rows=[{"kind": "lens", "lens": "mass", "label": "Blocking Footprint"}],
            summary_cards=[{"key": "family_count", "label": "Families in scope"}],
            field_overlap_rows=[{"key": "computer_technology", "label": "Computer technology"}],
            meta=ResponseMeta(page="compare.portfolios", artifact_sources=[]),
        )

    monkeypatch.setattr(compare_api.service, "get_portfolio_compare", fake_get_portfolio_compare)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/portfolios?left_owner_id=ALPHA&right_owner_id=BETA&top_family_limit=7")

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_kind"] == "portfolios"
    assert payload["left_entity"]["id"] == "ALPHA"
    assert payload["right_entity"]["id"] == "BETA"
    assert payload["rows"][0]["lens"] == "mass"
    assert payload["summary_cards"][0]["key"] == "family_count"
    assert payload["field_overlap_rows"][0]["label"] == "Computer technology"
    assert calls["left_owner_id"] == "ALPHA"
    assert calls["right_owner_id"] == "BETA"
    assert calls["top_family_limit"] == 7


def test_compare_families_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"left_family_id": None, "right_family_id": None}

    def fake_get_family_compare(left_family_id: str | None = None, right_family_id: str | None = None) -> CompareResponse:
        calls["left_family_id"] = left_family_id
        calls["right_family_id"] = right_family_id
        return CompareResponse(
            compare_kind="families",
            left_entity=PageIdentity(id=left_family_id or "", label=left_family_id or "", page_kind="family"),
            right_entity=PageIdentity(id=right_family_id or "", label=right_family_id or "", page_kind="family"),
            rows=[],
            summary_cards=[{"key": "family_size", "label": "Family size"}],
            forecast_rows=[{"key": "citation_outlook_3y", "label": "3y citation outlook"}],
            meta=ResponseMeta(page="compare.families", artifact_sources=[]),
        )

    monkeypatch.setattr(compare_api.service, "get_family_compare", fake_get_family_compare)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/families?left_family_id=123&right_family_id=456")

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_kind"] == "families"
    assert payload["left_entity"]["id"] == "123"
    assert payload["right_entity"]["id"] == "456"
    assert payload["summary_cards"][0]["key"] == "family_size"
    assert payload["forecast_rows"][0]["label"] == "3y citation outlook"
    assert calls["left_family_id"] == "123"
    assert calls["right_family_id"] == "456"


def test_compare_family_timeslice_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"family_id": None, "base_year": None, "compare_year": None}

    def fake_get_family_timeslice_compare(
        family_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> CompareResponse:
        calls["family_id"] = family_id
        calls["base_year"] = base_year
        calls["compare_year"] = compare_year
        return CompareResponse(
            compare_kind="families",
            compare_mode="timeslice",
            left_entity=PageIdentity(id=f"{family_id}:2026", label=f"Family {family_id} • 2026", page_kind="family"),
            right_entity=PageIdentity(id=f"{family_id}:2024", label=f"Family {family_id} • 2024", page_kind="family"),
            summary_cards=[{"key": "family_size_asof", "label": "Family size"}],
            meta=ResponseMeta(page="compare.families.timeslice", artifact_sources=[]),
        )

    monkeypatch.setattr(compare_api.service, "get_family_timeslice_compare", fake_get_family_timeslice_compare)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/families/timeslice?family_id=123&base_year=2026&compare_year=2024")

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_mode"] == "timeslice"
    assert payload["left_entity"]["id"] == "123:2026"
    assert payload["summary_cards"][0]["key"] == "family_size_asof"
    assert calls["family_id"] == "123"
    assert calls["base_year"] == 2026
    assert calls["compare_year"] == 2024


def test_compare_family_timeslice_options_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"family_id": None}

    def fake_get_family_timeslice_options(family_id: str):
        calls["family_id"] = family_id
        return {
            "entity_id": family_id,
            "available_years": [2026, 2024],
            "compare_safe_years": [2026, 2024],
            "default_base_year": 2026,
            "default_compare_year": 2024,
        }

    monkeypatch.setattr(compare_api.service, "get_family_timeslice_options", fake_get_family_timeslice_options)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/families/timeslice/options?family_id=123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entity_id"] == "123"
    assert payload["available_years"] == [2026, 2024]
    assert payload["default_compare_year"] == 2024
    assert calls["family_id"] == "123"


def test_compare_family_lookup_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"family_id": None}

    def fake_get_family_compare_lookup(family_id: str):
        calls["family_id"] = family_id
        return {
            "compare_kind": "families",
            "entity_id": family_id,
            "label": f"Family {family_id}",
            "in_scope": True,
            "primary_field": "Computer technology",
            "status": "fully_active",
            "family_count": 5,
            "timeslice_available": True,
            "default_base_year": 2026,
            "default_compare_year": 2024,
            "note": None,
        }

    monkeypatch.setattr(compare_api.service, "get_family_compare_lookup", fake_get_family_compare_lookup)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/families/lookup?family_id=123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_kind"] == "families"
    assert payload["entity_id"] == "123"
    assert payload["in_scope"] is True
    assert calls["family_id"] == "123"


def test_compare_family_suggestions_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"query": None, "limit": None}

    def fake_get_family_compare_suggestions(query: str, limit: int = 8):
        calls["query"] = query
        calls["limit"] = limit
        return {
            "query": query,
            "rows": [
                {
                    "family_id": "123",
                    "label": "123",
                    "owner_label": "Alpha Corp",
                    "primary_field": "Computer technology",
                    "status": "fully_active",
                }
            ],
        }

    monkeypatch.setattr(compare_api.service, "get_family_compare_suggestions", fake_get_family_compare_suggestions)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/families/suggestions?q=12&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "12"
    assert payload["rows"][0]["family_id"] == "123"
    assert calls["query"] == "12"
    assert calls["limit"] == 5


def test_compare_portfolio_timeslice_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"owner_id": None, "base_year": None, "compare_year": None}

    def fake_get_portfolio_timeslice_compare(
        owner_id: str,
        base_year: int | None = None,
        compare_year: int | None = None,
    ) -> CompareResponse:
        calls["owner_id"] = owner_id
        calls["base_year"] = base_year
        calls["compare_year"] = compare_year
        return CompareResponse(
            compare_kind="portfolios",
            compare_mode="timeslice",
            left_entity=PageIdentity(id=f"{owner_id}:2026", label=f"{owner_id} • 2026", page_kind="portfolio"),
            right_entity=PageIdentity(id=f"{owner_id}:2024", label=f"{owner_id} • 2024", page_kind="portfolio"),
            summary_cards=[{"key": "families_in_scope", "label": "Families in scope"}],
            meta=ResponseMeta(page="compare.portfolios.timeslice", artifact_sources=[]),
        )

    monkeypatch.setattr(compare_api.service, "get_portfolio_timeslice_compare", fake_get_portfolio_timeslice_compare)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/portfolios/timeslice?owner_id=ALPHA&base_year=2026&compare_year=2024")

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_mode"] == "timeslice"
    assert payload["left_entity"]["id"] == "ALPHA:2026"
    assert payload["summary_cards"][0]["key"] == "families_in_scope"
    assert calls["owner_id"] == "ALPHA"
    assert calls["base_year"] == 2026
    assert calls["compare_year"] == 2024


def test_compare_portfolio_timeslice_options_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"owner_id": None}

    def fake_get_portfolio_timeslice_options(owner_id: str):
        calls["owner_id"] = owner_id
        return {
            "entity_id": owner_id,
            "available_years": [2026, 2024],
            "compare_safe_years": [2026, 2024],
            "default_base_year": 2026,
            "default_compare_year": 2024,
        }

    monkeypatch.setattr(compare_api.service, "get_portfolio_timeslice_options", fake_get_portfolio_timeslice_options)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/portfolios/timeslice/options?owner_id=ALPHA")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entity_id"] == "ALPHA"
    assert payload["available_years"] == [2026, 2024]
    assert payload["default_compare_year"] == 2024
    assert calls["owner_id"] == "ALPHA"


def test_compare_portfolio_lookup_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"owner_id": None}

    def fake_get_portfolio_compare_lookup(owner_id: str):
        calls["owner_id"] = owner_id
        return {
            "compare_kind": "portfolios",
            "entity_id": owner_id,
            "label": "Alpha Corp",
            "in_scope": True,
            "primary_field": None,
            "status": None,
            "family_count": 18,
            "timeslice_available": True,
            "default_base_year": 2026,
            "default_compare_year": 2024,
            "note": None,
        }

    monkeypatch.setattr(compare_api.service, "get_portfolio_compare_lookup", fake_get_portfolio_compare_lookup)  # type: ignore[method-assign]

    response = client.get("/api/v1/compare/portfolios/lookup?owner_id=ALPHA")

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_kind"] == "portfolios"
    assert payload["entity_id"] == "ALPHA"
    assert payload["in_scope"] is True
    assert calls["owner_id"] == "ALPHA"
