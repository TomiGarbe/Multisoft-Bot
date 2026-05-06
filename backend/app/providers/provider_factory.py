from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.messaging.web_provider import WebProvider
from app.providers.ai.ollama_provider import OllamaProvider
from app.providers.ai.mock_provider import MockAIProvider
from app.interfaces.ai.ai_interface import AIInterface

def get_message_provider(channel_type: str):

    if channel_type == "web":
        return WebProvider()
    
    if channel_type == "mock":
        return MockMessageProvider()

    # otros providers (whatsapp, etc)


def get_ai_provider(provider_name: str | None = None) -> AIInterface:
    normalized = (provider_name or "ollama").strip().lower()
    if normalized == "mock":
        return MockAIProvider()
    return OllamaProvider()
