import logging
from typing import Any
import json

import httpx
from app.interfaces.ai.ai_interface import AIInterface
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(AIInterface):
    """Ollama AI Provider implementation"""

    def __init__(self, *, model: str | None = None, timeout_seconds: float | None = None):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.token = settings.OLLAMA_TOKEN
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    def supports_vision(self) -> bool:
        normalized_model = (self.model or "").strip().lower()
        return any(token in normalized_model for token in ("vision", "vl", "llava", "qwen2.5vl", "gemma3"))

    def supports_streaming(self) -> bool:
        return False

    def supports_tools(self) -> bool:
        return True

    async def generate(self, prompt: str) -> str:
        data = await self.generate_with_metadata(prompt)
        return str(data.get("response", ""))

    async def generate_with_metadata(self, prompt: str) -> dict[str, Any]:
        """
        Generate a response using Ollama AI.
        
        Args:
            prompt: The input prompt for the AI model
            
        Returns:
            The generated text response from Ollama
            
        Raises:
            ValueError: If the response is empty
            httpx.HTTPError: If there's an HTTP error communicating with Ollama
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        logger.warning(
            "[AI][OLLAMA][PAYLOAD] endpoint=/api/generate model=%s prompt_chars=%s stream=%s multimedia_included=%s",
            self.model,
            len(prompt or ""),
            False,
            False,
        )
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        logger.info("Ollama generate request (model=%s)", self.model)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                
                data = response.json()
                # Extract the generated text from response
                generated_text = data.get("response", "").strip()
                
                if not generated_text:
                    raise ValueError("Empty response received from Ollama")
                
                logger.info("Ollama generate response received (model=%s)", data.get("model") or self.model)
                return {
                    "response": generated_text,
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                    "model": data.get("model") or self.model,
                }

        except httpx.HTTPError as e:
            logger.error("[OLLAMA] HTTP error: %s", e)
            raise
        except ValueError as e:
            logger.error("[OLLAMA] Invalid response: %s", e)
            raise
        except Exception as e:
            logger.error("[OLLAMA] Unexpected error: %s", e)
            raise

    async def generate_chat_with_metadata(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not messages:
            raise ValueError("messages cannot be empty")

        endpoint = f"{self.base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        message_summaries = []
        multimedia_entries = 0
        for idx, message in enumerate(messages):
            content = message.get("content")
            content_kind = type(content).__name__
            content_chars = len(content) if isinstance(content, str) else None
            has_images_field = bool(message.get("images"))
            if has_images_field:
                multimedia_entries += 1
            message_summaries.append(
                {
                    "idx": idx,
                    "role": message.get("role"),
                    "content_kind": content_kind,
                    "content_chars": content_chars,
                    "has_images_field": has_images_field,
                    "has_tool_calls": bool(message.get("tool_calls")),
                }
            )
        logger.warning(
            "[AI][OLLAMA][PAYLOAD] endpoint=/api/chat model=%s messages=%s tools=%s multimedia_entries=%s summary=%s",
            self.model,
            len(messages),
            len(tools or []),
            multimedia_entries,
            message_summaries,
        )
        logger.info(
            "Ollama chat request (model=%s tools_count=%d)",
            self.model,
            len(tools or []),
        )

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        message = data.get("message") or {}
        tool_calls_raw = message.get("tool_calls") or []
        logger.info(
            "Ollama chat response received (model=%s done_reason=%s has_tool_calls=%s tool_calls_count=%d)",
            data.get("model") or self.model,
            data.get("done_reason"),
            bool(tool_calls_raw),
            len(tool_calls_raw),
        )

        tool_calls: list[dict[str, Any]] = []
        for idx, call in enumerate(tool_calls_raw):
            function_payload = call.get("function") or {}
            arguments = function_payload.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception:
                    arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            tool_calls.append(
                {
                    "id": f"ollama_tool_{idx}",
                    "type": "function",
                    "function": {
                        "name": function_payload.get("name"),
                        "arguments": arguments,
                        "arguments_raw": function_payload.get("arguments"),
                    },
                }
            )

        return {
            "response": str(message.get("content") or ""),
            "tool_calls": tool_calls,
            "assistant_message": {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": tool_calls_raw,
            },
            "finish_reason": data.get("done_reason"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
            "model": data.get("model") or self.model,
        }
