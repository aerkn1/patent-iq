import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.v1 import publications as publication_api
from application.services.publications import PublicationService
from domain.schemas.common import ResponseMeta
from domain.schemas.publication import PublicationOverviewResponse, PublicationSectionResponse
from main import app


class FakePublicationRepository:
    def artifacts(self) -> list:
        return []

    def get_publication_suggestions(self, query: str, limit: int = 8):
        return [
            {
                "publication_id": "EP2606406A1",
                "label": "EP2606406A1",
                "authority": "EP",
                "kind_code": "A1",
                "publication_date": "2013-07-10",
                "family_id": "57400072",
            },
            {
                "publication_id": "EP2606406B1",
                "label": "EP2606406B1",
                "authority": "EP",
                "kind_code": "B1",
                "publication_date": "2018-11-14",
                "family_id": "57400072",
            },
        ][:limit]

    def get_publication_member(self, publication_id: str):
        if publication_id.upper() != "EP2606406A1":
            return None
        return {
            "publication_number_full": "EP2606406A1",
            "pat_publn_id": 26064061,
            "appln_id": 11223344,
            "docdb_family_id": 57400072,
            "publn_auth": "EP",
            "publn_nr": "2606406",
            "publn_kind": "A1",
            "publn_date": "2013-07-10",
            "is_application_stage": True,
            "is_grant_stage": False,
            "is_modifier_stage": False,
            "scope_type": "mega_cluster_bounded",
            "snapshot_date": "2026-03-15",
        }

    def get_title_for_application(self, appln_id: int):
        return {"title_text": "Signal routing for adaptive network switching", "language_code": "en"}

    def get_filing_date_for_application(self, appln_id: int):
        return "2011-09-07"

    def get_abstract_for_application(self, appln_id: int):
        return {"abstract_text": "An adaptive routing system for network traffic.", "language_code": "en"}

    def get_claim_for_publication(self, publication_id: str):
        return {"claim_text": "A routing apparatus comprising an adaptive signal controller.", "language_code": "en"}

    def get_register_evidence(self, appln_id: int):
        return {
            "reg101_id": 77,
            "register_record_present": True,
            "ep_registered_license_flag": True,
            "ep_licensee_names": "Acme Licensing GmbH",
            "register_snapshot_date": "2026-03-15",
            "ep_display_status_text": "pending_examination",
            "status_source": "REGISTER_CORE",
            "display_snapshot_date": "2026-03-15",
            "ep_proc_step_maturity_score": 0.81,
            "ep_search_report_mailed_date": "2014-01-12",
            "ep_latest_proc_phase_code": "EXAM",
            "ep_latest_proc_result_code": "PENDING",
            "ep_proc_time_limit_days": 120,
            "ep_register_is_unitary_patent": False,
            "ep_register_up_status_code": None,
            "ep_register_up_status_text": None,
            "ep_register_up_event_latest_date": None,
            "ep_opposition_active": False,
            "ep_opposition_status_text": None,
            "ep_opponent_names": None,
            "ep_opponent_agent_names": None,
            "ep_appeal_active": False,
            "ep_appeal_result_text": None,
            "ep_register_lead_agent_name": "Meyer IP",
            "ep_register_lead_agent_country": "DE",
        }

    def get_related_family_publications(self, docdb_family_id: int, exclude_publication_id: str, limit: int = 6):
        return [
            {
                "publication_number_full": "WO2012131275A1",
                "publn_auth": "WO",
                "publn_kind": "A1",
                "publn_date": "2012-10-04",
                "is_application_stage": True,
                "is_grant_stage": False,
                "is_modifier_stage": False,
            },
            {
                "publication_number_full": "EP2606406B1",
                "publn_auth": "EP",
                "publn_kind": "B1",
                "publn_date": "2018-11-14",
                "is_application_stage": False,
                "is_grant_stage": True,
                "is_modifier_stage": False,
            },
        ]


class NonTextSectionDoesNotLoadTextRepository(FakePublicationRepository):
    def get_title_for_application(self, appln_id: int):
        raise AssertionError("Non-text sections should not load title rows.")

    def get_abstract_for_application(self, appln_id: int):
        raise AssertionError("Non-text sections should not load abstract rows.")

    def get_claim_for_publication(self, publication_id: str):
        raise AssertionError("Non-text sections should not load claim rows.")


def test_publication_overview_service_maps_evidence_first_payload() -> None:
    service = PublicationService(FakePublicationRepository())

    overview = service.get_overview("ep2606406a1")

    assert overview.identity.id == "EP2606406A1"
    assert overview.overview["authority"] == "EP"
    assert overview.overview["filing_date"] == "2011-09-07"
    assert overview.summary_cards[0]["value"] == "EP"
    summary_cards = {card["key"]: card["value"] for card in overview.summary_cards}
    assert summary_cards["filing_date"] == "2011-09-07"
    assert summary_cards["text_coverage"] == "Title + abstract"
    assert overview.text_availability[2]["status"] == "candidate"
    assert overview.register_evidence[2]["value"] == "Yes"
    assert overview.related_publications[1]["stage_label"] == "Grant"
    assert overview.meta.page == "publication.overview"


def test_publication_service_suggestions_return_publication_rows() -> None:
    service = PublicationService(FakePublicationRepository())

    response = service.get_publication_suggestions("EP260", limit=2)

    assert response.query == "EP260"
    assert len(response.rows) == 2
    assert response.rows[0].publication_id == "EP2606406A1"
    assert response.rows[0].family_id == "57400072"


def test_publication_sections_map_text_timeline_and_register_rows() -> None:
    service = PublicationService(FakePublicationRepository())

    text_section = service.get_section("EP2606406A1", "text")
    assert text_section.rows[0]["panel_key"] == "title"
    assert text_section.rows[2]["available"] is True
    assert text_section.summary == {
        "title_available": True,
        "abstract_available": True,
        "claim_1_available": True,
        "claim_source_mode": "epab_claim_1",
    }

    timeline_section = service.get_section("EP2606406A1", "legal_timeline")
    assert [row["event_type"] for row in timeline_section.rows] == [
        "Publication",
        "Search report mailed",
        "Register snapshot",
    ]
    assert timeline_section.summary["event_count"] == 3

    register_section = service.get_section("EP2606406A1", "register_evidence")
    assert register_section.summary == {
        "register_record_present": True,
        "register_snapshot_date": "2026-03-15",
        "license_flag": True,
        "unitary_patent": False,
        "opposition_active": False,
    }
    assert register_section.rows[7]["value"] == "Meyer IP"


def test_publication_non_text_sections_skip_text_lookups() -> None:
    service = PublicationService(NonTextSectionDoesNotLoadTextRepository())

    timeline_section = service.get_section("EP2606406A1", "legal_timeline")
    register_section = service.get_section("EP2606406A1", "register_evidence")

    assert timeline_section.summary["event_count"] == 3
    assert register_section.summary["register_record_present"] is True


def test_publication_service_raises_404_for_unknown_publication() -> None:
    service = PublicationService(FakePublicationRepository())

    with pytest.raises(HTTPException) as error:
        service.get_overview("UNKNOWN123")

    assert error.value.status_code == 404


def test_publication_routes_forward_to_service(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls = {"overview": None, "text": None, "legal_timeline": None, "register_evidence": None}

    def fake_overview(publication_id: str) -> PublicationOverviewResponse:
        calls["overview"] = publication_id
        return PublicationOverviewResponse(
            identity={"id": publication_id, "label": publication_id, "page_kind": "publication"},
            overview={"publication_id": publication_id},
            summary_cards=[],
            bibliography=[],
            family_context=[],
            text_availability=[],
            register_evidence=[],
            related_publications=[],
            meta=ResponseMeta(page="publication.overview", artifact_sources=[]),
        )

    def fake_section(publication_id: str, section: str) -> PublicationSectionResponse:
        calls[section] = publication_id
        return PublicationSectionResponse(
            publication_id=publication_id,
            summary={"section": section},
            rows=[{"section": section}],
            meta=ResponseMeta(page=f"publication.{section}", artifact_sources=[]),
        )

    monkeypatch.setattr(publication_api.service, "get_overview", fake_overview)  # type: ignore[method-assign]
    monkeypatch.setattr(publication_api.service, "get_section", fake_section)  # type: ignore[method-assign]

    response = client.get("/api/v1/publications/EP2606406A1/overview")
    assert response.status_code == 200
    assert calls["overview"] == "EP2606406A1"

    response = client.get("/api/v1/publications/EP2606406A1/text")
    assert response.status_code == 200
    assert calls["text"] == "EP2606406A1"

    response = client.get("/api/v1/publications/EP2606406A1/legal-timeline")
    assert response.status_code == 200
    assert calls["legal_timeline"] == "EP2606406A1"

    response = client.get("/api/v1/publications/EP2606406A1/register-evidence")
    assert response.status_code == 200
    assert calls["register_evidence"] == "EP2606406A1"


def test_publication_suggestions_route_forwards_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    calls: dict[str, object] = {"query": None, "limit": None}

    def fake_suggestions(query: str, limit: int = 8):
        calls["query"] = query
        calls["limit"] = limit
        return {
            "query": query,
            "rows": [
                {
                    "publication_id": "EP2606406A1",
                    "label": "EP2606406A1",
                    "authority": "EP",
                    "kind_code": "A1",
                    "publication_date": "2013-07-10",
                    "family_id": "57400072",
                }
            ],
        }

    monkeypatch.setattr(publication_api.service, "get_publication_suggestions", fake_suggestions)  # type: ignore[method-assign]

    response = client.get("/api/v1/publications/suggestions?q=EP260&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "EP260"
    assert payload["rows"][0]["publication_id"] == "EP2606406A1"
    assert calls["query"] == "EP260"
    assert calls["limit"] == 5
