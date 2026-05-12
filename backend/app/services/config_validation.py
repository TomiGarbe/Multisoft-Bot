from typing import Any
from app.services.config_structure import section_fields


def get_config_validation_status(config: Any) -> dict[str, Any]:
    """
    Single source of truth for channel config readiness validation.

    Required fields (dot notation):
    - identity.role
    - tone.tone
    """
    missing_fields: list[str] = []

    identity = section_fields(config, "identity")
    tone = section_fields(config, "tone")

    if not _has_non_empty_string(identity, "bot_name"):
        missing_fields.append("identity.bot_name")

    if not _has_non_empty_string(tone, "tone"):
        missing_fields.append("tone.tone")

    return {
        "is_valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }


def _has_non_empty_string(source: Any, child_key: str) -> bool:
    if not isinstance(source, dict):
        return False
    value = source.get(child_key)
    return isinstance(value, str) and bool(value.strip())
