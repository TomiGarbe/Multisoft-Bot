import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.internal.outbound_media import OutboundAttachment


class MessageSendRequest(BaseModel):
    conversation_id: uuid.UUID
    content: str = ""
    attachments: list[OutboundAttachment] = Field(default_factory=list)
    reply_to_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    direction: str
    sender_type: str
    message_type: str
    content: Optional[str] = None
    status: Optional[str] = None
    provider_message_id: Optional[str] = None
    replied_to_message_id: Optional[str] = None
    has_media: bool = False
    created_at: Optional[datetime] = None


class MessageSendResponse(BaseModel):
    status: str
