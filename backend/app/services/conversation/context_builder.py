"""
Builds the conversation context dict consumed by PromptBuilder.

Encapsulates: history fetching (last 15 messages), sender_type -> role mapping,
contact lookup, default user_type resolution, and user memory extraction.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.schemas.internal.message_enums import AttachmentType, MediaProcessingCapability, MediaProcessingStatus
from app.services.attachment_service import AttachmentService
from app.services.media_processing_service import MediaProcessingService
import app.services.message_service as message_service

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 15
_GROUP_FOCUS_LIMIT = 6
_TRANSCRIPTION_MAX_CHARS = 1800
_DOCUMENT_TEXT_MAX_CHARS = 2200
_IMAGE_HINT_MAX_CHARS = 220
_TRANSCRIPTION_WAIT_TIMEOUT_SECONDS = 1.8
_TRANSCRIPTION_WAIT_INTERVAL_SECONDS = 0.45


def build_conversation_context(
    db: Session,
    conversation: Conversation,
    current_message: Message,
    config: dict,
) -> dict:
    """Return the kwargs dict that PromptBuilder.build expects."""
    history_rows = _get_history_raw(db, conversation.id, current_message.tenant_id, exclude_id=current_message.id)
    contact = _get_contact(db, current_message.sender_contact_id)
    default_type = _resolve_default_type(config)
    user_type = _get_valid_contact_type(contact, config, default_type)
    user_memory = _extract_user_memory(contact)

    all_rows = [*history_rows, _to_message_row(current_message)]
    enrichment = _load_media_enrichment(db=db, tenant_id=current_message.tenant_id, message_rows=all_rows)

    history = _map_messages(history_rows, enrichment=enrichment)
    current_payload = _build_effective_payload_for_current(
        db=db,
        current_message=current_message,
        enrichment=enrichment,
    )
    current_message_text = current_payload["effective_text"]

    target_message = _resolve_target_message(current_message, history)
    group_context = _build_group_context(current_message, history)
    _log_current_message_media_state(db=db, current_message=current_message)
    _log_context_summary(
        conversation=conversation,
        current_message=current_message,
        history=history,
        current_payload=current_payload,
    )

    return {
        "messages": history,
        "user_memory": user_memory,
        "current_message": current_message_text,
        "current_message_attachments": current_payload.get("attachments", []),
        "current_message_derived_content": current_payload.get("derived_content", []),
        "user_type": user_type,
        "target_message": target_message,
        "group_context": group_context,
    }


def _to_message_row(message: Message) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "sender_type": message.sender_type,
        "content": message.content_text,
        "provider_message_id": message.provider_message_id,
        "sender_external_id": message.sender_external_id,
        "sender_name": message.sender_name,
        "replied_to_message_id": message.replied_to_message_id,
        "is_group": bool(message.is_group),
    }


def _load_media_enrichment(
    *,
    db: Session,
    tenant_id: uuid.UUID,
    message_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    attachment_service = AttachmentService(db)
    processing_service = MediaProcessingService(db)

    message_ids: list[uuid.UUID] = []
    for row in message_rows:
        raw_id = row.get("id")
        if not raw_id:
            continue
        try:
            message_ids.append(uuid.UUID(str(raw_id)))
        except ValueError:
            continue

    attachments = attachment_service.list_by_message_ids_and_tenant(message_ids=message_ids, tenant_id=tenant_id)
    attachments_by_message: dict[str, list[Any]] = {}
    for attachment in attachments:
        attachments_by_message.setdefault(str(attachment.message_id), []).append(attachment)

    attachment_ids = [item.id for item in attachments]
    artifacts = processing_service.list_artifacts_for_attachments(attachment_ids=attachment_ids, tenant_id=tenant_id)
    jobs = processing_service.list_jobs_for_attachments(attachment_ids=attachment_ids, tenant_id=tenant_id)

    artifacts_by_attachment: dict[str, dict[MediaProcessingCapability, Any]] = {}
    for artifact in artifacts:
        bucket = artifacts_by_attachment.setdefault(str(artifact.attachment_id), {})
        bucket[artifact.capability] = artifact

    jobs_by_attachment: dict[str, list[Any]] = {}
    for job in jobs:
        jobs_by_attachment.setdefault(str(job.attachment_id), []).append(job)

    return {
        "attachments_by_message": attachments_by_message,
        "artifacts_by_attachment": artifacts_by_attachment,
        "jobs_by_attachment": jobs_by_attachment,
    }


def _build_effective_payload_for_current(
    *,
    db: Session,
    current_message: Message,
    enrichment: dict[str, Any],
) -> dict[str, Any]:
    message_id = str(current_message.id)
    initial = _build_effective_payload_for_message(
        message_id=message_id,
        base_content=current_message.content_text or "",
        enrichment=enrichment,
        is_current=True,
    )
    if str(initial.get("effective_text") or "").strip():
        return initial

    attachments = (enrichment.get("attachments_by_message") or {}).get(message_id, [])
    audio_attachment_ids: list[str] = []
    for attachment in attachments:
        if getattr(attachment, "attachment_type", None) in {AttachmentType.AUDIO, AttachmentType.VIDEO}:
            audio_attachment_ids.append(str(attachment.id))
    if not audio_attachment_ids:
        return initial

    if not _has_pending_transcription(enrichment=enrichment, attachment_ids=audio_attachment_ids):
        return initial

    start = time.monotonic()
    deadline = start + _TRANSCRIPTION_WAIT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(_TRANSCRIPTION_WAIT_INTERVAL_SECONDS)
        refreshed = _reload_attachment_processing(
            db=db,
            tenant_id=current_message.tenant_id,
            attachment_ids=[uuid.UUID(item) for item in audio_attachment_ids],
        )
        enrichment["artifacts_by_attachment"] = refreshed["artifacts_by_attachment"]
        enrichment["jobs_by_attachment"] = refreshed["jobs_by_attachment"]

        candidate = _build_effective_payload_for_message(
            message_id=message_id,
            base_content=current_message.content_text or "",
            enrichment=enrichment,
            is_current=True,
        )
        if str(candidate.get("effective_text") or "").strip():
            logger.warning(
                "[AI][TRANSCRIPTION] included_after_wait message_id=%s wait_ms=%s",
                current_message.id,
                int((time.monotonic() - start) * 1000),
            )
            return candidate
        if not _has_pending_transcription(enrichment=enrichment, attachment_ids=audio_attachment_ids):
            break

    logger.warning("[AI][TRANSCRIPTION] pending_timeout message_id=%s", current_message.id)
    return initial


def _reload_attachment_processing(*, db: Session, tenant_id: uuid.UUID, attachment_ids: list[uuid.UUID]) -> dict[str, Any]:
    processing_service = MediaProcessingService(db)
    artifacts = processing_service.list_artifacts_for_attachments(attachment_ids=attachment_ids, tenant_id=tenant_id)
    jobs = processing_service.list_jobs_for_attachments(attachment_ids=attachment_ids, tenant_id=tenant_id)

    artifacts_by_attachment: dict[str, dict[MediaProcessingCapability, Any]] = {}
    for artifact in artifacts:
        bucket = artifacts_by_attachment.setdefault(str(artifact.attachment_id), {})
        bucket[artifact.capability] = artifact

    jobs_by_attachment: dict[str, list[Any]] = {}
    for job in jobs:
        jobs_by_attachment.setdefault(str(job.attachment_id), []).append(job)

    return {
        "artifacts_by_attachment": artifacts_by_attachment,
        "jobs_by_attachment": jobs_by_attachment,
    }


def _has_pending_transcription(*, enrichment: dict[str, Any], attachment_ids: list[str]) -> bool:
    jobs_by_attachment: dict[str, list[Any]] = enrichment.get("jobs_by_attachment") or {}
    pending_statuses = {
        MediaProcessingStatus.PENDING,
        MediaProcessingStatus.QUEUED,
        MediaProcessingStatus.PROCESSING,
    }
    for attachment_id in attachment_ids:
        for job in jobs_by_attachment.get(attachment_id, []):
            if job.capability == MediaProcessingCapability.TRANSCRIPTION and job.status in pending_statuses:
                return True
    return False


def _build_effective_payload_for_message(
    *,
    message_id: str,
    base_content: str,
    enrichment: dict[str, Any],
    is_current: bool,
) -> dict[str, Any]:
    text = (base_content or "").strip()
    attachments_by_message: dict[str, list[Any]] = enrichment.get("attachments_by_message") or {}
    artifacts_by_attachment: dict[str, dict[MediaProcessingCapability, Any]] = enrichment.get("artifacts_by_attachment") or {}
    jobs_by_attachment: dict[str, list[Any]] = enrichment.get("jobs_by_attachment") or {}

    attachments = attachments_by_message.get(message_id, [])
    transcription_chunks: list[str] = []
    extraction_chunks: list[str] = []
    image_hint_chunks: list[str] = []
    attachments_for_ai: list[dict[str, Any]] = []
    derived_content: list[dict[str, Any]] = []
    seen_transcriptions: set[str] = set()

    for attachment in attachments:
        attachment_type = getattr(attachment, "attachment_type", None)
        attachment_type_value = attachment_type.value if attachment_type else "unknown"
        attachments_for_ai.append(
            {
                "attachment_id": str(attachment.id),
                "attachment_type": attachment_type_value,
                "mime_type": str(getattr(attachment, "mime_type", None) or ""),
                "download_status": str(getattr(getattr(attachment, "download_status", None), "value", "unknown")),
            }
        )
        artifact_by_cap = artifacts_by_attachment.get(str(attachment.id), {})
        transcription = artifact_by_cap.get(MediaProcessingCapability.TRANSCRIPTION)
        extraction = artifact_by_cap.get(MediaProcessingCapability.DOCUMENT_EXTRACTION)

        if attachment_type in {AttachmentType.AUDIO, AttachmentType.VIDEO}:
            transcription_text = (getattr(transcription, "payload_text", None) or "").strip()
            if transcription_text:
                if transcription_text in seen_transcriptions:
                    logger.warning(
                        "[AI][TRANSCRIPTION] skipped_duplicate message_id=%s attachment_id=%s",
                        message_id,
                        attachment.id,
                    )
                else:
                    seen_transcriptions.add(transcription_text)
                    normalized = _truncate_text(transcription_text, _TRANSCRIPTION_MAX_CHARS)
                    transcription_chunks.append(f"[Audio transcription]\n{normalized}")
                    derived_content.append(
                        {
                            "kind": "audio_transcription",
                            "attachment_id": str(attachment.id),
                            "chars": len(normalized),
                        }
                    )
                    logger.warning(
                        "[AI][TRANSCRIPTION] included message_id=%s attachment_id=%s chars=%s truncated=%s",
                        message_id,
                        attachment.id,
                        len(transcription_text),
                        len(normalized) < len(transcription_text),
                    )
            else:
                _log_transcription_skip(
                    message_id=message_id,
                    attachment=attachment,
                    jobs_by_attachment=jobs_by_attachment,
                    is_current=is_current,
                )

        if attachment_type in {AttachmentType.DOCUMENT, AttachmentType.FILE}:
            extracted_text = (getattr(extraction, "payload_text", None) or "").strip()
            if extracted_text:
                normalized = _truncate_text(extracted_text, _DOCUMENT_TEXT_MAX_CHARS)
                extraction_chunks.append(f"[Document extracted text]\n{normalized}")
                derived_content.append(
                    {
                        "kind": "document_extraction",
                        "attachment_id": str(attachment.id),
                        "chars": len(normalized),
                    }
                )
        if attachment_type == AttachmentType.IMAGE:
            caption = (getattr(attachment, "caption", None) or "").strip()
            filename = (getattr(attachment, "filename", None) or getattr(attachment, "file_name", None) or "").strip()
            image_hint = caption or filename
            if image_hint:
                normalized = _truncate_text(image_hint, _IMAGE_HINT_MAX_CHARS)
                image_hint_chunks.append(f"[Image hint]\n{normalized}")
                derived_content.append(
                    {
                        "kind": "image_hint",
                        "attachment_id": str(attachment.id),
                        "chars": len(normalized),
                    }
                )

    content_parts = [item for item in [text, *transcription_chunks, *extraction_chunks, *image_hint_chunks] if item.strip()]
    effective_text = "\n\n".join(content_parts).strip()
    return {
        "effective_text": effective_text,
        "attachments": attachments_for_ai,
        "derived_content": derived_content,
    }


def _log_transcription_skip(*, message_id: str, attachment: Any, jobs_by_attachment: dict[str, list[Any]], is_current: bool) -> None:
    jobs = jobs_by_attachment.get(str(attachment.id), [])
    transcription_job = next((job for job in jobs if job.capability == MediaProcessingCapability.TRANSCRIPTION), None)
    if transcription_job is None:
        logger.warning(
            "[AI][TRANSCRIPTION] skipped message_id=%s attachment_id=%s reason=no_job",
            message_id,
            attachment.id,
        )
        return
    if transcription_job.status in {MediaProcessingStatus.PENDING, MediaProcessingStatus.QUEUED, MediaProcessingStatus.PROCESSING}:
        logger.warning(
            "[AI][TRANSCRIPTION] pending message_id=%s attachment_id=%s status=%s current=%s",
            message_id,
            attachment.id,
            transcription_job.status.value,
            is_current,
        )
        return
    if transcription_job.status == MediaProcessingStatus.FAILED:
        logger.warning(
            "[AI][TRANSCRIPTION] skipped message_id=%s attachment_id=%s reason=failed code=%s",
            message_id,
            attachment.id,
            transcription_job.last_error_code,
        )
        return
    logger.warning(
        "[AI][TRANSCRIPTION] skipped message_id=%s attachment_id=%s reason=no_text status=%s",
        message_id,
        attachment.id,
        transcription_job.status.value,
    )


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    logger.warning("[AI][TRANSCRIPTION] truncation_applied original_chars=%s max_chars=%s", len(value), max_chars)
    return value[:max_chars].rstrip() + "\n...[truncated]"


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


def _log_context_summary(
    *,
    conversation: Conversation,
    current_message: Message,
    history: list[dict],
    current_payload: dict[str, Any],
) -> None:
    attachments_count = len(current_payload.get("attachments") or [])
    derived_count = len(current_payload.get("derived_content") or [])
    logger.warning(
        "[AI][CONTEXT] assembled conversation_id=%s message_id=%s history_messages=%s current_message_chars=%s attachments=%s derived_entries=%s",
        conversation.id,
        current_message.id,
        len(history),
        len(str(current_payload.get("effective_text") or "")),
        attachments_count,
        derived_count,
    )


def _get_history_raw(
    db: Session,
    conversation_id: uuid.UUID,
    tenant_id: uuid.UUID,
    exclude_id: uuid.UUID,
) -> list[dict[str, Any]]:
    messages = message_service.get_messages(db, conversation_id, tenant_id=tenant_id)
    messages = [m for m in messages if m["id"] != str(exclude_id)]
    return messages[-_HISTORY_LIMIT:]


def _map_messages(messages: list[dict[str, Any]], *, enrichment: dict[str, Any]) -> list[dict]:
    mapped = []
    for msg in messages:
        sender_type = (msg.get("sender_type") or "").lower()
        message_id = str(msg.get("id") or "")
        payload = _build_effective_payload_for_message(
            message_id=message_id,
            base_content=(msg.get("content") or ""),
            enrichment=enrichment,
            is_current=False,
        )
        content = str(payload.get("effective_text") or "").strip()
        if not content:
            continue
        if sender_type == "contact":
            role = "user"
        elif sender_type in ("assistant", "bot"):
            role = "assistant"
        else:
            logger.warning("Unknown sender_type '%s' - skipping message", sender_type)
            continue
        mapped.append(
            {
                "role": role,
                "content": content,
                "id": message_id,
                "attachments": payload.get("attachments") or [],
                "derived_content": payload.get("derived_content") or [],
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
    sender_history = [m for m in history if sender_id and m.get("sender_external_id") == sender_id][-_GROUP_FOCUS_LIMIT:]
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
            "Contact type '%s' not in config - using default '%s' for contact: %s",
            current,
            default_type,
            contact.id,
        )
        return default_type
    return current


def _extract_user_memory(contact: Optional[Contact]) -> Optional[dict]:
    if not contact or not isinstance(contact.metadata_jsonb, dict):
        return None
    return contact.metadata_jsonb or None
