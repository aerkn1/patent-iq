from __future__ import annotations

import logging
from typing import Any

from application.llm.config import (
    MAX_TOKENS_PORTFOLIO_EVOLUTION,
    SNAPSHOT_DATE_FIXED_V1,
)
from application.llm.prompts import load_prompt, render_prompt
from application.llm.runner import LlmRunner, run_with_retries
from application.llm.advisory_validation import validate_and_sanitize_portfolio_evolution_advisory

from infrastructure.llm.cache_repo import AdvisoryCacheRepository
from infrastructure.llm.parquet_version import compute_parquet_version_hash

from application.services.portfolio_citation_service import PortfolioCitationService
from domain.errors import ValidationError, DataUnavailableError, InternalServerError


logger = logging.getLogger(__name__)


def _trend_direction_from_yoy(yoy: list[float]) -> str:
    if not yoy:
        return "STABILIZING"
    tail = yoy[-3:]
    avg = sum(tail) / len(tail)
    if avg > 0.05:
        return "ACCELERATING"
    if avg < -0.05:
        return "DECELERATING"
    return "STABILIZING"


class PortfolioEvolutionAdvisoryService:
    def __init__(self) -> None:
        self._cache = AdvisoryCacheRepository()
        self._runner = LlmRunner()
        self._citation_svc = PortfolioCitationService()

    async def build_input(self, owner_id: int) -> dict[str, Any]:
        if owner_id <= 0:
            raise ValidationError("owner_id must be positive")

        citation_ts = self._citation_svc.get_citation_timeseries(owner_id)
        series = (citation_ts or {}).get("series", [])
        yoy_vals = [float(r.get("citations_yoy_pct") or 0.0) for r in series]

        derived = {
            "trend_direction": _trend_direction_from_yoy(yoy_vals),
            "data_quality": {
                "coverage": "HIGH" if len(series) >= 8 else ("MEDIUM" if len(series) >= 4 else "LOW"),
                "notes": f"active_years={len(series)}",
            },
        }

        return {
            "context": {
                "analysis_type": "PORTFOLIO_EVOLUTION_ADVISORY",
                "owner_id": owner_id,
                "snapshot_date": SNAPSHOT_DATE_FIXED_V1,
            },
            "ui_payload": {
                "portfolio_citation_timeseries": citation_ts,
            },
            "derived": derived,
        }

    async def get_advisory(self, owner_id: int, *, force_refresh: bool = False) -> dict[str, Any]:
        input_obj = await self.build_input(owner_id)

        parquet_hash = compute_parquet_version_hash()
        snapshot_date = SNAPSHOT_DATE_FIXED_V1
        analysis_type = "PORTFOLIO_EVOLUTION_ADVISORY"
        cache_key = f"{analysis_type}:{owner_id}:{snapshot_date}:{parquet_hash}"

        if not force_refresh:
            cached = self._cache.get(cache_key=cache_key)
            if cached is not None and cached.parquet_version_hash == parquet_hash:
                logger.info("portfolio_evolution_advisory cache hit", extra={"owner_id": owner_id})
                return cached.payload

        system_prompt = load_prompt("system.txt")
        user_prompt = render_prompt(load_prompt("portfolio_evolution_user.txt"), data_obj=input_obj)

        def _validate(content: str) -> dict[str, Any]:
            return validate_and_sanitize_portfolio_evolution_advisory(llm_content=content, input_obj=input_obj)

        try:
            payload, model_used = run_with_retries(
                runner=self._runner,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=MAX_TOKENS_PORTFOLIO_EVOLUTION,
                validate_and_sanitize=_validate,
            )
        except ValidationError:
            raise
        except DataUnavailableError:
            raise
        except Exception as e:
            logger.exception("portfolio_evolution_advisory failed", extra={"owner_id": owner_id})
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
