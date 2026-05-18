from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.interfaces.media import MediaProcessingError
from app.providers.media_processing import get_media_processing_provider
from app.schemas.internal.media_processing import ProcessedArtifactCreate
from app.schemas.internal.message_enums import MediaProcessingCapability, ProcessedArtifactStorageBackend
from app.services.attachment_service import AttachmentService
from app.services.transcription_errors import TranscriptionError
from app.services.whisper_transcription_service import WhisperTranscriptionService

logger = logging.getLogger(__name__)


class MediaProcessingRuntimeService:
    def __init__(self, attachment_service: AttachmentService) -> None:
        self.attachment_service = attachment_service
        self.provider = get_media_processing_provider()
        self.whisper_service = WhisperTranscriptionService()

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
            normalized_mime = (attachment.mime_type or "").split(";")[0].strip().lower() or None
            logger.info(
                "[AI][TRANSCRIPTION][FILE_FOUND] attachment_id=%s message_id=%s mime_type=%s audio_path=%s provider=%s model=%s bytes=%s",
                attachment.id,
                attachment.message_id,
                normalized_mime,
                f"attachment_blob://{attachment.id}",
                "whisper_transcription",
                "faster_whisper",
                len(binary_data),
            )
            logger.info(
                "[AI][TRANSCRIPTION][START] attachment_id=%s message_id=%s mime_type=%s provider=%s model=%s",
                attachment.id,
                attachment.message_id,
                normalized_mime,
                "whisper_transcription",
                "faster_whisper",
            )
            try:
                result = self._transcribe_audio_with_whisper(
                    payload=binary_data,
                    filename=attachment.filename,
                    mime_type=attachment.mime_type,
                )
            except MediaProcessingError:
                logger.warning(
                    "[AI][TRANSCRIPTION][FAILED] attachment_id=%s message_id=%s mime_type=%s provider=%s model=%s",
                    attachment.id,
                    attachment.message_id,
                    normalized_mime,
                    "whisper_transcription",
                    "faster_whisper",
                )
                raise
            payload_text = str(result.get("text") or "") or None
            logger.info(
                "[AI][TRANSCRIPTION][SUCCESS] attachment_id=%s message_id=%s mime_type=%s provider=%s model=%s language=%s segments=%s text_chars=%s",
                attachment.id,
                attachment.message_id,
                normalized_mime,
                "whisper_transcription",
                (result.get("provider_response") or {}).get("metadata", {}).get("model") or "faster_whisper",
                result.get("language"),
                len(result.get("segments") or []),
                len(payload_text or ""),
            )
            return self._artifact(attachment, capability, result, payload_text)

        if capability == MediaProcessingCapability.DOCUMENT_EXTRACTION:
            logger.debug(
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
            logger.debug("[MULTIMEDIA][PROCESSING] extraction_completed attachment_id=%s", attachment.id)
            return self._artifact(attachment, capability, result, payload_text)

        raise MediaProcessingError("unsupported_capability", capability.value, retryable=False)

    def _transcribe_audio_with_whisper(
        self,
        *,
        payload: bytes,
        filename: str | None,
        mime_type: str | None,
    ) -> dict:
        suffix = self._resolve_audio_suffix(filename=filename, mime_type=mime_type)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(payload)
                temp_path = Path(temp_file.name)
            result = self.whisper_service.transcribe_file(audio_path=temp_path)
            return {
                "text": result.text,
                "language": result.detected_language,
                "duration_seconds": result.duration_seconds,
                "segments": [segment.model_dump(mode="json") for segment in result.segments],
                "provider_response": {
                    "metadata": result.metadata,
                },
            }
        except TranscriptionError as exc:
            logger.warning(
                "[AI][TRANSCRIPTION][FAILED] attachment_id=%s message_id=%s mime_type=%s provider=%s model=%s code=%s retryable=%s detail=%s",
                None,
                None,
                (mime_type or "").split(";")[0].strip().lower() or None,
                "whisper_transcription",
                "faster_whisper",
                exc.code,
                exc.retryable,
                exc.message,
            )
            raise MediaProcessingError(exc.code, exc.message, retryable=exc.retryable) from exc
        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass
                except OSError:
                    logger.warning("[MULTIMEDIA][PROCESSING] temp_audio_cleanup_failed path=%s", temp_path)

    def _validate_limits(self, *, attachment, payload: bytes, capability: MediaProcessingCapability) -> None:
        if not payload:
            raise MediaProcessingError("blob_empty", "attachment blob is empty", retryable=False)
        if capability == MediaProcessingCapability.TRANSCRIPTION:
            if attachment.size_bytes and attachment.size_bytes > settings.ATTACHMENT_MAX_AUDIO_BYTES:
                raise MediaProcessingError("audio_size_exceeded", str(attachment.size_bytes), retryable=False)
            if attachment.duration_ms and attachment.duration_ms > settings.MEDIA_MAX_AUDIO_DURATION_MS:
                raise MediaProcessingError("audio_duration_exceeded", str(attachment.duration_ms), retryable=False)
            normalized_mime = (attachment.mime_type or "").split(";")[0].strip().lower()
            if normalized_mime and not (normalized_mime.startswith("audio/") or normalized_mime.startswith("video/")):
                raise MediaProcessingError("audio_mime_invalid", normalized_mime, retryable=False)
        if capability == MediaProcessingCapability.DOCUMENT_EXTRACTION:
            if attachment.size_bytes and attachment.size_bytes > settings.ATTACHMENT_MAX_DOCUMENT_BYTES:
                raise MediaProcessingError("document_size_exceeded", str(attachment.size_bytes), retryable=False)

    def _artifact(self, attachment, capability: MediaProcessingCapability, result: dict, payload_text: str | None) -> ProcessedArtifactCreate:
        metadata = {
            "provider": "whisper_transcription" if capability == MediaProcessingCapability.TRANSCRIPTION else "local_media_processing",
            "generated_at_iso": datetime.now(timezone.utc).isoformat(),
            "mime_type": attachment.mime_type,
            "filename": attachment.filename,
        }
        if capability == MediaProcessingCapability.TRANSCRIPTION:
            metadata["audio_size_bytes"] = attachment.size_bytes
        if capability == MediaProcessingCapability.TRANSCRIPTION and result.get("language"):
            metadata["detected_language"] = result.get("language")
        if capability == MediaProcessingCapability.TRANSCRIPTION and result.get("duration_seconds") is not None:
            metadata["audio_duration_seconds"] = result.get("duration_seconds")
        if capability == MediaProcessingCapability.TRANSCRIPTION and isinstance(result.get("segments"), list):
            metadata["segment_count"] = len(result.get("segments") or [])
        provider_metadata = ((result.get("provider_response") or {}).get("metadata") or {})
        if capability == MediaProcessingCapability.TRANSCRIPTION and isinstance(provider_metadata, dict):
            metadata["transcription_model"] = provider_metadata.get("model")
            metadata["transcription_device"] = provider_metadata.get("device")
            metadata["transcription_compute_type"] = provider_metadata.get("compute_type")
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

    @staticmethod
    def _resolve_audio_suffix(*, filename: str | None, mime_type: str | None) -> str:
        if filename and "." in filename:
            suffix = "." + filename.rsplit(".", 1)[-1].lower()
            if suffix in {".mp3", ".wav", ".ogg", ".opus", ".webm", ".m4a", ".mp4", ".mov"}:
                return suffix
        by_mime = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/ogg": ".ogg",
            "audio/opus": ".opus",
            "audio/webm": ".webm",
            "audio/mp4": ".m4a",
            "audio/x-m4a": ".m4a",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "video/webm": ".webm",
        }
        normalized = (mime_type or "").split(";")[0].strip().lower()
        return by_mime.get(normalized, ".bin")
