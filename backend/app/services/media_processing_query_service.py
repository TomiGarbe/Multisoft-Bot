from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.schemas.media_processing import (
    AttachmentDerivedContentDTO,
    AttachmentProcessingJobDTO,
    AttachmentProcessingStatusDTO,
    ProcessedArtifactDTO,
)
from app.services.attachment_service import AttachmentService
from app.services.attachments.media_processing_orchestrator import MediaProcessingOrchestrator
from app.services.media_processing_service import MediaProcessingService
from app.schemas.internal.message_enums import MediaProcessingCapability


class MediaProcessingQueryService:
    def __init__(self, db: Session) -> None:
        self.processing_service = MediaProcessingService(db)
        self.orchestrator = MediaProcessingOrchestrator(db)
        self.attachment_service = AttachmentService(db)

    def get_processing_status(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> AttachmentProcessingStatusDTO:
        snapshot = self.orchestrator.get_processing_snapshot(attachment_id=attachment_id, tenant_id=tenant_id)
        jobs = self.processing_service.list_jobs_by_attachment(attachment_id=attachment_id, tenant_id=tenant_id)
        return AttachmentProcessingStatusDTO(
            attachment_id=attachment_id,
            status=snapshot.status,
            jobs=[
                AttachmentProcessingJobDTO(
                    id=job.id,
                    attachment_id=job.attachment_id,
                    capability=job.capability,
                    status=job.status,
                    retry_count=job.retry_count,
                    max_attempts=job.max_attempts,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    failed_at=job.failed_at,
                    last_error_code=job.last_error_code,
                    last_error_message=job.last_error_message,
                    metadata_json=job.metadata_json,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                )
                for job in jobs
            ],
        )

    def list_artifacts(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> list[ProcessedArtifactDTO]:
        artifacts = self.processing_service.list_artifacts_by_attachment(attachment_id=attachment_id, tenant_id=tenant_id)
        return self._to_artifact_dto(artifacts)

    def list_artifacts_by_capabilities(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        capabilities: list[MediaProcessingCapability],
    ) -> list[ProcessedArtifactDTO]:
        artifacts = self.processing_service.list_artifacts_by_capabilities(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            capabilities=capabilities,
        )
        return self._to_artifact_dto(artifacts)

    def _to_artifact_dto(self, artifacts) -> list[ProcessedArtifactDTO]:
        return [
            ProcessedArtifactDTO(
                id=item.id,
                attachment_id=item.attachment_id,
                capability=item.capability,
                storage_backend=item.storage_backend,
                storage_key=item.storage_key,
                payload_json=item.payload_json,
                payload_text=item.payload_text,
                content_type=item.content_type,
                size_bytes=item.size_bytes,
                metadata_json=item.metadata_json,
                generated_at=item.generated_at,
                created_at=item.created_at,
            )
            for item in artifacts
        ]

    def get_job(self, *, job_id: uuid.UUID, tenant_id: uuid.UUID) -> AttachmentProcessingJobDTO | None:
        job = self.processing_service.get_job(job_id=job_id, tenant_id=tenant_id)
        if job is None:
            return None
        return AttachmentProcessingJobDTO(
            id=job.id,
            attachment_id=job.attachment_id,
            capability=job.capability,
            status=job.status,
            retry_count=job.retry_count,
            max_attempts=job.max_attempts,
            started_at=job.started_at,
            completed_at=job.completed_at,
            failed_at=job.failed_at,
            last_error_code=job.last_error_code,
            last_error_message=job.last_error_message,
            metadata_json=job.metadata_json,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def list_derived_content_for_message(self, *, message_id: uuid.UUID, tenant_id: uuid.UUID) -> list[AttachmentDerivedContentDTO]:
        return self.list_derived_content_for_message_paginated(message_id=message_id, tenant_id=tenant_id)

    def list_derived_content_for_message_paginated(
        self,
        *,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
        truncate_text_chars: int | None = None,
    ) -> list[AttachmentDerivedContentDTO]:
        attachments = self.attachment_service.list_by_message_id_and_tenant(
            message_id=message_id,
            tenant_id=tenant_id,
            offset=max(offset, 0),
            limit=max(limit, 1),
        )
        attachment_ids = [item.id for item in attachments]
        all_artifacts = self.processing_service.list_artifacts_for_attachments(
            attachment_ids=attachment_ids,
            tenant_id=tenant_id,
        )
        artifacts_by_attachment: dict[uuid.UUID, dict[MediaProcessingCapability, object]] = {}
        for artifact in all_artifacts:
            bucket = artifacts_by_attachment.setdefault(artifact.attachment_id, {})
            bucket[artifact.capability] = artifact

        items: list[AttachmentDerivedContentDTO] = []
        for attachment in attachments:
            artifact_by_capability = artifacts_by_attachment.get(attachment.id, {})
            transcription = artifact_by_capability.get(MediaProcessingCapability.TRANSCRIPTION)
            extraction = artifact_by_capability.get(MediaProcessingCapability.DOCUMENT_EXTRACTION)
            items.append(
                AttachmentDerivedContentDTO(
                    attachment_id=attachment.id,
                    transcription_text=self._truncate_text(transcription.payload_text if transcription else None, truncate_text_chars),
                    extracted_text=self._truncate_text(extraction.payload_text if extraction else None, truncate_text_chars),
                    metadata_json={
                        "attachment_type": attachment.attachment_type.value,
                        "mime_type": attachment.mime_type,
                        "download_status": attachment.download_status.value,
                    },
                )
            )
        return items

    @staticmethod
    def _truncate_text(value: str | None, truncate_text_chars: int | None) -> str | None:
        if value is None or not truncate_text_chars or truncate_text_chars <= 0:
            return value
        if len(value) <= truncate_text_chars:
            return value
        return value[:truncate_text_chars]
