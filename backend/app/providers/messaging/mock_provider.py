import logging
from typing import Any, Optional

from app.core.utils import dict_get_any_case, safe_timestamp, to_bool
from app.interfaces.messaging.message_provider import MessageProvider
from app.schemas.internal.normalized_message import NormalizedMessage

logger = logging.getLogger(__name__)


class MockMessageProvider(MessageProvider):
    def normalize_incoming_payload(self, channel_id: str, payload: dict[str, Any]) -> NormalizedMessage:
        return NormalizedMessage(
            channel_id=channel_id,
            external_message_id=str(dict_get_any_case(payload, "id", default="") or ""),
            sender_external_id=dict_get_any_case(payload, "from", "sender_id"),
            sender_name=dict_get_any_case(payload, "sender_name"),
            content=dict_get_any_case(payload, "text", "body"),
            message_type=str(dict_get_any_case(payload, "type", default="text") or "text"),
            is_group=to_bool(dict_get_any_case(payload, "is_group", "isGroup"), default=False),
            group_id=dict_get_any_case(payload, "group_id", "fromId"),
            replied_to_message_id=dict_get_any_case(payload, "replied_to_message_id", "quotedMessageId", "replyToMessageId"),
            is_status=to_bool(dict_get_any_case(payload, "is_status", "isStatus"), default=False),
            is_bot=to_bool(dict_get_any_case(payload, "is_bot", "from_me", "fromMe"), default=False),
            has_media=to_bool(dict_get_any_case(payload, "has_media", "hasMedia"), default=False),
            media_url=dict_get_any_case(payload, "media_url", "mediaUrl"),
            timestamp=safe_timestamp(dict_get_any_case(payload, "timestamp")),
            raw_payload=payload,
        )

    def send_text(
        self,
        channel: str,
        to: str,
        content: str,
        *,
        reply_to_message_id: Optional[str] = None,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        logger.info(
            "[MOCK] send_text | channel=%s | to=%s | reply_to_message_id=%s | content=%s",
            channel, to, reply_to_message_id, content,
        )
        return {"status": "sent", "provider_message_id": "mock-id"}

    def send_media(
        self,
        channel: str,
        to: str,
        media_url: str,
        caption: str = None,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        logger.info(f"[MOCK] send_media | channel={channel} | to={to} | media_url={media_url} | caption={caption}")
        return {"status": "sent", "provider_message_id": "mock-id"}

    def reply_to_message(
        self,
        channel: str,
        to: str,
        content: str,
        reply_to_id: str,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        logger.info(f"[MOCK] reply_to_message | channel={channel} | to={to} | reply_to_id={reply_to_id} | content={content}")
        return {"status": "sent", "provider_message_id": "mock-id"}
