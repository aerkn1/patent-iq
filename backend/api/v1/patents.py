from typing import Optional
import logging
from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from application.services.patent_page_service import PatentPageService

from domain.schemas.forecast import CitationForecastTimeSeriesResponse, PatentForecastResponse
from domain.errors import ValidationError, NotFoundError, DataUnavailableError, InternalServerError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patents", tags=["Patents"])



@router.get("/search")
async def search_patents(
    q: str = Query(..., min_length=2, description="Search query for patent publication ID"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    try:
        service = PatentPageService()
        return await service.search_patents(query=q, limit=limit)
    except Exception:
        logger.exception("Patent search failed", extra={"query": q})
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )


@router.get(
    "/{appln_id}"
)
async def get_patent_page(
    appln_id: int = Path(..., ge=1, description="PATSTAT appln_id")
):
    logger.info("Patent page requested", extra={"appln_id": appln_id})

    try:
        return await PatentPageService().get_overview(appln_id)

    except ValidationError as e:
        logger.warning("Validation error", extra={"appln_id": appln_id, "error": str(e)})
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_ARGUMENT", "message": str(e)}},
        )

    except NotFoundError as e:
        logger.info("Patent not found", extra={"appln_id": appln_id})
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "PATENT_NOT_FOUND", "message": str(e)}},
        )

    except DataUnavailableError as e:
        logger.error("Dependency unavailable", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "DATA_UNAVAILABLE", "message": "Data temporarily unavailable"}},
        )

    except Exception:
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )

@router.get("/{appln_id}/analysis")
async def get_patent_analysis(
    appln_id: int = Path(..., ge=1, description="Application ID")
):
    try:
        payload = await PatentPageService().get_analysis_2(appln_id)
        return JSONResponse(status_code=200, content=payload)

    except ValidationError as e:
        logger.warning("Validation error", extra={"appln_id": appln_id, "error": str(e)})
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_ARGUMENT", "message": str(e)}})

    except NotFoundError as e:
        logger.info("Patent not found", extra={"appln_id": appln_id})
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "PATENT_NOT_FOUND", "message": str(e)}})

    except InternalServerError as e:
        logger.error("Internal error appln_id")
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_SERVICE_ERROR", "message": str(e)}})


@router.get("/{appln_id}/citation-metrics")
async def get_citation_metrics(
    appln_id: int = Path(..., ge=1, description="Application ID")
):
    try:
        payload = await PatentPageService().get_citation_metrics(appln_id)
        return JSONResponse(status_code=200, content=payload)
    
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_ARGUMENT", "message": str(e)}})

    except NotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "METRICS_NOT_FOUND", "message": str(e)}})

    except Exception as e:
        logger.exception("Error fetching citation metrics")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}})

@router.get("/{appln_id}/citation-ts")
async def get_citation_timeseries(
    appln_id: int = Path(..., ge=1, description="Application ID")
):
    try:
        payload = await PatentPageService().get_citation_timeseries(appln_id)
        return JSONResponse(status_code=200, content=payload)

    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_ARGUMENT", "message": str(e)}})

    except NotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "METRICS_NOT_FOUND", "message": str(e)}})

    except Exception as e:
        logger.exception("Error fetching citation timeseries")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}})



@router.get("/{appln_id}/citation-forecast-ts", response_model=CitationForecastTimeSeriesResponse)
async def get_citation_forecast_ts(
    appln_id: int = Path(..., ge=1, description="Application ID"),
    horizon: str = Query("3y", pattern="^(3y|5y)$"),
):
    try:
        return await PatentPageService().get_citation_forecast_ts(appln_id, horizon)
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"error": {"code": "INVALID_ARGUMENT", "message": str(e)}})
    except NotFoundError as e:
        return JSONResponse(status_code=404, content={"error": {"code": "METRICS_NOT_FOUND", "message": str(e)}})
    except Exception as e:
        logger.exception("Error fetching citation forecast timeseries")
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}})



@router.get("/{appln_id}/forecast", response_model=PatentForecastResponse)
async def get_patent_forecast(
    appln_id: int = Path(..., ge=1, description="Application ID"),
    horizon: str = Query("3y", pattern="^(3y|5y)$"),
):
    try:
        return await PatentPageService().get_patent_forecast(appln_id, horizon)
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"error": {"code": "INVALID_ARGUMENT", "message": str(e)}})
    except NotFoundError as e:
        return JSONResponse(status_code=404, content={"error": {"code": "METRICS_NOT_FOUND", "message": str(e)}})
    except Exception as e:
        logger.exception("Error fetching patent forecast")
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}})



