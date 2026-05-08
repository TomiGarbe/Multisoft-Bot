from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


def to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def safe_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_epoch_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except ValueError:
            return None
    return None


def safe_timestamp(value: Any, default_now: bool = True) -> datetime | None:
    parsed = parse_epoch_timestamp(value)
    if parsed is not None:
        return parsed
    if isinstance(value, str):
        try:
            iso_value = value.replace("Z", "+00:00")
            parsed_iso = datetime.fromisoformat(iso_value)
            return parsed_iso if parsed_iso.tzinfo else parsed_iso.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc) if default_now else None


def normalize_phone(value: Any) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D+", "", str(value))
    return digits or None


def dict_get_any_case(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    if not isinstance(payload, dict):
        return default

    for key in keys:
        if key in payload:
            return payload[key]

    lowered_map = {str(k).lower(): v for k, v in payload.items()}
    for key in keys:
        lowered_key = str(key).lower()
        if lowered_key in lowered_map:
            return lowered_map[lowered_key]
    return default


def safe_json_loads(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return default
