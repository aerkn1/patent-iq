from __future__ import annotations

from typing import Any, Optional
from infrastructure.repositories.portfolio_licensing_repo import (
    PortfolioLicensingRepository,
)

class PortfolioLicensingService:
    def __init__(self) -> None:
        self.repo = PortfolioLicensingRepository()

    @staticmethod
    def _safe_list(v: Any) -> list[str]:
        # DuckDB might return LIST as Python list already; if it’s a string, keep it as single-item list.
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        return [str(v)]

    @staticmethod
    def _round(v: Any, nd: int = 4) -> Optional[float]:
        if v is None:
            return None
        try:
            return round(float(v), nd)
        except Exception:
            return None

    def get_candidates(
        self,
        owner_id: int,
        limit: int = 50,
        offset: int = 0,
        min_industry_overlap: Optional[float] = None,
        min_cpc_overlap: Optional[float] = None,
    ) -> dict:
        rows = self.repo.get_candidates(
            owner_id=owner_id,
            limit=limit,
            offset=offset,
            min_industry_overlap=min_industry_overlap,
            min_cpc_overlap=min_cpc_overlap,
        )

        results = []
        for idx, r in enumerate(rows, start=offset + 1):
            results.append(
                {
                    "rank": idx,
                    "candidate": {
                        "owner_id": int(r["candidate_owner_id"]),
                        "owner_name": r.get("candidate_owner_name"),
                        "country": r.get("candidate_country"),
                        "peer_class": r.get("candidate_peer_class"),
                        "portfolio_size": int(r["candidate_portfolio_size"])
                        if r.get("candidate_portfolio_size") is not None
                        else None,
                    },
                    "overlap": {
                        "industry_overlap_score": self._round(r.get("industry_overlap_score"), 6),
                        "cpc_overlap_score": self._round(r.get("cpc_overlap_score"), 6),
                        "shared_industry_codes": self._safe_list(r.get("shared_industry_codes")),
                        "shared_cpc_codes": self._safe_list(r.get("shared_cpc_codes")),
                    },
                }
            )

        return {
            "portfolio": {"owner_id": owner_id},
            "pagination": {"limit": limit, "offset": offset, "returned": len(results)},
            "results": results,
            "metadata": {"contract_version": "v1", "data_snapshot": "2025-01-31"},
        }