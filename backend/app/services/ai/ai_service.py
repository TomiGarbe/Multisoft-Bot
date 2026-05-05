import logging
from typing import Any, Optional

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

    def __init__(self):
        self.provider: AIInterface = get_ai_provider()

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
