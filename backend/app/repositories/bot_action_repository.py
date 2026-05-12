from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.bot_action import BotAction, ChannelBotActionLink
from app.models.config import ChannelBotConfig


class BotActionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, bot_action: BotAction) -> BotAction:
        self.db.add(bot_action)
        return bot_action

    def update(self, bot_action: BotAction) -> BotAction:
        return bot_action

    def delete(self, bot_action: BotAction) -> None:
        self.db.delete(bot_action)

    def get_by_id(self, action_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[BotAction]:
        stmt = (
            select(BotAction)
            .where(BotAction.id == action_id, BotAction.tenant_id == tenant_id)
            .options(selectinload(BotAction.channel_links))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, tenant_id: uuid.UUID, name: str) -> Optional[BotAction]:
        stmt = select(BotAction).where(BotAction.tenant_id == tenant_id, BotAction.name == name).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        enabled: bool | None = None,
        search: str | None = None,
        channel_id: uuid.UUID | None = None,
    ) -> list[BotAction]:
        stmt = select(BotAction).where(BotAction.tenant_id == tenant_id)

        if enabled is not None:
            stmt = stmt.where(BotAction.enabled.is_(enabled))

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(BotAction.name.ilike(search_term))

        if channel_id is not None:
            channel_config_ids_subquery = (
                select(ChannelBotConfig.id).where(
                    ChannelBotConfig.channel_id == channel_id,
                    ChannelBotConfig.tenant_id == tenant_id,
                )
            )
            stmt = stmt.where(
                BotAction.id.in_(
                    select(ChannelBotActionLink.bot_action_id).where(
                        ChannelBotActionLink.channel_bot_config_id.in_(channel_config_ids_subquery)
                    )
                )
            )

        stmt = stmt.order_by(BotAction.created_at.desc())
        return self.db.execute(stmt).scalars().all()

    def get_enabled_by_tenant(self, tenant_id: uuid.UUID) -> list[BotAction]:
        stmt = (
            select(BotAction)
            .where(BotAction.tenant_id == tenant_id, BotAction.enabled.is_(True))
            .order_by(BotAction.created_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
