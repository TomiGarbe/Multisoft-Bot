from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.bot_action import BotActionExecution
from app.repositories.bot_action_execution_repository import BotActionExecutionRepository
from app.repositories.bot_action_repository import BotActionRepository
from app.services.bot_actions.auth_applier import apply_auth_config
from app.services.bot_actions.errors import ActionExecutionError
from app.services.bot_actions.http_client_service import HttpClientService
from app.schemas.internal.bot_actions.execution import ActionExecutionResult
from app.services.bot_actions.template_engine import render_template_object, render_template_value
from app.utils.bot_actions_constants import MAX_BODY_SIZE, MAX_RETRY_COUNT, MAX_TIMEOUT_MS
from app.utils.bot_actions_sanitization import sanitize_nested_secrets, truncate_payload
from app.utils.bot_actions_validators import validate_external_url_or_raise


class ActionExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.action_repository = BotActionRepository(db)
        self.execution_repository = BotActionExecutionRepository(db)
        self.http_client = HttpClientService()

    async def execute_test_action(
        self,
        *,
        tenant_id: uuid.UUID,
        action_id: uuid.UUID,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        action = self.action_repository.get_by_id(action_id=action_id, tenant_id=tenant_id)
        if action is None:
            raise LookupError("action_not_found")

        timeout_ms = action.timeout_ms or MAX_TIMEOUT_MS
        retry_count = action.retry_count if action.retry_count is not None else 0
        retry_count = min(max(retry_count, 0), MAX_RETRY_COUNT)

        try:
            rendered_url = render_template_value(action.url, variables)
            if not isinstance(rendered_url, str):
                raise ActionExecutionError("invalid_placeholder", "Rendered URL must be a string.")
            validate_external_url_or_raise(rendered_url)
        except ValueError:
            raise ActionExecutionError("forbidden_url")

        headers = render_template_object(action.headers_jsonb or {}, variables)
        query_params = render_template_object(action.query_params_jsonb or {}, variables)
        body = render_template_object(action.body_jsonb, variables)
        if body is not None and len(str(body).encode("utf-8")) > MAX_BODY_SIZE:
            raise ActionExecutionError("request_body_too_large", "Request body exceeds max allowed size.")

        headers = {str(k): str(v) for k, v in (headers or {}).items()}
        query_params = dict(query_params or {})

        auth_config = dict(action.auth_jsonb or {"type": "none"})
        final_headers, final_query_params = apply_auth_config(
            auth_config=auth_config,
            headers=headers,
            query_params=query_params,
        )

        request_payload = {
            "method": action.method.value,
            "url": rendered_url,
            "headers": final_headers,
            "query_params": final_query_params,
            "body": body,
            "timeout_ms": timeout_ms,
            "retry_count": retry_count,
        }
        sanitized_request = sanitize_nested_secrets(request_payload)
        sanitized_request["body"] = truncate_payload(sanitized_request.get("body"))

        result = await self.http_client.execute(
            method=action.method.value,
            url=rendered_url,
            headers=final_headers,
            query_params=final_query_params,
            body=body,
            timeout_ms=timeout_ms,
            retry_count=retry_count,
        )

        response_payload = result.model_dump(mode="json")
        sanitized_response = sanitize_nested_secrets(response_payload)
        sanitized_response["data"] = truncate_payload(sanitized_response.get("data"))
        sanitized_response["text"] = truncate_payload(sanitized_response.get("text"))

        self._log_execution(
            action_id=action.id,
            request=sanitized_request,
            response=sanitized_response,
            result=result,
        )

        return {
            "request": sanitized_request,
            "response": sanitized_response,
            "timing": {"duration_ms": result.duration_ms},
            "success": result.success,
            "error": result.error,
        }

    def _log_execution(
        self,
        *,
        action_id: uuid.UUID,
        request: dict[str, Any],
        response: dict[str, Any],
        result: ActionExecutionResult,
    ) -> None:
        execution = BotActionExecution(
            bot_action_id=action_id,
            request_jsonb=request,
            response_jsonb=response,
            status_code=result.status_code,
            success=result.success,
            error_message=result.error,
            duration_ms=result.duration_ms,
        )
        try:
            self.execution_repository.create(execution)
            self.execution_repository.commit()
        except Exception:
            self.execution_repository.rollback()
            raise
