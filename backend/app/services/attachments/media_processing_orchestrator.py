from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy.orm import Session

from app.services.attachment_service import AttachmentService
from app.services.attachments.media_processing_capability_service import MediaProcessingCapabilityService
from app.services.attachments.media_processing_dispatcher import MediaProcessingJobDispatch, media_processing_dispatcher
from app.services.attachments.media_processing_feature_service import MediaProcessingFeatureService
from app.services.attachments.media_processing_security_service import MediaProcessingSecurityService
from app.services.media_processing_service import MediaProcessingService
from app.schemas.internal.media_processing import AttachmentProcessingJobCreate, ProcessingLifecycleSnapshot
from app.schemas.internal.message_enums import MediaProcessingCapability, MediaProcessingStatus

logger = logging.getLogger(__name__)


class MediaProcessingOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.attachment_service = AttachmentService(db)
        self.processing_service = MediaProcessingService(db)
        self.capability_service = MediaProcessingCapabilityService()
        self.feature_service = MediaProcessingFeatureService(db)
        self.security_service = MediaProcessingSecurityService()

    def orchestrate_for_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> ProcessingLifecycleSnapshot | None:
        attachment = self.attachment_service.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            logger.warning("[MULTIMEDIA][PROCESSING] attachment_missing attachment_id=%s tenant_id=%s", attachment_id, tenant_id)
            return None
        if attachment.download_status.value != "completed":
            logger.debug(
                "[MULTIMEDIA][PROCESSING] waiting_download attachment_id=%s tenant_id=%s download_status=%s",
                attachment.id,
                attachment.tenant_id,
                attachment.download_status.value,
            )
            return None
        allowed, reason = self.security_service.validate_for_processing(attachment)
        if not allowed:
            logger.warning(
                "[MULTIMEDIA][PROCESSING] skipped_security attachment_id=%s tenant_id=%s reason=%s",
                attachment_id,
                tenant_id,
                reason,
            )
            return ProcessingLifecycleSnapshot(
                attachment_id=attachment_id,
                tenant_id=tenant_id,
                status=MediaProcessingStatus.SKIPPED,
                skipped_capabilities=[],
            )

        start = time.perf_counter()
        capabilities = self.capability_service.resolve_capabilities(attachment)
        filtered_capabilities = []
        channel_id = getattr(getattr(attachment, "message", None), "channel_id", None)
        for capability in capabilities:
            if (
                attachment.attachment_type.value == "audio"
                and getattr(getattr(attachment, "message", None), "direction", None) == "inbound"
                and capability == MediaProcessingCapability.TRANSCRIPTION
            ):
                filtered_capabilities.append(capability)
                continue
            decision = self.feature_service.is_capability_enabled(
                tenant_id=tenant_id,
                channel_id=channel_id,
                capability=capability,
            )
            if decision.enabled:
                filtered_capabilities.append(capability)
            else:
                logger.debug(
                    "[MULTIMEDIA][PROCESSING] capability_disabled attachment_id=%s tenant_id=%s capability=%s reason=%s",
                    attachment_id,
                    tenant_id,
                    capability.value,
                    decision.reason,
                )

        existing_jobs = self.processing_service.list_jobs_by_attachment(attachment_id=attachment_id, tenant_id=tenant_id)
        existing_capabilities = {item.capability for item in existing_jobs}
        jobs = []
        for capability in filtered_capabilities:
            if capability in existing_capabilities:
                logger.debug(
                    "[MULTIMEDIA][PROCESSING] duplicate_job_skipped attachment_id=%s tenant_id=%s capability=%s",
                    attachment_id,
                    tenant_id,
                    capability.value,
                )
                continue
            job = self.processing_service.create_job(
                AttachmentProcessingJobCreate(
                    tenant_id=tenant_id,
                    attachment_id=attachment_id,
                    capability=capability,
                    status=MediaProcessingStatus.QUEUED,
                )
            )
            self.processing_service.mark_job_queued(job=job)
            jobs.append(job)
        self.db.commit()

        for job in jobs:
            logger.info(
                "[MULTIMEDIA][PROCESSING] queued job_id=%s tenant_id=%s attachment_id=%s capability=%s",
                job.id,
                tenant_id,
                attachment_id,
                job.capability.value,
            )
            if job.capability.value == "transcription":
                logger.info(
                    "[AI][TRANSCRIPTION][JOB_CREATED] job_id=%s tenant_id=%s attachment_id=%s message_id=%s mime_type=%s provider=%s model=%s",
                    job.id,
                    tenant_id,
                    attachment_id,
                    getattr(attachment, "message_id", None),
                    attachment.mime_type,
                    "whisper_transcription",
                    "faster_whisper",
                )
            media_processing_dispatcher.enqueue(MediaProcessingJobDispatch(job_id=job.id, tenant_id=tenant_id))

        logger.debug(
            "[MULTIMEDIA][PROCESSING] jobs_created attachment_id=%s tenant_id=%s jobs=%s capabilities=%s size_bytes=%s duration_ms=%s",
            attachment_id,
            tenant_id,
            len(jobs),
            [cap.value for cap in filtered_capabilities],
            attachment.size_bytes,
            int((time.perf_counter() - start) * 1000),
        )
        return self.get_processing_snapshot(attachment_id=attachment_id, tenant_id=tenant_id)

    def get_processing_snapshot(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> ProcessingLifecycleSnapshot:
        jobs = self.processing_service.list_jobs_by_attachment(attachment_id=attachment_id, tenant_id=tenant_id)
        if not jobs:
            return ProcessingLifecycleSnapshot(
                attachment_id=attachment_id,
                tenant_id=tenant_id,
                status=MediaProcessingStatus.PENDING,
            )

        latest_status = self._reduce_status([job.status for job in jobs])
        completed = [job.capability for job in jobs if job.status == MediaProcessingStatus.COMPLETED]
        failed = [job.capability for job in jobs if job.status == MediaProcessingStatus.FAILED]
        skipped = [job.capability for job in jobs if job.status == MediaProcessingStatus.SKIPPED]
        updated_at = max((job.updated_at for job in jobs if job.updated_at is not None), default=None)
        return ProcessingLifecycleSnapshot(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            status=latest_status,
            completed_capabilities=completed,
            failed_capabilities=failed,
            skipped_capabilities=skipped,
            updated_at=updated_at,
        )

    def _reduce_status(self, statuses: list[MediaProcessingStatus]) -> MediaProcessingStatus:
        if any(status == MediaProcessingStatus.FAILED for status in statuses):
            if any(status == MediaProcessingStatus.COMPLETED for status in statuses):
                return MediaProcessingStatus.PARTIAL
            return MediaProcessingStatus.FAILED
        if any(status == MediaProcessingStatus.PROCESSING for status in statuses):
            return MediaProcessingStatus.PROCESSING
        if any(status == MediaProcessingStatus.QUEUED for status in statuses):
            return MediaProcessingStatus.QUEUED
        if any(status == MediaProcessingStatus.COMPLETED for status in statuses):
            if all(status in {MediaProcessingStatus.COMPLETED, MediaProcessingStatus.SKIPPED} for status in statuses):
                return MediaProcessingStatus.COMPLETED
            return MediaProcessingStatus.PARTIAL
        if all(status == MediaProcessingStatus.SKIPPED for status in statuses):
            return MediaProcessingStatus.SKIPPED
        return MediaProcessingStatus.PENDING
