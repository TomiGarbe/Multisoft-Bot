import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserBusiness(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_businesses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_user_businesses_user_business"),
    )

    user: Mapped["User"] = relationship("User", back_populates="business_links")
    business: Mapped["Tenant"] = relationship("Tenant", back_populates="user_business_links")
