from sqlalchemy import ForeignKey, Integer, BigInteger, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid


class UsageDaily(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "usage_daily"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    tokens_used: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    messages_inbound: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_outbound: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_active: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversations_started: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actions_executed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint("tenant_id", "date", name="uq_usage_daily_tenant_date"),)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")


class ContactUsageDaily(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "contact_usage_daily"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    tokens_used: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    messages_inbound: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_outbound: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversations_started: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint("contact_id", "date", name="uq_contact_usage_daily_contact_date"),)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="contact_usage_daily")