from sqlalchemy import String, ForeignKey, Boolean, Text, Integer, BigInteger, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid
from datetime import datetime
from typing import List, Optional


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    plan_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    tenant_users: Mapped[List["TenantUser"]] = relationship(
        "TenantUser", back_populates="tenant", cascade="all, delete-orphan"
    )
    channels: Mapped[List["Channel"]] = relationship(
        "Channel", back_populates="tenant", cascade="all, delete-orphan"
    )
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="tenant", cascade="all, delete-orphan"
    )
    chat_threads: Mapped[List["ChatThread"]] = relationship(
        "ChatThread", back_populates="tenant", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="tenant", cascade="all, delete-orphan"
    )
    settings: Mapped["TenantSettings"] = relationship(
        "TenantSettings", back_populates="tenant", cascade="all, delete-orphan", uselist=False
    )
    bot_configs: Mapped[List["TenantBotConfig"]] = relationship(
        "TenantBotConfig", back_populates="tenant", cascade="all, delete-orphan"
    )