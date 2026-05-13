from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.internal.message_enums import AttachmentDownloadStatus, AttachmentType, StorageBackend


class AttachmentCreate(BaseModel):
    message_id: uuid.UUID
    tenant_id: uuid.UUID
    attachment_type: AttachmentType
    storage_backend: StorageBackend = StorageBackend.NONE
    storage_key: Optional[str] = None
    provider_media_id: Optional[str] = None
    provider_url: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    extension: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    download_status: AttachmentDownloadStatus = AttachmentDownloadStatus.NOT_REQUESTED
    metadata_json: Optional[dict[str, Any]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    caption: Optional[str] = None
    provider_timestamp: Optional[datetime] = None
    file_data: Optional[bytes] = None


class AttachmentBlobCreate(BaseModel):
    attachment_id: uuid.UUID
    binary_data: bytes
