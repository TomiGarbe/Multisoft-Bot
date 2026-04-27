from app.providers.provider_factory import get_ai_provider
from app.interfaces.ai.ai_interface import AIInterface


class AIService:
    def __init__(self):
        self.provider: AIInterface = get_ai_provider()

    async def generate(self, prompt: str) -> str:
        return await self.provider.generate(prompt)
