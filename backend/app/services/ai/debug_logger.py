from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_SENSITIVE_KEYS = (
    "authorization",
    "token",
    "api_key",
    "apikey",
    "secret",
    "password",
    "pass",
    "jwt",
)


def is_ai_debug_enabled() -> bool:
    raw = os.getenv("AI_DEBUG_LOGS")
    if raw is None:
        return bool(settings.AI_DEBUG_LOGS or settings.DEBUG)
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def make_debug_id() -> str:
    return uuid.uuid4().hex[:8]


def mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, inner in value.items():
            key_lower = str(key).lower()
            if any(token in key_lower for token in _SENSITIVE_KEYS):
                masked[key] = "***"
            else:
                masked[key] = mask_sensitive(inner)
        return masked
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    return value


def to_pretty_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(mask_sensitive(value), ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(value)


def split_prompt_sections(prompt: str) -> dict[str, str]:
    if not prompt or not prompt.strip():
        return {"FULL_PROMPT": ""}

    markers = [
        "[IDENTIDAD]",
        "[TONO]",
        "[REGLAS]",
        "[OBJETIVOS]",
        "[CONTEXTO]",
        "[CONVERSACION]",
        "[MENSAJE ACTUAL]",
        "[MENSAJE TARGET]",
        "[CONTEXTO GRUPAL]",
    ]

    sections: dict[str, str] = {}
    current_name = "FULL_PROMPT"
    current_lines: list[str] = []

    for line in prompt.splitlines():
        candidate = line.strip()
        if candidate in markers:
            if current_lines:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = candidate.strip("[]")
            current_lines = [line]
            continue
        current_lines.append(line)

    if current_lines:
        sections[current_name] = "\n".join(current_lines).strip()

    return {k: v for k, v in sections.items() if v}


def log_block(*, debug_id: str, title: str, value: Any) -> None:
    logger.info("[AI-DEBUG][%s] ----- %s -----\n%s", debug_id, title, to_pretty_text(value))


def log_header(*, debug_id: str, metadata: dict[str, Any]) -> None:
    logger.info("[AI-DEBUG][%s] ========== AI REQUEST ==========", debug_id)
    log_block(debug_id=debug_id, title="META", value=metadata)


def log_footer(*, debug_id: str) -> None:
    logger.info("[AI-DEBUG][%s] =================================", debug_id)

