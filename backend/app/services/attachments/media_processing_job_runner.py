from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.attachment_service import AttachmentService
from app.interfaces.media import MediaProcessingError
from app.services.realtime_service import event_bus
from app.services.attachments.media_processing_runtime_service import MediaProcessingRuntimeService
from app.services.media_processing_service import MediaProcessingService
from app.services.retry_policy import RetryPolicy, run_with_retries
from app.schemas.internal.media_processing import (
    MetadataExtractionResult,
    ProcessedArtifactCreate,
)
from app.schemas.internal.message_enums import MediaProcessingCapability, ProcessedArtifactStorageBackend

logger = logging.getLogger(__name__)


class MediaProcessingJobRunner:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.processing_service = MediaProcessingService(db)
        self.attachment_service = AttachmentService(db)
        self.runtime_service = MediaProcessingRuntimeService(self.attachment_service)
        self.retry_policy = RetryPolicy(
            max_attempts=max(1, settings.MEDIA_PROCESSING_MAX_RETRIES + 1),
            initial_backoff_seconds=settings.MEDIA_PROCESSING_INITIAL_BACKOFF_SECONDS,
            max_backoff_seconds=settings.MEDIA_PROCESSING_MAX_BACKOFF_SECONDS,
        )

    def run(self, *, job_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        job = self.processing_service.get_job(job_id=job_id, tenant_id=tenant_id)
        if job is None:
            logger.warning("[MULTIMEDIA][PROCESSING] job_missing job_id=%s tenant_id=%s", job_id, tenant_id)
            return
        attachment = self.attachment_service.get_by_id_and_tenant(job.attachment_id, tenant_id)
        if attachment is None:
            self.processing_service.mark_job_failed(
                job=job, error_code="attachment_not_found", error_message="Attachment not found", retry_count=job.retry_count
            )
            self.db.commit()
            return

        self.processing_service.mark_job_processing(job=job)
        self.db.commit()
        logger.debug(
            "[MULTIMEDIA][PROCESSING] started job_id=%s tenant_id=%s attachment_id=%s capability=%s",
            job.id,
            tenant_id,
            job.attachment_id,
            job.capability.value,
        )
        started_at = time.perf_counter()

        try:
            artifact = run_with_retries(
                operation_name=f"media_processing_{job.capability.value}",
                operation=lambda: self._process_capability(job_capability=job.capability, attachment=attachment),
                policy=self.retry_policy,
                is_retryable=self._is_retryable_error,
                context={"job_id": str(job.id), "attachment_id": str(job.attachment_id)},
            )
            if artifact is None:
                self.processing_service.mark_job_skipped(job=job, reason="not_implemented_yet")
            else:
                self.processing_service.replace_artifact(artifact)
                logger.debug(
                    "[MULTIMEDIA][PROCESSING] artifact_generated job_id=%s attachment_id=%s capability=%s backend=%s",
                    job.id,
                    job.attachment_id,
                    job.capability.value,
                    artifact.storage_backend.value,
                )
                self.processing_service.mark_job_completed(
                    job=job,
                    metadata_json=self._build_completion_metadata(
                        artifact=artifact,
                        started_at=started_at,
                    ),
                )
                self._sync_transcription_metadata(
                    attachment=attachment,
                    job_capability=job.capability,
                    artifact=artifact,
                    job_status="completed",
                )
            self.db.commit()
            self._publish_transcription_update(attachment=attachment, job_capability=job.capability, job_status="completed")
            logger.info(
                "[MULTIMEDIA][PROCESSING] completed job_id=%s capability=%s duration_ms=%s",
                job.id,
                job.capability.value,
                int((time.perf_counter() - started_at) * 1000),
            )
        except Exception as exc:
            self.db.rollback()
            job = self.processing_service.get_job(job_id=job_id, tenant_id=tenant_id)
            if job is None:
                return
            self.processing_service.mark_job_failed(
                job=job,
                error_code=self._error_code(exc),
                error_message=str(exc),
                retry_count=job.retry_count + 1,
            )
            self._sync_transcription_metadata(
                attachment=attachment,
                job_capability=job.capability,
                artifact=None,
                job_status="failed",
                error_code=self._error_code(exc),
            )
            self.db.commit()
            self._publish_transcription_update(attachment=attachment, job_capability=job.capability, job_status="failed")
            logger.warning(
                "[MULTIMEDIA][PROCESSING] failed job_id=%s capability=%s error=%s",
                job.id,
                job.capability.value,
                exc,
            )

    def _build_completion_metadata(self, *, artifact: ProcessedArtifactCreate, started_at: float) -> dict:
        metadata = {
                        "completed_at_iso": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": int((time.perf_counter() - started_at) * 1000),
                        "estimated_cost_usd": 0.0,
                    }
        payload_json = artifact.payload_json or {}
        artifact_meta = artifact.metadata_json or {}
        if artifact.capability == MediaProcessingCapability.TRANSCRIPTION:
            metadata["transcription_language"] = payload_json.get("language") or artifact_meta.get("detected_language")
            metadata["transcription_duration_seconds"] = payload_json.get("duration_seconds")
            metadata["transcription_segment_count"] = len(payload_json.get("segments") or [])
            metadata["audio_size_bytes"] = artifact_meta.get("audio_size_bytes")
        return metadata

    def _process_capability(self, *, job_capability: MediaProcessingCapability, attachment) -> ProcessedArtifactCreate | None:
        if job_capability == MediaProcessingCapability.METADATA_EXTRACTION:
            payload_json = MetadataExtractionResult(
                mime_type=attachment.mime_type,
                size_bytes=attachment.size_bytes,
                duration_ms=attachment.duration_ms,
                width=attachment.width,
                height=attachment.height,
                checksum_sha256=attachment.checksum_sha256,
            ).model_dump(mode="json")
            return ProcessedArtifactCreate(
                tenant_id=attachment.tenant_id,
                attachment_id=attachment.id,
                capability=job_capability,
                storage_backend=ProcessedArtifactStorageBackend.INLINE_JSON,
                payload_json=payload_json,
                content_type="application/json",
                metadata_json={
                    "generated_at_iso": datetime.now(timezone.utc).isoformat(),
                    "provider": "foundation_phase_7",
                },
            )
        if job_capability in {
            MediaProcessingCapability.TRANSCRIPTION,
            MediaProcessingCapability.DOCUMENT_EXTRACTION,
        }:
            return self.runtime_service.process_capability(attachment=attachment, capability=job_capability)
        return None

    @staticmethod
    def _is_retryable_error(exc: Exception) -> bool:
        if isinstance(exc, MediaProcessingError):
            return exc.retryable
        return False

    @staticmethod
    def _error_code(exc: Exception) -> str:
        if isinstance(exc, MediaProcessingError):
            return exc.code
        return "processing_error"

    def _sync_transcription_metadata(
        self,
        *,
        attachment,
        job_capability: MediaProcessingCapability,
        artifact: ProcessedArtifactCreate | None,
        job_status: str,
        error_code: str | None = None,
    ) -> None:
        if job_capability != MediaProcessingCapability.TRANSCRIPTION:
            return
        metadata = dict(attachment.metadata_json or {})
        if job_status == "completed" and artifact is not None:
            provider_meta = dict((artifact.metadata_json or {}))
            payload_json = dict((artifact.payload_json or {}))
            transcription_text = (artifact.payload_text or "").strip()
            metadata["transcription"] = transcription_text or None
            metadata["transcription_status"] = "completed"
            metadata["transcription_provider"] = str(provider_meta.get("provider") or "whisper_transcription")
            metadata["transcription_language"] = payload_json.get("language") or provider_meta.get("detected_language")
            metadata["transcription_model"] = provider_meta.get("transcription_model") or "faster_whisper"
        elif job_status == "failed":
            metadata["transcription_status"] = "failed"
            if error_code:
                metadata["transcription_error_code"] = error_code
        self.attachment_service.update_attachment_metadata(attachment=attachment, metadata_json=metadata)

    def _publish_transcription_update(self, *, attachment, job_capability: MediaProcessingCapability, job_status: str) -> None:
        if job_capability != MediaProcessingCapability.TRANSCRIPTION:
            return
        event_bus.publish(
            "attachment_updated",
            {
                "type": "attachment_updated",
                "conversation_id": str(getattr(getattr(attachment, "message", None), "conversation_id", "") or ""),
                "message_id": str(attachment.message_id),
                "attachment_id": str(attachment.id),
                "processing_capability": "transcription",
                "processing_status": job_status,
            },
            tenant_id=attachment.tenant_id,
        )
