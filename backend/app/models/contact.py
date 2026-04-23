from sqlalchemy import String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid
from typing import List, Optional, Any


class Contact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "contacts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    document_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (Index("ix_contacts_tenant_phone", "tenant_id", "phone"),)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="contacts")
    contact_identities: Mapped[List["ContactIdentity"]] = relationship(
        "ContactIdentity", back_populates="contact", cascade="all, delete-orphan"
    )
    contact_usage_daily: Mapped[List["ContactUsageDaily"]] = relationship(
        "ContactUsageDaily", back_populates="contact", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender_contact", cascade="all, delete-orphan"
    )


class ContactIdentity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "contact_identities"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (UniqueConstraint("channel_type", "external_id", name="uq_contact_identities_channel_external"),)

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="contact_identities")