from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

from application.llm.config import (
    GROQ_MODEL_DEFAULT,
    GROQ_MODEL_FALLBACK,
)
from infrastructure.llm.groq_client import GroqChatClient, GroqRequestError, GroqAuthError
from domain.errors import DataUnavailableError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LlmRunResult:
    model: str
    content: str


class LlmRunner:
    def __init__(self) -> None:
        try:
            self.client = GroqChatClient()
        except GroqAuthError as e:
            raise DataUnavailableError("LLM credentials are not configured") from e

    async def run_json_advisory(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        repair_hint: Optional[str] = None,
        model: str = GROQ_MODEL_DEFAULT,
    ) -> LlmRunResult:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        if repair_hint:
             # Add a strict repair instruction as a system message.
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "REPAIR INSTRUCTIONS: The previous output failed validation. "
                        "Fix the issues described below and output ONLY valid JSON matching the schema.\n" + repair_hint
                    ),
                }
            )

        messages.append({"role": "user", "content": user_prompt})
        
        for attempt in range(3):
            try:
                # Groq supports response_format={"type": "json_object"}
                res = self.client.chat_completions_create(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    top_p=1.0,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                return LlmRunResult(model=model, content=res.content)
            except GroqRequestError as e:
                # Rate limits (429) backoff
                if "429" in str(e) and attempt < 2:
                    wait_time = 2 * (2 ** attempt) # 2s, 4s
                    logger.warning(f"Groq 429 rate limit. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise DataUnavailableError("LLM provider request failed") from e
            except Exception as e:
                 raise DataUnavailableError(f"LLM unexpected error: {e}") from e
        
        raise DataUnavailableError("LLM provider request failed after local retries")


async def run_with_retries(
    *,
    runner: LlmRunner,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    validate_and_sanitize: Callable[[str], dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    last_exc: Optional[Exception] = None

    for attempt, model in enumerate(
        [GROQ_MODEL_DEFAULT, GROQ_MODEL_DEFAULT, GROQ_MODEL_FALLBACK], start=1
    ):
        repair_hint = None if attempt == 1 else (str(last_exc) if last_exc else "Unknown validation error")

        try:
            out = await runner.run_json_advisory(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                repair_hint=repair_hint,
                model=model,
            )
        except Exception as e:
            last_exc = e
            continue

        try:
            payload = validate_and_sanitize(out.content)
            return payload, model
        except Exception as e:
            last_exc = e
            continue

    if isinstance(last_exc, DataUnavailableError):
        raise last_exc

    raise ValueError(f"LLM advisory failed after retries: {last_exc}")
