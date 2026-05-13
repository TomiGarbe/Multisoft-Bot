from __future__ import annotations

import json
from typing import Any

from app.schemas.internal.bot_actions.execution import ActionExecutionResult
from app.utils.ai_tool_constants import MAX_TOOL_RESULT_BYTES
from app.utils.bot_actions_sanitization import sanitize_nested_secrets, truncate_payload


def serialize_action_result_for_model(
    result: ActionExecutionResult,
    *,
    max_bytes: int = MAX_TOOL_RESULT_BYTES,
) -> dict[str, Any]:
    payload = {
        "success": result.success,
        "status_code": result.status_code,
        "data": truncate_payload(sanitize_nested_secrets(result.data), max_bytes=max_bytes),
        "error": truncate_payload(result.error, max_bytes=max_bytes) if result.error else None,
        "message": truncate_payload(result.message, max_bytes=max_bytes) if result.message else None,
        "exception_type": result.exception_type,
        "safe_details": truncate_payload(
            sanitize_nested_secrets(result.safe_details),
            max_bytes=max_bytes,
        ) if result.safe_details else None,
    }
    encoded = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    if len(encoded) <= max_bytes:
        return payload

    payload["data"] = "[truncated]"
    payload["error"] = truncate_payload(payload.get("error"), max_bytes=max_bytes // 2)
    return payload
