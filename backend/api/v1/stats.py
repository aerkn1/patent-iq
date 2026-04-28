from fastapi import APIRouter, Depends
from infrastructure.repositories.patent_core_repo import PatentCoreRepository
from infrastructure.repositories.portfolio_master_repo import PortfolioMasterRepository

from infrastructure.ml.model_registry import ModelRegistry

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/")
async def get_global_stats(
    patent_repo: PatentCoreRepository = Depends(PatentCoreRepository),
    portfolio_repo: PortfolioMasterRepository = Depends(PortfolioMasterRepository)
):
    total_patents = patent_repo.get_total_count()
    total_portfolios = portfolio_repo.get_total_count()

    try:
        registry = ModelRegistry.get()
        models_status = {
            "3y": "3y" in registry.models,
            "5y": "5y" in registry.models,
        }
    except RuntimeError:
        # In case registry is not initialized yet
        models_status = {"3y": False, "5y": False}
    
    return {
        "total_patents": total_patents,
        "total_portfolios": total_portfolios,
        # Harcoded for now as it's not dynamic, but could be in future
        "blocking_events": "500K+", 
        "ml_models": 3, # Keep for legacy compat if needed, or remove? User asked to replace. I'll keep it but we won't use it on UI.
        "models_status": models_status
    }
