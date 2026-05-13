from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.internal.message_enums import AttachmentType


class OutboundAttachment(BaseModel):
    type: AttachmentType = AttachmentType.FILE
    provider_url: Optional[str] = None
    provider_media_id: Optional[str] = None
    caption: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _normalize_attachment_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if not normalized.get("provider_url"):
            normalized["provider_url"] = normalized.get("url")
        if not normalized.get("provider_media_id"):
            normalized["provider_media_id"] = normalized.get("media_id")
        return normalized


class OutboundMediaMessage(BaseModel):
    attachments: list[OutboundAttachment] = Field(default_factory=list)
    fallback_text: Optional[str] = None

