import logging
logger = logging.getLogger(__name__)

class PromptBuilder:

    def build(
        self,
        config: dict,
        messages: list[dict],
        user_memory: dict | None,
        current_message: str | None,
        user_type: str,
    ) -> str:
        prompt = "\n\n".join(filter(None, [
            self.build_identity(config),
            self.build_tone(config),
            self.build_rules(config),
            self.build_objective(config, user_type),
            self.build_data_collection(config, user_type),
            self.build_actions(config, user_type),
            self.build_memory(user_memory),
            self.build_conversation(messages),
            self.build_current_message(current_message),
        ]))
        logger.warning("Built prompt for user_type=%s: %s", user_type, prompt)
        return prompt

    def build_identity(self, config: dict) -> str:
        identity = config.get("identity", {})
        return f"""[IDENTIDAD]
Sos {identity.get("role", "un asistente")}.

{identity.get("description", "")}
Industria: {identity.get("industry", "")}
Idioma: {identity.get("language", "")}
"""

    def build_tone(self, config: dict) -> str:
        tone = config.get("tone", {})
        rules = "\n".join(f"- {r}" for r in tone.get("style_rules", []))
        return f"""[TONO]
{tone.get("tone", "")}

Reglas de estilo:
{rules}
"""

    def build_rules(self, config: dict) -> str:
        rules_section = config.get("rules", {})
        rules = "\n".join(f"- {r}" for r in rules_section.get("rules", []))
        return f"""[REGLAS]
{rules}
"""

    def _filter_by_user_type(self, blocks: list, user_type: str) -> list:
        if not blocks:
            return []
        return [b for b in blocks if user_type in b.get("applies_to", [])]

    def build_objective(self, config: dict, user_type: str) -> str:
        valid = self._filter_by_user_type(config.get("objectives", []), user_type)
        if not valid:
            return ""
        lines = []
        for obj in valid:
            lines.append(f"Objetivo: {obj.get('description', '')}")
            if obj.get("objective_type"):
                lines.append(f"Tipo: {obj.get('objective_type')}")
            if obj.get("conversation_flow"):
                lines.append("Flujo:")
                for step in obj.get("conversation_flow", []):
                    lines.append(f"- {step}")
        return f"""[OBJETIVO]
{chr(10).join(lines)}
"""

    def build_data_collection(self, config: dict, user_type: str) -> str:
        valid = self._filter_by_user_type(config.get("data_collection", []), user_type)
        if not valid:
            return ""
        lines = []
        for dc in valid:
            for field in dc.get("fields", []):
                required = "obligatorio" if field.get("required") else "opcional"
                lines.append(f"- {field.get('name')} ({required})")
        return f"""[DATOS A RECOLECTAR]
{chr(10).join(lines)}
"""

    def build_actions(self, config: dict, user_type: str) -> str:
        valid = self._filter_by_user_type(config.get("actions", []), user_type)
        if not valid:
            return ""
        lines = []
        for block in valid:
            for action in block.get("actions", []):
                lines.append(f"- {action.get('name')}")
        return f"""[ACCIONES]
{chr(10).join(lines)}
"""

    def build_memory(self, user_memory: dict | None) -> str:
        if not user_memory or not isinstance(user_memory, dict):
            return ""
        lines = "\n".join(f"{key}: {value}" for key, value in user_memory.items())
        if not lines:
            return ""
        return f"[MEMORIA USUARIO]\n{lines}"

    def build_conversation(self, messages: list[dict]) -> str:
        if not messages or not isinstance(messages, list):
            return ""
        role_labels = {"user": "Usuario", "assistant": "Asistente"}
        lines = []
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            label = role_labels.get(role)
            if label and content:
                lines.append(f"{label}: {content}")
        if not lines:
            return ""
        return "[CONVERSACIÓN]\n" + "\n".join(lines)

    def build_current_message(self, current_message: str | None) -> str:
        if not current_message or not isinstance(current_message, str):
            return ""
        return f"[MENSAJE ACTUAL]\nUsuario: {current_message}"
