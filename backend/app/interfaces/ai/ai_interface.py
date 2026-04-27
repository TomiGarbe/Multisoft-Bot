from abc import ABC, abstractmethod


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
