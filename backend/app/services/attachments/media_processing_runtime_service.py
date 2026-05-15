from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.interfaces.media import MediaProcessingError
from app.providers.media_processing import get_media_processing_provider
from app.schemas.internal.media_processing import ProcessedArtifactCreate
from app.schemas.internal.message_enums import MediaProcessingCapability, ProcessedArtifactStorageBackend
from app.services.attachment_service import AttachmentService

logger = logging.getLogger(__name__)


class MediaProcessingRuntimeService:
    def __init__(self, attachment_service: AttachmentService) -> None:
        self.attachment_service = attachment_service
        self.provider = get_media_processing_provider()

    def process_capability(self, *, attachment, capability: MediaProcessingCapability) -> ProcessedArtifactCreate:
        payload = self.attachment_service.load_attachment_blob(
            attachment_id=attachment.id,
            tenant_id=attachment.tenant_id,
            storage_key=attachment.storage_key,
        )
        if payload is None:
            raise MediaProcessingError("blob_not_available", "attachment blob not available", retryable=False)

        binary_data = payload.payload
        self._validate_limits(attachment=attachment, payload=binary_data, capability=capability)

        if capability == MediaProcessingCapability.TRANSCRIPTION:
            logger.warning(
                "[MULTIMEDIA][PROCESSING] transcription_started attachment_id=%s mime=%s",
                attachment.id,
                attachment.mime_type,
            )
            result = self.provider.transcribe_audio(payload=binary_data, mime_type=attachment.mime_type, filename=attachment.filename)
            payload_text = str(result.get("text") or "") or None
            logger.warning("[MULTIMEDIA][PROCESSING] transcription_completed attachment_id=%s", attachment.id)
            return self._artifact(attachment, capability, result, payload_text)

        if capability == MediaProcessingCapability.DOCUMENT_EXTRACTION:
            logger.warning(
                "[MULTIMEDIA][PROCESSING] extraction_started attachment_id=%s mime=%s",
                attachment.id,
                attachment.mime_type,
            )
            result = self.provider.extract_document_text(
                payload=binary_data,
                mime_type=attachment.mime_type,
                filename=attachment.filename,
            )
            payload_text = str(result.get("text") or "") or None
            logger.warning("[MULTIMEDIA][PROCESSING] extraction_completed attachment_id=%s", attachment.id)
            return self._artifact(attachment, capability, result, payload_text)

        raise MediaProcessingError("unsupported_capability", capability.value, retryable=False)

    def _validate_limits(self, *, attachment, payload: bytes, capability: MediaProcessingCapability) -> None:
        if capability == MediaProcessingCapability.TRANSCRIPTION:
            if attachment.duration_ms and attachment.duration_ms > settings.MEDIA_MAX_AUDIO_DURATION_MS:
                raise MediaProcessingError("audio_duration_exceeded", str(attachment.duration_ms), retryable=False)
        if capability == MediaProcessingCapability.DOCUMENT_EXTRACTION:
            if attachment.size_bytes and attachment.size_bytes > settings.ATTACHMENT_MAX_DOCUMENT_BYTES:
                raise MediaProcessingError("document_size_exceeded", str(attachment.size_bytes), retryable=False)

    def _artifact(self, attachment, capability: MediaProcessingCapability, result: dict, payload_text: str | None) -> ProcessedArtifactCreate:
        metadata = {
            "provider": "local_media_processing",
            "generated_at_iso": datetime.now(timezone.utc).isoformat(),
            "mime_type": attachment.mime_type,
            "filename": attachment.filename,
        }
        if capability == MediaProcessingCapability.TRANSCRIPTION and result.get("language"):
            metadata["detected_language"] = result.get("language")
        if capability == MediaProcessingCapability.DOCUMENT_EXTRACTION and isinstance(result.get("pages"), list):
            metadata["page_count"] = len(result.get("pages") or [])
            if metadata["page_count"] > settings.MEDIA_MAX_DOCUMENT_PAGES:
                raise MediaProcessingError("document_pages_exceeded", str(metadata["page_count"]), retryable=False)

        return ProcessedArtifactCreate(
            tenant_id=attachment.tenant_id,
            attachment_id=attachment.id,
            capability=capability,
            storage_backend=ProcessedArtifactStorageBackend.INLINE_JSON,
            payload_json=result,
            payload_text=payload_text,
            content_type="application/json",
            size_bytes=len(payload_text.encode("utf-8")) if payload_text else None,
            metadata_json=metadata,
        )
