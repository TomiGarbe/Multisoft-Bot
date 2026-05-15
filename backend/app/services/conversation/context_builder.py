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
from app.services.attachment_service import AttachmentService
from app.services.media_processing_service import MediaProcessingService
from app.schemas.internal.message_enums import MediaProcessingCapability
import app.services.message_service as message_service

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 15
_GROUP_FOCUS_LIMIT = 6


def build_conversation_context(
    db: Session,
    conversation: Conversation,
    current_message: Message,
    config: dict,
) -> dict:
    """Return the kwargs dict that PromptBuilder.build expects."""
    history = _get_history(db, conversation.id, current_message.tenant_id, exclude_id=current_message.id)
    contact = _get_contact(db, current_message.sender_contact_id)
    default_type = _resolve_default_type(config)
    user_type = _get_valid_contact_type(contact, config, default_type)
    user_memory = _extract_user_memory(contact)
    target_message = _resolve_target_message(current_message, history)
    group_context = _build_group_context(current_message, history)
    _log_current_message_media_state(db=db, current_message=current_message)
    _log_context_summary(conversation=conversation, current_message=current_message, history=history)

    return {
        "messages": history,
        "user_memory": user_memory,
        "current_message": current_message.content_text,
        "user_type": user_type,
        "target_message": target_message,
        "group_context": group_context,
    }


def _log_current_message_media_state(*, db: Session, current_message: Message) -> None:
    attachment_service = AttachmentService(db)
    processing_service = MediaProcessingService(db)
    attachments = attachment_service.list_by_message_id_and_tenant(
        message_id=current_message.id,
        tenant_id=current_message.tenant_id,
    )
    attachment_types = sorted({str(item.attachment_type.value) for item in attachments})
    logger.warning(
        "[AI][CONTEXT] message_id=%s conversation_id=%s has_media=%s attachments=%s types=%s",
        current_message.id,
        current_message.conversation_id,
        bool(current_message.has_media),
        len(attachments),
        ",".join(attachment_types) if attachment_types else "none",
    )
    capabilities = [
        MediaProcessingCapability.TRANSCRIPTION,
        MediaProcessingCapability.DOCUMENT_EXTRACTION,
    ]
    for attachment in attachments:
        has_blob = attachment_service.attachment_blob_exists(
            attachment_id=attachment.id,
            tenant_id=current_message.tenant_id,
            storage_key=attachment.storage_key,
        )
        artifacts = processing_service.list_artifacts_by_capabilities(
            attachment_id=attachment.id,
            tenant_id=current_message.tenant_id,
            capabilities=capabilities,
        )
        artifacts_by_cap = {item.capability: item for item in artifacts}
        logger.warning(
            "[AI][ATTACHMENT] message_id=%s attachment_id=%s type=%s mime=%s status=%s backend=%s has_blob=%s has_provider_url=%s has_provider_media_id=%s",
            current_message.id,
            attachment.id,
            attachment.attachment_type.value,
            attachment.mime_type,
            attachment.download_status.value,
            attachment.storage_backend.value,
            has_blob,
            bool(attachment.provider_url),
            bool(attachment.provider_media_id),
        )
        _log_artifact_inclusion(attachment.id, "transcription", artifacts_by_cap.get(MediaProcessingCapability.TRANSCRIPTION))
        _log_artifact_inclusion(
            attachment.id,
            "extracted_text",
            artifacts_by_cap.get(MediaProcessingCapability.DOCUMENT_EXTRACTION),
        )


def _log_artifact_inclusion(attachment_id: uuid.UUID, artifact_name: str, artifact: Any) -> None:
    has_text = bool((getattr(artifact, "payload_text", None) or "").strip())
    logger.warning(
        "[AI][ARTIFACT] attachment_id=%s artifact=%s exists=%s has_text=%s included_in_prompt=%s",
        attachment_id,
        artifact_name,
        bool(artifact),
        has_text,
        False,
    )


def _log_context_summary(*, conversation: Conversation, current_message: Message, history: list[dict]) -> None:
    logger.warning(
        "[AI][CONTEXT] assembled conversation_id=%s message_id=%s history_messages=%s current_message_chars=%s",
        conversation.id,
        current_message.id,
        len(history),
        len((current_message.content_text or "").strip()),
    )


def _get_history(
    db: Session,
    conversation_id: uuid.UUID,
    tenant_id: uuid.UUID,
    exclude_id: uuid.UUID,
) -> list[dict]:
    messages = message_service.get_messages(db, conversation_id, tenant_id=tenant_id)
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
        mapped.append(
            {
                "role": role,
                "content": content,
                "provider_message_id": msg.get("provider_message_id"),
                "sender_external_id": msg.get("sender_external_id"),
                "sender_name": msg.get("sender_name"),
                "replied_to_message_id": msg.get("replied_to_message_id"),
                "is_group": bool(msg.get("is_group")),
            }
        )
    return mapped


def _resolve_target_message(current_message: Message, history: list[dict]) -> Optional[dict]:
    target_provider_id = current_message.replied_to_message_id
    if not target_provider_id:
        return None
    for msg in reversed(history):
        if msg.get("provider_message_id") == target_provider_id:
            return msg
    return {"provider_message_id": target_provider_id}


def _build_group_context(current_message: Message, history: list[dict]) -> Optional[dict]:
    if not current_message.is_group:
        return None

    sender_id = current_message.sender_external_id
    sender_history = [
        m for m in history
        if sender_id and m.get("sender_external_id") == sender_id
    ][-_GROUP_FOCUS_LIMIT:]
    mentioned_participants = sorted(
        {
            str(m.get("sender_external_id"))
            for m in history[-_HISTORY_LIMIT:]
            if m.get("sender_external_id")
        }
    )
    return {
        "current_sender_external_id": sender_id,
        "current_sender_name": current_message.sender_name,
        "current_replied_to_message_id": current_message.replied_to_message_id,
        "recent_messages_from_same_sender": sender_history,
        "recent_participants": mentioned_participants,
    }


def _get_contact(db: Session, contact_id: Optional[uuid.UUID]) -> Optional[Contact]:
    if not contact_id:
        return None
    return message_service.get_contact(db, contact_id)


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
