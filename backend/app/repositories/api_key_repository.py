import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from app.models import ApiKey, Channel, Tenant
from app.repositories.base_repository import BaseRepository


class ApiKeyRepository(BaseRepository):
    def create(self, api_key: ApiKey) -> ApiKey:
        self.db.add(api_key)
        return api_key

    def get_by_id_and_tenant(self, api_key_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_prefix(self, key_prefix: str) -> Optional[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.key_prefix == key_prefix)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_tenant(self, tenant_id: uuid.UUID) -> list[ApiKey]:
        stmt = (
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant_id)
            .order_by(ApiKey.created_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def deactivate(self, api_key: ApiKey) -> ApiKey:
        api_key.is_active = False
        return api_key

    def update_last_used(self, api_key: ApiKey) -> ApiKey:
        api_key.last_used_at = datetime.now(timezone.utc)
        return api_key

    def tenant_exists(self, tenant_id: uuid.UUID) -> bool:
        stmt = select(Tenant.id).where(Tenant.id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def channel_belongs_to_tenant(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        stmt = select(Channel.id).where(Channel.id == channel_id, Channel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def get_channel_by_id_and_tenant(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Channel]:
        stmt = select(Channel).where(Channel.id == channel_id, Channel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, api_key: ApiKey) -> None:
        self.db.refresh(api_key)

    def rollback(self) -> None:
        self.db.rollback()
