from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from application.services.market_intelligence_service import MarketIntelligenceService
from domain.errors import ValidationError

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-intelligence", tags=["Market"])


@router.get("/workspace")
async def get_market_workspace(
    market_state: str = Query("all", description="Market state filter"),
    segment_id: str | None = Query(None, description="Selected WIPO segment"),
    segment: str | None = Query(None, description="Legacy selected WIPO segment alias"),
):
    try:
        payload = MarketIntelligenceService().get_workspace(
            market_state=market_state,
            segment=segment_id or segment,
        )
        return JSONResponse(content=payload)
    except ValidationError as exc:
        logger.warning(
            "Invalid market workspace request",
            extra={"market_state": market_state, "segment_id": segment_id or segment},
        )
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_REQUEST", "message": str(exc)}},
        )
    except Exception:
        logger.exception(
            "Unhandled market workspace error",
            extra={"market_state": market_state, "segment_id": segment_id or segment},
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"}},
        )
