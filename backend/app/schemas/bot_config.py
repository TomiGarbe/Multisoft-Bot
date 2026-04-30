"""
Schemas for Bot Configuration API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class BotConfigContent(BaseModel):
    """
    Bot configuration content structure.
    
    Expected structure for PromptBuilder:
    """
    identity: str = Field(..., description="Bot description/personality")
    tone: str = Field(..., description="Communication style")
    behavior: list[str] = Field(..., description="List of behavioral rules")
    conversation: Dict[str, Any] = Field(default_factory=dict, description="Conversation settings")
    objectives: list[str] = Field(default_factory=list, description="Bot goals/objectives")
    data_collection: Dict[str, Any] = Field(default_factory=dict, description="Data handling policies")
    actions: list[Any] = Field(default_factory=list, description="Supported actions")
    user_type_config: Dict[str, Any] = Field(default_factory=dict, description="User type specific config")


class ChannelBotConfigCreate(BaseModel):
    """Create a new channel bot configuration"""
    channel_id: uuid.UUID
    config_jsonb: Dict[str, Any] = Field(..., description="Complete bot configuration")
    is_active: bool = Field(default=True)


class ChannelBotConfigUpdate(BaseModel):
    """Update existing channel bot configuration"""
    config_jsonb: Optional[Dict[str, Any]] = Field(None, description="Complete bot configuration")
    settings_jsonb: Optional[Dict[str, Any]] = Field(None, description="Channel settings configuration")
    user_types_jsonb: Optional[Dict[str, Any]] = Field(None, description="User types configuration")
    is_active: Optional[bool] = None


class ChannelBotConfigResponse(BaseModel):
    """Response model for channel bot configuration"""
    id: uuid.UUID
    tenant_id: uuid.UUID
    channel_id: uuid.UUID
    is_active: bool
    version: int
    config_jsonb: Dict[str, Any]
    settings_jsonb: Optional[Dict[str, Any]] = None
    user_types_jsonb: Optional[Dict[str, Any]] = None
    created_by_user_id: Optional[uuid.UUID] = None
    updated_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelBotConfigListResponse(BaseModel):
    """List response model for channel bot configurations"""
    id: uuid.UUID
    channel_id: uuid.UUID
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
