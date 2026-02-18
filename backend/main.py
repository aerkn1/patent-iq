from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()
from api.v1.patents import router as patent_router
from api.v1.portfolios import router as portfolios_router
from api.v1.stats import router as stats_router
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.duckdb.connection import DuckDBConnection
import logging

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Warm up the cache
    logger.info("Startup: Initializing DuckDB and checking cache...")
    try:
        # This triggers CacheManager.ensure_cache()
        DuckDBConnection.get_connection()
        logger.info("Startup: Cache verification complete.")

        # Load ML models for citation forecast
        from infrastructure.ml.model_registry import ModelRegistry
        ModelRegistry.initialize()
        logger.info("Startup: ML models loaded. Forecast ready.")

        logger.info("Startup: Backend ready.")
    except Exception as e:
        logger.error(f"Startup Failed: Could not initialize: {e}")
        raise e
    yield
    # Shutdown logic if needed (e.g. closing connection)
    
app = FastAPI(
    title="Patent Intelligence API",
    version="v1",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    patent_router,
    prefix="/api/v1"
)

app.include_router(portfolios_router)
app.include_router(stats_router, prefix="/api/v1")