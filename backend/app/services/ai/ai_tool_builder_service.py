from __future__ import annotations

from typing import Any

from app.models.bot_action import BotAction


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

        return {
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
