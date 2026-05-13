from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StorageSaveRequest:
    attachment_id: uuid.UUID
    tenant_id: uuid.UUID
    payload: bytes
    mime_type: Optional[str] = None


@dataclass(frozen=True)
class StorageObject:
    payload: bytes
    size_bytes: int
    mime_type: Optional[str] = None


@dataclass(frozen=True)
class StorageAccessReference:
    backend: str
    reference: str
    expires_in_seconds: Optional[int] = None


class StorageProvider(ABC):
    @abstractmethod
    def save(self, request: StorageSaveRequest) -> str:
        pass

    @abstractmethod
    def load(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
        byte_range: Optional[tuple[int, int]] = None,
    ) -> Optional[StorageObject]:
        pass

    @abstractmethod
    def delete(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    def exists(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
    ) -> bool:
        pass

    @abstractmethod
    def generate_access_reference(
        self,
        *,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str] = None,
        ttl_seconds: int = 300,
    ) -> StorageAccessReference:
        pass

