from app.services.ai.config_resolver import get_sections_by_type


class PromptBuilder:

    def build(
        self,
        config: dict,
        messages: list[dict],
        user_memory: dict | None,
        current_message: str | None,
        user_type: str,
    ) -> str:
        config = get_sections_by_type(config, user_type)

        prompt = "\n\n".join([
            self.build_identity(config),
            self.build_tone(config),
            self.build_rules(config),
            self.build_objective(config),
            self.build_data_collection(config),
            self.build_actions(config),
            self.build_memory(user_memory),
            self.build_conversation(messages),
            self.build_current_message(current_message),
        ])

        return prompt

    def build_identity(self, config: dict) -> str:
        identity = config.get("identity", "")
        if not identity:
            return ""
        return f"[IDENTIDAD]\n{identity}"

    def build_tone(self, config: dict) -> str:
        tone = config.get("tone", "")
        if not tone:
            return ""
        return f"[TONO]\n{tone}"

    def build_rules(self, config: dict) -> str:
        rules = config.get("rules", [])
        if not rules or not isinstance(rules, list):
            return ""
        lines = "\n".join(f"* {rule}" for rule in rules)
        return f"[REGLAS]\n{lines}"

    def build_objective(self, config: dict) -> str:
        objectives = config.get("objectives", [])
        if not objectives or not isinstance(objectives, list):
            return ""
        lines = "\n".join(f"* {obj}" for obj in objectives)
        return f"[OBJETIVO]\n{lines}"

    def build_data_collection(self, config: dict) -> str:
        data_collection = config.get("data_collection", [])
        if not data_collection or not isinstance(data_collection, list):
            return ""
        lines = "\n".join(f"* {item}" for item in data_collection)
        return f"[RECOLECCIÓN DE DATOS]\n{lines}"

    def build_actions(self, config: dict) -> str:
        actions = config.get("actions", [])
        if not actions or not isinstance(actions, list):
            return ""
        lines = "\n".join(f"* {action}" for action in actions)
        return f"[ACCIONES]\n{lines}"

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
        return f"[CONVERSACIÓN]\n" + "\n".join(lines)

    def build_current_message(self, current_message: str | None) -> str:
        if not current_message or not isinstance(current_message, str):
            return ""
        return f"[MENSAJE ACTUAL]\nUsuario: {current_message}"
