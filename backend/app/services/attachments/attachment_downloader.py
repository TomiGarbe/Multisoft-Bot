from __future__ import annotations

import base64
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.interfaces.media import MediaResolver
from app.providers.media_resolvers.factory import get_media_resolver
from app.schemas.internal.message_enums import AttachmentDownloadStatus, AttachmentType, StorageBackend
from app.services.attachment_service import AttachmentService
from app.services.attachments.media_processing_orchestrator import MediaProcessingOrchestrator
from app.services.retry_policy import RetryPolicy, run_with_retries

logger = logging.getLogger(__name__)


class AttachmentDownloadError(Exception):
    pass


@dataclass(frozen=True)
class ResolvedMedia:
    binary_data: bytes
    mime_type: Optional[str]
    source: str


class AttachmentDownloader:
    def __init__(
        self,
        db: Session,
        *,
        resolver_factory: Callable[[str | None], MediaResolver] = get_media_resolver,
    ) -> None:
        self.db = db
        self.attachment_service = AttachmentService(db)
        self._resolver_factory = resolver_factory
        self._timeout = httpx.Timeout(settings.ATTACHMENT_DOWNLOAD_TIMEOUT_SECONDS)
        self._download_policy = RetryPolicy(
            max_attempts=max(1, settings.ATTACHMENT_DOWNLOAD_MAX_RETRIES + 1),
            initial_backoff_seconds=settings.ATTACHMENT_DOWNLOAD_INITIAL_BACKOFF_SECONDS,
            max_backoff_seconds=settings.ATTACHMENT_DOWNLOAD_MAX_BACKOFF_SECONDS,
        )
        self._resolve_policy = RetryPolicy(
            max_attempts=max(1, settings.ATTACHMENT_DOWNLOAD_MAX_RETRIES + 1),
            initial_backoff_seconds=settings.ATTACHMENT_DOWNLOAD_INITIAL_BACKOFF_SECONDS,
            max_backoff_seconds=settings.ATTACHMENT_DOWNLOAD_MAX_BACKOFF_SECONDS,
        )
        self._allowed_mimes = set(settings.attachment_allowed_mime_types_list)

    def process_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        attachment = self.attachment_service.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            logger.warning("attachment_download_missing attachment_id=%s tenant_id=%s", attachment_id, tenant_id)
            return

        started_at = time.perf_counter()
        metadata = dict(attachment.metadata_json or {})
        metadata["download_started_at"] = int(time.time())
        metadata["download_started_at_iso"] = datetime.now(timezone.utc).isoformat()
        metadata["download_error"] = None
        metadata["download_attempts"] = int(metadata.get("download_attempts") or 0) + 1
        self.attachment_service.update_download_state(
            attachment=attachment,
            status=AttachmentDownloadStatus.DOWNLOADING,
            metadata_json=metadata,
        )
        self.db.commit()

        logger.info(
            "attachment_download_start attachment_id=%s tenant_id=%s provider_media_id=%s mime=%s",
            attachment.id,
            attachment.tenant_id,
            attachment.provider_media_id,
            attachment.mime_type,
        )

        try:
            resolved = self._resolve_media(attachment, metadata)
            self._validate_payload(attachment, resolved.binary_data)
            mime = self._resolve_mime(attachment.mime_type, resolved.mime_type, resolved.binary_data)
            self._validate_mime(mime)
            self._validate_size(attachment, len(resolved.binary_data))

            checksum = hashlib.sha256(resolved.binary_data).hexdigest()
            storage_key = self.attachment_service.save_attachment_blob(
                attachment_id=attachment.id,
                tenant_id=attachment.tenant_id,
                binary_data=resolved.binary_data,
            )

            metadata["download_source"] = resolved.source
            metadata["download_completed_at"] = int(time.time())
            metadata["download_completed_at_iso"] = datetime.now(timezone.utc).isoformat()
            metadata["resolved_mime"] = mime
            self.attachment_service.update_download_state(
                attachment=attachment,
                status=AttachmentDownloadStatus.COMPLETED,
                metadata_json=metadata,
                mime_type=mime,
                size_bytes=len(resolved.binary_data),
                checksum_sha256=checksum,
                storage_backend=StorageBackend.DB,
            )
            attachment.storage_key = storage_key
            self.db.commit()
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            logger.info(
                "attachment_download_done attachment_id=%s provider_media_id=%s mime=%s size=%s duration_ms=%s",
                attachment.id,
                attachment.provider_media_id,
                mime,
                len(resolved.binary_data),
                elapsed_ms,
            )
            MediaProcessingOrchestrator(self.db).orchestrate_for_attachment(
                attachment_id=attachment.id,
                tenant_id=attachment.tenant_id,
            )
        except Exception as exc:
            self.db.rollback()
            attachment = self.attachment_service.get_by_id_and_tenant(attachment_id, tenant_id)
            if attachment is None:
                return
            metadata = dict(attachment.metadata_json or {})
            metadata["download_error"] = str(exc)
            metadata["download_failed_at"] = int(time.time())
            metadata["download_failed_at_iso"] = datetime.now(timezone.utc).isoformat()
            self.attachment_service.update_download_state(
                attachment=attachment,
                status=AttachmentDownloadStatus.FAILED,
                metadata_json=metadata,
            )
            self.db.commit()
            logger.warning(
                "attachment_download_failed attachment_id=%s provider_media_id=%s error=%s",
                attachment.id,
                attachment.provider_media_id,
                exc,
            )

    def _resolve_media(self, attachment: Any, metadata: dict[str, Any]) -> ResolvedMedia:
        if attachment.provider_url:
            return self._download_from_url(str(attachment.provider_url))

        base64_data = metadata.get("base64_data")
        if base64_data:
            return self._decode_base64(str(base64_data))

        provider_media_id = str(attachment.provider_media_id or "").strip()
        if provider_media_id:
            provider_name = str(metadata.get("provider") or "").strip().lower()
            resolver = self._resolver_factory(provider_name)
            logger.info(
                "attachment_media_resolver_selected attachment_id=%s provider=%s resolver=%s provider_media_id=%s",
                attachment.id,
                provider_name or "unknown",
                resolver.__class__.__name__,
                provider_media_id,
            )

            def _resolve_reference() -> ResolvedMedia:
                resolution = resolver.resolve(provider_media_id=provider_media_id, metadata=metadata)
                if resolution is None or not resolution.download_url:
                    raise AttachmentDownloadError("provider_media_id_without_resolver")
                resolved_media = self._download_from_url(resolution.download_url)
                metadata.update(resolution.metadata)
                metadata["resolved_by"] = resolver.__class__.__name__
                return ResolvedMedia(
                    binary_data=resolved_media.binary_data,
                    mime_type=resolved_media.mime_type,
                    source=resolution.source,
                )

            return run_with_retries(
                operation_name="attachment_media_resolution",
                operation=_resolve_reference,
                policy=self._resolve_policy,
                is_retryable=self._is_retryable_resolution_error,
                context={
                    "attachment_id": str(attachment.id),
                    "provider": provider_name or "unknown",
                    "provider_media_id": provider_media_id,
                },
            )

        raise AttachmentDownloadError("no_media_source")

    def _download_from_url(self, url: str) -> ResolvedMedia:
        if not self._is_valid_url(url):
            raise AttachmentDownloadError("invalid_url")

        def _fetch() -> ResolvedMedia:
            try:
                with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    data = response.content
                    mime = response.headers.get("content-type")
                    return ResolvedMedia(binary_data=data, mime_type=mime, source="provider_url")
            except Exception as exc:
                raise AttachmentDownloadError(f"download_failed: {exc}") from exc

        return run_with_retries(
            operation_name="attachment_download_http",
            operation=_fetch,
            policy=self._download_policy,
            is_retryable=self._is_retryable_download_error,
            context={"url": url},
        )

    def _decode_base64(self, data: str) -> ResolvedMedia:
        payload = data
        header_mime = None
        if data.startswith("data:") and "," in data:
            prefix, payload = data.split(",", 1)
            maybe_mime = prefix.split(";")[0].replace("data:", "").strip().lower()
            if maybe_mime:
                header_mime = maybe_mime
        try:
            decoded = base64.b64decode(payload, validate=True)
        except Exception as exc:
            raise AttachmentDownloadError(f"invalid_base64: {exc}") from exc
        return ResolvedMedia(binary_data=decoded, mime_type=header_mime, source="base64_data")

    def _resolve_mime(self, current_mime: Optional[str], downloaded_mime: Optional[str], binary_data: bytes) -> str:
        candidate = (downloaded_mime or current_mime or "").split(";")[0].strip().lower()
        if candidate:
            return candidate

        sniff = binary_data[:16]
        if sniff.startswith(b"\x89PNG"):
            return "image/png"
        if sniff.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if sniff.startswith(b"GIF8"):
            return "image/gif"
        if sniff.startswith(b"%PDF"):
            return "application/pdf"
        return "application/octet-stream"

    def _validate_payload(self, attachment: Any, data: bytes) -> None:
        if not data:
            raise AttachmentDownloadError("empty_payload")
        if attachment.size_bytes and len(data) < int(attachment.size_bytes * 0.3):
            raise AttachmentDownloadError("payload_size_inconsistent")

    def _validate_mime(self, mime_type: str) -> None:
        if mime_type not in self._allowed_mimes:
            raise AttachmentDownloadError(f"mime_not_allowed:{mime_type}")

    def _validate_size(self, attachment: Any, size: int) -> None:
        atype = attachment.attachment_type
        limits = {
            AttachmentType.IMAGE: settings.ATTACHMENT_MAX_IMAGE_BYTES,
            AttachmentType.AUDIO: settings.ATTACHMENT_MAX_AUDIO_BYTES,
            AttachmentType.VIDEO: settings.ATTACHMENT_MAX_VIDEO_BYTES,
            AttachmentType.DOCUMENT: settings.ATTACHMENT_MAX_DOCUMENT_BYTES,
            AttachmentType.FILE: settings.ATTACHMENT_MAX_DOCUMENT_BYTES,
        }
        max_size = limits.get(atype, settings.ATTACHMENT_MAX_DOCUMENT_BYTES)
        if size > max_size:
            raise AttachmentDownloadError(f"size_exceeded:{size}>{max_size}")

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        except Exception:
            return False

    def _is_retryable_resolution_error(self, exc: Exception) -> bool:
        return self._is_retryable_download_error(exc)

    def _is_retryable_download_error(self, exc: Exception) -> bool:
        error_text = str(exc).lower()
        non_retryable_markers = (
            "invalid_url",
            "invalid_base64",
            "mime_not_allowed",
            "size_exceeded",
            "empty_payload",
            "payload_size_inconsistent",
            "provider_media_id_without_resolver",
            "no_media_source",
        )
        if any(marker in error_text for marker in non_retryable_markers):
            return False
        root = exc.__cause__ if exc.__cause__ is not None else exc
        if isinstance(root, httpx.TimeoutException):
            return True
        if isinstance(root, httpx.NetworkError):
            return True
        if isinstance(root, httpx.HTTPStatusError):
            return root.response.status_code >= 500 or root.response.status_code == 429
        return "download_failed" in error_text
