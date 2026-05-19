from abc import ABC, abstractmethod
from typing import Any


class AIInterface(ABC):
    """Base interface for AI providers"""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a response based on the given prompt.
        
        Args:
            prompt: The input prompt for the AI model
            
        Returns:
            The generated text response from the AI model
            
        Raises:
            Exception: If the AI provider fails to generate a response
        """
        pass

    async def generate_with_metadata(self, prompt: str) -> dict[str, Any]:
        """
        Optional richer response for providers that expose usage counters.
        Default implementation preserves backward compatibility.
        """
        response = await self.generate(prompt)
        return {
            "response": response,
            "prompt_eval_count": None,
            "eval_count": None,
            "model": None,
        }

    async def generate_chat_with_metadata(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Optional chat+tools interface.
        Default fallback keeps backwards compatibility by flattening to prompt.
        """
        prompt = "\n".join(str(message.get("content") or "") for message in messages if message.get("content"))
        return await self.generate_with_metadata(prompt)

    def supports_vision(self) -> bool:
        return False

    def supports_text(self) -> bool:
        return True

    def supports_audio(self) -> bool:
        return self.supports_vision()

    def supports_documents(self) -> bool:
        return self.supports_vision()

    def supports_video(self) -> bool:
        return self.supports_vision()

    def supports_streaming(self) -> bool:
        return False

    def supports_tools(self) -> bool:
        return False
