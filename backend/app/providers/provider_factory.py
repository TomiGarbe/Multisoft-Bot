from app.providers.messaging.mock_provider import MockMessageProvider
from app.providers.ai.mock_provider import MockAIProvider


def get_message_provider(type: str = "mock") -> MockMessageProvider:
    return MockMessageProvider()


def get_ai_provider() -> MockAIProvider:
    return MockAIProvider()
