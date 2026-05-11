from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.timezones import DEFAULT_TENANT_TIMEZONE

_tenant_timezone_ctx: ContextVar[str] = ContextVar("tenant_timezone", default=DEFAULT_TENANT_TIMEZONE)


def set_current_tenant_timezone(timezone_name: str | None) -> None:
    if not timezone_name:
        _tenant_timezone_ctx.set(DEFAULT_TENANT_TIMEZONE)
        return
    _tenant_timezone_ctx.set(timezone_name)


def reset_current_tenant_timezone() -> None:
    _tenant_timezone_ctx.set(DEFAULT_TENANT_TIMEZONE)


def get_current_tenant_timezone() -> str:
    return _tenant_timezone_ctx.get()


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_tenant_timezone(value: datetime, timezone_name: str | None = None) -> datetime:
    aware_utc = ensure_aware_utc(value)
    target_name = timezone_name or get_current_tenant_timezone()
    try:
        target_tz = ZoneInfo(target_name)
    except ZoneInfoNotFoundError:
        target_tz = ZoneInfo(DEFAULT_TENANT_TIMEZONE)
    return aware_utc.astimezone(target_tz)


def encode_datetime_for_response(value: datetime) -> str:
    return to_tenant_timezone(value).isoformat()
