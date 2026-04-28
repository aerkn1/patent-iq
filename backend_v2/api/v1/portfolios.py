from fastapi import APIRouter

from application.services.portfolios import PortfolioService
from domain.schemas.portfolio import (
    PortfolioFamiliesResponse,
    PortfolioFieldsResponse,
    PortfolioThreatResponse,
    PortfolioClassificationResponse,
    PortfolioForecastResponse,
    PortfolioOverviewResponse,
    PortfolioOwnerSearchResponse,
    PortfolioSectionResponse,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])
service = PortfolioService()


@router.get("/search", response_model=PortfolioOwnerSearchResponse)
def search_portfolio_owners(query: str, limit: int = 8) -> PortfolioOwnerSearchResponse:
    return service.search_owners(query=query, limit=limit)


@router.get("/{owner_id}/overview", response_model=PortfolioOverviewResponse)
def get_portfolio_overview(owner_id: str, as_of_year: int | None = None) -> PortfolioOverviewResponse:
    return service.get_overview(owner_id=owner_id, as_of_year=as_of_year)


@router.get("/{owner_id}/families", response_model=PortfolioFamiliesResponse)
def get_portfolio_families(
    owner_id: str,
    as_of_year: int | None = None,
    limit: int = 10,
    offset: int = 0,
    q: str | None = None,
    status: str | None = None,
    primary_field: str | None = None,
    sort: str | None = None,
) -> PortfolioFamiliesResponse:
    return service.get_families(
        owner_id=owner_id,
        as_of_year=as_of_year,
        limit=limit,
        offset=offset,
        q=q,
        status=status,
        primary_field=primary_field,
        sort=sort,
    )


@router.get("/{owner_id}/fields", response_model=PortfolioFieldsResponse)
def get_portfolio_fields(owner_id: str, as_of_year: int | None = None) -> PortfolioFieldsResponse:
    return service.get_fields(owner_id=owner_id, as_of_year=as_of_year)


@router.get("/{owner_id}/field-timeseries", response_model=PortfolioSectionResponse)
def get_portfolio_field_timeseries(
    owner_id: str,
    as_of_year: int | None = None,
    limit_fields: int = 8,
) -> PortfolioSectionResponse:
    return service.get_field_timeseries(owner_id=owner_id, as_of_year=as_of_year, limit_fields=limit_fields)


@router.get("/{owner_id}/citation-summary", response_model=PortfolioSectionResponse)
def get_portfolio_citation_summary(
    owner_id: str,
    as_of_year: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_summary(owner_id=owner_id, as_of_year=as_of_year)


@router.get("/{owner_id}/citation-timeseries", response_model=PortfolioSectionResponse)
def get_portfolio_citation_timeseries(
    owner_id: str,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_timeseries(owner_id=owner_id, year_from=year_from, year_to=year_to)


@router.get("/{owner_id}/citation-families", response_model=PortfolioSectionResponse)
def get_portfolio_citation_families(
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    wipo_field: str | None = None,
    status: str | None = None,
    sort: str | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_families(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        wipo_field=wipo_field,
        status=status,
        sort=sort,
    )


@router.get("/{owner_id}/citation-attackers", response_model=PortfolioSectionResponse)
def get_portfolio_citation_attackers(
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    wipo_field: str | None = None,
    jurisdiction_code: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_attackers(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        wipo_field=wipo_field,
        jurisdiction_code=jurisdiction_code,
        year_from=year_from,
        year_to=year_to,
    )


@router.get("/{owner_id}/citation-fields", response_model=PortfolioSectionResponse)
def get_portfolio_citation_fields(
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    jurisdiction_code: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_fields(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        jurisdiction_code=jurisdiction_code,
        year_from=year_from,
        year_to=year_to,
    )


@router.get("/{owner_id}/citation-jurisdictions", response_model=PortfolioSectionResponse)
def get_portfolio_citation_jurisdictions(
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    wipo_field: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_jurisdictions(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        wipo_field=wipo_field,
        year_from=year_from,
        year_to=year_to,
    )


@router.get("/{owner_id}/citation-cpc-groups", response_model=PortfolioSectionResponse)
def get_portfolio_citation_cpc_groups(
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    wipo_field: str | None = None,
    jurisdiction_code: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_citation_cpc_groups(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        wipo_field=wipo_field,
        jurisdiction_code=jurisdiction_code,
        year_from=year_from,
        year_to=year_to,
    )


@router.get("/{owner_id}/filing-timeseries", response_model=PortfolioSectionResponse)
def get_portfolio_filing_timeseries(
    owner_id: str,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_filing_timeseries(owner_id=owner_id, year_from=year_from, year_to=year_to)


@router.get("/{owner_id}/status-timeseries", response_model=PortfolioSectionResponse)
def get_portfolio_status_timeseries(
    owner_id: str,
    year_from: int | None = None,
    year_to: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_status_timeseries(owner_id=owner_id, year_from=year_from, year_to=year_to)


@router.get("/{owner_id}/jurisdiction-unlocks", response_model=PortfolioSectionResponse)
def get_portfolio_jurisdiction_unlocks(
    owner_id: str,
    year_from: int | None = None,
    year_to: int | None = None,
    jurisdiction_limit: int = 20,
) -> PortfolioSectionResponse:
    return service.get_jurisdiction_unlock_history(
        owner_id=owner_id,
        year_from=year_from,
        year_to=year_to,
        jurisdiction_limit=jurisdiction_limit,
    )


@router.get("/{owner_id}/threats", response_model=PortfolioThreatResponse)
def get_portfolio_threats(
    owner_id: str,
    limit: int = 10,
    offset: int = 0,
    wipo_field: str | None = None,
) -> PortfolioThreatResponse:
    return service.get_threats(owner_id=owner_id, limit=limit, offset=offset, wipo_field=wipo_field)


@router.get("/{owner_id}/market-context", response_model=PortfolioSectionResponse)
def get_portfolio_market_context(
    owner_id: str,
    horizon: str = "3y",
    as_of_year: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_market_context(owner_id=owner_id, horizon=horizon, as_of_year=as_of_year)


@router.get("/{owner_id}/classification", response_model=PortfolioClassificationResponse)
def get_portfolio_classification(
    owner_id: str,
    as_of_year: int | None = None,
    limit: int = 10,
    offset: int = 0,
    classification_type: str = "CPC_MAIN_GROUP",
    timeseries_fields: int = 6,
    wipo_field: str | None = None,
) -> PortfolioClassificationResponse:
    return service.get_classification(
        owner_id=owner_id,
        as_of_year=as_of_year,
        limit=limit,
        offset=offset,
        classification_type=classification_type,
        timeseries_fields=timeseries_fields,
        wipo_field=wipo_field,
    )


@router.get("/{owner_id}/forecast", response_model=PortfolioForecastResponse)
def get_portfolio_forecast(
    owner_id: str,
    as_of_year: int | None = None,
    horizon: str = "3y",
) -> PortfolioForecastResponse:
    return service.get_forecast(owner_id=owner_id, as_of_year=as_of_year, horizon=horizon)


@router.get("/{owner_id}/forecast-contributors", response_model=PortfolioSectionResponse)
def get_portfolio_forecast_contributors(
    owner_id: str,
    horizon: str = "3y",
    contributor_scope: str = "phase03_future_citations",
    limit: int = 10,
    offset: int = 0,
) -> PortfolioSectionResponse:
    return service.get_forecast_contributors(
        owner_id=owner_id,
        horizon=horizon,
        contributor_scope=contributor_scope,
        limit=limit,
        offset=offset,
    )


@router.get("/{owner_id}/compare-timeslice", response_model=PortfolioSectionResponse)
def get_portfolio_compare_timeslice(
    owner_id: str,
    base_year: int | None = None,
    compare_year: int | None = None,
) -> PortfolioSectionResponse:
    return service.get_compare_timeslice(owner_id=owner_id, base_year=base_year, compare_year=compare_year)


@router.get("/{owner_id}/pending-grants", response_model=PortfolioSectionResponse)
def get_portfolio_pending_grants(
    owner_id: str,
    horizon: str = "24m",
    branch_jurisdiction_code: str | None = None,
    branch_wipo_field: str | None = None,
    branch_limit: int = 25,
) -> PortfolioSectionResponse:
    return service.get_pending_grants(
        owner_id=owner_id,
        horizon=horizon,
        branch_jurisdiction_code=branch_jurisdiction_code,
        branch_wipo_field=branch_wipo_field,
        branch_limit=branch_limit,
    )
