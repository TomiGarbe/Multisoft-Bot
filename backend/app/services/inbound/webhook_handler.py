import logging

from sqlalchemy.orm import Session

from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.inbound.normalizer import normalize
import app.services.message_service as message_service
from app.services.conversation import conversation_engine

logger = logging.getLogger(__name__)


def handle_webhook(db: Session, channel_id: str, payload: dict) -> None:
    if payload.get("is_status") or payload.get("type") == "status":
        return

    normalized: NormalizedMessage = normalize(channel_id, payload)

    message = message_service.create_inbound_message(db, normalized)
    if not message:
        return

    conversation_ctx = {"id": str(message.conversation_id), "status": "open"}
    recent_messages = message_service.get_messages(db, message.conversation_id)

    response_text = conversation_engine.process_message(conversation_ctx, recent_messages)
    if response_text:
        message_service.send_message(db, {
            "conversation_id": str(message.conversation_id),
            "content": response_text,
        })
