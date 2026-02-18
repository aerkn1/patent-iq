# application/services/portfolio_discovery_service.py

import math
from typing import Optional

from infrastructure.repositories.portfolio_cpc_repo import PortfolioCpcRepository
from infrastructure.repositories.portfolio_industry_repo import PortfolioIndustryRepository
from infrastructure.repositories.portfolio_rank_repo import PortfolioRankRepository
from infrastructure.repositories.portfolio_master_repo import PortfolioMasterRepository
from infrastructure.repositories.portfolio_country_repo import PortfolioCountryRepository
from infrastructure.repositories.portfolio_legal_repo import PortfolioLegalRepository

class PortfolioDiscoveryService:

    def __init__(self):
        self.cpc_repo = PortfolioCpcRepository()
        self.industry_repo = PortfolioIndustryRepository()
        self.rank_repo = PortfolioRankRepository()
        self.master_repo = PortfolioMasterRepository()
        self.country_repo = PortfolioCountryRepository()
        self.legal_repo = PortfolioLegalRepository()

    def _empty_response(self, dimension: str, value: str, limit: int) -> dict:
        return {
            "query": {
                "dimension": dimension,
                "value": value,
                "limit": limit
            },
            "results": [],
            "metadata": {
                "contract_version": "v1"
            }
        }

    def _adjusted_power_score(self, portfolio: dict, active_count: Optional[float] = None) -> float:
        power_pct = float(portfolio.get("portfolio_power_score_pct") or 0.0)
        n_patents = float(active_count if active_count is not None else portfolio.get("n_patents") or 0.0)
        return power_pct * math.log(1.0 + n_patents)

    async def discover(self, dimension: str, value: str, limit: int) -> dict:

        if dimension == "CPC":
            owner_ids = self.cpc_repo.get_owners_by_cpc(value, limit=limit)
        elif dimension == "INDUSTRY":
            owner_ids = self.industry_repo.get_owners_by_industry(value, limit=limit)
        else:
            owner_ids = self.country_repo.get_by_country(value)

        if not owner_ids:
            return self._empty_response(dimension, value, limit)

        portfolios = self.rank_repo.get_by_owner_ids(owner_ids)
        legal_map = self.legal_repo.get_legal_aggregations(owner_ids)

        portfolios = sorted(
            portfolios,
            key=lambda p: self._adjusted_power_score(
                p,
                active_count=max(
                    (legal_map.get(p["owner_id"], {}).get("n_patents", 0)
                     - legal_map.get(p["owner_id"], {}).get("abandoned_count", 0)),
                    0,
                )
                if p.get("owner_id") in legal_map
                else None,
            ),
            reverse=True
        )[:limit]

        owner_names = self.master_repo.get_owner_names(
            [p["owner_id"] for p in portfolios]
        )

        results = []
        for i, p in enumerate(portfolios, start=1):
            legal = legal_map.get(p["owner_id"], {})
            active_count = max(int(legal.get("n_patents", 0) - legal.get("abandoned_count", 0)), 0) if legal else None
            adjusted_score = self._adjusted_power_score(p, active_count=active_count)
            results.append({
                "rank": i,
                "owner_id": p["owner_id"],
                "owner_name": owner_names.get(p["owner_id"], "UNKNOWN"),
                "n_patents": p["n_patents"],
                "portfolio_power_pct": round(p["portfolio_power_score_pct"], 2),
                "adjusted_power_score": round(adjusted_score, 2),
                "portfolio_tier": p["portfolio_tier"],
                "peer_class": p.get("peer_class"),
            })

        return {
            "query": {
                "dimension": dimension,
                "value": value,
                "limit": limit
            },
            "results": results,
            "metadata": {
                "contract_version": "v1",
                "data_snapshot": "2025-01-31"
            }
        }



    async def search_portfolios(self, query: str, limit: int = 20) -> dict:
        if not query or len(query.strip()) < 2:
            return {"results": []}

        # Search master table
        raw_results = self.master_repo.search_by_name(query, limit=limit)
        
        if not raw_results:
            return {"results": []}

        # Get enriched data for these portfolios (ranking, etc.)
        owner_ids = [r["owner_id"] for r in raw_results]
        portfolios = self.rank_repo.get_by_owner_ids(owner_ids)
        legal_map = self.legal_repo.get_legal_aggregations(owner_ids)
        
        # Create a map for quick lookup
        rank_map = {p["owner_id"]: p for p in portfolios}

        results = []
        for r in raw_results:
            owner_id = r["owner_id"]
            rank_data = rank_map.get(owner_id, {})
            legal = legal_map.get(owner_id, {})
            active_count = max(int(legal.get("n_patents", 0) - legal.get("abandoned_count", 0)), 0) if legal else None
            adjusted_score = self._adjusted_power_score(rank_data, active_count=active_count) if rank_data else 0.0
            
            results.append({
                "owner_id": owner_id,
                "owner_name": r["owner_name"],
                "country": r.get("country"),
                "n_patents": rank_data.get("n_patents", 0),
                "portfolio_power_pct": round(rank_data.get("portfolio_power_score_pct", 0), 2),
                "adjusted_power_score": round(adjusted_score, 2),
                "portfolio_tier": rank_data.get("portfolio_tier", "UNKNOWN"),
            })
            
        # Re-sort by relevance (match length) and then power
        # Already sorted by length in repo, let's keep that but prioritize power slightly? 
        # Actually client usually wants closest name match first.
            
        return {
            "query": query,
            "results": results
        }
        