from enum import Enum as PyEnum
import uuid
from typing import Any, List, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.utils.bot_actions_helpers import normalize_tool_name, validate_tool_name


class HttpMethod(str, PyEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class BotAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bot_actions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trigger_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    method: Mapped[HttpMethod] = mapped_column(Enum(HttpMethod, name="http_method_enum"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    headers_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    query_params_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    body_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    variables_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    auth_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    response_config_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    timeout_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_bot_actions_tenant_name"),
        Index("ix_bot_actions_tenant_id", "tenant_id"),
        Index("ix_bot_actions_enabled", "enabled"),
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="bot_actions")
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_user_id], back_populates="created_bot_actions"
    )
    updated_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[updated_by_user_id], back_populates="updated_bot_actions"
    )
    channel_links: Mapped[List["ChannelBotActionLink"]] = relationship(
        "ChannelBotActionLink", back_populates="bot_action", cascade="all, delete-orphan"
    )
    executions: Mapped[List["BotActionExecution"]] = relationship(
        "BotActionExecution", back_populates="bot_action"
    )

    @validates("name")
    def _normalize_name(self, key: str, value: str) -> str:
        normalized_name = normalize_tool_name(value)
        return validate_tool_name(normalized_name)


class ChannelBotActionLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "channel_bot_action_links"

    channel_bot_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_bot_configs.id", ondelete="CASCADE"), nullable=False
    )
    bot_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bot_actions.id", ondelete="CASCADE"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("channel_bot_config_id", "bot_action_id", name="uq_channel_bot_action_link"),
        Index("ix_channel_bot_action_links_channel_bot_config_id", "channel_bot_config_id"),
        Index("ix_channel_bot_action_links_bot_action_id", "bot_action_id"),
    )

    channel_bot_config: Mapped["ChannelBotConfig"] = relationship(
        "ChannelBotConfig", back_populates="bot_action_links"
    )
    bot_action: Mapped["BotAction"] = relationship("BotAction", back_populates="channel_links")


class BotActionExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bot_action_executions"

    bot_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bot_actions.id", ondelete="SET NULL"), nullable=True
    )
    channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    request_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    response_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_bot_action_executions_bot_action_id", "bot_action_id"),
        Index("ix_bot_action_executions_channel_id", "channel_id"),
        Index("ix_bot_action_executions_conversation_id", "conversation_id"),
        Index("ix_bot_action_executions_created_at", "created_at"),
    )

    bot_action: Mapped[Optional["BotAction"]] = relationship("BotAction", back_populates="executions")
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="bot_action_executions")
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", back_populates="bot_action_executions"
    )
