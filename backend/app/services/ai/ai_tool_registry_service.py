from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.bot_action import BotAction, ChannelBotActionLink
from app.models.config import ChannelBotConfig
from app.services.ai.ai_tool_builder_service import AIToolBuilderService


class AIToolRegistryService:
    def __init__(self, db: Session):
        self.db = db
        self.builder = AIToolBuilderService()

    def get_available_actions(
        self,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> list[BotAction]:
        base_stmt = (
            select(BotAction.id, BotAction.created_at)
            .join(ChannelBotActionLink, ChannelBotActionLink.bot_action_id == BotAction.id)
            .join(ChannelBotConfig, ChannelBotConfig.id == ChannelBotActionLink.channel_bot_config_id)
            .where(
                BotAction.tenant_id == tenant_id,
                BotAction.enabled.is_(True),
                ChannelBotActionLink.enabled.is_(True),
                ChannelBotConfig.tenant_id == tenant_id,
                ChannelBotConfig.channel_id == channel_id,
                ChannelBotConfig.is_active.is_(True),
            )
        )
        # PostgreSQL DISTINCT ON requires ORDER BY to start with the same expressions.
        dedup_subquery = (
            base_stmt
            .order_by(BotAction.id.asc(), BotAction.created_at.desc())
            .distinct(BotAction.id)
            .subquery()
        )
        stmt = (
            select(BotAction)
            .join(dedup_subquery, dedup_subquery.c.id == BotAction.id)
            .order_by(dedup_subquery.c.created_at.desc())
        )
        try:
            return self.db.execute(stmt).scalars().all()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def get_tools(
        self,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> tuple[list[dict[str, Any]], dict[str, BotAction]]:
        actions = self.get_available_actions(tenant_id=tenant_id, channel_id=channel_id)
        mapping = {action.name: action for action in actions}
        tools = [self.builder.build_from_action(action) for action in actions]
        return tools, mapping
