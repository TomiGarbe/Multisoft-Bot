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
        context = {
            "messages": messages,
            "user_memory": user_memory,
            "current_message": current_message,
            "user_type": user_type,
        }
        prompt = self.build_prompt(config=config, context=context)
        logger.warning("Built prompt for user_type=%s: %s", user_type, prompt)
        return prompt

    def build_prompt(self, config: dict, context: dict) -> str:
        user_type = context.get("user_type", "default")
        sections = [
            self.build_identity(config),
            self.build_tone(config),
            self.build_rules(config),
            self.build_objective(config, user_type),
            self.build_conversation_context(context),
        ]
        return "\n\n".join(section for section in sections if section).strip()

    def build_identity(self, config: dict) -> str:
        identity = config.get("identity", {})
        lines = []

        role = identity.get("role")
        bot_name = identity.get("bot_name")
        industry = identity.get("industry")
        language = identity.get("language")
        description = identity.get("description")

        if role:
            lines.append(f"Rol: {role}")
        if bot_name:
            lines.append(f"Nombre del bot: {bot_name}")
        if industry:
            lines.append(f"Industria: {industry}")
        if language:
            lines.append(f"Idioma: {language}")
        if description:
            lines.append(f"Descripcion: {description}")

        if not lines:
            return ""
        return "[IDENTIDAD]\n" + "\n".join(lines)

    def build_tone(self, config: dict) -> str:
        tone = config.get("tone", {})
        lines = []

        tone_value = tone.get("tone")
        if tone_value:
            lines.append(f"Tono: {tone_value}")

        style_rules = [rule for rule in tone.get("style_rules", []) if rule]
        if style_rules:
            lines.append("Reglas de estilo:")
            lines.extend(f"- {rule}" for rule in style_rules)

        if not lines:
            return ""
        return "[TONO]\n" + "\n".join(lines)

    def build_rules(self, config: dict) -> str:
        rules_section = config.get("rules", {})
        lines = []

        rules = [rule for rule in rules_section.get("rules", []) if rule]
        if rules:
            lines.append("Reglas:")
            lines.extend(f"- {rule}" for rule in rules)

        fallback = rules_section.get("fallback_message") or config.get("behavior", {}).get("fallback_message")
        if fallback:
            lines.append(f"Fallback: {fallback}")

        if not lines:
            return ""
        return "[REGLAS]\n" + "\n".join(lines)

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
            description = obj.get("description")
            objective_type = obj.get("objective_type")
            if description:
                lines.append(f"Objetivo: {description}")
            if objective_type:
                lines.append(f"Tipo: {objective_type}")
            flow = [step for step in obj.get("conversation_flow", []) if step]
            if flow:
                lines.append("Flujo:")
                lines.extend(f"- {step}" for step in flow)

        if not lines:
            return ""
        return "[OBJETIVOS]\n" + "\n".join(lines)

    def build_conversation(self, messages: list[dict]) -> str:
        if not messages or not isinstance(messages, list):
            return ""

        role_labels = {"user": "Usuario", "assistant": "Asistente"}
        lines = []
        for msg in messages:
            role = (msg.get("role") or "").lower()
            content = msg.get("content")
            label = role_labels.get(role)
            if label and content:
                lines.append(f"{label}: {content}")

        if not lines:
            return ""
        return "[CONVERSACION]\n" + "\n".join(lines)

    def build_current_message(self, current_message: str | None) -> str:
        if not current_message or not isinstance(current_message, str):
            return ""
        return f"[MENSAJE ACTUAL]\nUsuario: {current_message}"

    def build_conversation_context(self, context: dict) -> str:
        chunks = []

        user_memory = context.get("user_memory")
        if isinstance(user_memory, dict) and user_memory:
            memory_lines = [
                f"- {key}: {value}"
                for key, value in user_memory.items()
                if value is not None and str(value).strip()
            ]
            if memory_lines:
                chunks.append("Memoria de usuario:\n" + "\n".join(memory_lines))

        conversation = self.build_conversation(context.get("messages", []))
        current_message = self.build_current_message(context.get("current_message"))

        if conversation:
            chunks.append(conversation)
        if current_message:
            chunks.append(current_message)

        if not chunks:
            return ""
        return "[CONTEXTO]\n" + "\n\n".join(chunks)


def build_prompt(config: dict, context: dict) -> str:
    return PromptBuilder().build_prompt(config=config, context=context)
