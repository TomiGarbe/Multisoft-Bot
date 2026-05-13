from __future__ import annotations

import logging
from typing import Any

from app.models.bot_action import BotAction

logger = logging.getLogger(__name__)


class AIToolBuilderService:
    def build_from_action(self, action: BotAction) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        for variable in (action.variables_jsonb or []):
            if not isinstance(variable, dict):
                continue
            name = str(variable.get("name") or "").strip()
            if not name:
                continue
            var_type = str(variable.get("type") or "string").strip().lower()
            description = str(variable.get("description") or "").strip()
            properties[name] = {
                "type": var_type if var_type in {"string", "number", "boolean", "object", "array"} else "string",
                "description": description or f"Parametro '{name}' para ejecutar la accion.",
            }
            if bool(variable.get("required")):
                required.append(name)

        description_parts: list[str] = []
        if action.description:
            description_parts.append(action.description.strip())
        if action.trigger_prompt:
            description_parts.append(f"Cuando usar: {action.trigger_prompt.strip()}")

        tool_payload = {
            "type": "function",
            "function": {
                "name": action.name,
                "description": " ".join(part for part in description_parts if part).strip() or f"Ejecuta '{action.name}'.",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
        logger.info(
            "AI TOOL BUILT (name=%s method=%s url=%s description=%s schema=%s)",
            action.name,
            getattr(action.method, "value", None),
            action.url,
            tool_payload["function"]["description"],
            tool_payload["function"]["parameters"],
        )
        return tool_payload
