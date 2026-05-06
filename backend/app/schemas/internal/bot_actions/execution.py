from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActionExecutionResult(BaseModel):
    success: bool
    status_code: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    data: Any = None
    text: str | None = None
    duration_ms: int
    error: str | None = None
