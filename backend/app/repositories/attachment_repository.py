from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.conversation import AttachmentBlob, MessageAttachment
from app.repositories.base_repository import BaseRepository
from app.schemas.internal.attachment_persistence import AttachmentCreate
from app.schemas.internal.message_enums import AttachmentDownloadStatus, StorageBackend


class AttachmentRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_attachment(self, data: AttachmentCreate) -> MessageAttachment:
        attachment = MessageAttachment(
            message_id=data.message_id,
            tenant_id=data.tenant_id,
            attachment_type=data.attachment_type,
            storage_backend=data.storage_backend,
            storage_key=data.storage_key,
            provider_media_id=data.provider_media_id,
            provider_url=data.provider_url,
            mime_type=data.mime_type,
            filename=data.filename,
            extension=data.extension,
            size_bytes=data.size_bytes,
            checksum_sha256=data.checksum_sha256,
            download_status=data.download_status,
            metadata_json=data.metadata_json,
            width=data.width,
            height=data.height,
            duration_ms=data.duration_ms,
            caption=data.caption,
            provider_timestamp=data.provider_timestamp,
            # Legacy compatibility columns
            file_name=data.filename,
            file_extension=data.extension,
            file_size_bytes=data.size_bytes,
            metadata_jsonb=data.metadata_json,
            duration_seconds=(data.duration_ms // 1000) if data.duration_ms is not None else None,
            file_data=data.file_data,
        )
        self.db.add(attachment)
        self.db.flush()
        return attachment

    def bulk_create_attachments(self, records: Sequence[AttachmentCreate]) -> list[MessageAttachment]:
        return [self.create_attachment(record) for record in records]

    def create_or_update_blob(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        binary_data: bytes,
    ) -> AttachmentBlob:
        attachment = self.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            raise ValueError("attachment_not_found")
        stmt = select(AttachmentBlob).where(AttachmentBlob.attachment_id == attachment_id)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.binary_data = binary_data
            self.db.flush()
            return existing
        blob = AttachmentBlob(attachment_id=attachment_id, binary_data=binary_data)
        self.db.add(blob)
        self.db.flush()
        return blob

    def get_blob_by_attachment_id(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        byte_range: Optional[tuple[int, int]] = None,
    ) -> Optional[bytes]:
        attachment = self.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            return None
        if byte_range is None:
            stmt = select(AttachmentBlob.binary_data).where(AttachmentBlob.attachment_id == attachment_id)
            return self.db.execute(stmt).scalar_one_or_none()

        start, end = byte_range
        if start < 0 or end < start:
            return None
        length = end - start + 1
        stmt = select(func.substring(AttachmentBlob.binary_data, start + 1, length)).where(
            AttachmentBlob.attachment_id == attachment_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def blob_exists(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        attachment = self.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            return False
        stmt = select(exists().where(AttachmentBlob.attachment_id == attachment_id))
        return bool(self.db.execute(stmt).scalar())

    def delete_blob_by_attachment_id(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        attachment = self.get_by_id_and_tenant(attachment_id, tenant_id)
        if attachment is None:
            return
        stmt = delete(AttachmentBlob).where(AttachmentBlob.attachment_id == attachment_id)
        self.db.execute(stmt)
        self.db.flush()

    def get_by_provider_media_id(self, tenant_id: uuid.UUID, provider_media_id: str) -> Optional[MessageAttachment]:
        stmt = select(MessageAttachment).where(
            MessageAttachment.tenant_id == tenant_id,
            MessageAttachment.provider_media_id == provider_media_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_idempotent_match(
        self,
        *,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        provider_media_id: Optional[str],
        checksum_sha256: Optional[str],
        provider_url: Optional[str],
    ) -> Optional[MessageAttachment]:
        clauses = [MessageAttachment.message_id == message_id, MessageAttachment.tenant_id == tenant_id]
        matchers = []
        if provider_media_id:
            matchers.append(MessageAttachment.provider_media_id == provider_media_id)
        if checksum_sha256:
            matchers.append(MessageAttachment.checksum_sha256 == checksum_sha256)
        if provider_url:
            matchers.append(MessageAttachment.provider_url == provider_url)

        if not matchers:
            return None

        stmt = select(MessageAttachment).where(and_(*clauses), or_(*matchers))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_and_tenant(self, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[MessageAttachment]:
        stmt = select(MessageAttachment).where(
            MessageAttachment.id == attachment_id,
            MessageAttachment.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_message_id_and_tenant(
        self,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: Optional[int] = None,
    ) -> list[MessageAttachment]:
        stmt = select(MessageAttachment).where(
            MessageAttachment.message_id == message_id,
            MessageAttachment.tenant_id == tenant_id,
        )
        stmt = stmt.order_by(MessageAttachment.created_at.asc()).offset(max(offset, 0))
        if limit is not None:
            stmt = stmt.limit(max(limit, 1))
        return list(self.db.execute(stmt).scalars().all())

    def list_by_message_ids_and_tenant(
        self,
        *,
        message_ids: Sequence[uuid.UUID],
        tenant_id: uuid.UUID,
    ) -> list[MessageAttachment]:
        if not message_ids:
            return []
        stmt = select(MessageAttachment).where(
            MessageAttachment.tenant_id == tenant_id,
            MessageAttachment.message_id.in_(message_ids),
        )
        stmt = stmt.order_by(MessageAttachment.created_at.asc())
        return list(self.db.execute(stmt).scalars().all())

    def update_download_state(
        self,
        *,
        attachment: MessageAttachment,
        status: AttachmentDownloadStatus,
        metadata_json: Optional[dict] = None,
        mime_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
        checksum_sha256: Optional[str] = None,
        storage_backend: Optional[StorageBackend] = None,
    ) -> MessageAttachment:
        attachment.download_status = status
        if metadata_json is not None:
            attachment.metadata_json = metadata_json
            attachment.metadata_jsonb = metadata_json
        if mime_type is not None:
            attachment.mime_type = mime_type
        if size_bytes is not None:
            attachment.size_bytes = size_bytes
            attachment.file_size_bytes = size_bytes
        if checksum_sha256 is not None:
            attachment.checksum_sha256 = checksum_sha256
        if storage_backend is not None:
            attachment.storage_backend = storage_backend
        self.db.flush()
        return attachment

    def update_metadata_json(self, *, attachment: MessageAttachment, metadata_json: dict) -> MessageAttachment:
        attachment.metadata_json = metadata_json
        attachment.metadata_jsonb = metadata_json
        self.db.flush()
        return attachment
