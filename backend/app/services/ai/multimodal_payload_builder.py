from __future__ import annotations

import base64
import imghdr
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.internal.message_enums import AttachmentType, AttachmentDownloadStatus
from app.services.attachment_service import AttachmentService

logger = logging.getLogger(__name__)


class AIMultimodalPayloadBuilder:
    def __init__(self, db: Session) -> None:
        self._attachment_service = AttachmentService(db)

    def build_user_content(
        self,
        *,
        tenant_id: uuid.UUID,
        message_id: uuid.UUID | None,
        user_text: str,
        supports_vision: bool,
    ) -> tuple[str | list[dict[str, Any]], dict[str, int]]:
        text_value = (user_text or "").strip()
        if not supports_vision or not message_id:
            return text_value, {"images_included": 0, "images_skipped": 0, "included_image_bytes": 0}

        image_parts, stats = self._load_image_parts(tenant_id=tenant_id, message_id=message_id)
        if not image_parts:
            return text_value, stats

        content_parts: list[dict[str, Any]] = [{"type": "text", "text": text_value or "Analiza estas imagenes."}]
        content_parts.extend(image_parts)
        return content_parts, stats

    def _load_image_parts(self, *, tenant_id: uuid.UUID, message_id: uuid.UUID) -> tuple[list[dict[str, Any]], dict[str, int]]:
        attachments = self._attachment_service.list_by_message_id_and_tenant(message_id=message_id, tenant_id=tenant_id)
        image_attachments = [item for item in attachments if item.attachment_type == AttachmentType.IMAGE]
        if not image_attachments:
            return [], {"images_included": 0, "images_skipped": 0, "included_image_bytes": 0}

        max_images = max(1, settings.AI_VISION_MAX_IMAGES_PER_REQUEST)
        max_bytes = max(1, settings.AI_VISION_MAX_IMAGE_BYTES)
        allowed_mimes = set(settings.ai_vision_allowed_mime_types_list)
        parts: list[dict[str, Any]] = []
        stats = {"images_included": 0, "images_skipped": 0, "included_image_bytes": 0}
        seen_keys: set[str] = set()

        for attachment in image_attachments:
            dedup_key = str(getattr(attachment, "checksum_sha256", None) or attachment.id)
            if dedup_key in seen_keys:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=duplicate_attachment",
                    attachment.id,
                )
                stats["images_skipped"] += 1
                continue
            seen_keys.add(dedup_key)

            if len(parts) >= max_images:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=max_images_limit max_images=%s",
                    attachment.id,
                    max_images,
                )
                stats["images_skipped"] += 1
                break

            mime_type = str(attachment.mime_type or "").strip().lower()
            if mime_type not in allowed_mimes:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=invalid_mime mime=%s",
                    attachment.id,
                    mime_type or "unknown",
                )
                stats["images_skipped"] += 1
                continue

            status = getattr(attachment, "download_status", None)
            if status not in {AttachmentDownloadStatus.COMPLETED, AttachmentDownloadStatus.DOWNLOADED}:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=attachment_not_ready status=%s",
                    attachment.id,
                    getattr(status, "value", "unknown"),
                )
                stats["images_skipped"] += 1
                continue

            declared_size = int(attachment.size_bytes or 0)
            if declared_size > max_bytes:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=image_too_large declared_bytes=%s max_bytes=%s",
                    attachment.id,
                    declared_size,
                    max_bytes,
                )
                stats["images_skipped"] += 1
                continue

            blob = self._attachment_service.load_attachment_blob(
                attachment_id=attachment.id,
                tenant_id=tenant_id,
                storage_key=attachment.storage_key,
            )
            if blob is None or not blob.payload:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=blob_missing",
                    attachment.id,
                )
                stats["images_skipped"] += 1
                continue
            if blob.size_bytes > max_bytes:
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=image_too_large payload_bytes=%s max_bytes=%s",
                    attachment.id,
                    blob.size_bytes,
                    max_bytes,
                )
                stats["images_skipped"] += 1
                continue
            if not self._is_valid_image_blob(blob.payload):
                logger.warning(
                    "[AI][MULTIMODAL] image_skipped attachment_id=%s reason=corrupt_or_invalid_image",
                    attachment.id,
                )
                stats["images_skipped"] += 1
                continue

            encoded = base64.b64encode(blob.payload).decode("ascii")
            parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{encoded}",
                    },
                }
            )
            logger.info(
                "[AI][MULTIMODAL] image_included attachment_id=%s mime=%s bytes=%s",
                attachment.id,
                mime_type,
                blob.size_bytes,
            )
            stats["images_included"] += 1
            stats["included_image_bytes"] += int(blob.size_bytes)
        logger.info(
            "[AI][MULTIMODAL] image_selection_done message_id=%s included=%s skipped=%s included_bytes=%s",
            message_id,
            stats["images_included"],
            stats["images_skipped"],
            stats["included_image_bytes"],
        )
        return parts, stats

    @staticmethod
    def _is_valid_image_blob(payload: bytes) -> bool:
        if not payload:
            return False
        return imghdr.what(None, payload) is not None
