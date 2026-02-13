import os
import logging
from dataclasses import dataclass
from typing import Any, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class GeminiAuthError(RuntimeError):
    pass


class GeminiRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeminiChatResult:
    model: str
    content: str
    raw: Any


class GeminiChatClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise GeminiAuthError("GEMINI_API_KEY is not set")
        
        genai.configure(api_key=self._api_key)

    def chat_completions_create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        top_p: float = 0.95,
        max_tokens: int = 2048,
        response_format: Optional[dict[str, Any]] = None,
    ) -> GeminiChatResult:
        try:
            # Extract system instruction if present
            system_instruction = None
            history = []
            
            # Convert OpenAI-style messages to Gemini history
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    history.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    history.append({"role": "model", "parts": [content]})
            
            # Configure generation config
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_tokens,
            }
            
            if response_format and response_format.get("type") == "json_object":
                generation_config["response_mime_type"] = "application/json"

            # Create model instance
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                generation_config=generation_config,
            )

            # Generate content
            # For a single turn (since we rebuild history each time), just use generate_content
            # The 'history' logic above is useful if we were using start_chat, but here we just need the last user message
            # effectively. However, prompts often have context. 
            # In our use case (runner.py), we usually send [system, user]. 
            # So the 'history' list contains just the user prompt.
            
            if not history:
                raise GeminiRequestError("No user message found in prompt")
                
            last_user_msg = history[-1]["parts"][0]
            
            # Safety settings - we want low blocking for this use case
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = gemini_model.generate_content(
                last_user_msg,
                safety_settings=safety_settings
            )
            
            if not response.text:
                 raise GeminiRequestError(f"Gemini returned empty response: {response.prompt_feedback}")

            return GeminiChatResult(
                model=model,
                content=response.text,
                raw=response
            )

        except Exception as e:
            logger.exception("Gemini request failed")
            raise GeminiRequestError(f"Gemini request failed: {e}") from e
