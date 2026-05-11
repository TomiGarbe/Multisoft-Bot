"""
Webhook adapter: normaliza el payload del canal y delega al handler central.

NO orquesta nada del flujo de procesamiento — para eso existe
`incoming_message_handler.handle_incoming_message`, que es el único punto
de entrada para mensajes entrantes.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.policies.inbound_whatsapp_whitelist import should_process_incoming_message
from app.repositories.channel_repository import ChannelRepository
from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.message_service import ensure_message_id
from app.services.inbound.incoming_message_handler import handle_incoming_message
from app.providers.provider_factory import get_message_provider

logger = logging.getLogger(__name__)


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


async def handle_webhook(db: Session, channel_id: str, payload: dict, tenant_id: uuid.UUID) -> None:
    channel = ChannelRepository(db).get_by_id_and_tenant(uuid.UUID(channel_id), tenant_id)
    if not channel:
        logger.warning("Channel not found or outside tenant scope for webhook: channel=%s tenant=%s", channel_id, tenant_id)
        return

    provider = get_message_provider(_resolve_channel_provider_name(channel))
    normalized: NormalizedMessage = provider.normalize_incoming_payload(channel_id, payload)
    ensure_message_id(normalized)

    if normalized.is_status:
        logger.info("Ignoring status message for channel=%s", normalized.channel_id)
        return

    if (channel.type or "").strip().lower() == "whatsapp":
        allowed = should_process_incoming_message(
            is_group=normalized.is_group,
            sender_phone=normalized.sender_external_id,
            group_id=normalized.group_id,
        )
        if not allowed:
            logger.info(
                "Ignoring inbound message from unauthorized sender/group"
                " channel=%s is_group=%s sender=%s group=%s",
                normalized.channel_id,
                normalized.is_group,
                normalized.sender_external_id,
                normalized.group_id,
            )
            return

    await handle_incoming_message(db, normalized, tenant_id=tenant_id)
