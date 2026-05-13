from __future__ import annotations

import uuid
from typing import Optional

from app.interfaces.storage import StorageAccessReference, StorageObject, StorageProvider, StorageSaveRequest
from app.repositories.attachment_repository import AttachmentRepository


class DatabaseStorageProvider(StorageProvider):
    backend_name = "database"

    def __init__(self, repository: AttachmentRepository) -> None:
        self.repository = repository

    def save(self, request: StorageSaveRequest) -> str:
        self.repository.create_or_update_blob(
            attachment_id=request.attachment_id,
            tenant_id=request.tenant_id,
            binary_data=request.payload,
        )
        return str(request.attachment_id)

    def load(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
        byte_range: Optional[tuple[int, int]] = None,
    ) -> Optional[StorageObject]:
        blob = self.repository.get_blob_by_attachment_id(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            byte_range=byte_range,
        )
        if blob is None:
            return None
        return StorageObject(payload=blob, size_bytes=len(blob))

    def delete(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
    ) -> None:
        self.repository.delete_blob_by_attachment_id(attachment_id=attachment_id, tenant_id=tenant_id)

    def exists(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
    ) -> bool:
        return self.repository.blob_exists(attachment_id=attachment_id, tenant_id=tenant_id)

    def generate_access_reference(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
        ttl_seconds: int = 300,
    ) -> StorageAccessReference:
        return StorageAccessReference(
            backend=self.backend_name,
            reference=storage_key or str(attachment_id),
            expires_in_seconds=ttl_seconds,
        )

