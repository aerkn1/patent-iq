from __future__ import annotations

import logging
from typing import Any

from application.llm.config import (
    MAX_TOKENS_PORTFOLIO,
    SNAPSHOT_DATE_FIXED_V1,
)
from application.llm.prompts import build_system_prompt, build_user_prompt
from application.llm.runner import LlmRunner, run_with_retries
from application.llm.advisory_validation import (
    validate_and_sanitize_portfolio_advisory,
)
from infrastructure.llm.cache_repo import AdvisoryCacheRepository
from infrastructure.llm.parquet_version import compute_parquet_version_hash

from application.services.portfolio_page_service import PortfolioOverviewService
from application.services.portfolio_analytics_service import PortfolioAnalyticsService
from application.services.portfolio_citation_service import PortfolioCitationService
from application.services.portfolio_licensing_service import PortfolioLicensingService

from domain.errors import ValidationError, NotFoundError, DataUnavailableError, InternalServerError


logger = logging.getLogger(__name__)


def _trend_direction_from_yoy(yoy: list[float]) -> str:
    if not yoy:
        return "STABILIZING"
    # Use last 3 values
    tail = yoy[-3:]
    avg = sum(tail) / len(tail)
    if avg > 0.05:
        return "ACCELERATING"
    if avg < -0.05:
        return "DECELERATING"
    return "STABILIZING"


def _portfolio_data_quality(n_patents_effective: float, active_years: int, cites_per_patent: float | None) -> tuple[str, str]:
    if n_patents_effective >= 20 and active_years >= 8 and cites_per_patent is not None:
        return "HIGH", f"Sufficient coverage: n_patents_effective={n_patents_effective}, active_years={active_years}"
    if n_patents_effective >= 10 and active_years >= 4:
        return "MEDIUM", f"Moderate coverage: n_patents_effective={n_patents_effective}, active_years={active_years}"
    return "LOW", f"Limited coverage: n_patents_effective={n_patents_effective}, active_years={active_years}"


class PortfolioAdvisoryService:
    def __init__(self) -> None:
        self._cache = AdvisoryCacheRepository()
        self._runner = LlmRunner()

        self._overview_svc = PortfolioOverviewService()
        self._analytics_svc = PortfolioAnalyticsService()
        self._citation_svc = PortfolioCitationService()
        self._licensing_svc = PortfolioLicensingService()

    async def build_input(self, owner_id: int) -> dict[str, Any]:
        if owner_id <= 0:
            raise ValidationError("owner_id must be positive")

        overview = await self._overview_svc.get_overview(owner_id)
        analytics = await self._analytics_svc.get_analytics(owner_id)
        citation_metrics = self._citation_svc.get_citation_metrics(owner_id)
        citation_ts = self._citation_svc.get_citation_timeseries(owner_id)
        licensing_candidates = self._licensing_svc.get_candidates(owner_id=owner_id, limit=10, offset=0)

        series = (citation_ts or {}).get("series", [])
        active_years = len(series)
        last = series[-1] if series else {}
        yoy_vals = [float(r.get("citations_yoy_pct") or 0.0) for r in series]

        n_pe = float((citation_metrics or {}).get("portfolio_size", {}).get("n_patents_effective") or 0.0)
        cpp = (citation_metrics or {}).get("citation_volume", {}).get("cites_per_patent")
        cpp_val = float(cpp) if cpp is not None else None

        coverage, dq_notes = _portfolio_data_quality(n_pe, active_years, cpp_val)

        licensing_results = (licensing_candidates or {}).get("results", [])
        industry_scores = [float(r.get("overlap", {}).get("industry_overlap_score") or 0.0) for r in licensing_results]
        cpc_scores = [float(r.get("overlap", {}).get("cpc_overlap_score") or 0.0) for r in licensing_results]

        # flatten shared codes
        industries: dict[str, int] = {}
        cpcs: dict[str, int] = {}
        for r in licensing_results:
            for code in r.get("overlap", {}).get("shared_industry_codes", []) or []:
                industries[str(code)] = industries.get(str(code), 0) + 1
            for code in r.get("overlap", {}).get("shared_cpc_codes", []) or []:
                cpcs[str(code)] = cpcs.get(str(code), 0) + 1

        top_industries = [k for k, _ in sorted(industries.items(), key=lambda kv: kv[1], reverse=True)[:5]]
        top_cpcs = [k for k, _ in sorted(cpcs.items(), key=lambda kv: kv[1], reverse=True)[:5]]

        candidate_density = "HIGH" if len(licensing_results) >= 10 else ("MEDIUM" if len(licensing_results) >= 5 else "LOW")

        analytics_data = analytics or {}
        categories = analytics_data.get("categories", {})
        citations = analytics_data.get("citations", {})
        legal = analytics_data.get("legal", {})
        blocking_power = analytics_data.get("blocking_power", {})
        innovation = analytics_data.get("innovation", {})

        derived = {
            "portfolio_timeseries_summary": {
                "current_phase": str(last.get("citation_phase") or "UNKNOWN"),
                "recent_yoy_growth_pct": float(last.get("citations_yoy_pct") or 0.0),
                "trend_direction": _trend_direction_from_yoy(yoy_vals),
                "active_years": active_years,
            },
            "licensing_context_summary": {
                "candidate_density": candidate_density,
                "avg_industry_overlap": float(sum(industry_scores) / len(industry_scores)) if industry_scores else 0.0,
                "avg_cpc_overlap": float(sum(cpc_scores) / len(cpc_scores)) if cpc_scores else 0.0,
                "top_industries": top_industries,
                "top_cpc_classes": top_cpcs,
            },
            "categories_summary": {
                "portfolio_category": categories.get("portfolio_category", "UNKNOWN"),
                "counts": categories.get("counts", {}),
                "shares": categories.get("shares", {}),
            },
            "blocking_summary": {
                "dominant_driver": blocking_power.get("dominant_driver", "UNKNOWN"),
                "drivers": blocking_power.get("drivers", {}),
                "top_patents_count": len(blocking_power.get("top_patents", [])),
            },
            "innovation_summary": {
                "avg_innovation_score": innovation.get("avg_innovation_score"),
                "avg_h_index_proxy": innovation.get("avg_h_index_proxy"),
                "avg_field_normalized_citations": innovation.get("avg_field_normalized_citations"),
                "top_patents_count": len(innovation.get("top_patents", [])),
            },
            "legal_summary": {
                "abandoned_ratio": legal.get("abandoned_ratio"),
                "legal_strength_avg": legal.get("legal_strength_avg"),
                "legal_unknown_ratio": legal.get("legal_unknown_ratio"),
                "maintenance_profile": legal.get("maintenance_profile", "UNKNOWN"),
            },
            "citation_summary": {
                "forward_total": citations.get("forward_total", 0),
                "backward_total": citations.get("backward_total", 0),
                "self_forward_rate": citations.get("self_citations", {}).get("self_forward_rate", 0.0),
                "self_backward_rate": citations.get("self_citations", {}).get("self_backward_rate", 0.0),
            },
            "data_quality": {
                "coverage": coverage,
                "notes": dq_notes,
            },
        }

        return {
            "context": {
                "analysis_type": "PORTFOLIO_ADVISORY",
                "owner_id": owner_id,
                "snapshot_date": SNAPSHOT_DATE_FIXED_V1,
            },
            "ui_payload": {
                "portfolio_overview": overview,
                "portfolio_analytics": analytics,
                "portfolio_citation_metrics": citation_metrics,
                "portfolio_citation_timeseries": citation_ts,
                "portfolio_licensing_candidates": licensing_candidates,
            },
            "derived": derived,
        }

    def _filter_input_data(self, input_obj: dict[str, Any], bucket: str | None) -> dict[str, Any]:
        if not bucket or bucket == "strategy":
            return input_obj
            
        derived = input_obj["derived"].copy()
        ui_payload = input_obj["ui_payload"].copy()
        
        if bucket == "technology":
            keys_to_keep = {"innovation_summary", "blocking_summary", "data_quality"}
            derived = {k: v for k, v in derived.items() if k in keys_to_keep}
            
            if "portfolio_analytics" in ui_payload:
                pa = ui_payload["portfolio_analytics"] or {}
                ui_payload["portfolio_analytics"] = {
                    "innovation": pa.get("innovation"),
                    "blocking_power": pa.get("blocking_power"),
                }
                
        elif bucket == "commercial":
            keys_to_keep = {"licensing_context_summary", "categories_summary", "data_quality"}
            derived = {k: v for k, v in derived.items() if k in keys_to_keep}
            
            # Keep licensing candidates
            # Remove unrelated analytics
            if "portfolio_analytics" in ui_payload:
                pa = ui_payload["portfolio_analytics"] or {}
                ui_payload["portfolio_analytics"] = {
                    "categories": pa.get("categories"),
                }
            # Remove citation data from payload to save space
            if "portfolio_citation_timeseries" in ui_payload:
                del ui_payload["portfolio_citation_timeseries"]
                
        elif bucket == "legal":
            keys_to_keep = {"legal_summary", "citation_summary", "data_quality"}
            derived = {k: v for k, v in derived.items() if k in keys_to_keep}
            
            if "portfolio_analytics" in ui_payload:
                pa = ui_payload["portfolio_analytics"] or {}
                ui_payload["portfolio_analytics"] = {
                    "legal": pa.get("legal"),
                    "citations": pa.get("citations"),
                }
            # Remove licensing candidates
            if "portfolio_licensing_candidates" in ui_payload:
                del ui_payload["portfolio_licensing_candidates"]

        return {
            "context": input_obj["context"],
            "ui_payload": ui_payload,
            "derived": derived,
        }

    async def get_advisory(self, owner_id: int, *, bucket: str | None = None, force_refresh: bool = False) -> dict[str, Any]:
        full_input = await self.build_input(owner_id)
        
        # Slicing
        input_obj = self._filter_input_data(full_input, bucket)

        parquet_hash = compute_parquet_version_hash()
        snapshot_date = SNAPSHOT_DATE_FIXED_V1
        analysis_type = "PORTFOLIO_ADVISORY"
        
        # Cache key includes bucket
        bucket_key = bucket if bucket else "full"
        cache_key = f"{analysis_type}:{owner_id}:{snapshot_date}:{parquet_hash}:{bucket_key}"

        if not force_refresh:
            cached = self._cache.get(cache_key=cache_key)
            if cached is not None and cached.parquet_version_hash == parquet_hash:
                logger.info("portfolio_advisory cache hit", extra={"owner_id": owner_id, "bucket": bucket})
                return cached.payload

        system_prompt = build_system_prompt()
        
        # Determine prompt file
        if bucket:
            prompt_name = f"portfolio/{bucket}.json"
        else:
            prompt_name = "portfolio_user.json"

        user_prompt = build_user_prompt(prompt_name, data_obj=input_obj)

        def _validate(content: str) -> dict[str, Any]:
            return validate_and_sanitize_portfolio_advisory(llm_content=content, input_obj=input_obj)

        try:
            payload, model_used = await run_with_retries(
                runner=self._runner,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=MAX_TOKENS_PORTFOLIO,
                validate_and_sanitize=_validate,
            )
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except DataUnavailableError:
            raise
        except Exception as e:
            logger.exception("portfolio_advisory failed", extra={"owner_id": owner_id, "bucket": bucket})
            raise InternalServerError() from e

        self._cache.set(
            cache_key=cache_key,
            analysis_type=analysis_type,
            entity_id=owner_id,
            snapshot_date=snapshot_date,
            parquet_version_hash=parquet_hash,
            model=model_used,
            payload=payload,
            ttl_days=30,
        )

        return payload
