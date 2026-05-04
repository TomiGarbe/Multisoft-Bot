import uuid
from typing import Any, Optional

from sqlalchemy import select

from app.models import Channel, Tenant
from app.models.auth import TenantUser
from app.repositories.base_repository import BaseRepository


class ChannelRepository(BaseRepository):
    def get_by_id(self, channel_id: uuid.UUID) -> Optional[Channel]:
        return super().get_by_id(Channel, channel_id)

    def get_by_id_and_tenant(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Channel]:
        stmt = select(Channel).where(Channel.id == channel_id, Channel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(self) -> list[Channel]:
        stmt = select(Channel)
        return self.db.execute(stmt).scalars().all()

    def get_all_by_tenant(self, tenant_id: uuid.UUID) -> list[Channel]:
        stmt = select(Channel).where(Channel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalars().all()

    def get_all_by_user_id(self, user_id: uuid.UUID) -> list[Channel]:
        stmt = (
            select(Channel)
            .join(Tenant, Tenant.id == Channel.tenant_id)
            .join(TenantUser, TenantUser.tenant_id == Tenant.id)
            .where(TenantUser.user_id == user_id)
        )
        return self.db.execute(stmt).scalars().all()

    def tenant_exists(self, tenant_id: uuid.UUID) -> bool:
        stmt = select(Tenant.id).where(Tenant.id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def get_by_tenant_and_external_id(
        self,
        tenant_id: uuid.UUID,
        external_id: str,
    ) -> Optional[Channel]:
        stmt = select(Channel).where(
            Channel.tenant_id == tenant_id,
            Channel.external_id == external_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_tenant_and_external_id_excluding_id(
        self,
        tenant_id: uuid.UUID,
        external_id: str,
        channel_id: uuid.UUID,
    ) -> Optional[Channel]:
        stmt = select(Channel).where(
            Channel.tenant_id == tenant_id,
            Channel.external_id == external_id,
            Channel.id != channel_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, channel: Channel) -> Channel:
        self.db.add(channel)
        return channel

    def update(self, channel: Channel, **kwargs: Any) -> Channel:
        for key, value in kwargs.items():
            setattr(channel, key, value)
        return channel

    def delete(self, channel: Channel) -> None:
        super().delete(channel)

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, channel: Channel) -> None:
        self.db.refresh(channel)

    def rollback(self) -> None:
        self.db.rollback()
