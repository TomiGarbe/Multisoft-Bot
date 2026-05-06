import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.config import ChannelBotConfig


class ChannelConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id_and_tenant(self, config_id: uuid.UUID, tenant_id: uuid.UUID) -> ChannelBotConfig | None:
        stmt = (
            select(ChannelBotConfig)
            .where(ChannelBotConfig.id == config_id, ChannelBotConfig.tenant_id == tenant_id)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_existing_channel_ids_by_tenant(self, channel_ids: list[uuid.UUID], tenant_id: uuid.UUID) -> set[uuid.UUID]:
        if not channel_ids:
            return set()
        stmt = select(Channel.id).where(Channel.id.in_(channel_ids), Channel.tenant_id == tenant_id)
        return {channel_id for (channel_id,) in self.db.execute(stmt).all()}

    def get_channel_by_id(self, channel_id: uuid.UUID) -> Channel | None:
        return self.db.get(Channel, channel_id)

    def get_active_by_channel_id(self, channel_id: uuid.UUID) -> ChannelBotConfig | None:
        stmt = (
            select(ChannelBotConfig)
            .where(
                ChannelBotConfig.channel_id == channel_id,
                ChannelBotConfig.is_active.is_(True),
            )
            .order_by(ChannelBotConfig.version.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, channel_config: ChannelBotConfig) -> ChannelBotConfig:
        self.db.add(channel_config)
        return channel_config

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
