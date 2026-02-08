import os
from dataclasses import dataclass
from typing import Any, Optional

import requests
import logging

logger = logging.getLogger(__name__)


GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"


class GroqAuthError(RuntimeError):
    pass


class GroqRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class GroqChatResult:
    model: str
    content: str
    raw: dict[str, Any]


class GroqChatClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = GROQ_OPENAI_BASE_URL,
        timeout_seconds: int = 60,
    ) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self._api_key:
            raise GroqAuthError("GROQ_API_KEY is not set")

        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def chat_completions_create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 1200,
        response_format: Optional[dict[str, Any]] = None,
        extra_body: Optional[dict[str, Any]] = None,
    ) -> GroqChatResult:
        url = f"{self._base_url}/chat/completions"
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            body["response_format"] = response_format
        if extra_body:
            body.update(extra_body)

        try:
            resp = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                json=body,
                timeout=self._timeout_seconds,
            )
        except Exception as e:
            raise GroqRequestError(f"Groq request failed: {e}") from e

        if resp.status_code >= 400:
            # Avoid leaking secrets; Groq error bodies are typically safe JSON.
            error_msg = f"Groq HTTP {resp.status_code}: {resp.text[:500]}"
            logger.error(error_msg)
            raise GroqRequestError(error_msg)

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as e:
            raise GroqRequestError(
                f"Unexpected Groq response structure: {str(data)[:500]}"
            ) from e

        return GroqChatResult(model=model, content=content or "", raw=data)
