import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserTenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_tenants"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenants_user_tenant"),
    )

    user: Mapped["User"] = relationship("User", back_populates="tenant_scopes")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="user_tenant_links")
