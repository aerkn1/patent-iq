from fastapi import APIRouter

from application.services.market_intelligence import MarketIntelligenceService
from domain.schemas.market_intelligence import MarketOverviewResponse, MarketSectionResponse, MarketWorkspaceResponse

router = APIRouter(prefix="/market-intelligence", tags=["market_intelligence"])
service = MarketIntelligenceService()


@router.get("/overview", response_model=MarketOverviewResponse)
def get_market_overview(as_of_year: int | None = None) -> MarketOverviewResponse:
    return service.get_overview(as_of_year=as_of_year)


@router.get("/workspace", response_model=MarketWorkspaceResponse)
def get_market_workspace(
    market_state: str = "all",
    segment_id: str | None = None,
    as_of_year: int | None = None,
) -> MarketWorkspaceResponse:
    return service.get_workspace(market_state=market_state, segment_id=segment_id, as_of_year=as_of_year)


@router.get("/overview-history", response_model=MarketSectionResponse)
def get_market_overview_history() -> MarketSectionResponse:
    return service.get_market_overview_history()


@router.get("/leading-jurisdictions", response_model=MarketSectionResponse)
def get_market_leading_jurisdictions(
    as_of_year: int | None = None,
    limit_per_field: int = 5,
) -> MarketSectionResponse:
    return service.get_leading_jurisdictions(as_of_year=as_of_year, limit_per_field=limit_per_field)


@router.get("/segments", response_model=MarketSectionResponse)
def get_market_segments() -> MarketSectionResponse:
    return service.get_section(section="segments")


@router.get("/segments/{segment_id}", response_model=MarketSectionResponse)
def get_market_segment(segment_id: str) -> MarketSectionResponse:
    return service.get_section(section="segment_detail", segment_id=segment_id)


@router.get("/segments/{segment_id}/timeseries", response_model=MarketSectionResponse)
def get_market_segment_timeseries(segment_id: str) -> MarketSectionResponse:
    return service.get_section(section="segment_timeseries", segment_id=segment_id)


@router.get("/segments/{segment_id}/owners", response_model=MarketSectionResponse)
def get_market_segment_owners(segment_id: str) -> MarketSectionResponse:
    return service.get_section(section="segment_owners", segment_id=segment_id)


@router.get("/segments/{segment_id}/jurisdictions", response_model=MarketSectionResponse)
def get_market_segment_jurisdictions(segment_id: str) -> MarketSectionResponse:
    return service.get_section(section="segment_jurisdictions", segment_id=segment_id)


@router.get("/segments/{segment_id}/cpc-jurisdictions", response_model=MarketSectionResponse)
def get_market_segment_cpc_jurisdictions(
    segment_id: str,
    as_of_year: int | None = None,
    cpc_main_group: str | None = None,
    jurisdiction_code: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_segment_cpc_jurisdictions(
        segment_id=segment_id,
        as_of_year=as_of_year,
        cpc_main_group=cpc_main_group,
        jurisdiction_code=jurisdiction_code,
        limit=limit,
        offset=offset,
    )


@router.get("/segments/{segment_id}/cpc-owners", response_model=MarketSectionResponse)
def get_market_segment_cpc_owners(
    segment_id: str,
    cpc_main_group: str,
    as_of_year: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_segment_cpc_owners(
        segment_id=segment_id,
        cpc_main_group=cpc_main_group,
        as_of_year=as_of_year,
        limit=limit,
        offset=offset,
    )


@router.get("/segments/{segment_id}/cpc-citing-owners", response_model=MarketSectionResponse)
def get_market_segment_cpc_citing_owners(
    segment_id: str,
    cpc_main_group: str,
    as_of_year: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_segment_cpc_citing_owners(
        segment_id=segment_id,
        cpc_main_group=cpc_main_group,
        as_of_year=as_of_year,
        limit=limit,
        offset=offset,
    )


@router.get("/segments/{segment_id}/applications-grants", response_model=MarketSectionResponse)
def get_market_segment_applications_grants(
    segment_id: str,
    year_from: int | None = None,
    year_to: int | None = None,
    jurisdiction_limit: int = 12,
) -> MarketSectionResponse:
    return service.get_segment_applications_grants(
        segment_id=segment_id,
        year_from=year_from,
        year_to=year_to,
        jurisdiction_limit=jurisdiction_limit,
    )


@router.get("/segments/{segment_id}/grant-mix", response_model=MarketSectionResponse)
def get_market_segment_grant_mix(
    segment_id: str,
    as_of_year: int | None = None,
    limit: int = 12,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_segment_grant_mix(segment_id=segment_id, as_of_year=as_of_year, limit=limit, offset=offset)


@router.get("/segments/{segment_id}/unitary-patent", response_model=MarketSectionResponse)
def get_market_segment_unitary_patent(
    segment_id: str,
    jurisdiction_limit: int = 18,
) -> MarketSectionResponse:
    return service.get_segment_unitary_patent_summary(segment_id=segment_id, jurisdiction_limit=jurisdiction_limit)


@router.get("/cpc-trends", response_model=MarketSectionResponse)
def get_market_cpc_trends(
    segment_id: str | None = None,
    as_of_year: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_cpc_trends(segment_id=segment_id, as_of_year=as_of_year, limit=limit, offset=offset)


@router.get("/citation-trends", response_model=MarketSectionResponse)
def get_market_citation_trends(
    segment_id: str | None = None,
    as_of_year: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_citation_trends(segment_id=segment_id, as_of_year=as_of_year, limit=limit, offset=offset)


@router.get("/citation-jurisdictions", response_model=MarketSectionResponse)
def get_market_citation_jurisdictions(
    segment_id: str | None = None,
    as_of_year: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_citation_jurisdictions(segment_id=segment_id, as_of_year=as_of_year, limit=limit, offset=offset)


@router.get("/citation-attackers", response_model=MarketSectionResponse)
def get_market_citation_attackers(
    segment_id: str | None = None,
    as_of_year: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> MarketSectionResponse:
    return service.get_citation_attackers(segment_id=segment_id, as_of_year=as_of_year, limit=limit, offset=offset)
