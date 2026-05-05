from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from datetime import datetime
from typing import List, Optional


class UserType(str, PyEnum):
    ADMIN = "ADMIN"
    BACKDOOR = "BACKDOOR"
    BUSINESS_USER = "BUSINESS_USER"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_backdoor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType, name="user_type_enum"),
        default=UserType.BUSINESS_USER,
        nullable=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant_links: Mapped[List["TenantUser"]] = relationship(
        "TenantUser", back_populates="user", cascade="all, delete-orphan"
    )
    business_links: Mapped[List["UserBusiness"]] = relationship(
        "UserBusiness", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
