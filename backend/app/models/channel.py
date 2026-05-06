from sqlalchemy import String, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid
from typing import List, Optional, Any


class Channel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id", name="uq_tenant_external_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="channels")
    chat_threads: Mapped[List["ChatThread"]] = relationship(
        "ChatThread", back_populates="channel", cascade="all, delete-orphan"
    )
    channel_bot_configs: Mapped[List["ChannelBotConfig"]] = relationship(
        "ChannelBotConfig", back_populates="channel", cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship("ApiKey", back_populates="channel")
    bot_action_executions: Mapped[List["BotActionExecution"]] = relationship(
        "BotActionExecution", back_populates="channel"
    )
