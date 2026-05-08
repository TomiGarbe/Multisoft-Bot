from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.messaging.web_provider import WebProvider
from app.providers.messaging.whatsapp_multisoft_provider import WhatsAppMultisoftProvider
from app.providers.ai.ollama_provider import OllamaProvider
from app.providers.ai.mock_provider import MockAIProvider
from app.interfaces.ai.ai_interface import AIInterface

def get_message_provider(channel_type: str):
    normalized = (channel_type or "").strip().lower()

    if normalized == "web":
        return WebProvider()

    if normalized == "whatsapp":
        return WhatsAppMultisoftProvider()

    if normalized == "mock":
        return MockMessageProvider()

    raise ValueError(f"Unsupported message provider channel type: {channel_type}")


def get_ai_provider(provider_name: str | None = None) -> AIInterface:
    normalized = (provider_name or "ollama").strip().lower()
    if normalized == "mock":
        return MockAIProvider()
    return OllamaProvider()
