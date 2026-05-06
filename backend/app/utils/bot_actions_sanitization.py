from __future__ import annotations

from typing import Any

from app.utils.bot_actions_constants import SENSITIVE_FIELD_NAMES
from app.utils.bot_actions_constants import MAX_BODY_SIZE


_MASK = "********"


def _mask_secret(value: str) -> str:
    prefix = value.split(" ", 1)[0] if " " in value else None
    if prefix and prefix.lower() == "bearer":
        return f"Bearer {_MASK}"
    return _MASK


def is_sensitive_field(field_name: str) -> bool:
    return field_name.strip().lower() in SENSITIVE_FIELD_NAMES


def sanitize_mapping_secrets(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None

    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str) and is_sensitive_field(key):
            sanitized[key] = _mask_secret(value)
        else:
            sanitized[key] = value
    return sanitized


def sanitize_nested_secrets(data: Any) -> Any:
    if isinstance(data, dict):
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str) and is_sensitive_field(key):
                sanitized[key] = _mask_secret(value)
            else:
                sanitized[key] = sanitize_nested_secrets(value)
        return sanitized
    if isinstance(data, list):
        return [sanitize_nested_secrets(item) for item in data]
    return data


def truncate_payload(value: Any, *, max_bytes: int = MAX_BODY_SIZE) -> Any:
    if value is None:
        return None
    text = str(value)
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return f"{truncated}...[truncated]"


def sanitize_auth_config(auth_config: dict[str, Any] | None) -> dict[str, Any] | None:
    if auth_config is None:
        return None

    sanitized = dict(auth_config)
    auth_type = str(sanitized.get("type", "")).lower()

    if auth_type == "bearer" and isinstance(sanitized.get("token"), str):
        sanitized["token"] = _MASK
    elif auth_type == "api_key" and isinstance(sanitized.get("value"), str):
        sanitized["value"] = _MASK
    elif auth_type == "basic":
        if isinstance(sanitized.get("password"), str):
            sanitized["password"] = _MASK
    elif auth_type == "custom" and isinstance(sanitized.get("headers"), dict):
        sanitized["headers"] = sanitize_mapping_secrets(sanitized["headers"])

    return sanitized
