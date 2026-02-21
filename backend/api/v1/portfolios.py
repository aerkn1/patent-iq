from typing import Optional

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from application.services.portfolio_discovery_service import PortfolioDiscoveryService
from application.services.portfolio_page_service import PortfolioOverviewService
from application.services.portfolio_analytics_service import PortfolioAnalyticsService
from application.services.portfolio_patents_service import PortfolioPatentsService
from application.services.portfolio_licensing_service import PortfolioLicensingService
from application.services.portfolio_citation_service import PortfolioCitationService
from application.services.portfolio_forecast_service import PortfolioForecastService

from domain.schemas.portfolio_citation import PortfolioCitationMetricsResponse, PortfolioCitationTimeSeriesResponse
from domain.schemas.forecast import PortfolioForecastResponse as PortfolioForecastSchema
from domain.errors import ValidationError, NotFoundError, DataUnavailableError, InternalServerError

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portfolios", tags=["Portfolios"])


@router.get("/{owner_id}/overview")
async def get_portfolio_overview(
    owner_id: int = Path(..., gt=0, description="Portfolio owner_id")
):
    """
    Portfolio Overview v1
    """
    try:
        service = PortfolioOverviewService()
        result = await service.get_overview(owner_id)
        return JSONResponse(content=result)

    except ValidationError as e:
        logger.warning(
            "Portfolio overview validation error",
            extra={"owner_id": owner_id, "error": str(e)},
        )
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_REQUEST", "message": str(e)}},
        )

    except NotFoundError as e:
        logger.info(
            "Portfolio not found",
            extra={"owner_id": owner_id},
        )
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": str(e)}},
        )

    except Exception as e:
        logger.exception(
            "Unhandled portfolio overview error",
            extra={"owner_id": owner_id},
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )

@router.get("/{owner_id}/analytics")
async def get_portfolio_analytics(owner_id: int):
    try:
        result = await PortfolioAnalyticsService().get_analytics(owner_id)
        return JSONResponse(content=result)
        
    except NotFoundError as e:
        logger.info(
            "Portfolio not found",
            extra={"owner_id": owner_id},
        )
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": str(e)}},
        )

    except Exception as e:
        logger.exception(
            "Unhandled portfolio overview error",
            extra={"owner_id": owner_id},
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )

@router.get("/discover")
async def discover_portfolios(
    dimension: str = Query(..., regex="^(CPC|INDUSTRY|COUNTRY)$"),
    value: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        service = PortfolioDiscoveryService()
        
        result =await service.discover(
            dimension=dimension,
            value=value,
            limit=limit
        )

        return JSONResponse(content=result)

    except NotFoundError as e:
        logger.info(
            "Portfolio discovery not found",
        )
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": str(e)}},
        )

    except Exception as e:
        logger.exception(
            "Unhandled portfolio overview error",
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )


@router.get("/search")
async def search_portfolios(
    q: str = Query(..., min_length=2, description="Search query for portfolio name"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    try:
        service = PortfolioDiscoveryService()
        return await service.search_portfolios(query=q, limit=limit)
    except Exception as e:
        logger.exception("Portfolio search failed", extra={"query": q})
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )


@router.get("/{owner_id}/patents")
async def get_portfolio_patents(
    owner_id: int,
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    sort: str = "blocking_power_pct",
    order: str = "desc",
    limit: int = 25,
    offset: int = 0,
):
    filters = {
        "category": category,
        "jurisdiction": jurisdiction,
    }

    try:
        service = PortfolioPatentsService()
        return service.get_patents(
            owner_id=owner_id,
            filters=filters,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
        )
        
    except NotFoundError as e:
        logger.info(
            "Portfolio discovery not found",
        )
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": str(e)}},
        )

    except Exception as e:
        logger.exception(
            "Unhandled portfolio overview error",
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )


@router.get("/{owner_id}/licensing-candidates")
async def get_portfolio_licensing_candidates(
    owner_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    min_industry_overlap: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_cpc_overlap: Optional[float] = Query(None, ge=0.0, le=1.0),
):
    service = PortfolioLicensingService()
    return service.get_candidates(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        min_industry_overlap=min_industry_overlap,
        min_cpc_overlap=min_cpc_overlap,
    )

@router.get("/{owner_id}/citation-metrics", response_model=PortfolioCitationMetricsResponse)
async def get_portfolio_citation_metrics(owner_id: int):
    try:
        service = PortfolioCitationService()
        return service.get_citation_metrics(owner_id)
    except NotFoundError as e:
        return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "message": str(e)})
    except Exception as e:
        logger.exception("Error fetching portfolio citation metrics", extra={"owner_id": owner_id})
        return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR", "message": "Unexpected error"})


@router.get("/{owner_id}/citation-ts", response_model=PortfolioCitationTimeSeriesResponse)
async def get_portfolio_citation_timeseries(owner_id: int):
    try:
        service = PortfolioCitationService()
        return service.get_citation_timeseries(owner_id)
    except Exception as e:
        logger.exception("Error fetching portfolio citation timeseries", extra={"owner_id": owner_id})
        return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR", "message": "Unexpected error"})
@router.get("/{owner_id}/citation-forecast-ts")
async def get_portfolio_citation_forecast_timeseries(
    owner_id: int = Path(..., gt=0, description="Portfolio owner_id"),
    horizon: str = Query("3y", pattern="^(3y|5y)$"),
):
    try:
        service = PortfolioCitationService()
        return await service.get_citation_forecast_ts(owner_id, horizon)
    except Exception as e:
        logger.exception("Error fetching portfolio citation forecast timeseries", extra={"owner_id": owner_id})
        return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR", "message": "Unexpected error"})




@router.get("/{owner_id}/forecast", response_model=PortfolioForecastSchema)
async def get_portfolio_forecast(
    owner_id: int = Path(..., gt=0, description="Portfolio owner_id"),
    horizon: str = Query(..., pattern="^(3y|5y)$", description="Forecast horizon"),
    segments: bool = Query(
        False,
        description="Whether to include segment distributions in the response",
    ),
    segments_top_k: int = Query(
        10,
        ge=3,
        le=50,
        description="Keep top-K CPC subclasses; fold the remainder into OTHER",
    ),
    cpc_top_n_per_patent: int = Query(
        5,
        ge=1,
        le=20,
        description="Limit CPC rows per patent for performance; remainder goes into OTHER",
    ),
):
    try:
        payload = await PortfolioForecastService().get_forecast(
            owner_id=owner_id,
            horizon=horizon,
            segments=segments,
            segments_top_k=segments_top_k,
            cpc_top_n_per_patent=cpc_top_n_per_patent,
        )
        return JSONResponse(status_code=200, content=payload)

    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"error": "INVALID_REQUEST", "message": str(e)},
        )

    except NotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": "NOT_FOUND", "message": str(e)},
        )

    except Exception:
        logger.exception("Unhandled portfolio forecast error", extra={"owner_id": owner_id})
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"},
        )
