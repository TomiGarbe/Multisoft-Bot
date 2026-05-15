from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.messaging.web_provider import WebProvider
from app.providers.messaging.whatsapp_multisoft_provider import WhatsAppMultisoftProvider
from app.providers.messaging.catalog import normalize_provider_value
from app.providers.ai.ollama_provider import OllamaProvider
from app.providers.ai.deepseek_provider import DeepSeekProvider
from app.providers.ai.mock_provider import MockAIProvider
from app.interfaces.ai.ai_interface import AIInterface
from app.core.config import settings

_PRIMARY_PROVIDER = "deepseek"

def get_message_provider(provider_name: str):
    normalized = normalize_provider_value(provider_name)

    if normalized == "multisoft":
        return WhatsAppMultisoftProvider()

    if normalized == "web":
        return WebProvider()

    if normalized == "mock":
        return MockMessageProvider()

    raise ValueError(f"Unsupported message provider: {provider_name}")


def get_ai_provider(
    provider_name: str | None = None,
    *,
    model: str | None = None,
    timeout_seconds: float | None = None,
) -> AIInterface:
    normalized = (provider_name or settings.AI_PROVIDER or _PRIMARY_PROVIDER).strip().lower()
    if normalized == "mock":
        return MockAIProvider()
    if normalized == "deepseek":
        return DeepSeekProvider(model=model, timeout_seconds=timeout_seconds)
    if normalized == "ollama":
        return OllamaProvider(model=model, timeout_seconds=timeout_seconds)
    raise ValueError(f"Unsupported AI provider: {normalized}")
