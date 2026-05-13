from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.media_processing import AttachmentProcessingJob, ProcessedArtifact
from app.repositories.base_repository import BaseRepository
from app.schemas.internal.media_processing import AttachmentProcessingJobCreate, ProcessedArtifactCreate
from app.schemas.internal.message_enums import MediaProcessingStatus


class MediaProcessingRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_job(self, data: AttachmentProcessingJobCreate) -> AttachmentProcessingJob:
        job = AttachmentProcessingJob(
            tenant_id=data.tenant_id,
            attachment_id=data.attachment_id,
            capability=data.capability,
            status=data.status,
            max_attempts=data.max_attempts,
            metadata_json=data.metadata_json,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def list_jobs_by_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> list[AttachmentProcessingJob]:
        stmt = select(AttachmentProcessingJob).where(
            AttachmentProcessingJob.attachment_id == attachment_id,
            AttachmentProcessingJob.tenant_id == tenant_id,
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_job(self, *, job_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[AttachmentProcessingJob]:
        stmt = select(AttachmentProcessingJob).where(
            AttachmentProcessingJob.id == job_id,
            AttachmentProcessingJob.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def update_job_state(
        self,
        *,
        job: AttachmentProcessingJob,
        status: MediaProcessingStatus,
        retry_count: Optional[int] = None,
        next_retry_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        failed_at: Optional[datetime] = None,
        last_error_code: Optional[str] = None,
        last_error_message: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> AttachmentProcessingJob:
        job.status = status
        if retry_count is not None:
            job.retry_count = retry_count
        if next_retry_at is not None:
            job.next_retry_at = next_retry_at
        if started_at is not None:
            job.started_at = started_at
        if completed_at is not None:
            job.completed_at = completed_at
        if failed_at is not None:
            job.failed_at = failed_at
        if last_error_code is not None:
            job.last_error_code = last_error_code
        if last_error_message is not None:
            job.last_error_message = last_error_message
        if metadata_json is not None:
            job.metadata_json = metadata_json
        self.db.flush()
        return job

    def create_artifact(self, data: ProcessedArtifactCreate) -> ProcessedArtifact:
        artifact = ProcessedArtifact(
            tenant_id=data.tenant_id,
            attachment_id=data.attachment_id,
            capability=data.capability,
            storage_backend=data.storage_backend,
            storage_key=data.storage_key,
            payload_json=data.payload_json,
            payload_text=data.payload_text,
            content_type=data.content_type,
            size_bytes=data.size_bytes,
            metadata_json=data.metadata_json,
        )
        self.db.add(artifact)
        self.db.flush()
        return artifact

    def replace_artifact(self, data: ProcessedArtifactCreate) -> ProcessedArtifact:
        self.db.execute(
            delete(ProcessedArtifact).where(
                ProcessedArtifact.tenant_id == data.tenant_id,
                ProcessedArtifact.attachment_id == data.attachment_id,
                ProcessedArtifact.capability == data.capability,
            )
        )
        self.db.flush()
        return self.create_artifact(data)

    def list_artifacts_by_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> list[ProcessedArtifact]:
        stmt = select(ProcessedArtifact).where(
            ProcessedArtifact.attachment_id == attachment_id,
            ProcessedArtifact.tenant_id == tenant_id,
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_artifacts_by_capabilities(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        capabilities: Sequence,
    ) -> list[ProcessedArtifact]:
        stmt = select(ProcessedArtifact).where(
            ProcessedArtifact.attachment_id == attachment_id,
            ProcessedArtifact.tenant_id == tenant_id,
            ProcessedArtifact.capability.in_(capabilities),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_artifacts_for_attachments(
        self,
        *,
        attachment_ids: Sequence[uuid.UUID],
        tenant_id: uuid.UUID,
    ) -> list[ProcessedArtifact]:
        if not attachment_ids:
            return []
        stmt = select(ProcessedArtifact).where(
            ProcessedArtifact.tenant_id == tenant_id,
            ProcessedArtifact.attachment_id.in_(attachment_ids),
        )
        return list(self.db.execute(stmt).scalars().all())
