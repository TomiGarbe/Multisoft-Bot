import logging
from typing import Any, Callable, Optional

from app.providers.provider_factory import get_ai_provider
from app.interfaces.ai.ai_interface import AIInterface
from app.services.conversation.guards import should_use_ai

logger = logging.getLogger(__name__)


class AIService:
    """
    Punto único de ejecución de IA. Toda invocación al proveedor pasa por aquí.

    - `generate_for_conversation`: entrada de producción. Aplica el gate
      `should_use_ai` (modo "ai" + config válida) antes de llamar al proveedor.
    - `generate`: llamada cruda. Sólo para flujos sin conversación
      (p.ej. /ai/test). El caller debe haber validado la config primero.
    """

    def __init__(
        self,
        provider: AIInterface | None = None,
        provider_resolver: Callable[[str | None], AIInterface] = get_ai_provider,
        provider_name: str | None = None,
    ):
        self.provider: AIInterface = provider or provider_resolver(provider_name)

    async def generate_for_conversation(
        self,
        prompt: str,
        conversation: Any,
        channel_config: Any,
    ) -> Optional[str]:
        if not should_use_ai(conversation, channel_config):
            logger.info(
                "AI gate blocked execution (conversation_id=%s)",
                getattr(conversation, "id", None),
            )
            return None
        return await self.provider.generate(prompt)

    async def generate(self, prompt: str) -> str:
        return await self.provider.generate(prompt)

    async def generate_with_metadata(self, prompt: str) -> dict[str, Any]:
        return await self.provider.generate_with_metadata(prompt)

    async def generate_chat_with_metadata(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        uses_default_chat = (
            self.provider.__class__.generate_chat_with_metadata
            is AIInterface.generate_chat_with_metadata
        )
        if uses_default_chat:
            logger.warning(
                "AI provider does not implement native tool-calling chat endpoint (provider=%s). "
                "Falling back to flattened prompt; tools may be ignored.",
                self.provider.__class__.__name__,
            )
        return await self.provider.generate_chat_with_metadata(messages, tools=tools)
