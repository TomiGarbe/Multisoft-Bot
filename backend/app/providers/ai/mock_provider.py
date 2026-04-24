import logging
from app.interfaces.ai.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class MockAIProvider(AIProvider):

    def generate_response(self, conversation: dict, messages: list) -> str:
        logger.info(f"[MOCK] generate_response | conversation_id={conversation.get('id')} | messages_count={len(messages)}")
        return "This is a mock response"
