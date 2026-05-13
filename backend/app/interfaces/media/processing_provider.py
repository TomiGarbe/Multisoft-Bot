from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class MediaProcessingProvider(Protocol):
    def transcribe_audio(self, *, payload: bytes, mime_type: str | None, filename: str | None) -> dict[str, Any]: ...

    def extract_ocr(self, *, payload: bytes, mime_type: str | None, filename: str | None) -> dict[str, Any]: ...

    def extract_document_text(self, *, payload: bytes, mime_type: str | None, filename: str | None) -> dict[str, Any]: ...


@dataclass(frozen=True)
class MediaProcessingError(Exception):
    code: str
    message: str
    retryable: bool = False

    def __str__(self) -> str:
        return f"{self.code}:{self.message}"
