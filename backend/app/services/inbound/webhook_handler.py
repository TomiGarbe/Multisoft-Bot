import logging

from sqlalchemy.orm import Session

from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.inbound.normalizer import normalize
from app.services.inbound.message_processor import MessageProcessor
import app.services.message_service as message_service

logger = logging.getLogger(__name__)

_message_processor = MessageProcessor()


async def handle_webhook(db: Session, channel_id: str, payload: dict) -> None:
    """
    Maneja webhooks entrantes de canales.

    Flujo:
    1. Normalizar payload
    2. Crear mensaje inbound
    3. Procesar con IA si aplica
    4. Enviar respuesta via outbound
    """
    if payload.get("is_status") or payload.get("type") == "status":
        return

    normalized: NormalizedMessage = normalize(channel_id, payload)

    message = message_service.create_inbound_message(db, normalized)
    if not message:
        return

    response_text = await _message_processor.process_inbound_message(
        db,
        message,
        normalized.content,
    )

    if response_text:
        try:
            message_service.send_message(db, {
                "conversation_id": str(message.conversation_id),
                "content": response_text,
            })
        except Exception:
            logger.exception(
                "Failed to send outbound message for conversation: %s",
                message.conversation_id,
            )
