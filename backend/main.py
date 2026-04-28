import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.settings import get_settings
from api.v1.patents import router as patent_router
from api.v1.portfolios import router as portfolios_router
from api.v1.stats import router as stats_router
from api.v1.market import router as market_router
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.duckdb.connection import DuckDBConnection
import logging

logger = logging.getLogger("uvicorn")
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Warm up the cache
    logger.info("Startup: Initializing DuckDB and checking cache...")
    try:
        # This triggers CacheManager.ensure_cache()
        DuckDBConnection.get_connection()
        logger.info("Startup: Cache verification complete.")

        # Load ML models for citation forecast
        if settings.load_ml_models_on_startup:
            from infrastructure.ml.model_registry import ModelRegistry
            ModelRegistry.initialize()
            logger.info("Startup: ML models loaded. Forecast ready.")
        else:
            logger.info("Startup: ML model loading skipped by config.")

        logger.info("Startup: Backend ready.")
    except Exception as e:
        logger.error(f"Startup Failed: Could not initialize: {e}")
        raise e
    yield
    # Shutdown: close DuckDB connection
    DuckDBConnection.close()
    logger.info("Shutdown: DuckDB connection closed.")
    
app = FastAPI(
    title="Patent Intelligence API",
    version="v1",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patent_router, prefix=settings.api_v1_prefix)
app.include_router(portfolios_router, prefix=settings.api_v1_prefix)
app.include_router(stats_router, prefix=settings.api_v1_prefix)
app.include_router(market_router, prefix=settings.api_v1_prefix)
