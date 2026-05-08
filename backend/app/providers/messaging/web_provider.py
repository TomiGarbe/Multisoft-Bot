import uuid
from typing import Any, Optional

from app.core.utils import dict_get_any_case, safe_timestamp, to_bool
from app.interfaces.messaging.message_provider import MessageProvider
from app.schemas.internal.normalized_message import NormalizedMessage


class WebProvider(MessageProvider):
    def normalize_incoming_payload(self, channel_id: str, payload: dict[str, Any]) -> NormalizedMessage:
        external_id = str(dict_get_any_case(payload, "id", "external_message_id", default="") or "")
        return NormalizedMessage(
            channel_id=channel_id,
            external_message_id=external_id,
            sender_external_id=dict_get_any_case(payload, "from", "sender_id"),
            sender_name=dict_get_any_case(payload, "sender_name", "notifyName"),
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
        channel_id: str,
        to: str,
        content: str,
        *,
        reply_to_message_id: Optional[str] = None,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ):
        return {
            "provider_message_id": str(uuid.uuid4()),
            "status": "sent",
        }

    def send_media(
        self,
        channel_id: str,
        to: str,
        media_url: str,
        caption: str | None,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ):
        return {
            "provider_message_id": str(uuid.uuid4()),
            "status": "sent",
        }

    def reply_to_message(
        self,
        channel_id: str,
        to: str,
        content: str,
        reply_to_id: str,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ):
        return {
            "provider_message_id": str(uuid.uuid4()),
            "status": "sent",
        }
