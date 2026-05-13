from __future__ import annotations

from sqlalchemy.orm import Session

from app.providers.storage.database_storage_provider import DatabaseStorageProvider
from app.repositories.attachment_repository import AttachmentRepository


def get_storage_provider(db: Session) -> DatabaseStorageProvider:
    return DatabaseStorageProvider(AttachmentRepository(db))

