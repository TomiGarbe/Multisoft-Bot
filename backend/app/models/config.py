from sqlalchemy import ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid
from typing import Optional, Any


class ChannelBotConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Bot configuration per channel.
    
    Contains the complete bot behavior configuration for a specific channel:
    - identity: Bot description/personality
    - tone: Communication style
    - behavior: List of behavioral rules
    - conversation: Conversation settings
    - objectives: Bot goals/objectives
    - data_collection: Data handling policies
    - actions: Supported actions
    - user_type_config: User type specific configurations
    """
    __tablename__ = "channel_bot_configs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    config_jsonb: Mapped[Any] = mapped_column(JSONB, nullable=False)
    user_types_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    settings_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="channel_bot_configs")
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])
