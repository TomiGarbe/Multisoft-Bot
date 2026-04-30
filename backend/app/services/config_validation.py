from typing import Any


def get_config_validation_status(config: Any) -> dict[str, Any]:
    """
    Single source of truth for channel config readiness validation.

    Required fields (dot notation):
    - identity.role
    - tone.tone
    """
    missing_fields: list[str] = []

    if not _has_non_empty_string(config, "identity", "role"):
        missing_fields.append("identity.role")

    if not _has_non_empty_string(config, "tone", "tone"):
        missing_fields.append("tone.tone")

    return {
        "is_valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }


def _has_non_empty_string(source: Any, parent_key: str, child_key: str) -> bool:
    if not isinstance(source, dict):
        return False

    parent = source.get(parent_key)
    if not isinstance(parent, dict):
        return False

    value = parent.get(child_key)
    return isinstance(value, str) and bool(value.strip())
