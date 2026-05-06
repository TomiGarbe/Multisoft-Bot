from typing import Any

from app.interfaces.ai.ai_interface import AIInterface


class MockAIProvider(AIInterface):
    async def generate(self, prompt: str) -> str:
        return "This is a mock response"

    async def generate_with_metadata(self, prompt: str) -> dict[str, Any]:
        return {
            "response": await self.generate(prompt),
            "prompt_eval_count": 0,
            "eval_count": 0,
            "model": "mock",
        }

