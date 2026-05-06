from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.bot_action import HttpMethod
from app.schemas.internal.bot_actions.contracts import ActionAuthConfig, ActionResponseConfig, ActionVariableSchema


class BotActionCreate(BaseModel):
    name: str
    description: str | None = None
    enabled: bool = True
    trigger_prompt: str | None = None
    ai_instructions: str | None = None
    method: HttpMethod
    url: str
    headers_jsonb: dict[str, str] | None = None
    query_params_jsonb: dict[str, str] | None = None
    body_jsonb: dict[str, Any] | list[Any] | str | None = None
    variables_jsonb: list[ActionVariableSchema] = Field(default_factory=list)
    auth_jsonb: ActionAuthConfig
    response_config_jsonb: ActionResponseConfig
    timeout_ms: int | None = None
    retry_count: int | None = None


class BotActionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    trigger_prompt: str | None = None
    ai_instructions: str | None = None
    method: HttpMethod | None = None
    url: str | None = None
    headers_jsonb: dict[str, str] | None = None
    query_params_jsonb: dict[str, str] | None = None
    body_jsonb: dict[str, Any] | list[Any] | str | None = None
    variables_jsonb: list[ActionVariableSchema] | None = None
    auth_jsonb: ActionAuthConfig | None = None
    response_config_jsonb: ActionResponseConfig | None = None
    timeout_ms: int | None = None
    retry_count: int | None = None


class BotActionEnabledUpdate(BaseModel):
    enabled: bool


class ChannelActionReplaceRequest(BaseModel):
    action_ids: list[uuid.UUID] = Field(default_factory=list)


class BotActionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None = None
    enabled: bool
    trigger_prompt: str | None = None
    ai_instructions: str | None = None
    method: HttpMethod
    url: str
    headers_jsonb: dict[str, str] | None = None
    query_params_jsonb: dict[str, str] | None = None
    body_jsonb: dict[str, Any] | list[Any] | str | None = None
    variables_jsonb: list[ActionVariableSchema]
    auth_jsonb: dict[str, Any]
    response_config_jsonb: ActionResponseConfig
    timeout_ms: int | None = None
    retry_count: int | None = None
    created_by_user_id: uuid.UUID | None = None
    updated_by_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotActionListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    enabled: bool
    method: HttpMethod
    url: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotActionTestRequest(BaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)


class ActionExecutionResultSchema(BaseModel):
    success: bool
    status_code: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    data: Any = None
    text: str | None = None
    duration_ms: int
    error: str | None = None


class BotActionTestResponse(BaseModel):
    request: dict[str, Any]
    response: ActionExecutionResultSchema
    timing: dict[str, int]
    success: bool
    error: str | None = None
