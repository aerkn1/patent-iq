from fastapi.testclient import TestClient

from api.v1 import families as families_api
from main import app

client = TestClient(app)


def test_family_suggestions_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {"query": None, "limit": None}

    def fake_get_family_suggestions(query: str, limit: int = 8):
        calls["query"] = query
        calls["limit"] = limit
        return {
            "query": query,
            "rows": [
                {
                    "family_id": "123",
                    "label": "123",
                    "owner_label": "Apple",
                    "primary_field": "Computer technology",
                    "status": "fully_active",
                }
            ],
        }

    monkeypatch.setattr(families_api.service, "get_family_suggestions", fake_get_family_suggestions)  # type: ignore[method-assign]

    response = client.get("/api/v1/families/suggestions?q=12&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "12"
    assert payload["rows"][0]["family_id"] == "123"
    assert calls["query"] == "12"
    assert calls["limit"] == 5
