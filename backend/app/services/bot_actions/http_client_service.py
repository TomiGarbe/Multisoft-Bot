from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.services.bot_actions.errors import ActionExecutionError
from app.schemas.internal.bot_actions.execution import ActionExecutionResult
from app.utils.bot_actions_constants import MAX_RESPONSE_SIZE

logger = logging.getLogger(__name__)


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
                    logger.warning(
                        "TOOL HTTP TIMEOUT (method=%s url=%s attempt=%s/%s error=%s)",
                        method,
                        url,
                        attempt + 1,
                        attempts,
                        str(exc),
                        exc_warning=True,
                    )
                    last_error = ActionExecutionError(
                        "request_timeout",
                        str(exc),
                        exception_type=exc.__class__.__name__,
                    )
                    if attempt >= attempts - 1:
                        break
                except httpx.ConnectError as exc:
                    logger.warning(
                        "TOOL HTTP CONNECTION ERROR (method=%s url=%s attempt=%s/%s error=%s)",
                        method,
                        url,
                        attempt + 1,
                        attempts,
                        str(exc),
                        exc_warning=True,
                    )
                    last_error = ActionExecutionError(
                        "http_connection_error",
                        str(exc),
                        exception_type=exc.__class__.__name__,
                    )
                    if attempt >= attempts - 1:
                        break
                except httpx.DecodingError as exc:
                    logger.warning(
                        "TOOL HTTP DECODING ERROR (method=%s url=%s attempt=%s/%s error=%s)",
                        method,
                        url,
                        attempt + 1,
                        attempts,
                        str(exc),
                        exc_warning=True,
                    )
                    last_error = ActionExecutionError(
                        "http_decoding_error",
                        "Response decompression failed",
                        exception_type=exc.__class__.__name__,
                        safe_details={"raw_error": str(exc)},
                    )
                    if attempt >= attempts - 1:
                        break
                except ActionExecutionError as exc:
                    logger.warning(
                        "TOOL HTTP ACTION EXECUTION ERROR (method=%s url=%s error_code=%s message=%s)",
                        method,
                        url,
                        exc.code,
                        str(exc),
                        exc_warning=True,
                    )
                    last_error = exc
                    break
                except Exception as exc:  # pragma: no cover
                    logger.warning(
                        "TOOL HTTP UNEXPECTED EXCEPTION (method=%s url=%s exception_class=%s message=%s)",
                        method,
                        url,
                        exc.__class__.__name__,
                        str(exc),
                        exc_warning=True,
                    )
                    last_error = ActionExecutionError(
                        "action_execution_failed",
                        str(exc),
                        exception_type=exc.__class__.__name__,
                    )
                    break

        duration_ms = int((time.perf_counter() - started) * 1000)
        return ActionExecutionResult(
            success=False,
            duration_ms=duration_ms,
            error=last_error.code if last_error else "action_execution_failed",
            message=(last_error.message if last_error else "Action execution failed"),
            exception_type=(last_error.exception_type if last_error else None),
            safe_details=(last_error.safe_details if last_error else None),
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
            "headers": dict(headers or {}),
            "params": query_params,
        }
        if body is not None:
            if isinstance(body, (dict, list)):
                request_kwargs["json"] = body
            else:
                request_kwargs["content"] = str(body)

        try:
            response = await client.request(**request_kwargs)
        except httpx.DecodingError as exc:
            response_headers = request_kwargs["headers"]
            accept_encoding = str(response_headers.get("Accept-Encoding", "")).strip().lower()
            if accept_encoding != "identity":
                logger.warning(
                    "HTTP DECODE ERROR - retrying with Accept-Encoding=identity (method=%s url=%s error=%s)",
                    method,
                    url,
                    str(exc),
                )
                response_headers["Accept-Encoding"] = "identity"
                response = await client.request(**request_kwargs)
            else:
                raise

        if len(response.content) > MAX_RESPONSE_SIZE:
            raise ActionExecutionError("response_too_large", "Response exceeds max allowed size.")
        return response

    @staticmethod
    def _normalize_response(*, response: httpx.Response, duration_ms: int) -> ActionExecutionResult:
        headers = {k.lower(): v for k, v in response.headers.items()}
        logger.info(
            "HTTP response metadata (status=%s content_type=%s content_encoding=%s transfer_encoding=%s)",
            response.status_code,
            headers.get("content-type"),
            headers.get("content-encoding"),
            headers.get("transfer-encoding"),
        )
        success = 200 <= response.status_code < 400
        data: Any = None
        text: str | None = None

        content_type = headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError) as exc:
                text = response.text
                if success:
                    data = text
                else:
                    return ActionExecutionResult(
                        success=False,
                        status_code=response.status_code,
                        headers=headers,
                        data=None,
                        text=text,
                        duration_ms=duration_ms,
                        error="invalid_response",
                        message="Failed to parse JSON response body.",
                        exception_type=exc.__class__.__name__,
                        safe_details={"parse_error": str(exc)},
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

