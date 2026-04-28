from fastapi import APIRouter

from api.v1.compare import router as compare_router
from api.v1.data_room import router as data_room_router
from api.v1.families import router as families_router
from api.v1.market_intelligence import router as market_intelligence_router
from api.v1.portfolios import router as portfolios_router
from api.v1.publications import router as publications_router
from api.v1.semantic import router as semantic_router
from api.v1.stats import router as stats_router

v1_router = APIRouter()
v1_router.include_router(portfolios_router)
v1_router.include_router(families_router)
v1_router.include_router(publications_router)
v1_router.include_router(market_intelligence_router)
v1_router.include_router(compare_router)
v1_router.include_router(semantic_router)
v1_router.include_router(data_room_router)
v1_router.include_router(stats_router)
