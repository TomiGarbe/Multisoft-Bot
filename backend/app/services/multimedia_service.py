from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.models.conversation import MessageAttachment
from app.schemas.attachment import (
    AttachmentBlobDTO,
    AttachmentDTO,
    AttachmentDownloadStatusDTO,
    AttachmentMetadataDTO,
    MultimediaMessageDTO,
)
from app.schemas.internal.message_enums import AttachmentType
from app.services.attachment_service import AttachmentService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AttachmentBlobPayload:
    content: bytes
    descriptor: AttachmentBlobDTO


class MultimediaService:
    def __init__(self, attachment_service: AttachmentService) -> None:
        self.attachment_service = attachment_service
        self.allowed_mimes = set(settings.attachment_allowed_mime_types_list)

    def get_attachment(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[AttachmentDTO]:
        attachment = self.attachment_service.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            return None
        return AttachmentDTO(
            metadata=self._metadata_dto(attachment),
            blob_available=self.attachment_service.attachment_blob_exists(
                attachment_id=attachment.id,
                tenant_id=tenant_id,
                storage_key=attachment.storage_key,
            ),
        )

    def list_attachments_for_message(
        self,
        *,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        offset: int = 0,
        limit: Optional[int] = None,
    ) -> MultimediaMessageDTO:
        items = self.attachment_service.list_by_message_id_and_tenant(
            message_id,
            tenant_id,
            offset=offset,
            limit=limit,
        )
        attachments = [
            AttachmentDTO(
                metadata=self._metadata_dto(item),
                blob_available=self.attachment_service.attachment_blob_exists(
                    attachment_id=item.id,
                    tenant_id=tenant_id,
                    storage_key=item.storage_key,
                ),
            )
            for item in items
        ]
        return MultimediaMessageDTO(message_id=message_id, attachments=attachments)

    def get_download_status(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Optional[AttachmentDownloadStatusDTO]:
        attachment = self.attachment_service.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            return None
        return AttachmentDownloadStatusDTO(
            attachment_id=attachment.id,
            status=attachment.download_status,
            storage_backend=attachment.storage_backend,
            storage_key=attachment.storage_key,
            size_bytes=attachment.size_bytes,
            checksum_sha256=attachment.checksum_sha256,
            mime_type=attachment.mime_type,
            metadata_json=attachment.metadata_json,
        )

    def get_blob(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        range_header: Optional[str],
        as_download: bool,
    ) -> Optional[AttachmentBlobPayload]:
        attachment = self.attachment_service.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            logger.warning(
                "[MULTIMEDIA][STREAM] attachment_not_found attachment_id=%s tenant_id=%s",
                attachment_id,
                tenant_id,
            )
            return None

        total_size = int(attachment.size_bytes or 0)
        parsed_range = self._parse_range(range_header=range_header, total_size=total_size)
        storage_obj = self.attachment_service.load_attachment_blob(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            storage_key=attachment.storage_key,
            byte_range=parsed_range,
        )
        if storage_obj is None:
            logger.warning(
                "[MULTIMEDIA][STREAM] blob_not_found attachment_id=%s tenant_id=%s",
                attachment_id,
                tenant_id,
            )
            return None

        mime_type = (attachment.mime_type or storage_obj.mime_type or "application/octet-stream").split(";")[0].strip()
        if mime_type not in self.allowed_mimes:
            mime_type = "application/octet-stream"
        disposition = self._build_content_disposition(attachment, as_download=as_download)
        start = parsed_range[0] if parsed_range else None
        end = parsed_range[1] if parsed_range else None

        descriptor = AttachmentBlobDTO(
            attachment_id=attachment_id,
            size_bytes=storage_obj.size_bytes,
            mime_type=mime_type,
            content_disposition=disposition,
            range_start=start,
            range_end=end,
            total_size=total_size if total_size > 0 else None,
            is_partial=parsed_range is not None,
        )
        logger.warning(
            "[MULTIMEDIA][STREAM] blob_ready attachment_id=%s tenant_id=%s as_download=%s mime=%s size_bytes=%s is_partial=%s range_start=%s range_end=%s",
            attachment_id,
            tenant_id,
            as_download,
            mime_type,
            storage_obj.size_bytes,
            parsed_range is not None,
            start,
            end,
        )
        return AttachmentBlobPayload(content=storage_obj.payload, descriptor=descriptor)

    def _metadata_dto(self, attachment: MessageAttachment) -> AttachmentMetadataDTO:
        return AttachmentMetadataDTO(
            id=attachment.id,
            message_id=attachment.message_id,
            tenant_id=attachment.tenant_id,
            attachment_type=attachment.attachment_type,
            storage_backend=attachment.storage_backend,
            storage_key=attachment.storage_key,
            provider_media_id=attachment.provider_media_id,
            provider_url=attachment.provider_url,
            mime_type=attachment.mime_type,
            filename=attachment.filename,
            extension=attachment.extension,
            size_bytes=attachment.size_bytes,
            checksum_sha256=attachment.checksum_sha256,
            download_status=attachment.download_status,
            metadata_json=attachment.metadata_json,
            width=attachment.width,
            height=attachment.height,
            duration_ms=attachment.duration_ms,
            caption=attachment.caption,
            provider_timestamp=attachment.provider_timestamp,
            created_at=attachment.created_at,
        )

    def _parse_range(self, *, range_header: Optional[str], total_size: int) -> Optional[tuple[int, int]]:
        if not range_header or total_size <= 0:
            return None
        value = range_header.strip().lower()
        if not value.startswith("bytes="):
            return None
        range_part = value.split("=", 1)[1].split(",", 1)[0].strip()
        if "-" not in range_part:
            return None
        start_raw, end_raw = range_part.split("-", 1)
        try:
            if start_raw == "":
                suffix = int(end_raw)
                if suffix <= 0:
                    return None
                start = max(total_size - suffix, 0)
                end = total_size - 1
                return (start, end)
            start = int(start_raw)
            end = int(end_raw) if end_raw else total_size - 1
        except ValueError:
            return None
        if start < 0 or end < start or start >= total_size:
            return None
        return (start, min(end, total_size - 1))

    def _build_content_disposition(self, attachment: MessageAttachment, *, as_download: bool) -> str:
        filename = (attachment.filename or "").strip() or f"{attachment.id}.{self._default_extension(attachment)}"
        disposition_kind = "attachment" if as_download else "inline"
        return f'{disposition_kind}; filename="{filename}"'

    def _default_extension(self, attachment: MessageAttachment) -> str:
        if attachment.extension:
            return attachment.extension
        mapping = {
            AttachmentType.IMAGE: "jpg",
            AttachmentType.AUDIO: "mp3",
            AttachmentType.VIDEO: "mp4",
            AttachmentType.DOCUMENT: "pdf",
            AttachmentType.FILE: "bin",
        }
        return mapping.get(attachment.attachment_type, "bin")
