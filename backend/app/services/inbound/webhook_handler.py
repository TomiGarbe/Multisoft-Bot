"""
Webhook adapter: normaliza el payload del canal y delega al handler central.

NO orquesta nada del flujo de procesamiento — para eso existe
`incoming_message_handler.handle_incoming_message`, que es el único punto
de entrada para mensajes entrantes.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.inbound.incoming_message_handler import handle_incoming_message
from app.services.inbound.normalizer import normalize

logger = logging.getLogger(__name__)


async def handle_webhook(db: Session, channel_id: str, payload: dict, tenant_id: uuid.UUID) -> None:
    if payload.get("is_status") or payload.get("type") == "status":
        return

    normalized: NormalizedMessage = normalize(channel_id, payload)
    await handle_incoming_message(db, normalized, tenant_id=tenant_id)
