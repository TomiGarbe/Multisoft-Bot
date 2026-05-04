from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid


class ChannelCreate(BaseModel):
    tenant_id: uuid.UUID
    type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    external_id: str = Field(..., min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ChannelUpdate(BaseModel):
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    external_id: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ChannelResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    type: str
    name: str
    external_id: str
    config: Optional[Dict[str, Any]] = None
    is_active: bool

    model_config = {"from_attributes": True}


class ChannelConfigBundleResponse(BaseModel):
    config: dict
    settings: dict
    user_types: dict
