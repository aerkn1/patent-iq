# main.py
from fastapi import FastAPI
from api.v1.patents import router as patent_router
from api.v1.portfolios import router as portfolios_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Patent Intelligence API",
    version="v1"
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