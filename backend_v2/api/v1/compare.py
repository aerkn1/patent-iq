from fastapi import APIRouter

from application.services.compare import CompareService
from domain.schemas.compare import (
    CompareFamilySuggestionResponse,
    CompareResponse,
    CompareScopeLookupResponse,
    CompareTimesliceOptionsResponse,
)

router = APIRouter(prefix="/compare", tags=["compare"])
service = CompareService()


@router.get("/families", response_model=CompareResponse)
def get_family_compare(
    left_family_id: str | None = None,
    right_family_id: str | None = None,
) -> CompareResponse:
    return service.get_family_compare(left_family_id=left_family_id, right_family_id=right_family_id)


@router.get("/families/timeslice", response_model=CompareResponse)
def get_family_timeslice_compare(
    family_id: str,
    base_year: int | None = None,
    compare_year: int | None = None,
) -> CompareResponse:
    return service.get_family_timeslice_compare(
        family_id=family_id,
        base_year=base_year,
        compare_year=compare_year,
    )


@router.get("/families/timeslice/options", response_model=CompareTimesliceOptionsResponse)
def get_family_timeslice_options(family_id: str) -> CompareTimesliceOptionsResponse:
    return service.get_family_timeslice_options(family_id=family_id)


@router.get("/families/lookup", response_model=CompareScopeLookupResponse)
def get_family_compare_lookup(family_id: str) -> CompareScopeLookupResponse:
    return service.get_family_compare_lookup(family_id=family_id)


@router.get("/families/suggestions", response_model=CompareFamilySuggestionResponse)
def get_family_compare_suggestions(q: str, limit: int = 8) -> CompareFamilySuggestionResponse:
    return service.get_family_compare_suggestions(query=q, limit=limit)


@router.get("/portfolios", response_model=CompareResponse)
def get_portfolio_compare(
    left_owner_id: str,
    right_owner_id: str,
    top_family_limit: int = 5,
) -> CompareResponse:
    return service.get_portfolio_compare(
        left_owner_id=left_owner_id,
        right_owner_id=right_owner_id,
        top_family_limit=top_family_limit,
    )


@router.get("/portfolios/timeslice", response_model=CompareResponse)
def get_portfolio_timeslice_compare(
    owner_id: str,
    base_year: int | None = None,
    compare_year: int | None = None,
) -> CompareResponse:
    return service.get_portfolio_timeslice_compare(
        owner_id=owner_id,
        base_year=base_year,
        compare_year=compare_year,
    )


@router.get("/portfolios/timeslice/options", response_model=CompareTimesliceOptionsResponse)
def get_portfolio_timeslice_options(owner_id: str) -> CompareTimesliceOptionsResponse:
    return service.get_portfolio_timeslice_options(owner_id=owner_id)


@router.get("/portfolios/lookup", response_model=CompareScopeLookupResponse)
def get_portfolio_compare_lookup(owner_id: str) -> CompareScopeLookupResponse:
    return service.get_portfolio_compare_lookup(owner_id=owner_id)
