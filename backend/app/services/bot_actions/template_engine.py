from __future__ import annotations

import re
from typing import Any

from app.services.bot_actions.errors import ActionExecutionError
from app.utils.bot_actions_constants import INVALID_PLACEHOLDER_PATTERN, PLACEHOLDER_PATTERN

_PLACEHOLDER_RE = re.compile(PLACEHOLDER_PATTERN)
_INVALID_PLACEHOLDER_RE = re.compile(INVALID_PLACEHOLDER_PATTERN)


def extract_placeholders(value: str) -> list[str]:
    invalid = _INVALID_PLACEHOLDER_RE.findall(value)
    bad_tokens = [f"{{{{{token}}}}}" for token in invalid if not re.fullmatch(r"[a-z][a-z0-9_]*", token.strip())]
    if bad_tokens:
        raise ActionExecutionError(
            code="invalid_placeholder",
            message=f"Invalid placeholders found: {', '.join(sorted(set(bad_tokens)))}",
        )
    return _PLACEHOLDER_RE.findall(value)


def render_template_value(value: Any, variables: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    placeholders = extract_placeholders(value)
    missing = sorted({name for name in placeholders if name not in variables})
    if missing:
        raise ActionExecutionError(
            code="missing_placeholder_variable",
            message=f"Missing placeholder variables: {', '.join(missing)}",
        )

    if placeholders and _PLACEHOLDER_RE.fullmatch(value):
        variable_name = placeholders[0]
        return variables[variable_name]

    rendered = value
    for name in placeholders:
        rendered = rendered.replace(f"{{{{{name}}}}}", str(variables[name]))
    return rendered


def render_template_object(value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k: render_template_object(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [render_template_object(item, variables) for item in value]
    return render_template_value(value, variables)

