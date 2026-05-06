from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field
from dataclasses import dataclass


class ApiKeyCreate(BaseModel):
    tenant_id: uuid.UUID
    channel_id: Optional[uuid.UUID] = None
    name: str = Field(..., min_length=1, max_length=150)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    channel_id: Optional[uuid.UUID] = None
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyResponse):
    api_key: str


@dataclass
class MachineIdentity:
    api_key_id: uuid.UUID
    tenant_id: uuid.UUID
    channel_id: Optional[uuid.UUID]
    name: str


@dataclass
class WebhookAuthContext:
    api_key: MachineIdentity
    tenant_id: uuid.UUID
    channel_id: uuid.UUID
    provider_signature: Optional[str] = None
