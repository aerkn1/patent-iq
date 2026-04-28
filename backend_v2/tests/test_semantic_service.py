from application.services.semantic import SemanticService


class FakeSemanticRepository:
    def artifacts(self) -> list:
        return []

    def get_family_vector_support(self, family_id: str):
        if family_id == "999":
            return {"abstract": False, "claims": False}
        if family_id == "111":
            return {"abstract": True, "claims": False}
        return {"abstract": True, "claims": True}

    def get_anchor_row(self, family_id: str, vector_space: str):
        rows = {
            ("111", "abstract"): {
                "docdb_family_id": 111,
                "primary_wipo_field": "Computer technology",
                "owner_name_harmonized": "ALPHA",
                "family_composite_status": "fully_active",
                "queryable_text": "Anchor abstract text",
                "embedding": [1.0, 0.0],
            },
            ("123", "abstract"): {
                "docdb_family_id": 123,
                "primary_wipo_field": "Digital communication",
                "owner_name_harmonized": "ALPHA",
                "family_composite_status": "fully_active",
                "queryable_text": "Anchor abstract text",
                "embedding": [1.0, 0.0],
            },
            ("123", "claims"): {
                "docdb_family_id": 123,
                "primary_wipo_field": "Digital communication",
                "owner_name_harmonized": "ALPHA",
                "family_composite_status": "fully_active",
                "queryable_text": "Anchor claim text",
                "embedding": [1.0, 0.0],
            },
            ("456", "abstract"): {
                "docdb_family_id": 456,
                "primary_wipo_field": "Digital communication",
                "owner_name_harmonized": "BETA",
                "family_composite_status": "fully_active",
                "queryable_text": "Peer abstract text",
                "embedding": [0.8, 0.2],
            },
            ("456", "claims"): {
                "docdb_family_id": 456,
                "primary_wipo_field": "Digital communication",
                "owner_name_harmonized": "BETA",
                "family_composite_status": "fully_active",
                "queryable_text": "Peer claim text",
                "embedding": [0.9, 0.1],
            },
        }
        return rows.get((family_id, vector_space), {})

    def get_space_summary(self, vector_space: str):
        return {
            "vector_space": vector_space,
            "searchable_family_count": 100,
            "total_context_family_count": 1000,
            "vector_coverage_pct": 0.1,
            "abstract_fallback_count": 90,
            "claim_backed_count": 10,
        }

    def get_anchor_search_results(self, family_id: str, vector_space: str, **kwargs):
        return (
            [
                {
                    "docdb_family_id": 456,
                    "primary_wipo_field": "Digital communication",
                    "owner_name_harmonized": "BETA",
                    "family_ui_blocking_power_score": 8.4,
                    "oecd_quality_percentile": 0.91,
                    "family_composite_status": "fully_active",
                    "representative_stage": "STANDARD_GRANT",
                    "text_provenance": "PATSTAT_ABSTRACT",
                    "text_source_type": "PATSTAT_ABSTRACT",
                    "is_abstract_fallback": True,
                    "family_earliest_priority_date": "2020-01-01",
                    "text_excerpt": "Peer abstract text",
                    "semantic_similarity": 0.812,
                }
            ],
            1,
        )

    def get_text_query_search_results(self, query_embedding: list[float], vector_space: str, **kwargs):
        return (
            [
                {
                    "docdb_family_id": 789,
                    "primary_wipo_field": "Computer technology",
                    "owner_name_harmonized": "GAMMA",
                    "family_ui_blocking_power_score": 7.1,
                    "oecd_quality_percentile": 0.64,
                    "family_composite_status": "fully_active",
                    "representative_stage": "STANDARD_GRANT",
                    "text_provenance": "PATSTAT_ABSTRACT",
                    "text_source_type": "PATSTAT_ABSTRACT",
                    "is_abstract_fallback": True,
                    "family_earliest_priority_date": "2021-04-04",
                    "text_excerpt": "Free-text semantic neighbor",
                    "semantic_similarity": 0.744,
                }
            ],
            1,
        )

    def get_family_compare_context(self, family_id: str):
        rows = {
            "123": {
                "docdb_family_id": 123,
                "label": "123",
                "owner_name_harmonized": "ALPHA",
                "primary_wipo_field": "Digital communication",
                "family_composite_status": "fully_active",
                "family_ui_blocking_power_score": 8.0,
                "oecd_quality_percentile": 0.77,
                "representative_stage": "STANDARD_GRANT",
                "text_provenance": "EPAB_EP123",
                "family_earliest_priority_date": "2018-01-01",
                "abstract_supported": True,
                "claims_supported": True,
                "text_excerpt": "Left text",
            },
            "456": {
                "docdb_family_id": 456,
                "label": "456",
                "owner_name_harmonized": "BETA",
                "primary_wipo_field": "Digital communication",
                "family_composite_status": "fully_active",
                "family_ui_blocking_power_score": 7.5,
                "oecd_quality_percentile": 0.73,
                "representative_stage": "STANDARD_GRANT",
                "text_provenance": "EPAB_EP456",
                "family_earliest_priority_date": "2019-02-02",
                "abstract_supported": True,
                "claims_supported": True,
                "text_excerpt": "Right text",
            },
        }
        return rows.get(family_id, {})

    def get_pair_similarity(self, left_family_id: str, right_family_id: str, vector_space: str):
        rows = {
            ("123", "456", "abstract"): 0.81,
            ("123", "456", "claims"): 0.92,
        }
        return rows.get((left_family_id, right_family_id, vector_space))

    def get_family_anchor_suggestions(self, query: str, vector_space: str, limit: int = 8):
        return [
            {
                "family_id": "123",
                "label": "123",
                "owner_name_harmonized": "ALPHA",
                "primary_wipo_field": "Digital communication",
                "family_composite_status": "fully_active",
            },
            {
                "family_id": "456",
                "label": "456",
                "owner_name_harmonized": "BETA",
                "primary_wipo_field": "Digital communication",
                "family_composite_status": "fully_active",
            },
        ][:limit]


class FakeSemanticQueryEncoder:
    def encode_text(self, query_text: str, vector_space: str) -> list[float]:
        assert vector_space == "abstract"
        assert "sensor" in query_text.lower()
        return [0.2, 0.8]


def test_family_anchor_search_returns_structured_semantic_payload():
    service = SemanticService(repository=FakeSemanticRepository(), query_encoder=FakeSemanticQueryEncoder())

    response = service.get_family_anchor_search("123", vector_space="claims", limit=10)

    assert response.query_mode == "family_anchor"
    assert response.vector_space == "claims"
    assert response.anchor_entity is not None
    assert response.anchor_entity.id == "123"
    assert response.summary_cards[0]["key"] == "searchable_families"
    assert response.result_rows[0]["family_id"] == "456"
    assert response.meta.support_level.value == "candidate_only"
    assert response.meta.pagination is not None
    assert response.meta.pagination.total_count == 1


def test_family_anchor_search_rejects_unsupported_space():
    service = SemanticService(repository=FakeSemanticRepository(), query_encoder=FakeSemanticQueryEncoder())

    try:
        service.get_family_anchor_search("111", vector_space="claims")
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "status_code", None) == 400
        assert "Available spaces: abstract" in str(getattr(exc, "detail", ""))
    else:  # pragma: no cover
        raise AssertionError("Expected HTTPException for unsupported vector space")


def test_family_semantic_compare_returns_space_split_similarity():
    service = SemanticService(repository=FakeSemanticRepository(), query_encoder=FakeSemanticQueryEncoder())

    response = service.get_family_semantic_compare("123", "456")

    assert response.compare_kind == "semantic_families"
    assert response.left_entity is not None
    assert response.left_entity.id == "123"
    assert response.right_entity is not None
    assert response.right_entity.id == "456"
    assert response.entity_summaries[0]["role"] == "anchor"
    assert response.entity_summaries[0]["family_id"] == "123"
    assert response.entity_summaries[0]["family_earliest_priority_date"] == "2018-01-01"
    assert response.summary_cards[0]["key"] == "abstract_similarity"
    assert response.summary_cards[1]["key"] == "claims_similarity"
    assert len(response.compare_rows) == 2
    assert response.compare_rows[0]["value"] == 0.81
    assert response.compare_rows[1]["value"] == 0.92


def test_family_anchor_suggestions_return_vector_scoped_rows():
    service = SemanticService(repository=FakeSemanticRepository(), query_encoder=FakeSemanticQueryEncoder())

    response = service.get_family_anchor_suggestions("12", vector_space="claims", limit=5)

    assert response.query == "12"
    assert response.vector_space == "claims"
    assert len(response.rows) == 2
    assert response.rows[0].family_id == "123"


def test_text_discovery_search_returns_structured_semantic_payload():
    service = SemanticService(repository=FakeSemanticRepository(), query_encoder=FakeSemanticQueryEncoder())

    response = service.get_text_discovery_search("distributed sensor fusion for road-scene detection", vector_space="abstract", limit=6)

    assert response.query_mode == "free_text"
    assert response.vector_space == "abstract"
    assert response.anchor_entity is None
    assert response.summary is not None
    assert response.summary["query_text_excerpt"].startswith("distributed sensor fusion")
    assert response.result_rows[0]["family_id"] == "789"
    assert response.meta.pagination is not None
    assert response.meta.pagination.total_count == 1


def test_text_discovery_search_rejects_claim_space():
    service = SemanticService(repository=FakeSemanticRepository(), query_encoder=FakeSemanticQueryEncoder())

    try:
        service.get_text_discovery_search("distributed sensor fusion for road-scene detection", vector_space="claims")
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "status_code", None) == 400
        assert "limited to abstract scope" in str(getattr(exc, "detail", ""))
    else:  # pragma: no cover
        raise AssertionError("Expected HTTPException for unsupported free-text vector space")
