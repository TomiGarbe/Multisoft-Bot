from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.internal.message_enums import (
    MediaProcessingCapability,
    MediaProcessingStatus,
    ProcessedArtifactStorageBackend,
)


class AttachmentProcessingJobDTO(BaseModel):
    id: uuid.UUID
    attachment_id: uuid.UUID
    capability: MediaProcessingCapability
    status: MediaProcessingStatus
    retry_count: int
    max_attempts: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProcessedArtifactDTO(BaseModel):
    id: uuid.UUID
    attachment_id: uuid.UUID
    capability: MediaProcessingCapability
    storage_backend: ProcessedArtifactStorageBackend
    storage_key: Optional[str] = None
    payload_json: Optional[dict[str, Any]] = None
    payload_text: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata_json: Optional[dict[str, Any]] = None
    generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AttachmentProcessingStatusDTO(BaseModel):
    attachment_id: uuid.UUID
    status: MediaProcessingStatus
    jobs: list[AttachmentProcessingJobDTO]


class AttachmentDerivedContentDTO(BaseModel):
    attachment_id: uuid.UUID
    transcription_text: Optional[str] = None
    extracted_text: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
