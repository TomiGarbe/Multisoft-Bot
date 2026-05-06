from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.schemas.internal.bot_actions.contracts import ActionAuthConfig, ActionResponseConfig, ActionVariableSchema
from app.utils.bot_actions_helpers import (
    normalize_tool_name,
    validate_external_url,
    validate_placeholders,
    validate_tool_name,
    validate_variable_name,
)

_AUTH_CONFIG_ADAPTER = TypeAdapter(ActionAuthConfig)
_VARIABLE_SCHEMA_ADAPTER = TypeAdapter(list[ActionVariableSchema])


def validate_tool_name_or_raise(value: str) -> str:
    return validate_tool_name(value)


def normalize_tool_name_or_raise(value: str) -> str:
    normalized = normalize_tool_name(value)
    return validate_tool_name(normalized)


def validate_variable_name_or_raise(value: str) -> str:
    return validate_variable_name(value)


def validate_external_url_or_raise(value: str) -> str:
    return validate_external_url(value)


def validate_placeholders_or_raise(value: str, allowed_variables: list[str] | None = None) -> list[str]:
    return validate_placeholders(value, allowed_variables=allowed_variables)


def validate_auth_config_or_raise(data: Any) -> Any:
    try:
        return _AUTH_CONFIG_ADAPTER.validate_python(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid auth config: {exc}") from exc


def validate_response_config_or_raise(data: Any) -> ActionResponseConfig:
    try:
        return ActionResponseConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid response config: {exc}") from exc


def validate_variable_schemas_or_raise(data: Any) -> list[ActionVariableSchema]:
    try:
        return _VARIABLE_SCHEMA_ADAPTER.validate_python(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid variable schema list: {exc}") from exc


def validate_placeholders_in_action_parts_or_raise(
    *,
    url: str,
    headers: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    body: str | None = None,
    allowed_variables: list[str] | None = None,
) -> dict[str, list[str]]:
    collected: dict[str, list[str]] = {"url": validate_placeholders_or_raise(url, allowed_variables)}

    if headers:
        header_placeholders: list[str] = []
        for value in headers.values():
            header_placeholders.extend(validate_placeholders_or_raise(value, allowed_variables))
        collected["headers"] = header_placeholders

    if query_params:
        query_placeholders: list[str] = []
        for value in query_params.values():
            query_placeholders.extend(validate_placeholders_or_raise(value, allowed_variables))
        collected["query_params"] = query_placeholders

    if body is not None:
        collected["body"] = validate_placeholders_or_raise(body, allowed_variables)

    return collected
