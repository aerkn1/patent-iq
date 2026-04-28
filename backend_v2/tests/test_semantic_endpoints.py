from fastapi.testclient import TestClient

from api.v1 import semantic as semantic_api
from domain.schemas.common import ResponseMeta
from domain.schemas.semantic import SemanticCompareResponse, SemanticSearchResponse
from main import app

client = TestClient(app)


def test_semantic_family_search_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {}

    def fake_get_family_anchor_search(
        family_id: str,
        *,
        vector_space: str = "abstract",
        limit: int = 12,
        offset: int = 0,
        same_field_only: bool = False,
        exclude_same_owner: bool = False,
        selected_family_id: str | None = None,
    ) -> SemanticSearchResponse:
        calls.update(
            {
                "family_id": family_id,
                "vector_space": vector_space,
                "limit": limit,
                "offset": offset,
                "same_field_only": same_field_only,
                "exclude_same_owner": exclude_same_owner,
                "selected_family_id": selected_family_id,
            }
        )
        return SemanticSearchResponse(
            vector_space=vector_space,
            summary={"anchor_family_id": family_id},
            result_rows=[{"family_id": "456"}],
            meta=ResponseMeta(page="semantic.family_anchor_search", artifact_sources=[]),
        )

    monkeypatch.setattr(semantic_api.service, "get_family_anchor_search", fake_get_family_anchor_search)  # type: ignore[method-assign]

    response = client.get(
        "/api/v1/semantic/families/search?family_id=123&vector_space=claims&limit=8&offset=2&same_field_only=true&exclude_same_owner=true&selected_family_id=456"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vector_space"] == "claims"
    assert payload["summary"]["anchor_family_id"] == "123"
    assert payload["result_rows"][0]["family_id"] == "456"
    assert calls["family_id"] == "123"
    assert calls["vector_space"] == "claims"
    assert calls["limit"] == 8
    assert calls["offset"] == 2
    assert calls["same_field_only"] is True
    assert calls["exclude_same_owner"] is True
    assert calls["selected_family_id"] == "456"


def test_semantic_family_suggestions_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {}

    def fake_get_family_anchor_suggestions(
        query: str,
        *,
        vector_space: str = "abstract",
        limit: int = 8,
    ):
        calls.update(
            {
                "query": query,
                "vector_space": vector_space,
                "limit": limit,
            }
        )
        return {
            "query": query,
            "vector_space": vector_space,
            "rows": [
                {
                    "family_id": "123",
                    "label": "123",
                    "owner_name_harmonized": "ALPHA",
                    "primary_wipo_field": "Digital communication",
                    "family_composite_status": "fully_active",
                }
            ],
        }

    monkeypatch.setattr(semantic_api.service, "get_family_anchor_suggestions", fake_get_family_anchor_suggestions)  # type: ignore[method-assign]

    response = client.get("/api/v1/semantic/families/suggestions?q=12&vector_space=claims&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "12"
    assert payload["vector_space"] == "claims"
    assert payload["rows"][0]["family_id"] == "123"
    assert calls["query"] == "12"
    assert calls["vector_space"] == "claims"
    assert calls["limit"] == 5


def test_semantic_text_search_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {}

    def fake_get_text_discovery_search(
        query_text: str,
        *,
        vector_space: str = "abstract",
        limit: int = 12,
        offset: int = 0,
    ) -> SemanticSearchResponse:
        calls.update(
            {
                "query_text": query_text,
                "vector_space": vector_space,
                "limit": limit,
                "offset": offset,
            }
        )
        return SemanticSearchResponse(
            query_mode="free_text",
            vector_space=vector_space,
            summary={"query_text_excerpt": query_text},
            result_rows=[{"family_id": "789"}],
            meta=ResponseMeta(page="semantic.text_discovery_search", artifact_sources=[]),
        )

    monkeypatch.setattr(semantic_api.service, "get_text_discovery_search", fake_get_text_discovery_search)  # type: ignore[method-assign]

    response = client.get("/api/v1/semantic/text/search?q=distributed%20sensor%20fusion&vector_space=abstract&limit=7&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "free_text"
    assert payload["vector_space"] == "abstract"
    assert payload["summary"]["query_text_excerpt"] == "distributed sensor fusion"
    assert payload["result_rows"][0]["family_id"] == "789"
    assert calls["query_text"] == "distributed sensor fusion"
    assert calls["vector_space"] == "abstract"
    assert calls["limit"] == 7
    assert calls["offset"] == 1


def test_semantic_family_compare_endpoint_forwards_query_params(monkeypatch):
    calls: dict[str, object] = {}

    def fake_get_family_semantic_compare(left_family_id: str, right_family_id: str) -> SemanticCompareResponse:
        calls["left_family_id"] = left_family_id
        calls["right_family_id"] = right_family_id
        return SemanticCompareResponse(
            left_entity={"id": left_family_id, "label": left_family_id, "page_kind": "family"},
            right_entity={"id": right_family_id, "label": right_family_id, "page_kind": "family"},
            entity_summaries=[
                {
                    "role": "anchor",
                    "family_id": left_family_id,
                    "entity_label": f"Family {left_family_id}",
                    "owner_name_harmonized": "ALPHA",
                },
                {
                    "role": "selected",
                    "family_id": right_family_id,
                    "entity_label": f"Family {right_family_id}",
                    "owner_name_harmonized": "BETA",
                },
            ],
            summary_cards=[{"key": "abstract_similarity", "label": "Abstract similarity"}],
            compare_rows=[{"key": "claims_similarity", "label": "Claim similarity"}],
            meta=ResponseMeta(page="semantic.family_compare", artifact_sources=[]),
        )

    monkeypatch.setattr(semantic_api.service, "get_family_semantic_compare", fake_get_family_semantic_compare)  # type: ignore[method-assign]

    response = client.get("/api/v1/semantic/families/compare?left_family_id=123&right_family_id=456")

    assert response.status_code == 200
    payload = response.json()
    assert payload["left_entity"]["id"] == "123"
    assert payload["right_entity"]["id"] == "456"
    assert payload["entity_summaries"][0]["family_id"] == "123"
    assert payload["entity_summaries"][1]["family_id"] == "456"
    assert payload["summary_cards"][0]["key"] == "abstract_similarity"
    assert payload["compare_rows"][0]["key"] == "claims_similarity"
    assert calls["left_family_id"] == "123"
    assert calls["right_family_id"] == "456"
