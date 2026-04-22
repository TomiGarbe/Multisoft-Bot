from sqlalchemy import String, ForeignKey, Boolean, Text, Integer, BigInteger, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid
from datetime import datetime
from typing import List, Optional, Any


class Channel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "channels"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="channels")
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="channel", cascade="all, delete-orphan"
    )
    channel_bot_configs: Mapped[List["ChannelBotConfig"]] = relationship(
        "ChannelBotConfig", back_populates="channel", cascade="all, delete-orphan"
    )