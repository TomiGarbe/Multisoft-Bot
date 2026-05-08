"""
Webhook adapter: normaliza el payload del canal y delega al handler central.

NO orquesta nada del flujo de procesamiento — para eso existe
`incoming_message_handler.handle_incoming_message`, que es el único punto
de entrada para mensajes entrantes.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.repositories.channel_repository import ChannelRepository
from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.message_service import ensure_message_id
from app.services.inbound.incoming_message_handler import handle_incoming_message
from app.providers.provider_factory import get_message_provider

logger = logging.getLogger(__name__)


async def handle_webhook(db: Session, channel_id: str, payload: dict, tenant_id: uuid.UUID) -> None:
    channel = ChannelRepository(db).get_by_id_and_tenant(uuid.UUID(channel_id), tenant_id)
    if not channel:
        logger.warning("Channel not found or outside tenant scope for webhook: channel=%s tenant=%s", channel_id, tenant_id)
        return

    provider = get_message_provider(channel.type)
    normalized: NormalizedMessage = provider.normalize_incoming_payload(channel_id, payload)
    ensure_message_id(normalized)

    if normalized.is_status:
        logger.info("Ignoring status message for channel=%s", normalized.channel_id)
        return

    await handle_incoming_message(db, normalized, tenant_id=tenant_id)
