from __future__ import annotations

from typing import Any


class ActionExecutionError(Exception):
    def __init__(
        self,
        code: str,
        message: str | None = None,
        *,
        exception_type: str | None = None,
        safe_details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message or code
        self.exception_type = exception_type
        self.safe_details = safe_details
        super().__init__(self.message)
