import logging
from typing import Any, Optional

from app.core.utils import dict_get_any_case, safe_timestamp, to_bool
from app.interfaces.messaging.message_provider import MessageProvider
from app.providers.messaging.attachment_normalization import (
    normalize_attachments_from_payload,
    resolve_message_type,
)
from app.schemas.internal.message_enums import MessageType
from app.schemas.internal.normalized_message import NormalizedMessage
from app.schemas.internal.outbound_media import OutboundMediaMessage

logger = logging.getLogger(__name__)


class MockMessageProvider(MessageProvider):
    def normalize_incoming_payload(self, channel_id: str, payload: dict[str, Any]) -> NormalizedMessage:
        message_type = resolve_message_type(dict_get_any_case(payload, "type", default=MessageType.TEXT.value))
        attachments = normalize_attachments_from_payload(
            payload,
            provider="mock",
            fallback_message_type=message_type,
        )
        return NormalizedMessage(
            channel_id=channel_id,
            external_message_id=str(dict_get_any_case(payload, "id", default="") or ""),
            sender_external_id=dict_get_any_case(payload, "from", "sender_id"),
            sender_name=dict_get_any_case(payload, "sender_name"),
            content=dict_get_any_case(payload, "text", "body"),
            message_type=message_type,
            is_group=to_bool(dict_get_any_case(payload, "is_group", "isGroup"), default=False),
            group_id=dict_get_any_case(payload, "group_id", "fromId"),
            replied_to_message_id=dict_get_any_case(payload, "replied_to_message_id", "quotedMessageId", "replyToMessageId"),
            is_status=to_bool(dict_get_any_case(payload, "is_status", "isStatus"), default=False),
            is_bot=to_bool(dict_get_any_case(payload, "is_bot", "from_me", "fromMe"), default=False),
            has_media=bool(attachments),
            attachments=attachments,
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
        media_message: OutboundMediaMessage,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        logger.info(
            "[MOCK] send_media channel=%s to=%s attachments_count=%s fallback_text=%s",
            channel,
            to,
            len(media_message.attachments),
            media_message.fallback_text,
        )
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
