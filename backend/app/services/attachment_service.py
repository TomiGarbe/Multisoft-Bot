from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.interfaces.storage import StorageObject, StorageSaveRequest
from app.models.conversation import MessageAttachment
from app.providers.storage import get_storage_provider
from app.repositories.attachment_repository import AttachmentRepository
from app.schemas.internal.attachment_persistence import AttachmentCreate
from app.schemas.internal.message_enums import AttachmentDownloadStatus, StorageBackend


class AttachmentService:
    def __init__(self, db: Session) -> None:
        self.repository = AttachmentRepository(db)
        self.storage_provider = get_storage_provider(db)

    def save_attachment(self, data: AttachmentCreate) -> MessageAttachment:
        existing = self.repository.find_idempotent_match(
            message_id=data.message_id,
            tenant_id=data.tenant_id,
            provider_media_id=data.provider_media_id,
            checksum_sha256=data.checksum_sha256,
            provider_url=data.provider_url,
        )
        if existing:
            return existing
        return self.repository.create_attachment(data)

    def save_attachments_bulk(self, records: Sequence[AttachmentCreate]) -> list[MessageAttachment]:
        saved: list[MessageAttachment] = []
        for record in records:
            saved.append(self.save_attachment(record))
        return saved

    def save_attachment_blob(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID, binary_data: bytes) -> str:
        request = StorageSaveRequest(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            payload=binary_data,
        )
        return self.storage_provider.save(request)

    def load_attachment_blob(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
        byte_range: Optional[tuple[int, int]] = None,
    ) -> Optional[StorageObject]:
        return self.storage_provider.load(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            storage_key=storage_key,
            byte_range=byte_range,
        )

    def attachment_blob_exists(self, *, attachment_id: uuid.UUID, tenant_id: uuid.UUID, storage_key: Optional[str]) -> bool:
        return self.storage_provider.exists(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            storage_key=storage_key,
        )

    def find_by_provider_media_id(self, tenant_id: uuid.UUID, provider_media_id: str) -> Optional[MessageAttachment]:
        return self.repository.get_by_provider_media_id(tenant_id, provider_media_id)

    def get_by_id_and_tenant(self, attachment_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[MessageAttachment]:
        return self.repository.get_by_id_and_tenant(attachment_id, tenant_id)

    def list_by_message_id_and_tenant(
        self,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: Optional[int] = None,
    ) -> list[MessageAttachment]:
        return self.repository.list_by_message_id_and_tenant(
            message_id,
            tenant_id,
            offset=offset,
            limit=limit,
        )

    def list_by_message_ids_and_tenant(
        self,
        *,
        message_ids: Sequence[uuid.UUID],
        tenant_id: uuid.UUID,
    ) -> list[MessageAttachment]:
        return self.repository.list_by_message_ids_and_tenant(
            message_ids=message_ids,
            tenant_id=tenant_id,
        )

    def generate_access_reference(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str],
        ttl_seconds: int = 300,
    ) -> str:
        ref = self.storage_provider.generate_access_reference(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            storage_key=storage_key,
            ttl_seconds=ttl_seconds,
        )
        return ref.reference

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
        self._validate_transition(current=attachment.download_status, target=status)
        return self.repository.update_download_state(
            attachment=attachment,
            status=status,
            metadata_json=metadata_json,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            storage_backend=storage_backend,
        )

    def update_attachment_metadata(self, *, attachment: MessageAttachment, metadata_json: dict) -> MessageAttachment:
        return self.repository.update_metadata_json(attachment=attachment, metadata_json=metadata_json)

    @staticmethod
    def _validate_transition(*, current: AttachmentDownloadStatus, target: AttachmentDownloadStatus) -> None:
        if current == target:
            return
        valid: dict[AttachmentDownloadStatus, set[AttachmentDownloadStatus]] = {
            AttachmentDownloadStatus.NOT_REQUESTED: {AttachmentDownloadStatus.PENDING},
            AttachmentDownloadStatus.PENDING: {AttachmentDownloadStatus.DOWNLOADING, AttachmentDownloadStatus.FAILED},
            AttachmentDownloadStatus.DOWNLOADING: {AttachmentDownloadStatus.COMPLETED, AttachmentDownloadStatus.FAILED},
            AttachmentDownloadStatus.COMPLETED: set(),
            AttachmentDownloadStatus.DOWNLOADED: set(),
            AttachmentDownloadStatus.FAILED: {AttachmentDownloadStatus.PENDING},
        }
        if target not in valid.get(current, set()):
            raise ValueError(f"invalid_download_state_transition:{current.value}->{target.value}")
