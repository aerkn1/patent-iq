from fastapi import APIRouter

from application.services.publications import PublicationService
from domain.schemas.publication import PublicationOverviewResponse, PublicationSectionResponse, PublicationSuggestionResponse

router = APIRouter(prefix="/publications", tags=["publications"])
service = PublicationService()


@router.get("/suggestions", response_model=PublicationSuggestionResponse)
def get_publication_suggestions(q: str, limit: int = 8) -> PublicationSuggestionResponse:
    return service.get_publication_suggestions(query=q, limit=limit)


@router.get("/{publication_id}/overview", response_model=PublicationOverviewResponse)
def get_publication_overview(publication_id: str) -> PublicationOverviewResponse:
    return service.get_overview(publication_id=publication_id)


@router.get("/{publication_id}/text", response_model=PublicationSectionResponse)
def get_publication_text(publication_id: str) -> PublicationSectionResponse:
    return service.get_section(publication_id=publication_id, section="text")


@router.get("/{publication_id}/legal-timeline", response_model=PublicationSectionResponse)
def get_publication_legal_timeline(publication_id: str) -> PublicationSectionResponse:
    return service.get_section(publication_id=publication_id, section="legal_timeline")


@router.get("/{publication_id}/register-evidence", response_model=PublicationSectionResponse)
def get_publication_register_evidence(publication_id: str) -> PublicationSectionResponse:
    return service.get_section(publication_id=publication_id, section="register_evidence")
