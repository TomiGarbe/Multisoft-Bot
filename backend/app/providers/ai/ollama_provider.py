import logging
from typing import Any
import json

import httpx
from app.interfaces.ai.ai_interface import AIInterface
from app.core.config import settings
from app.services.ai.debug_logger import is_ai_debug_enabled, log_block, make_debug_id, mask_sensitive

logger = logging.getLogger(__name__)


class OllamaProvider(AIInterface):
    """Ollama AI Provider implementation"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.token = settings.OLLAMA_TOKEN

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
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        debug_enabled = is_ai_debug_enabled()
        debug_id = make_debug_id() if debug_enabled else None
        if debug_enabled and debug_id is not None:
            log_block(
                debug_id=debug_id,
                title="PROVIDER_REQUEST::GENERATE",
                value={
                    "endpoint": endpoint,
                    "provider": "ollama",
                    "payload": payload,
                    "headers": mask_sensitive(headers),
                    "options": {
                        "temperature": None,
                        "max_tokens": None,
                        "response_format": None,
                        "tool_calling": False,
                    },
                },
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=300.0  # 5 minutes timeout for AI generation
                )
                response.raise_for_status()
                
                data = response.json()
                if debug_enabled and debug_id is not None:
                    log_block(
                        debug_id=debug_id,
                        title="PROVIDER_RESPONSE::GENERATE_RAW",
                        value=data,
                    )

                # Extract the generated text from response
                generated_text = data.get("response", "").strip()
                
                if not generated_text:
                    raise ValueError("Empty response received from Ollama")
                
                logger.info("[OLLAMA] Generated response for prompt: %.50s...", prompt)
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

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        debug_enabled = is_ai_debug_enabled()
        debug_id = make_debug_id() if debug_enabled else None
        if debug_enabled and debug_id is not None:
            log_block(
                debug_id=debug_id,
                title="PROVIDER_REQUEST::CHAT",
                value={
                    "endpoint": endpoint,
                    "provider": "ollama",
                    "payload": payload,
                    "headers": mask_sensitive(headers),
                    "options": {
                        "temperature": None,
                        "max_tokens": None,
                        "response_format": None,
                        "tool_calling": bool(tools),
                        "tools_count": len(tools or []),
                    },
                },
            )

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        if debug_enabled and debug_id is not None:
            log_block(
                debug_id=debug_id,
                title="PROVIDER_RESPONSE::CHAT_RAW",
                value=data,
            )

        message = data.get("message") or {}
        tool_calls_raw = message.get("tool_calls") or []
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
