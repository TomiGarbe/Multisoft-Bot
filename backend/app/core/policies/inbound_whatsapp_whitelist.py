from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.core.utils import normalize_phone


def _parse_csv_as_set(raw: Optional[str]) -> set[str]:
    if not raw:
        return set()
    return {item.strip() for item in str(raw).split(",") if item and item.strip()}


def _allowed_numbers() -> set[str]:
    return {normalize_phone(value) for value in _parse_csv_as_set(settings.WHATSAPP_ALLOWED_NUMBERS) if normalize_phone(value)}


def _allowed_groups() -> set[str]:
    return _parse_csv_as_set(settings.WHATSAPP_ALLOWED_GROUPS)


def is_allowed_number(phone: str | None) -> bool:
    normalized = normalize_phone(phone)
    if not normalized:
        return False
    return normalized in _allowed_numbers()


def is_allowed_group(group_id: str | None) -> bool:
    if not group_id:
        return False
    return group_id.strip() in _allowed_groups()


def should_process_incoming_message(
    *,
    is_group: bool,
    sender_phone: str | None,
    group_id: str | None,
) -> bool:
    if is_group:
        return is_allowed_group(group_id)
    return is_allowed_number(sender_phone)
