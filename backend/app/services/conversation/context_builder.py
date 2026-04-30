"""
Builds the conversation context dict consumed by PromptBuilder.

Encapsulates: history fetching (last 15 messages), sender_type → role mapping,
contact lookup, default user_type resolution, and user memory extraction.
"""

import logging
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.conversation import Conversation, Message
import app.services.message_service as message_service

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 15


def build_conversation_context(
    db: Session,
    conversation: Conversation,
    current_message: Message,
    config: dict,
) -> dict:
    """Return the kwargs dict that PromptBuilder.build expects."""
    history = _get_history(db, conversation.id, exclude_id=current_message.id)
    contact = _get_contact(db, current_message.sender_contact_id)
    default_type = _resolve_default_type(config)
    _ensure_contact_type(db, contact, default_type)
    user_type = _get_valid_contact_type(contact, config, default_type)
    user_memory = _extract_user_memory(contact)

    return {
        "messages": history,
        "user_memory": user_memory,
        "current_message": current_message.content_text,
        "user_type": user_type,
    }


def _get_history(db: Session, conversation_id: uuid.UUID, exclude_id: uuid.UUID) -> list[dict]:
    messages = message_service.get_messages(db, conversation_id)
    messages = [m for m in messages if m["id"] != str(exclude_id)]
    messages = messages[-_HISTORY_LIMIT:]
    return _map_messages(messages)


def _map_messages(messages: list[dict]) -> list[dict]:
    mapped = []
    for msg in messages:
        sender_type = (msg.get("sender_type") or "").lower()
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if sender_type == "contact":
            role = "user"
        elif sender_type in ("assistant", "bot"):
            role = "assistant"
        else:
            logger.warning("Unknown sender_type '%s' — skipping message", sender_type)
            continue
        mapped.append({"role": role, "content": content})
    return mapped


def _get_contact(db: Session, contact_id: Optional[uuid.UUID]) -> Optional[Contact]:
    if not contact_id:
        return None
    return db.query(Contact).filter(Contact.id == contact_id).first()


def _resolve_default_type(config: dict) -> str:
    default_type = config.get("default_type")
    if default_type:
        return default_type
    user_types = config.get("user_type_config", {})
    if isinstance(user_types, dict):
        for type_name, type_config in user_types.items():
            if isinstance(type_config, dict) and type_config.get("is_default"):
                return type_name
    return "default"


def _ensure_contact_type(db: Session, contact: Optional[Contact], default_type: str) -> None:
    if not contact or contact.current_type is not None:
        return
    try:
        contact.current_type = default_type
        db.commit()
        logger.info("Assigned initial current_type '%s' to contact: %s", default_type, contact.id)
    except Exception:
        logger.exception("Failed to set initial current_type for contact: %s", contact.id)


def _get_valid_contact_type(
    contact: Optional[Contact],
    config: dict,
    default_type: str,
) -> str:
    if not contact:
        return default_type
    current = contact.current_type or default_type
    user_types = config.get("user_type_config", {})
    if isinstance(user_types, dict) and user_types and current not in user_types:
        logger.warning(
            "Contact type '%s' not in config — using default '%s' for contact: %s",
            current, default_type, contact.id,
        )
        return default_type
    return current


def _extract_user_memory(contact: Optional[Contact]) -> Optional[dict]:
    if not contact or not isinstance(contact.metadata_jsonb, dict):
        return None
    return contact.metadata_jsonb or None


def apply_user_type_on_completion(
    db: Session,
    contact_id: Optional[uuid.UUID],
    config: dict,
) -> None:
    """Bump contact.current_type if the active objective declares an on_completion target."""
    if not contact_id:
        return
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return
    objective = config.get("objective", {})
    if not isinstance(objective, dict):
        return
    on_completion = objective.get("on_completion")
    if not on_completion:
        return
    try:
        contact.current_type = on_completion
        db.commit()
        logger.info("Updated current_type to '%s' for contact: %s", on_completion, contact.id)
    except Exception:
        logger.exception("Failed to update current_type for contact: %s", contact.id)
