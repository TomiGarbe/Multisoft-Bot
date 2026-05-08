import logging
import uuid
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.utils import dict_get_any_case, normalize_phone, safe_timestamp, to_bool
from app.interfaces.messaging.message_provider import MessageProvider
from app.schemas.internal.normalized_message import NormalizedMessage

logger = logging.getLogger(__name__)


class WhatsAppMultisoftProvider(MessageProvider):
    def normalize_incoming_payload(self, channel_id: str, payload: dict[str, Any]) -> NormalizedMessage:
        sender_id_raw = dict_get_any_case(payload, "from", "sender_id", "senderId")
        sender_id = normalize_phone(sender_id_raw) or (str(sender_id_raw) if sender_id_raw else None)
        message_type = str(dict_get_any_case(payload, "type", default="text") or "text").lower()
        is_status = (
            to_bool(dict_get_any_case(payload, "is_status", "isStatus"), default=False)
            or message_type == "status"
        )
        has_media = to_bool(dict_get_any_case(payload, "has_media", "hasMedia"), default=False)
        media_url = dict_get_any_case(payload, "media_url", "mediaUrl")
        if media_url:
            has_media = True

        return NormalizedMessage(
            channel_id=channel_id,
            external_message_id=str(
                dict_get_any_case(payload, "id", "messageId", "provider_message_id", default="") or ""
            ),
            sender_external_id=sender_id,
            sender_name=dict_get_any_case(payload, "sender_name", "notifyName", "name"),
            content=dict_get_any_case(payload, "text", "body", "message"),
            message_type=message_type,
            is_group=to_bool(dict_get_any_case(payload, "is_group", "isGroup"), default=False),
            group_id=dict_get_any_case(payload, "group_id", "fromId", "chatId"),
            replied_to_message_id=dict_get_any_case(
                payload,
                "replied_to_message_id",
                "quotedMessageId",
                "quoted_message_id",
                "replyToMessageId",
                "contextMessageId",
            ),
            is_status=is_status,
            is_bot=to_bool(dict_get_any_case(payload, "is_bot", "from_me", "fromMe"), default=False),
            has_media=has_media,
            media_url=media_url,
            timestamp=safe_timestamp(dict_get_any_case(payload, "timestamp", "createdAt")),
            raw_payload=payload,
        )

    def _resolve_webhook_url(self, channel_config: Optional[dict[str, Any]]) -> str:
        config_url = None
        if isinstance(channel_config, dict):
            config_url = channel_config.get("webhook_url")
        url = config_url or settings.WHATSAPP_MULTISOFT_WEBHOOK_URL
        if not url:
            raise ValueError("Missing WhatsApp webhook URL. Configure channel.config.webhook_url or WHATSAPP_MULTISOFT_WEBHOOK_URL")
        return str(url)

    def _resolve_from_number(
        self,
        channel_external_id: Optional[str],
        channel_config: Optional[dict[str, Any]],
    ) -> str:
        config_from = None
        if isinstance(channel_config, dict):
            config_from = channel_config.get("from_number")
        from_number = config_from or channel_external_id
        if not from_number:
            raise ValueError("Missing from number. Configure channel.external_id or channel.config.from_number")
        return str(from_number)

    def send_message(
        self,
        to_number: str,
        from_number: str,
        message: str,
        *,
        webhook_url: str,
        reply_to_message_id: Optional[str] = None,
    ) -> dict:
        timeout = httpx.Timeout(settings.WHATSAPP_MULTISOFT_TIMEOUT_SECONDS)
        data = {
            "number": str(to_number),
            "from": str(from_number),
            "message": message,
        }
        if reply_to_message_id:
            data["replyToMessageId"] = str(reply_to_message_id)

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(webhook_url, data=data)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.exception(
                "WhatsApp Multisoft HTTP error status=%s to=%s from=%s",
                exc.response.status_code,
                to_number,
                from_number,
            )
            raise
        except httpx.HTTPError:
            logger.exception("WhatsApp Multisoft transport error to=%s from=%s", to_number, from_number)
            raise

        provider_id = None
        try:
            payload = response.json()
            provider_id = payload.get("id") or payload.get("messageId") or payload.get("provider_message_id")
        except ValueError:
            payload = {"raw_text": response.text}

        return {
            "status": "sent",
            "provider_message_id": str(provider_id or uuid.uuid4()),
            "raw_response": payload,
        }

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
        webhook_url = self._resolve_webhook_url(channel_config)
        from_number = self._resolve_from_number(channel_external_id, channel_config)
        return self.send_message(
            to,
            from_number,
            content,
            webhook_url=webhook_url,
            reply_to_message_id=reply_to_message_id,
        )

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
        content = (caption or "").strip()
        if not content:
            content = media_url
        return self.send_text(
            channel,
            to,
            content,
            reply_to_message_id=reply_to_id,
            channel_external_id=channel_external_id,
            channel_config=channel_config,
        )

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
        return self.send_text(
            channel,
            to,
            content,
            channel_external_id=channel_external_id,
            channel_config=channel_config,
        )
