from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChannelConfigContent(BaseModel):
    identity: dict[str, Any] = Field(default_factory=dict, description="Bot identity/personality section")
    tone: dict[str, Any] = Field(default_factory=dict, description="Communication style section")
    rules: dict[str, Any] = Field(default_factory=dict, description="Behavioral rules section")
    behavior: dict[str, Any] = Field(default_factory=dict, description="Runtime behavior section")
    objectives: list[Any] = Field(default_factory=list, description="Bot goals/objectives")
    data_collection: list[Any] = Field(default_factory=list, description="Data collection rules")
    actions: list[Any] = Field(default_factory=list, description="Supported actions")
    user_type_config: dict[str, Any] = Field(default_factory=dict, description="Per-user-type config")


class ChannelConfigCreate(BaseModel):
    channel_id: uuid.UUID
    config_jsonb: dict[str, Any]
    is_active: bool = True


class ChannelConfigUpdate(BaseModel):
    config_jsonb: Optional[dict[str, Any]] = Field(None, description="Complete bot configuration")
    settings_jsonb: Optional[dict[str, Any]] = Field(None, description="Channel settings configuration")
    user_types_jsonb: Optional[dict[str, Any]] = Field(None, description="User types configuration")
    channel_ids: Optional[list[uuid.UUID]] = Field(
        None,
        description="Optional list of channels to apply the same config payload in bulk",
    )
    is_active: Optional[bool] = None


class ChannelConfigResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    channel_id: uuid.UUID
    is_active: bool
    version: int
    config_jsonb: dict[str, Any]
    settings_jsonb: Optional[dict[str, Any]] = None
    user_types_jsonb: Optional[dict[str, Any]] = None
    created_by_user_id: Optional[uuid.UUID] = None
    updated_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelConfigListResponse(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelConfigValidationStatusResponse(BaseModel):
    is_valid: bool
    missing_fields: list[str]
