from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.media_processing_repository import MediaProcessingRepository
from app.schemas.internal.media_processing import AttachmentProcessingJobCreate, ProcessedArtifactCreate
from app.schemas.internal.message_enums import MediaProcessingStatus
from app.schemas.internal.message_enums import MediaProcessingCapability


class MediaProcessingService:
    def __init__(self, db: Session) -> None:
        self.repository = MediaProcessingRepository(db)

    def create_job(self, data: AttachmentProcessingJobCreate):
        return self.repository.create_job(data)

    def list_jobs_by_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID):
        return self.repository.list_jobs_by_attachment(attachment_id=attachment_id, tenant_id=tenant_id)

    def list_jobs_for_attachments(self, *, attachment_ids: list[uuid.UUID], tenant_id: uuid.UUID):
        return self.repository.list_jobs_for_attachments(attachment_ids=attachment_ids, tenant_id=tenant_id)

    def get_job(self, *, job_id: uuid.UUID, tenant_id: uuid.UUID):
        return self.repository.get_job(job_id=job_id, tenant_id=tenant_id)

    def mark_job_queued(self, *, job) -> None:
        self.repository.update_job_state(job=job, status=MediaProcessingStatus.QUEUED)

    def mark_job_processing(self, *, job) -> None:
        self.repository.update_job_state(
            job=job,
            status=MediaProcessingStatus.PROCESSING,
            started_at=datetime.now(timezone.utc),
        )

    def mark_job_completed(self, *, job, metadata_json: Optional[dict] = None) -> None:
        self.repository.update_job_state(
            job=job,
            status=MediaProcessingStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
            metadata_json=metadata_json,
        )

    def mark_job_skipped(self, *, job, reason: str) -> None:
        metadata = dict(job.metadata_json or {})
        metadata["skip_reason"] = reason
        self.repository.update_job_state(
            job=job,
            status=MediaProcessingStatus.SKIPPED,
            completed_at=datetime.now(timezone.utc),
            metadata_json=metadata,
        )

    def mark_job_failed(self, *, job, error_code: str, error_message: str, retry_count: int) -> None:
        self.repository.update_job_state(
            job=job,
            status=MediaProcessingStatus.FAILED,
            failed_at=datetime.now(timezone.utc),
            last_error_code=error_code,
            last_error_message=error_message,
            retry_count=retry_count,
        )

    def replace_artifact(self, data: ProcessedArtifactCreate):
        return self.repository.replace_artifact(data)

    def list_artifacts_by_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID):
        return self.repository.list_artifacts_by_attachment(attachment_id=attachment_id, tenant_id=tenant_id)

    def list_artifacts_for_attachments(self, *, attachment_ids: list[uuid.UUID], tenant_id: uuid.UUID):
        return self.repository.list_artifacts_for_attachments(attachment_ids=attachment_ids, tenant_id=tenant_id)

    def list_artifacts_by_capabilities(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        capabilities: list[MediaProcessingCapability],
    ):
        return self.repository.list_artifacts_by_capabilities(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            capabilities=capabilities,
        )
