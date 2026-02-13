import os
import logging
import json
from dataclasses import dataclass
from typing import Any, Optional, Dict, List

import openai
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

logger = logging.getLogger(__name__)


class OpenAIAuthError(RuntimeError):
    pass


class OpenAIRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAIChatResult:
    model: str
    content: str
    raw: Any


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise OpenAIAuthError("OPENAI_API_KEY is not set")
        
        self.client = OpenAI(api_key=self._api_key)

    def chat_completions_create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1, # User requested small non-zero temp
        top_p: float = 1.0,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> OpenAIChatResult:
        try:
            # Map standard params to OpenAI params
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            if content is None:
                raise OpenAIRequestError("OpenAI returned empty content")

            return OpenAIChatResult(
                model=model,
                content=content,
                raw=response
            )

        except AuthenticationError as e:
            raise OpenAIAuthError(f"OpenAI authentication failed: {e}") from e
        except RateLimitError as e:
            raise OpenAIRequestError(f"OpenAI rate limit exceeded: {e}") from e
        except APIError as e:
            logger.exception("OpenAI request failed")
            raise OpenAIRequestError(f"OpenAI request failed: {e}") from e
        except Exception as e:
            logger.exception("OpenAI unexpected error")
            raise OpenAIRequestError(f"OpenAI unexpected error: {e}") from e
