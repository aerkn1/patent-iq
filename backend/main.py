from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.v1.patents import router as patent_router
from api.v1.portfolios import router as portfolios_router
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
        logger.info("Startup: Cache verification complete. Backend ready.")
    except Exception as e:
        logger.error(f"Startup Failed: Could not initialize database: {e}")
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
    prefix="/api/v1",
    tags=["Patents"]
)

app.include_router(portfolios_router)