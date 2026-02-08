from __future__ import annotations

import logging
from typing import Any

from application.llm.config import (
    MAX_TOKENS_PATENT,
    SNAPSHOT_DATE_FIXED_V1,
)
from application.llm.prompts import load_prompt, render_prompt
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

        derived = {
            "patent_metrics_summary": {
                "total_citations": total_citations or 0,
            },
            "patent_timeseries_summary": {
                "current_phase": _phase_from_timing_class((citation_metrics or {}).get("timing_class")),
                "recent_growth": _recent_growth_from_timeseries(series),
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

    async def get_advisory(self, appln_id: int, *, force_refresh: bool = False) -> dict[str, Any]:
        input_obj = await self.build_input(appln_id)

        parquet_hash = compute_parquet_version_hash()
        snapshot_date = SNAPSHOT_DATE_FIXED_V1
        analysis_type = "PATENT_ADVISORY"
        cache_key = f"{analysis_type}:{appln_id}:{snapshot_date}:{parquet_hash}"

        if not force_refresh:
            cached = self._cache.get(cache_key=cache_key)
            if cached is not None and cached.parquet_version_hash == parquet_hash:
                logger.info("patent_advisory cache hit", extra={"appln_id": appln_id})
                return cached.payload

        system_prompt = load_prompt("system.txt")
        user_prompt = render_prompt(load_prompt("patent_user.txt"), data_obj=input_obj)

        def _validate(content: str) -> dict[str, Any]:
            return validate_and_sanitize_patent_advisory(llm_content=content, input_obj=input_obj)

        try:
            payload, model_used = run_with_retries(
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
            logger.exception("patent_advisory failed", extra={"appln_id": appln_id})
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
