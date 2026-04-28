from fastapi import APIRouter

from application.services.families import FamilyService
from domain.schemas.family import FamilyOverviewResponse, FamilySectionResponse, FamilySuggestionResponse

router = APIRouter(prefix="/families", tags=["families"])
service = FamilyService()


@router.get("/suggestions", response_model=FamilySuggestionResponse)
def get_family_suggestions(q: str, limit: int = 8) -> FamilySuggestionResponse:
    return service.get_family_suggestions(query=q, limit=limit)


@router.get("/{family_id}/overview", response_model=FamilyOverviewResponse)
def get_family_overview(family_id: str, as_of_year: int | None = None) -> FamilyOverviewResponse:
    return service.get_overview(family_id=family_id, as_of_year=as_of_year)


@router.get("/{family_id}/legal", response_model=FamilySectionResponse)
def get_family_legal(family_id: str, as_of_year: int | None = None) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="legal", as_of_year=as_of_year)


@router.get("/{family_id}/fields", response_model=FamilySectionResponse)
def get_family_fields(family_id: str, as_of_year: int | None = None) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="fields", as_of_year=as_of_year)


@router.get("/{family_id}/timeseries", response_model=FamilySectionResponse)
def get_family_timeseries(family_id: str, as_of_year: int | None = None) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="timeseries", as_of_year=as_of_year)


@router.get("/{family_id}/members", response_model=FamilySectionResponse)
def get_family_members(
    family_id: str,
    limit: int = 10,
    offset: int = 0,
) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="members", limit=limit, offset=offset)


@router.get("/{family_id}/semantic-context", response_model=FamilySectionResponse)
def get_family_semantic_context(family_id: str) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="semantic_context")


@router.get("/{family_id}/forecasts", response_model=FamilySectionResponse)
def get_family_forecasts(family_id: str) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="forecasts")


@router.get("/{family_id}/citations", response_model=FamilySectionResponse)
def get_family_citations(
    family_id: str,
    limit: int = 10,
    offset: int = 0,
    owner_filter: str | None = None,
) -> FamilySectionResponse:
    return service.get_section(
        family_id=family_id,
        section="citations",
        limit=limit,
        offset=offset,
        owner_filter=owner_filter,
    )


@router.get("/{family_id}/classification", response_model=FamilySectionResponse)
def get_family_classification(family_id: str, as_of_year: int | None = None) -> FamilySectionResponse:
    return service.get_section(family_id=family_id, section="classification", as_of_year=as_of_year)
