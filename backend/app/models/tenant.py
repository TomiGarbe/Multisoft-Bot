from sqlalchemy import String, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from typing import List, Optional


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    plan_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    branding_jsonb: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    features_jsonb: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

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
    wallet: Mapped["TenantWallet"] = relationship(
        "TenantWallet",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan"
    )
    user_tenant_links: Mapped[List["UserTenant"]] = relationship(
        "UserTenant", back_populates="tenant", cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey", back_populates="tenant", cascade="all, delete-orphan"
    )
