from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.bot_action import BotAction
from app.services.ai.tool_result_serializer import serialize_action_result_for_model
from app.services.bot_actions import ActionExecutionError, ActionExecutionService, ActionExecutionResult

logger = logging.getLogger(__name__)


class AIToolExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.executor = ActionExecutionService(db)

    async def execute_tool_call(
        self,
        *,
        tenant_id: uuid.UUID,
        action: BotAction,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        logger.info(
            "AI TOOL EXECUTION START (tenant_id=%s action_name=%s action_id=%s args=%s method=%s url=%s)",
            tenant_id,
            action.name,
            action.id,
            arguments,
            getattr(action.method, "value", None),
            action.url,
        )
        try:
            execution_payload = await self.executor.execute_test_action(
                tenant_id=tenant_id,
                action_id=action.id,
                variables=arguments,
            )
            logger.info(
                "AI TOOL EXECUTION HTTP TRACE (action_name=%s request=%s response=%s)",
                action.name,
                execution_payload.get("request"),
                execution_payload.get("response"),
            )
            response_payload = execution_payload.get("response") or {}
            result = ActionExecutionResult.model_validate(response_payload)
            serialized = serialize_action_result_for_model(result)
            logger.info(
                "AI TOOL RESULT SERIALIZED (action_name=%s result_for_model=%s)",
                action.name,
                serialized,
            )
            return serialized
        except (LookupError, ActionExecutionError, ValueError) as exc:
            logger.warning(
                "AI TOOL EXECUTION CONTROLLED ERROR (action_name=%s exception_class=%s error=%s)",
                action.name,
                exc.__class__.__name__,
                str(exc),
                exc_info=True,
            )
            return {
                "success": False,
                "status_code": None,
                "error": str(exc),
            }
        except Exception:
            logger.warning(
                "AI TOOL EXECUTION EXCEPTION (action_name=%s)",
                action.name,
                exc_info=True,
            )
            return {
                "success": False,
                "status_code": None,
                "error": "tool_execution_failed",
            }
