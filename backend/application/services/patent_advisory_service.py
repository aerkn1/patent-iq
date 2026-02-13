from __future__ import annotations

import logging
from typing import Any

from application.llm.config import (
    MAX_TOKENS_PATENT,
    SNAPSHOT_DATE_FIXED_V1,
)
from application.llm.prompts import build_system_prompt, build_user_prompt
from application.llm.runner import LlmRunner, run_with_retries
from application.llm.advisory_validation import validate_and_sanitize_patent_advisory

from infrastructure.llm.cache_repo import AdvisoryCacheRepository
from infrastructure.llm.parquet_version import compute_parquet_version_hash

from application.services.patent_page_service import PatentPageService

from domain.errors import ValidationError, DataUnavailableError, InternalServerError


logger = logging.getLogger(__name__)


def _patent_data_quality(citation_span_years: int | None, total_citations: int | None) -> tuple[str, str]:
    span = int(citation_span_years or 0)
    cites = int(total_citations or 0)

    if span >= 6 or (cites >= 15 and span >= 4):
        return "HIGH", f"Sufficient coverage: citation_span_years={span}, total_citations={cites}"
    if span >= 3:
        return "MEDIUM", f"Moderate coverage: citation_span_years={span}, total_citations={cites}"
    return "LOW", f"Limited coverage: citation_span_years={span}, total_citations={cites}"


def _phase_from_timing_class(timing_class: str | None) -> str:
    tc = (timing_class or "").upper()
    if tc == "EARLY":
        return "EMERGING"
    if tc == "MID":
        return "PEAK"
    if tc == "LATE":
        return "DECLINING"
    return "UNKNOWN"


def _recent_growth_from_timeseries(series: list[dict[str, Any]]) -> str:
    if len(series) < 2:
        return "STABILIZING"
    last = int(series[-1].get("new_forward_cites") or 0)
    prev = int(series[-2].get("new_forward_cites") or 0)
    if last > prev:
        return "ACCELERATING"
    if last < prev:
        return "DECELERATING"
    return "STABILIZING"


class PatentAdvisoryService:
    def __init__(self) -> None:
        self._cache = AdvisoryCacheRepository()
        self._runner = LlmRunner()
        self._svc = PatentPageService()

    async def build_input(self, appln_id: int) -> dict[str, Any]:
        if appln_id <= 0:
            raise ValidationError("appln_id must be positive")

        patent_overview = await self._svc.get_overview(appln_id)
        patent_analysis = await self._svc.get_analysis_2(appln_id)
        citation_metrics = await self._svc.get_citation_metrics(appln_id)
        citation_ts = await self._svc.get_citation_timeseries(appln_id)

        total_citations = None
        if citation_metrics:
            total_citations = int((citation_metrics.get("early_cites") or 0) + (citation_metrics.get("mid_cites") or 0) + (citation_metrics.get("late_cites") or 0))

        coverage, notes = _patent_data_quality(
            citation_span_years=(citation_metrics or {}).get("citation_span_years"),
            total_citations=total_citations,
        )

        series = (citation_ts or {}).get("series", [])

        analysis = patent_analysis or {}
        overview = patent_overview or {}

        tech = analysis.get("technology", {})
        market = analysis.get("market", {})
        legal = analysis.get("legal", {})
        innovation = analysis.get("innovation", {})
        blocking = analysis.get("blocking_power_breakdown", {})
        licensing = analysis.get("licensing_readiness_breakdown", {})
        rankings = analysis.get("rankings", {})
        family = overview.get("family", {})

        top_cpcs = [c["code"] for c in tech.get("distribution", {}).get("cpc_subclasses", [])[:5]]
        top_industries = [i["code"] for i in market.get("distribution", {}).get("industries", [])[:5]]

        derived = {
            "patent_metrics_summary": {
                "total_citations": total_citations or 0,
            },
            "patent_timeseries_summary": {
                "current_phase": _phase_from_timing_class((citation_metrics or {}).get("timing_class")),
                "recent_growth": _recent_growth_from_timeseries(series),
            },
            "technology_summary": {
                "top_cpcs": top_cpcs,
                "diversification": tech.get("diversification", {}).get("interpretation", ""),
                "entropy_normalized": tech.get("diversification", {}).get("normalized"),
            },
            "market_summary": {
                "top_industries": top_industries,
                "diversification": market.get("diversification", {}).get("interpretation", ""),
                "entropy_normalized": market.get("diversification", {}).get("normalized"),
            },
            "legal_summary": {
                "opposition_count": legal.get("opposition_count", 0),
                "lapse_count": legal.get("lapse_count", 0),
                "renewal_payment_count": legal.get("renewal_payment_count", 0),
                "legal_uncertainty": legal.get("legal_uncertainty", False),
            },
            "innovation_summary": {
                "innovation_score": innovation.get("innovation_score"),
                "tech_field_influence": innovation.get("tech_field_influence"),
                "field_attention": innovation.get("field_attention"),
            },
            "blocking_summary": {
                "forward_impact_score": blocking.get("diagnostics", {}).get("forward_impact_score"),
                "family_breadth_normalized": blocking.get("diagnostics", {}).get("family_breadth_normalized"),
                "tech_breadth_penalty": blocking.get("diagnostics", {}).get("tech_breadth_penalty"),
                "self_blocking_rate": blocking.get("diagnostics", {}).get("self_blocking_rate"),
            },
            "licensing_summary": {
                "forward_impact_score": licensing.get("forward_impact_score"),
                "claim_chartability_score": licensing.get("claim_chartability_score"),
                "market_relevance_score": licensing.get("market_relevance_score"),
                "legal_confidence_score": licensing.get("legal_confidence_score"),
                "final_readiness_score": licensing.get("final_readiness_score"),
            },
            "rankings_summary": {
                "blocking_power_pct_global": rankings.get("blocking_power", {}).get("percentile_global"),
                "technology_pct_global": rankings.get("technology_axis", {}).get("percentile_global"),
                "market_pct_global": rankings.get("market_axis", {}).get("percentile_global"),
            },
            "family_summary": {
                "family_members_count": family.get("family_members_count"),
                "family_jurisdiction_count": family.get("family_jurisdiction_count"),
                "major_office_grant_auths": family.get("major_office_grant_auths"),
                "family_cpc_subclass_count": family.get("family_cpc_subclass_count"),
            },
            "data_quality": {
                "coverage": coverage,
                "notes": notes,
            },
        }

        return {
            "context": {
                "analysis_type": "PATENT_ADVISORY",
                "appln_id": appln_id,
                "snapshot_date": SNAPSHOT_DATE_FIXED_V1,
            },
            "ui_payload": {
                "patent_overview": patent_overview,
                "patent_analysis": patent_analysis,
                "citation_metrics": citation_metrics,
                "citation_timeseries": citation_ts,
            },
            "derived": derived,
        }

    def _filter_input_data(self, input_obj: dict[str, Any], bucket: str | None) -> dict[str, Any]:
        if not bucket or bucket == "strategy":
            return input_obj
        
        # Deep copy structure to avoid mutating cache if we cached the full input
        # But build_input returns a fresh dict, so shallow copy of top levels is fine, 
        # but we are filtering inner dicts.
        
        derived = input_obj["derived"].copy()
        ui_payload = input_obj["ui_payload"].copy()
        
        # Filter derived
        if bucket == "technology":
            keys_to_keep = {"technology_summary", "innovation_summary", "data_quality", "patent_metrics_summary"}
            derived = {k: v for k, v in derived.items() if k in keys_to_keep}
            
            # Filter ui_payload (patent_analysis is main big object)
            if "patent_analysis" in ui_payload:
                pa = ui_payload["patent_analysis"] or {}
                ui_payload["patent_analysis"] = {
                    "technology": pa.get("technology"),
                    "innovation": pa.get("innovation"),
                }

        elif bucket == "market":
            keys_to_keep = {"market_summary", "data_quality", "patent_metrics_summary"}
            derived = {k: v for k, v in derived.items() if k in keys_to_keep}
            
            if "patent_analysis" in ui_payload:
                pa = ui_payload["patent_analysis"] or {}
                ui_payload["patent_analysis"] = {
                    "market": pa.get("market"),
                }

        elif bucket == "legal":
            keys_to_keep = {"legal_summary", "blocking_summary", "family_summary", "data_quality", "patent_metrics_summary"}
            derived = {k: v for k, v in derived.items() if k in keys_to_keep}
             
            if "patent_analysis" in ui_payload:
                pa = ui_payload["patent_analysis"] or {}
                ui_payload["patent_analysis"] = {
                    "legal": pa.get("legal"),
                    "blocking_power_breakdown": pa.get("blocking_power_breakdown"),
                }
        
        return {
            "context": input_obj["context"],
            "ui_payload": ui_payload,
            "derived": derived,
        }

    async def get_advisory(self, appln_id: int, *, bucket: str | None = None, force_refresh: bool = False) -> dict[str, Any]:
        full_input = await self.build_input(appln_id)
        
        # Slicing
        input_obj = self._filter_input_data(full_input, bucket)

        parquet_hash = compute_parquet_version_hash()
        snapshot_date = SNAPSHOT_DATE_FIXED_V1
        analysis_type = "PATENT_ADVISORY"
        
        # Cache key includes bucket
        bucket_key = bucket if bucket else "full"
        cache_key = f"{analysis_type}:{appln_id}:{snapshot_date}:{parquet_hash}:{bucket_key}"

        if not force_refresh:
            cached = self._cache.get(cache_key=cache_key)
            if cached is not None and cached.parquet_version_hash == parquet_hash:
                logger.info("patent_advisory cache hit", extra={"appln_id": appln_id, "bucket": bucket})
                return cached.payload

        system_prompt = build_system_prompt()
        
        # Determine prompt file
        if bucket:
            prompt_name = f"patent/{bucket}.json"
        else:
            prompt_name = "patent_user.json"
            
        user_prompt = build_user_prompt(prompt_name, data_obj=input_obj)

        def _validate(content: str) -> dict[str, Any]:
            return validate_and_sanitize_patent_advisory(llm_content=content, input_obj=input_obj)

        try:
            payload, model_used = await run_with_retries(
                runner=self._runner,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=MAX_TOKENS_PATENT,
                validate_and_sanitize=_validate,
            )
        except ValidationError:
            raise
        except DataUnavailableError:
            raise
        except Exception as e:
            logger.exception("patent_advisory failed", extra={"appln_id": appln_id, "bucket": bucket})
            raise InternalServerError() from e

        self._cache.set(
            cache_key=cache_key,
            analysis_type=analysis_type,
            entity_id=appln_id,
            snapshot_date=snapshot_date,
            parquet_version_hash=parquet_hash,
            model=model_used,
            payload=payload,
            ttl_days=30,
        )

        return payload
