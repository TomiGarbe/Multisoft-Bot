import logging
from app.interfaces.messaging.message_provider import MessageProvider

logger = logging.getLogger(__name__)


class MockMessageProvider(MessageProvider):

    def send_text(self, channel: str, to: str, content: str) -> dict:
        logger.info(f"[MOCK] send_text | channel={channel} | to={to} | content={content}")
        return {"status": "sent", "provider_message_id": "mock-id"}

    def send_media(self, channel: str, to: str, media_url: str, caption: str = None) -> dict:
        logger.info(f"[MOCK] send_media | channel={channel} | to={to} | media_url={media_url} | caption={caption}")
        return {"status": "sent", "provider_message_id": "mock-id"}

    def reply_to_message(self, channel: str, to: str, content: str, reply_to_id: str) -> dict:
        logger.info(f"[MOCK] reply_to_message | channel={channel} | to={to} | reply_to_id={reply_to_id} | content={content}")
        return {"status": "sent", "provider_message_id": "mock-id"}
