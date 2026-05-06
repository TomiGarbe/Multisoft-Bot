from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.services.bot_actions.errors import ActionExecutionError
from app.schemas.internal.bot_actions.execution import ActionExecutionResult
from app.utils.bot_actions_constants import MAX_RESPONSE_SIZE


class HttpClientService:
    async def execute(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        query_params: dict[str, Any] | None,
        body: Any,
        timeout_ms: int,
        retry_count: int,
    ) -> ActionExecutionResult:
        started = time.perf_counter()
        timeout_seconds = timeout_ms / 1000
        attempts = retry_count + 1
        last_error: ActionExecutionError | None = None

        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            for attempt in range(attempts):
                try:
                    response = await self._send_request(
                        client=client,
                        method=method,
                        url=url,
                        headers=headers,
                        query_params=query_params,
                        body=body,
                    )
                    duration_ms = int((time.perf_counter() - started) * 1000)
                    if response.status_code >= 500 and attempt < attempts - 1:
                        continue
                    return self._normalize_response(response=response, duration_ms=duration_ms)
                except httpx.TimeoutException as exc:
                    last_error = ActionExecutionError("request_timeout", str(exc))
                    if attempt >= attempts - 1:
                        break
                except httpx.ConnectError as exc:
                    last_error = ActionExecutionError("http_connection_error", str(exc))
                    if attempt >= attempts - 1:
                        break
                except ActionExecutionError as exc:
                    last_error = exc
                    break
                except Exception as exc:  # pragma: no cover
                    last_error = ActionExecutionError("action_execution_failed", str(exc))
                    break

        duration_ms = int((time.perf_counter() - started) * 1000)
        return ActionExecutionResult(
            success=False,
            duration_ms=duration_ms,
            error=last_error.code if last_error else "action_execution_failed",
        )

    async def _send_request(
        self,
        *,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        query_params: dict[str, Any] | None,
        body: Any,
    ) -> httpx.Response:
        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": query_params,
        }
        if body is not None:
            if isinstance(body, (dict, list)):
                request_kwargs["json"] = body
            else:
                request_kwargs["content"] = str(body)

        async with client.stream(**request_kwargs) as response:
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > MAX_RESPONSE_SIZE:
                    raise ActionExecutionError("response_too_large", "Response exceeds max allowed size.")
                chunks.append(chunk)
            content = b"".join(chunks)
            built = httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=content,
                request=response.request,
            )
            return built

    @staticmethod
    def _normalize_response(*, response: httpx.Response, duration_ms: int) -> ActionExecutionResult:
        headers = {k.lower(): v for k, v in response.headers.items()}
        success = 200 <= response.status_code < 400
        data: Any = None
        text: str | None = None

        content_type = headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                data = response.json()
            except json.JSONDecodeError as exc:
                text = response.text
                return ActionExecutionResult(
                    success=False,
                    status_code=response.status_code,
                    headers=headers,
                    data=None,
                    text=text,
                    duration_ms=duration_ms,
                    error=f"invalid_response: {exc}",
                )
        else:
            text = response.text

        error = None if success else "action_execution_failed"
        return ActionExecutionResult(
            success=success,
            status_code=response.status_code,
            headers=headers,
            data=data,
            text=text,
            duration_ms=duration_ms,
            error=error,
        )

