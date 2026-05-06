from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.internal.bot_actions.enums import (
    ActionAuthType,
    ActionResponseType,
    ActionVariableType,
    ApiKeyLocation,
)
from app.utils.bot_actions_helpers import validate_variable_name


class ActionVariableSchema(BaseModel):
    name: str
    type: ActionVariableType
    required: bool
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_variable_name(value)


class NoAuthConfig(BaseModel):
    type: Literal[ActionAuthType.NONE] = ActionAuthType.NONE


class BearerAuthConfig(BaseModel):
    type: Literal[ActionAuthType.BEARER] = ActionAuthType.BEARER
    token: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("token is required for bearer auth.")
        return value


class ApiKeyAuthConfig(BaseModel):
    type: Literal[ActionAuthType.API_KEY] = ActionAuthType.API_KEY
    key: str
    value: str
    location: ApiKeyLocation

    @field_validator("key", "value")
    @classmethod
    def validate_key_value(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("api key fields cannot be empty.")
        return value


class BasicAuthConfig(BaseModel):
    type: Literal[ActionAuthType.BASIC] = ActionAuthType.BASIC
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def validate_credentials(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("username and password are required for basic auth.")
        return value


class CustomAuthConfig(BaseModel):
    type: Literal[ActionAuthType.CUSTOM] = ActionAuthType.CUSTOM
    headers: dict[str, str]

    @field_validator("headers")
    @classmethod
    def validate_headers(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("headers are required for custom auth.")
        invalid_keys = [k for k in value.keys() if not isinstance(k, str) or not k.strip()]
        if invalid_keys:
            raise ValueError("custom auth headers must have non-empty string keys.")
        return value


ActionAuthConfig = Annotated[
    NoAuthConfig | BearerAuthConfig | ApiKeyAuthConfig | BasicAuthConfig | CustomAuthConfig,
    Field(discriminator="type"),
]


class ActionResponseConfig(BaseModel):
    response_type: ActionResponseType
    success_path: str | None = None
    error_path: str | None = None

