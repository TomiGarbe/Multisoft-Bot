from datetime import datetime
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.internal.message_enums import (
    AttachmentDownloadStatus,
    AttachmentType,
    MessageType,
    StorageBackend,
)


class AttachmentMetadata(BaseModel):
    storage_backend: StorageBackend = StorageBackend.NONE
    download_status: AttachmentDownloadStatus = AttachmentDownloadStatus.NOT_REQUESTED
    provider: Optional[str] = None
    checksum_sha256: Optional[str] = None
    source: Optional[str] = None


class NormalizedAttachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: AttachmentType
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    extension: Optional[str] = None
    size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    provider_media_id: Optional[str] = None
    provider_url: Optional[str] = None
    base64_data: Optional[str] = None
    caption: Optional[str] = None
    metadata: AttachmentMetadata = Field(default_factory=AttachmentMetadata)


class NormalizedMessage(BaseModel):
    channel_id: str
    external_message_id: str

    conversation_id: Optional[str] = None

    sender_external_id: Optional[str] = None
    sender_name: Optional[str] = None

    content: Optional[str] = None

    message_type: MessageType = MessageType.TEXT

    is_group: bool
    group_id: Optional[str] = None
    replied_to_message_id: Optional[str] = None

    is_status: bool
    is_bot: bool = False

    has_media: bool = False
    attachments: list[NormalizedAttachment] = Field(default_factory=list)

    timestamp: Optional[datetime] = None

    raw_payload: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def _sync_legacy_fields(self) -> "NormalizedMessage":
        self.has_media = bool(self.attachments)

        if self.attachments and self.message_type == MessageType.TEXT:
            self.message_type = MessageType.MEDIA

        return self
