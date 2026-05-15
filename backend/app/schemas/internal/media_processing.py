from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.internal.message_enums import (
    MediaProcessingCapability,
    MediaProcessingStatus,
    ProcessedArtifactStorageBackend,
)


class TranscriptionResult(BaseModel):
    text: Optional[str] = None
    segments: list[dict[str, Any]] = Field(default_factory=list)
    language: Optional[str] = None


class DocumentExtractionResult(BaseModel):
    text: Optional[str] = None
    pages: list[dict[str, Any]] = Field(default_factory=list)


class EmbeddingResult(BaseModel):
    model: Optional[str] = None
    vector_dimensions: Optional[int] = None
    vector_reference: Optional[str] = None


class ModerationResult(BaseModel):
    flagged: bool = False
    categories: list[str] = Field(default_factory=list)
    score: Optional[float] = None


class ThumbnailResult(BaseModel):
    thumbnail_keys: list[str] = Field(default_factory=list)
    width: Optional[int] = None
    height: Optional[int] = None


class MetadataExtractionResult(BaseModel):
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    checksum_sha256: Optional[str] = None


class ProcessedArtifactCreate(BaseModel):
    tenant_id: uuid.UUID
    attachment_id: uuid.UUID
    capability: MediaProcessingCapability
    storage_backend: ProcessedArtifactStorageBackend = ProcessedArtifactStorageBackend.INLINE_JSON
    storage_key: Optional[str] = None
    payload_json: Optional[dict[str, Any]] = None
    payload_text: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata_json: Optional[dict[str, Any]] = None


class AttachmentProcessingJobCreate(BaseModel):
    tenant_id: uuid.UUID
    attachment_id: uuid.UUID
    capability: MediaProcessingCapability
    status: MediaProcessingStatus = MediaProcessingStatus.PENDING
    max_attempts: int = 3
    metadata_json: Optional[dict[str, Any]] = None


class ProcessingLifecycleSnapshot(BaseModel):
    attachment_id: uuid.UUID
    tenant_id: uuid.UUID
    status: MediaProcessingStatus
    completed_capabilities: list[MediaProcessingCapability] = Field(default_factory=list)
    failed_capabilities: list[MediaProcessingCapability] = Field(default_factory=list)
    skipped_capabilities: list[MediaProcessingCapability] = Field(default_factory=list)
    updated_at: Optional[datetime] = None
