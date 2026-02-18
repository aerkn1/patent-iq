# application/services/portfolio_overview_service.py

from domain.errors import ValidationError, NotFoundError, DataUnavailableError, InternalServerError

from infrastructure.repositories.portfolio_master_repo import PortfolioMasterRepository
from infrastructure.repositories.portfolio_axis_repo import PortfolioAxisRepository
from infrastructure.repositories.portfolio_final_repo import PortfolioFinalRepository
from infrastructure.repositories.portfolio_rank_repo import PortfolioRankRepository
from infrastructure.repositories.portfolio_size_repo import PortfolioSizeRepository
from infrastructure.repositories.portfolio_peer_meta_repo import PortfolioPeerMetaRepository
from infrastructure.repositories.portfolio_industry_stats_repo import PortfolioIndustryStatsRepository
from infrastructure.repositories.portfolio_cpc_stats_repo import PortfolioCpcStatsRepository
from infrastructure.repositories.portfolio_industry_repo import PortfolioIndustryRepository
from infrastructure.repositories.portfolio_cpc_repo import PortfolioCpcRepository
from infrastructure.repositories.portfolio_family_metrics_repo import PortfolioFamilyMetricsRepository
from infrastructure.repositories.portfolio_grant_mix_repo import PortfolioGrantMixRepository
from infrastructure.repositories.portfolio_legal_repo import PortfolioLegalRepository


class PortfolioOverviewService:

    def __init__(self):
        self.master_repo = PortfolioMasterRepository()
        self.axis_repo = PortfolioAxisRepository()
        self.final_repo = PortfolioFinalRepository()
        self.rank_repo = PortfolioRankRepository()
        self.size_repo = PortfolioSizeRepository()
        self.peer_meta_repo = PortfolioPeerMetaRepository()
        self.cpc_stats_repo =  PortfolioCpcStatsRepository()
        self.ind_stats_repo = PortfolioIndustryStatsRepository()
        self.cpc_repo =  PortfolioCpcRepository()
        self.ind_repo = PortfolioIndustryRepository()
        self.family_metrics_repo = PortfolioFamilyMetricsRepository()
        self.grant_mix_repo = PortfolioGrantMixRepository()
        self.legal_repo = PortfolioLegalRepository()

    async def get_overview(self, owner_id: int) -> dict:
        if owner_id <= 0:
            raise ValidationError("owner_id must be positive")

        # --- Identity ---
        master = self.master_repo.get(owner_id)
        if master is None:
            raise NotFoundError(f"Portfolio {owner_id} not found")

        # --- Metrics ---
        axes = self.axis_repo.get(owner_id)
        final = self.final_repo.get(owner_id)
        rank = self.rank_repo.get(owner_id)
        size = self.size_repo.get(owner_id)
        peer_meta = self.peer_meta_repo.get(owner_id)
        cpc_stats = self.cpc_stats_repo.get(owner_id)
        ind_stats = self.ind_stats_repo.get(owner_id)
        cpc_top = self.cpc_repo.get_top(owner_id)
        cpc_top = self.cpc_repo.get_top(owner_id)
        ind_top = self.ind_repo.get_top(owner_id)
        
        # --- New Metrics ---
        family_metrics = self.family_metrics_repo.get(owner_id) or {}
        grant_mix_list = self.grant_mix_repo.get(owner_id) or []
        legal_metrics = self.legal_repo.get_legal_aggregation(owner_id) or {}

        

        if not all([axes, final, rank, size]):
            raise NotFoundError(f"Incomplete portfolio data for {owner_id}")

        # --- Assemble response ---
        total_patents = int(legal_metrics.get("n_patents") or size["n_patents"] or 0)
        abandoned_count = int(legal_metrics.get("abandoned_count") or 0)
        active_count = max(total_patents - abandoned_count, 0)

        return {
            "portfolio": {
                "owner_id": owner_id,
                "owner_name": master["owner_name"],
                "owner_type": master["owner_type"],
                "country": master["country"],
                 "size": {
                    "n_patents": size["n_patents"],
                    "n_unique_patents": size["n_unique_patents"],
                    "size_bucket": peer_meta["portfolio_size_bucket"] if peer_meta else "UNKNOWN",
                },
                "status_counts": {
                    "total": total_patents,
                    "active": active_count,
                    "abandoned": abandoned_count,
                },
            },
            "radar": {
              "technology": self._round3(rank["tech_axis_score_norm"]),
              "market": self._round3(rank["market_axis_score_norm"]),
              "blocking": self._round3(final["blocking_power_portfolio_pct"]),
              "legal": self._round3(final["legal_strength_portfolio"]),
              "licensing": self._round3(final["licensing_readiness_portfolio_pct"])
            },
            "strength": {
                "blocking_power": {
                    "raw": self._round3(final["blocking_power_portfolio"]),
                    "percentile": self._round3(final["blocking_power_portfolio_pct"])
                },
                "licensing_readiness": {
                    "raw": self._round3(final["licensing_readiness_portfolio"]),
                    "percentile": self._round3(final["licensing_readiness_portfolio_pct"])
                },
                "legal_strength": {
                    "raw": self._round3(final["legal_strength_portfolio"]),
                },
                "portfolio_general": {
                    "power_score": self._round3(final["portfolio_power_score_pct"]),
                }
            },
            "technology_profile": {
                "axis_score": round(rank["tech_axis_score_norm"], 3),
                "diversification": self._format_diversification(cpc_stats),
                "top_cpc_classes": cpc_top,
            },

            "market_profile": {
                "axis_score": round(rank["market_axis_score_norm"], 3),
                "diversification": self._format_diversification(ind_stats),
                "top_industries": ind_top,
            },


            "ranking": {
                "portfolio_power_score": self._round3(rank["portfolio_power_score"]),
                "percentile_global": self._round3(rank["portfolio_percentile"]),
                "rank_global": int(rank["portfolio_rank"]),
                "tier": rank["portfolio_tier"],
            },

            "health": {
                "abandoned_ratio": self._round3(final["abandoned_ratio"]),
                "legal_unknown_ratio": self._round3(final["legal_unknown_ratio"]),
            },
            "global_positioning": {
                "portfolio_percentile": self._round3(rank["portfolio_percentile"]),
                "portfolio_rank": int(rank["portfolio_rank"]),
                "portfolio_tier": rank["portfolio_tier"],
            },
            "peer_positioning": {
                "peer_group_id": peer_meta["peer_group_id"],
                "peer_percentile": self._round3(peer_meta["peer_percentile"]),
                "peer_class": peer_meta["peer_class"],
                "peer_zscore": self._round3(peer_meta["peer_zscore"]),
                "n_peers": int(peer_meta["n_peers"]),
            },
            "metadata": {
                "contract_version": "v1",
                "confidence": "HIGH",
            },
            "family_metrics": {
                "active_patent_families": family_metrics.get("n_families_unique", 0),
                "effective_patents": family_metrics.get("n_patents_effective", 0),
                "avg_family_size": self._round3(family_metrics.get("family_members_count_avg", 0)),
                "avg_jurisdiction_reach": self._round3(family_metrics.get("family_jurisdiction_count_avg", 0)),
                "major_office_coverage": self._round3(family_metrics.get("major_office_grant_coverage_index", 0)),
            },
            "grant_coverage": {
                "EP": self._round3((family_metrics.get("has_ep_grant_share", 0) or 0) * 100),
                "US": self._round3((family_metrics.get("has_us_grant_share", 0) or 0) * 100),
                "CN": self._round3((family_metrics.get("has_cn_grant_share", 0) or 0) * 100),
                "JP": self._round3((family_metrics.get("has_jp_grant_share", 0) or 0) * 100),
                "KR": self._round3((family_metrics.get("has_kr_grant_share", 0) or 0) * 100),
            },
            "grant_mix": [
                {
                    "publn_auth": x["publn_auth"],
                    "granted_share": self._round3(x["granted_share"])
                }
                for x in grant_mix_list
            ]
        }

    # ---------- helpers ----------
    
    @staticmethod
    def _format_diversification(stats: dict) -> dict:
        ent = stats["entropy_norm"]
        
        if ent < 0.35:
            label = "HIGHLY_FOCUSED"
        elif ent < 0.55:
            label = "FOCUSED"
        elif ent < 0.75:
            label = "MODERATELY_DIVERSIFIED"
        else:
            label = "BROADLY_DIVERSIFIED"
        
        return {
            "entropy_norm": round(ent, 3),
            "top_k_share": round(stats["top_k_share"], 3),
            "long_tail_share": round(stats["long_tail_share"], 3),
            "interpretation": label,
            }
    
    @staticmethod
    def _round3(value) -> float:
        try:
            return round(float(value), 3)
        except Exception:
            return 0.0