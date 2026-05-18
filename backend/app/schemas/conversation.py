import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    tenant_id: uuid.UUID
    chat_thread_id: uuid.UUID
    assigned_user_id: Optional[uuid.UUID] = None
    status: str = "open"
    mode: Literal["ai", "human"] = "ai"
    started_at: datetime
    last_message_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    chat_thread_id: uuid.UUID
    channel_id: uuid.UUID
    channel_name: Optional[str] = None
    channel_type: Optional[str] = None
    channel_provider: Optional[str] = None
    status: str
    mode: Literal["ai", "human"]
    channel_config_id: Optional[uuid.UUID] = None
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None


class ContactChatResponse(BaseModel):
    contact_id: uuid.UUID
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_current_type: Optional[str] = None
    active_conversation_id: Optional[uuid.UUID] = None
    active_conversation_status: Optional[str] = None
    active_conversation_mode: Optional[Literal["ai", "human"]] = None
    channel_id: Optional[uuid.UUID] = None
    channel_name: Optional[str] = None
    channel_type: Optional[str] = None
    channel_provider: Optional[str] = None
    channel_config_id: Optional[uuid.UUID] = None
    last_message_at: Optional[datetime] = None
    last_message: Optional[str] = None
    unread_count: int = 0
    conversations_count: int = 0
    messages_count: int = 0


class ConversationModeUpdateRequest(BaseModel):
    mode: Literal["ai", "human"]


class ConversationModeUpdateResponse(BaseModel):
    id: str
    mode: Literal["ai", "human"]


class ContactTypeUpdateRequest(BaseModel):
    type_key: str


class ContactTypeUpdateResponse(BaseModel):
    contact_id: str
    type_key: str
