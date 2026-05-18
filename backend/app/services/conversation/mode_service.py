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
from app.services.conversation.lifecycle_service import ConversationLifecycleService
from app.services.conversation.guards import is_config_valid

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
    if conversation.mode == mode and conversation.status == "open":
        return
    opened = ConversationLifecycleService(db).switch_mode_with_new_session(
        conversation=conversation,
        target_mode=mode,
        resolution="legacy_mode_switch",
    )
    logger.info("Set mode='%s' with new session: old=%s new=%s", mode, conversation.id, opened.id)
