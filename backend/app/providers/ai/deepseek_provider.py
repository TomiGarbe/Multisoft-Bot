import asyncio
import logging
import time
import json
from typing import Any

import httpx

from app.core.config import settings
from app.interfaces.ai.ai_interface import AIInterface

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIInterface):
    """DeepSeek AI Provider implementation via official Chat Completions API."""

    def __init__(
        self,
        *,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = model or settings.DEEPSEEK_MODEL
        self.timeout_seconds = timeout_seconds or settings.DEEPSEEK_TIMEOUT_SECONDS
        self.max_retries = max(0, settings.DEEPSEEK_MAX_RETRIES)
        self.initial_backoff_seconds = max(0.0, settings.DEEPSEEK_INITIAL_BACKOFF_SECONDS)
        self.max_backoff_seconds = max(self.initial_backoff_seconds, settings.DEEPSEEK_MAX_BACKOFF_SECONDS)

    def supports_vision(self) -> bool:
        normalized_model = (self.model or "").strip().lower()
        return any(token in normalized_model for token in ("vl", "vision", "v4"))

    def supports_streaming(self) -> bool:
        return False

    def supports_tools(self) -> bool:
        return True

    async def generate(self, prompt: str) -> str:
        data = await self.generate_with_metadata(prompt)
        return str(data.get("response") or "")

    async def generate_with_metadata(self, prompt: str) -> dict[str, Any]:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        return await self.generate_chat_with_metadata(
            [{"role": "user", "content": prompt}],
            tools=None,
        )

    async def generate_chat_with_metadata(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError("DeepSeek API key is missing")
        if not messages:
            raise ValueError("messages cannot be empty")
        self._validate_messages(messages)

        endpoint = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        multimodal_messages = 0
        for msg in messages:
            if isinstance(msg.get("content"), list):
                multimodal_messages += 1
        approx_payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        logger.info(
            "DeepSeek request start (model=%s messages=%d tools_count=%d multimodal_messages=%d approx_payload_bytes=%d timeout_seconds=%s)",
            self.model,
            len(messages),
            len(tools or []),
            multimodal_messages,
            approx_payload_bytes,
            self.timeout_seconds,
        )
        started = time.perf_counter()
        data = await self._post_with_retries(endpoint=endpoint, payload=payload)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        choices = data.get("choices") or []
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message") or {}
        content = self._normalize_message_content(message.get("content"))

        usage = data.get("usage") or {}
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        model_name = str(data.get("model") or self.model)
        tool_calls_raw = message.get("tool_calls") or []

        tool_calls: list[dict[str, Any]] = []
        for idx, call in enumerate(tool_calls_raw):
            function_payload = call.get("function") or {}
            arguments = function_payload.get("arguments")
            if isinstance(arguments, str):
                try:
                    import json

                    arguments = json.loads(arguments)
                except Exception:
                    arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            tool_calls.append(
                {
                    "id": call.get("id") or f"deepseek_tool_{idx}",
                    "type": "function",
                    "function": {
                        "name": function_payload.get("name"),
                        "arguments": arguments,
                        "arguments_raw": function_payload.get("arguments"),
                    },
                }
            )

        logger.info(
            "DeepSeek request end (model=%s finish_reason=%s tool_calls=%d duration_ms=%d prompt_tokens=%s completion_tokens=%s)",
            model_name,
            first_choice.get("finish_reason"),
            len(tool_calls_raw),
            elapsed_ms,
            input_tokens,
            output_tokens,
        )
        return {
            "response": content.strip(),
            "tool_calls": tool_calls,
            "assistant_message": {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls_raw,
            },
            "finish_reason": first_choice.get("finish_reason"),
            "prompt_eval_count": input_tokens,
            "eval_count": output_tokens,
            "model": model_name,
        }

    async def _post_with_retries(self, *, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        last_error: Exception | None = None
        max_attempts = self.max_retries + 1

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    status = response.status_code
                    if status in (408, 429) or 500 <= status <= 599:
                        error = httpx.HTTPStatusError(
                            f"DeepSeek retryable HTTP status: {status}",
                            request=response.request,
                            response=response,
                        )
                        raise error
                    response.raise_for_status()
                    parsed = response.json()
                    if not isinstance(parsed, dict):
                        raise ValueError("Invalid DeepSeek response format")
                    return parsed
                except Exception as exc:
                    last_error = exc
                    retryable = self._is_retryable(exc)
                    logger.warning(
                        "DeepSeek request failure (attempt=%d/%d retryable=%s error=%s)",
                        attempt,
                        max_attempts,
                        retryable,
                        exc,
                    )
                    if attempt >= max_attempts or not retryable:
                        break
                    await asyncio.sleep(self._backoff_seconds(attempt))

        if last_error is not None:
            if isinstance(last_error, httpx.TimeoutException):
                raise TimeoutError("DeepSeek request timed out") from last_error
            if isinstance(last_error, httpx.HTTPStatusError) and last_error.response is not None:
                status = last_error.response.status_code
                if status == 429:
                    raise RuntimeError("DeepSeek rate limit exceeded") from last_error
                if status == 400:
                    raise ValueError("DeepSeek rejected request payload (HTTP 400)") from last_error
                if status in (401, 403):
                    raise PermissionError(f"DeepSeek authentication/authorization failed (HTTP {status})") from last_error
                raise RuntimeError(f"DeepSeek API request failed with HTTP {status}") from last_error
            raise RuntimeError("DeepSeek provider unavailable") from last_error
        raise RuntimeError("DeepSeek request failed unexpectedly")

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            return exc.response.status_code in (408, 429) or 500 <= exc.response.status_code <= 599
        return False

    def _backoff_seconds(self, attempt_number: int) -> float:
        step = self.initial_backoff_seconds * (2 ** max(0, attempt_number - 1))
        return min(step, self.max_backoff_seconds)

    @staticmethod
    def _normalize_message_content(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_value = str(item.get("text") or "").strip()
                    if text_value:
                        text_parts.append(text_value)
            if text_parts:
                return "\n".join(text_parts)
        return str(content)

    @staticmethod
    def _validate_messages(messages: list[dict[str, Any]]) -> None:
        for idx, message in enumerate(messages):
            role = message.get("role")
            content = message.get("content")
            if role not in {"system", "user", "assistant", "tool"}:
                raise ValueError(f"Invalid message role at index {idx}")
            if content is None:
                raise ValueError(f"Missing message content at index {idx}")
            if isinstance(content, str):
                continue
            if isinstance(content, list):
                for part_idx, part in enumerate(content):
                    if not isinstance(part, dict):
                        raise ValueError(f"Invalid multimodal part at message {idx} part {part_idx}")
                    if part.get("type") not in {"text", "image_url"}:
                        raise ValueError(f"Unsupported multimodal part type at message {idx} part {part_idx}")
                continue
            raise ValueError(f"Invalid message content type at index {idx}")
