from __future__ import annotations

from io import BytesIO
from typing import Any

import httpx
from pypdf import PdfReader

from app.core.config import settings
from app.interfaces.media import MediaProcessingError, MediaProcessingProvider


class LocalMediaProcessingProvider(MediaProcessingProvider):
    def transcribe_audio(self, *, payload: bytes, mime_type: str | None, filename: str | None) -> dict[str, Any]:
        if not settings.MEDIA_STT_ENABLED:
            raise MediaProcessingError("stt_disabled", "speech-to-text disabled", retryable=False)
        if not settings.MEDIA_STT_API_KEY:
            raise MediaProcessingError("stt_missing_api_key", "stt api key missing", retryable=False)

        audio_name = filename or "audio_input"
        files = {"file": (audio_name, payload, mime_type or "application/octet-stream")}
        data = {"model": settings.MEDIA_STT_MODEL}

        try:
            response = httpx.post(
                f"{settings.MEDIA_STT_BASE_URL.rstrip('/')}/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.MEDIA_STT_API_KEY}"},
                files=files,
                data=data,
                timeout=settings.MEDIA_STT_TIMEOUT_SECONDS,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise MediaProcessingError("stt_transport_error", str(exc), retryable=True) from exc

        if response.status_code in {429, 500, 502, 503, 504}:
            raise MediaProcessingError("stt_upstream_retryable", response.text[:400], retryable=True)
        if response.status_code >= 400:
            raise MediaProcessingError("stt_upstream_error", response.text[:400], retryable=False)

        body = response.json()
        if not isinstance(body, dict):
            raise MediaProcessingError("stt_invalid_response", "invalid stt response format", retryable=False)

        return {
            "text": body.get("text"),
            "language": body.get("language"),
            "segments": body.get("segments") if isinstance(body.get("segments"), list) else [],
            "provider_response": body,
        }

    def extract_document_text(self, *, payload: bytes, mime_type: str | None, filename: str | None) -> dict[str, Any]:
        normalized_mime = (mime_type or "").split(";")[0].strip().lower()
        if normalized_mime == "application/pdf" or (filename or "").lower().endswith(".pdf"):
            return self._extract_pdf(payload)

        try:
            text = payload.decode("utf-8")
            return {
                "text": text,
                "pages": [{"page": 1, "length": len(text)}],
                "mime_type": normalized_mime or "text/plain",
            }
        except UnicodeDecodeError as exc:
            raise MediaProcessingError("unsupported_document_encoding", str(exc), retryable=False) from exc

    def _extract_pdf(self, payload: bytes) -> dict[str, Any]:
        try:
            reader = PdfReader(BytesIO(payload))
            page_items: list[dict[str, Any]] = []
            all_text: list[str] = []
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                all_text.append(page_text)
                page_items.append({"page": index, "length": len(page_text)})
            return {
                "text": "\n\n".join(all_text).strip() or None,
                "pages": page_items,
                "pdf_page_count": len(reader.pages),
            }
        except Exception as exc:
            raise MediaProcessingError("pdf_extraction_failed", str(exc), retryable=False) from exc
