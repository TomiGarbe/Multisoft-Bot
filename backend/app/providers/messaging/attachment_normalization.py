from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from app.core.utils import dict_get_any_case
from app.schemas.internal.message_enums import AttachmentType, MessageType, StorageBackend
from app.schemas.internal.normalized_message import AttachmentMetadata, NormalizedAttachment

logger = logging.getLogger(__name__)


def resolve_message_type(raw_type: Any) -> MessageType:
    value = str(raw_type or "").strip().lower()
    aliases = {
        "ptt": MessageType.AUDIO.value,
        "voice": MessageType.AUDIO.value,
        "voice_note": MessageType.AUDIO.value,
        "photo": MessageType.IMAGE.value,
        "img": MessageType.IMAGE.value,
        "doc": MessageType.DOCUMENT.value,
    }
    value = aliases.get(value, value)
    allowed = {
        MessageType.TEXT.value,
        MessageType.AUDIO.value,
        MessageType.IMAGE.value,
        MessageType.VIDEO.value,
        MessageType.DOCUMENT.value,
        MessageType.FILE.value,
        MessageType.MEDIA.value,
    }
    if value in allowed:
        return MessageType(value)
    return MessageType.TEXT


def attachment_type_from_message_type(message_type: MessageType) -> AttachmentType:
    mapping = {
        MessageType.AUDIO: AttachmentType.AUDIO,
        MessageType.IMAGE: AttachmentType.IMAGE,
        MessageType.VIDEO: AttachmentType.VIDEO,
        MessageType.DOCUMENT: AttachmentType.DOCUMENT,
    }
    return mapping.get(message_type, AttachmentType.FILE)


def _to_int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_mime_type(value: Any) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip().lower()
    if not raw:
        return None
    normalized = raw.split(";", maxsplit=1)[0].strip()
    return normalized or None


def _attachment_type_from_mime(mime_type: Optional[str]) -> Optional[AttachmentType]:
    if not mime_type:
        return None
    if mime_type.startswith("image/"):
        return AttachmentType.IMAGE
    if mime_type.startswith("audio/"):
        return AttachmentType.AUDIO
    if mime_type.startswith("video/"):
        return AttachmentType.VIDEO
    if mime_type in {
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }:
        return AttachmentType.DOCUMENT
    return None


def _coalesce_attachment_type(raw: dict[str, Any], fallback: MessageType) -> AttachmentType:
    raw_type = resolve_message_type(dict_get_any_case(raw, "type", "attachment_type", default=fallback.value))
    by_raw = attachment_type_from_message_type(raw_type)
    mime_type = _normalize_mime_type(dict_get_any_case(raw, "mime_type", "mimeType", "mimetype", "contentType", "content_type"))
    by_mime = _attachment_type_from_mime(mime_type)
    if by_mime is not None and by_raw == AttachmentType.FILE:
        return by_mime
    if by_mime is not None and raw_type in {MessageType.MEDIA, MessageType.FILE, MessageType.TEXT, MessageType.UNKNOWN}:
        return by_mime
    return by_raw


def _coalesce_extension(filename: Optional[str], extension: Optional[str], mime_type: Optional[str]) -> Optional[str]:
    if extension:
        return str(extension).strip().lstrip(".").lower() or None
    if filename:
        suffix = Path(str(filename)).suffix
        if suffix:
            return suffix.lstrip(".").lower() or None
    if mime_type and "/" in str(mime_type):
        guessed = str(mime_type).split("/", maxsplit=1)[1].split(";")[0].strip().lower()
        return guessed or None
    return None


def _resolve_storage_backend(provider_url: Optional[str], base64_data: Optional[str], provider_media_id: Optional[str]) -> StorageBackend:
    if base64_data:
        return StorageBackend.BASE64
    if provider_url:
        return StorageBackend.PROVIDER
    if provider_media_id:
        return StorageBackend.PROVIDER
    return StorageBackend.NONE


def normalize_attachment(
    raw: dict[str, Any],
    *,
    provider: str,
    fallback_message_type: MessageType,
    fallback_caption: Optional[str] = None,
) -> NormalizedAttachment:
    mime_type = _normalize_mime_type(dict_get_any_case(raw, "mime_type", "mimeType", "mimetype", "contentType", "content_type"))
    filename = dict_get_any_case(raw, "filename", "file_name", "name")
    extension = dict_get_any_case(raw, "extension", "ext")
    provider_media_id = dict_get_any_case(raw, "provider_media_id", "media_id", "id", "file_id", "providerFileId")
    provider_url = dict_get_any_case(raw, "provider_url", "url", "file_url", "fileUrl")
    base64_data = dict_get_any_case(raw, "base64_data", "base64", "data_base64", "dataBase64", "data")
    caption = dict_get_any_case(raw, "caption")
    if caption is None:
        caption = fallback_caption

    metadata = AttachmentMetadata(
        storage_backend=_resolve_storage_backend(provider_url, base64_data, provider_media_id),
        provider=provider,
        source="inbound_webhook",
    )
    normalized = NormalizedAttachment(
        type=_coalesce_attachment_type(raw, fallback_message_type),
        mime_type=mime_type,
        filename=str(filename) if filename is not None else None,
        extension=_coalesce_extension(
            str(filename) if filename is not None else None,
            str(extension) if extension is not None else None,
            str(mime_type) if mime_type is not None else None,
        ),
        size_bytes=_to_int_or_none(dict_get_any_case(raw, "size_bytes", "size", "file_size", "content_length", "filesize", "fileSize")),
        width=_to_int_or_none(dict_get_any_case(raw, "width")),
        height=_to_int_or_none(dict_get_any_case(raw, "height")),
        duration_ms=_to_int_or_none(dict_get_any_case(raw, "duration_ms", "duration", "durationMs")),
        provider_media_id=str(provider_media_id) if provider_media_id is not None else None,
        provider_url=str(provider_url) if provider_url is not None else None,
        base64_data=str(base64_data) if base64_data is not None else None,
        caption=str(caption) if caption is not None else None,
        metadata=metadata,
    )
    logger.debug(
        "[MULTIMEDIA][NORMALIZE] attachment type=%s mime=%s size_bytes=%s provider_media_id=%s has_provider_url=%s has_base64=%s storage_backend=%s",
        normalized.type.value,
        normalized.mime_type,
        normalized.size_bytes,
        normalized.provider_media_id,
        bool(normalized.provider_url),
        bool(normalized.base64_data),
        normalized.metadata.storage_backend.value,
    )
    return normalized


def normalize_attachments_from_payload(
    payload: dict[str, Any],
    *,
    provider: str,
    fallback_message_type: MessageType,
) -> list[NormalizedAttachment]:
    raw_attachments = dict_get_any_case(payload, "attachments", default=[]) or []
    if not isinstance(raw_attachments, list):
        raw_attachments = []
    for media_key in ("image", "audio", "video", "document", "file", "media"):
        media_obj = dict_get_any_case(payload, media_key)
        if isinstance(media_obj, dict):
            enriched = dict(media_obj)
            enriched.setdefault("type", media_key)
            # Multisoft inbound media payload shape.
            if dict_get_any_case(enriched, "base64_data", "base64", "data_base64", "dataBase64") is None:
                payload_data = dict_get_any_case(enriched, "data")
                if payload_data is not None:
                    enriched["base64_data"] = payload_data
            if dict_get_any_case(enriched, "mime_type", "mimeType", "mimetype") is None:
                media_mime = dict_get_any_case(enriched, "mimetype")
                if media_mime is not None:
                    enriched["mime_type"] = media_mime
            if dict_get_any_case(enriched, "size_bytes", "size", "filesize") is None:
                media_size = dict_get_any_case(enriched, "filesize")
                if media_size is not None:
                    enriched["size_bytes"] = media_size
            raw_attachments.append(enriched)

    normalized: list[NormalizedAttachment] = []
    if isinstance(raw_attachments, list):
        for raw in raw_attachments:
            if not isinstance(raw, dict):
                continue
            normalized.append(
                normalize_attachment(
                    raw,
                    provider=provider,
                    fallback_message_type=fallback_message_type,
                    fallback_caption=dict_get_any_case(payload, "caption"),
                )
            )

    if normalized:
        logger.debug(
            "[MULTIMEDIA][NORMALIZE] attachments_array_detected count=%s provider=%s fallback_message_type=%s",
            len(normalized),
            provider,
            fallback_message_type.value,
        )
        return normalized

    legacy = {
        "type": dict_get_any_case(payload, "type", "attachment_type", default=fallback_message_type.value),
        "provider_url": dict_get_any_case(payload, "provider_url", "url", "fileUrl"),
        "provider_media_id": dict_get_any_case(payload, "provider_media_id", "media_id", "file_id", "providerFileId"),
        "base64_data": dict_get_any_case(payload, "base64_data", "base64", "dataBase64"),
        "caption": dict_get_any_case(payload, "caption"),
        "mime_type": dict_get_any_case(payload, "mime_type", "mimeType"),
        "filename": dict_get_any_case(payload, "filename", "file_name"),
        "extension": dict_get_any_case(payload, "extension", "ext"),
        "size_bytes": dict_get_any_case(payload, "size_bytes", "size", "file_size"),
        "width": dict_get_any_case(payload, "width"),
        "height": dict_get_any_case(payload, "height"),
        "duration_ms": dict_get_any_case(payload, "duration_ms", "duration", "durationMs"),
    }
    has_any_media_source = any([legacy["provider_url"], legacy["provider_media_id"], legacy["base64_data"]])
    if not has_any_media_source:
        return []
    logger.debug(
        "[MULTIMEDIA][NORMALIZE] legacy_media_payload_detected provider=%s fallback_message_type=%s",
        provider,
        fallback_message_type.value,
    )
    return [
        normalize_attachment(
            legacy,
            provider=provider,
            fallback_message_type=fallback_message_type,
            fallback_caption=dict_get_any_case(payload, "caption"),
        )
    ]
