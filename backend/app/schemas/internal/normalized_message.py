from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NormalizedMessage(BaseModel):
    channel_id: str
    external_message_id: str

    conversation_id: Optional[str] = None

    sender_external_id: Optional[str] = None
    sender_name: Optional[str] = None

    content: Optional[str] = None

    message_type: str  # "text", "image", etc.

    is_group: bool
    group_id: Optional[str] = None

    is_status: bool
    is_bot: bool = False

    has_media: bool
    media_url: Optional[str] = None

    timestamp: Optional[datetime] = None

    raw_payload: Optional[dict] = None
