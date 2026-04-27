from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.ai.ollama_provider import OllamaProvider
from app.interfaces.ai.ai_interface import AIInterface


def get_message_provider(type: str = "mock") -> MockMessageProvider:
    return MockMessageProvider()


def get_ai_provider() -> AIInterface:
    """
    Get the AI provider instance.
    
    Currently hardcoded to return OllamaProvider.
    In the future, this can be extended with conditional logic
    to support multiple providers based on configuration.
    
    Returns:
        AIInterface: An instance of OllamaProvider
    """
    return OllamaProvider()
