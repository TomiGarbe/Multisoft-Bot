from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.internal.message_enums import AttachmentDownloadStatus, AttachmentType, StorageBackend


class AttachmentMetadataDTO(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    tenant_id: uuid.UUID
    attachment_type: AttachmentType
    storage_backend: StorageBackend
    storage_key: Optional[str] = None
    provider_media_id: Optional[str] = None
    provider_url: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    extension: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    download_status: AttachmentDownloadStatus
    metadata_json: Optional[dict[str, Any]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    caption: Optional[str] = None
    provider_timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AttachmentDTO(BaseModel):
    metadata: AttachmentMetadataDTO
    blob_available: bool


class AttachmentBlobDTO(BaseModel):
    attachment_id: uuid.UUID
    size_bytes: int
    mime_type: str
    content_disposition: str
    range_start: Optional[int] = None
    range_end: Optional[int] = None
    total_size: Optional[int] = None
    is_partial: bool = False


class OutboundAttachmentDTO(BaseModel):
    type: AttachmentType
    provider_url: Optional[str] = None
    provider_media_id: Optional[str] = None
    caption: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimediaMessageDTO(BaseModel):
    message_id: uuid.UUID
    attachments: list[AttachmentDTO]


class AttachmentDownloadStatusDTO(BaseModel):
    attachment_id: uuid.UUID
    status: AttachmentDownloadStatus
    storage_backend: StorageBackend
    storage_key: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    mime_type: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
