"""
Transiciones de `conversation.mode` (ai ↔ human).

El backend es la única fuente de verdad del modo. Cada transición se persiste
con un único `UPDATE conversations SET mode = :mode WHERE id = :id`, atómico
a nivel de DB, para evitar race conditions entre workers que reciban el mismo
mensaje en paralelo. Nunca mutamos el modo solo en memoria.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.services.conversation.guards import is_config_valid
import app.services.message_service as message_service

logger = logging.getLogger(__name__)


class InvalidChannelConfigError(ValueError):
    """No se puede activar IA porque la config del canal es inválida."""


def enable_ai(db: Session, conversation: Conversation, channel_config: Any) -> None:
    if not is_config_valid(channel_config):
        raise InvalidChannelConfigError(
            f"Cannot enable AI for conversation {conversation.id}: invalid channel config"
        )
    _set_mode(db, conversation, "ai")


def disable_ai(db: Session, conversation: Conversation) -> None:
    _set_mode(db, conversation, "human")


def _set_mode(db: Session, conversation: Conversation, mode: str) -> None:
    message_service.set_conversation_mode(db, conversation, mode)
    logger.info("Set mode='%s' for conversation: %s", mode, conversation.id)
