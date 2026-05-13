from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.media_processing import (
    AttachmentDerivedContentDTO,
    AttachmentProcessingJobDTO,
    AttachmentProcessingStatusDTO,
    ProcessedArtifactDTO,
)
from app.schemas.internal.message_enums import MediaProcessingCapability
from app.services.media_processing_query_service import MediaProcessingQueryService

router = APIRouter(tags=["media-processing"])


def _service(db: Session) -> MediaProcessingQueryService:
    return MediaProcessingQueryService(db)


@router.get("/attachments/{attachment_id}/status", response_model=AttachmentProcessingStatusDTO)
async def get_attachment_processing_status(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    return _service(db).get_processing_status(attachment_id=attachment_id, tenant_id=current_tenant_id)


@router.get("/attachments/{attachment_id}/artifacts", response_model=list[ProcessedArtifactDTO])
async def list_attachment_processing_artifacts(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    return _service(db).list_artifacts(attachment_id=attachment_id, tenant_id=current_tenant_id)


@router.get("/attachments/{attachment_id}/transcription", response_model=list[ProcessedArtifactDTO])
async def get_attachment_transcription(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    return [
        item
        for item in _service(db).list_artifacts_by_capabilities(
            attachment_id=attachment_id,
            tenant_id=current_tenant_id,
            capabilities=[MediaProcessingCapability.TRANSCRIPTION],
        )
    ]


@router.get("/attachments/{attachment_id}/ocr", response_model=list[ProcessedArtifactDTO])
async def get_attachment_ocr(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    return [
        item
        for item in _service(db).list_artifacts_by_capabilities(
            attachment_id=attachment_id,
            tenant_id=current_tenant_id,
            capabilities=[MediaProcessingCapability.OCR],
        )
    ]


@router.get("/attachments/{attachment_id}/thumbnails", response_model=list[ProcessedArtifactDTO])
async def get_attachment_thumbnails(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    return [
        item
        for item in _service(db).list_artifacts_by_capabilities(
            attachment_id=attachment_id,
            tenant_id=current_tenant_id,
            capabilities=[MediaProcessingCapability.THUMBNAILS],
        )
    ]


@router.get("/attachments/{attachment_id}/extracted-text", response_model=list[ProcessedArtifactDTO])
async def get_attachment_extracted_text(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    return [
        item
        for item in _service(db).list_artifacts_by_capabilities(
            attachment_id=attachment_id,
            tenant_id=current_tenant_id,
            capabilities=[MediaProcessingCapability.DOCUMENT_EXTRACTION],
        )
    ]


@router.get("/jobs/{job_id}", response_model=AttachmentProcessingJobDTO)
async def get_processing_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    job = _service(db).get_job(job_id=job_id, tenant_id=current_tenant_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing job not found")
    return job


@router.get("/messages/{message_id}/derived-content", response_model=list[AttachmentDerivedContentDTO])
async def list_message_derived_content(
    message_id: uuid.UUID,
    offset: int = 0,
    limit: int = 100,
    truncate_text_chars: int | None = None,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    safe_limit = max(1, min(limit, 500))
    safe_truncate = None if truncate_text_chars is None else max(0, min(truncate_text_chars, 20000))
    return _service(db).list_derived_content_for_message_paginated(
        message_id=message_id,
        tenant_id=current_tenant_id,
        offset=max(offset, 0),
        limit=safe_limit,
        truncate_text_chars=safe_truncate,
    )
