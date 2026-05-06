from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.bot_action import BotAction, ChannelBotActionLink
from app.models.config import ChannelBotConfig


class ChannelBotActionLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def assign_actions_to_channel(
        self,
        *,
        channel_bot_config_id: uuid.UUID,
        action_ids: list[uuid.UUID],
    ) -> list[ChannelBotActionLink]:
        links: list[ChannelBotActionLink] = []
        for action_id in action_ids:
            link = ChannelBotActionLink(
                channel_bot_config_id=channel_bot_config_id,
                bot_action_id=action_id,
                enabled=True,
            )
            self.db.add(link)
            links.append(link)
        return links

    def get_channel_actions(self, channel_bot_config_id: uuid.UUID) -> list[BotAction]:
        stmt = (
            select(BotAction)
            .join(ChannelBotActionLink, ChannelBotActionLink.bot_action_id == BotAction.id)
            .where(
                ChannelBotActionLink.channel_bot_config_id == channel_bot_config_id,
                ChannelBotActionLink.enabled.is_(True),
            )
            .options(selectinload(BotAction.channel_links))
            .order_by(BotAction.created_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def replace_channel_actions(
        self,
        *,
        channel_bot_config_id: uuid.UUID,
        action_ids: list[uuid.UUID],
    ) -> list[ChannelBotActionLink]:
        self.db.execute(
            delete(ChannelBotActionLink).where(ChannelBotActionLink.channel_bot_config_id == channel_bot_config_id)
        )
        return self.assign_actions_to_channel(channel_bot_config_id=channel_bot_config_id, action_ids=action_ids)

    def get_channel_bot_config(self, config_id: uuid.UUID, tenant_id: uuid.UUID) -> ChannelBotConfig | None:
        stmt = (
            select(ChannelBotConfig)
            .where(ChannelBotConfig.id == config_id, ChannelBotConfig.tenant_id == tenant_id)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
