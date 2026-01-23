from infrastructure.repositories.portfolio_patents_repo import PortfolioPatentsRepository
from infrastructure.repositories.portfolio_category_repo import PortfolioCategoryRepository
from infrastructure.repositories.portfolio_citations_repo import PortfolioCitationsRepository

from infrastructure.repositories.portfolio_legal_repo import PortfolioLegalRepository
from infrastructure.repositories.portfolio_blocking_repo import PortfolioBlockingRepository
from infrastructure.repositories.portfolio_innovation_repo import PortfolioInnovationRepository

class PortfolioAnalyticsService:
    def __init__(self):
        self.patents_repo = PortfolioPatentsRepository()
        self.category_repo = PortfolioCategoryRepository()
        self.citations_repo = PortfolioCitationsRepository()
        self.legal_repo = PortfolioLegalRepository()
        self.blocking_repo = PortfolioBlockingRepository()
        self.innovation_repo = PortfolioInnovationRepository()

    def _safe_share(self, n: int, total: int) -> float:
        return float(n) / float(total) if total > 0 else 0.0

    def _portfolio_category_label(self, shares: dict[str, float]) -> str:
        crown = shares.get("CROWN_JEWEL", 0.0)
        fortress = shares.get("FORTRESS", 0.0)
        hidden = shares.get("HIDDEN_GEM", 0.0)
        deadwood = shares.get("DEADWOOD", 0.0)
        core = shares.get("CORE_ASSET", 0.0)

        if crown >= 0.05 and fortress >= 0.20:
            return "FORTRESS_WITH_CROWN_JEWELS"
        if hidden >= 0.02 and deadwood <= 0.60:
            return "HIDDEN_GEM_PORTFOLIO"
        if deadwood >= 0.80:
            return "DEADWOOD_HEAVY"
        if core >= 0.20:
            return "CORE_ASSET_HEAVY"
        return "MIXED"

    async def get_analytics(self, owner_id: int) -> dict:
        if owner_id <= 0:
            # use your ValidationError in real code
            raise ValueError("owner_id must be positive")

        appln_ids = self.patents_repo.list_appln_ids(owner_id)
        if not appln_ids:
            # use your NotFoundError in real code
            raise KeyError(f"Portfolio {owner_id} not found or empty")

        counts = self.category_repo.get_category_counts(owner_id)
        total = sum(counts.values())
        shares = {k: round(self._safe_share(v, total), 4) for k, v in counts.items()}

        totals = self.citations_repo.get_totals(owner_id)

        backward_total = totals["backward_total"]
        forward_total = totals["forward_total"]
        
        self_forward_total = totals["self_forward_total"]
        self_backward_total = totals["self_backward_total"]
        
        self_forward_rate = round(self_forward_total / forward_total, 4) if forward_total > 0 else 0.0
        self_backward_rate = round(self_backward_total / backward_total, 4) if backward_total > 0 else 0.0 

        legal_raw = self.legal_repo.get_legal_aggregation(owner_id)
        blocking_drivers = self.blocking_repo.get_blocking_drivers(owner_id)
        top_blocking = self.blocking_repo.get_top_blocking_patents(owner_id)
        innovation = self.innovation_repo.get_innovation_aggregation(owner_id)
        top_innovative = self.innovation_repo.get_top_innovative_patents(owner_id)

        return {
            "portfolio": {"owner_id": owner_id},
            "categories": {
                "counts": counts,
                "shares": shares,
                "portfolio_category": self._portfolio_category_label(shares),
            },
            "citations": {
                "forward_total": forward_total,
                "backward_total": backward_total,
                "backward_npl_total": totals["backward_npl_total"],
                "self_citations": {
                    "forward_total": self_forward_total,
                    "backward_total": self_backward_total,
                    "self_forward_rate": self_forward_rate,
                    "self_backward_rate": self_backward_rate,
                    "avg_self_forward_rate": round(totals["avg_self_forward_rate"], 4),
                    "avg_self_blocking_rate": round(totals["avg_self_blocking_rate"], 4),
                },
                "distribution": {
                    "forward_buckets": self.citations_repo.get_forward_buckets(owner_id),
                    "backward_buckets": self.citations_repo.get_backward_buckets(owner_id),
                }
            },
            "legal": self._legal_profile(legal_raw),
            "blocking_power": {
                "drivers": blocking_drivers,
                "dominant_driver": self._dominant_blocking_driver(blocking_drivers),
                "top_patents": top_blocking,
            },
            "innovation": {
                **innovation,
                "top_patents": top_innovative,
            },
            "metadata": {
                "contract_version": "v1",
                "data_snapshot": "2025-01-31",
                "confidence": "HIGH",
            },
        }


    @staticmethod
    def _legal_profile(legal: dict) -> dict:
        abandoned = legal["abandoned_ratio"]
        unknown = legal["legal_unknown_ratio"]
        strength = legal["legal_strength_avg"]
    
        if abandoned > 0.6:
            profile = "WEAKLY_MAINTAINED"
        elif strength >= 0.7 and abandoned < 0.2:
            profile = "DEFENSIVELY_MAINTAINED"
        else:
            profile = "SELECTIVELY_MAINTAINED"
    
        return {
            **legal,
            "maintenance_profile": profile
        }
    
    @staticmethod
    def _dominant_blocking_driver(drivers: dict) -> str:
        filtered = {k: abs(v) for k, v in drivers.items()}
        return max(filtered, key=filtered.get) if filtered else "UNKNOWN"