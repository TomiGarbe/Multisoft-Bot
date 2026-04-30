from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.messaging.web_provider import WebProvider
from app.providers.ai.ollama_provider import OllamaProvider
from app.interfaces.ai.ai_interface import AIInterface

def get_message_provider(channel_type: str):

    if channel_type == "web":
        return WebProvider()
    
    if channel_type == "mock":
        return MockMessageProvider()

    # otros providers (whatsapp, etc)


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
