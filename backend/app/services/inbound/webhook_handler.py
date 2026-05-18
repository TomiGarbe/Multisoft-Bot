"""
Webhook adapter: keeps request-time work minimal and provider-agnostic.
"""

import logging
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.policies.inbound_whatsapp_whitelist import should_process_incoming_message
from app.providers.provider_factory import get_message_provider
from app.repositories.channel_repository import ChannelRepository
from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.inbound.incoming_message_handler import handle_incoming_message
from app.services.message_service import ensure_message_id

logger = logging.getLogger(__name__)


def _pretty_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    except Exception:
        return str(value)


def _log_normalized_media_summary(normalized: NormalizedMessage, provider_name: str) -> None:
    if not normalized.attachments:
        return

    attachment_types = ",".join(item.type.value for item in normalized.attachments)
    logger.warning(
        "[MULTIMEDIA][INBOUND] message_id=%s provider=%s channel_id=%s attachments=%s types=%s",
        normalized.external_message_id,
        provider_name,
        normalized.channel_id,
        len(normalized.attachments),
        attachment_types,
    )
    for index, attachment in enumerate(normalized.attachments, start=1):
        logger.warning(
            "[MULTIMEDIA][INBOUND][ATTACHMENT] provider=%s channel_id=%s message_id=%s idx=%s type=%s mime=%s size_bytes=%s provider_media_id=%s has_provider_url=%s has_base64=%s",
            provider_name,
            normalized.channel_id,
            normalized.external_message_id,
            index,
            attachment.type.value,
            attachment.mime_type,
            attachment.size_bytes,
            attachment.provider_media_id,
            bool(attachment.provider_url),
            bool(attachment.base64_data),
        )


def validate_minimal_webhook_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Invalid payload: expected JSON object")
    if not payload:
        raise ValueError("Invalid payload: empty JSON object")
    return payload


def _resolve_channel_provider_name(channel) -> str:
    if isinstance(channel.config_jsonb, dict):
        provider = channel.config_jsonb.get("provider")
        if isinstance(provider, str) and provider.strip():
            return provider
    if (channel.type or "").strip().lower() == "whatsapp":
        return "multisoft"
    if (channel.type or "").strip().lower() == "web":
        return "web"
    return channel.type


def resolve_webhook_channel_and_provider(
    db: Session,
    *,
    channel_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> tuple[object, str]:
    channel = ChannelRepository(db).get_by_id_and_tenant(channel_id, tenant_id)
    if not channel:
        raise ValueError("Channel not found or outside tenant scope")

    provider_name = _resolve_channel_provider_name(channel)
    return channel, provider_name


async def process_webhook_payload(
    db: Session,
    *,
    channel_id: uuid.UUID,
    payload: dict[str, Any],
    tenant_id: uuid.UUID,
    provider_name: str,
) -> None:
    logger.warning(
        "[PIPELINE][RECEIVED] provider=%s tenant_id=%s channel_id=%s",
        provider_name,
        tenant_id,
        channel_id,
    )
    channel_repo = ChannelRepository(db)
    channel = channel_repo.get_by_id_and_tenant(channel_id, tenant_id)
    if not channel:
        logger.warning(
            "webhook_channel_missing tenant_id=%s channel_id=%s",
            tenant_id,
            channel_id,
        )
        return

    provider = get_message_provider(provider_name)
    normalized: NormalizedMessage = provider.normalize_incoming_payload(str(channel_id), payload)
    logger.warning("[WEBHOOK][NORMALIZED] %s", _pretty_json(normalized.model_dump(mode="json")))
    ensure_message_id(normalized)
    _log_normalized_media_summary(normalized, provider_name)
    logger.warning(
        "[PIPELINE][NORMALIZED] provider=%s channel_id=%s message_id=%s message_type=%s has_media=%s attachments=%s content_chars=%s",
        provider_name,
        normalized.channel_id,
        normalized.external_message_id,
        normalized.message_type.value,
        normalized.has_media,
        len(normalized.attachments),
        len((normalized.content or "").strip()),
    )

    if normalized.is_status:
        logger.info("webhook_status_ignored channel_id=%s", normalized.channel_id)
        return

    if (channel.type or "").strip().lower() == "whatsapp":
        allowed = should_process_incoming_message(
            is_group=normalized.is_group,
            sender_phone=normalized.sender_external_id,
            group_id=normalized.group_id,
        )
        if not allowed:
            logger.info(
                "webhook_sender_not_allowed channel_id=%s is_group=%s sender=%s group=%s",
                normalized.channel_id,
                normalized.is_group,
                normalized.sender_external_id,
                normalized.group_id,
            )
            return

    await handle_incoming_message(db, normalized, tenant_id=tenant_id)
