from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.bot_action import BotAction
from app.services.ai.tool_result_serializer import serialize_action_result_for_model
from app.services.bot_actions import ActionExecutionError, ActionExecutionService, ActionExecutionResult


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
        try:
            execution_payload = await self.executor.execute_test_action(
                tenant_id=tenant_id,
                action_id=action.id,
                variables=arguments,
            )
            response_payload = execution_payload.get("response") or {}
            result = ActionExecutionResult.model_validate(response_payload)
            return serialize_action_result_for_model(result)
        except (LookupError, ActionExecutionError, ValueError) as exc:
            return {
                "success": False,
                "status_code": None,
                "error": str(exc),
            }
        except Exception:
            return {
                "success": False,
                "status_code": None,
                "error": "tool_execution_failed",
            }
