from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.messaging.web_provider import WebProvider
from app.providers.messaging.whatsapp_multisoft_provider import WhatsAppMultisoftProvider
from app.providers.messaging.catalog import normalize_provider_value
from app.providers.ai.ollama_provider import OllamaProvider
from app.providers.ai.mock_provider import MockAIProvider
from app.interfaces.ai.ai_interface import AIInterface

def get_message_provider(provider_name: str):
    normalized = normalize_provider_value(provider_name)

    if normalized == "multisoft":
        return WhatsAppMultisoftProvider()

    if normalized == "web":
        return WebProvider()

    if normalized == "mock":
        return MockMessageProvider()

    raise ValueError(f"Unsupported message provider: {provider_name}")


def get_ai_provider(provider_name: str | None = None) -> AIInterface:
    normalized = (provider_name or "ollama").strip().lower()
    if normalized == "mock":
        return MockAIProvider()
    return OllamaProvider()
