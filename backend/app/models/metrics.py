from sqlalchemy import ForeignKey, Integer, BigInteger, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid


class ContactUsage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Usage tracking per conversation (1 record per active conversation)."""
    __tablename__ = "contact_usage"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    bot_message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("conversation_id", name="uq_contact_usage_conversation"),
        Index("ix_contact_usage_contact_id", "contact_id"),
        Index("ix_contact_usage_conversation_id", "conversation_id"),
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="contact_usage")
    conversation: Mapped["Conversation"] = relationship("Conversation")


class AIUsageEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular AI usage events: 1 row per AI request."""
    __tablename__ = "ai_usage_events"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    __table_args__ = (
        Index("ix_ai_usage_events_tenant_id", "tenant_id"),
        Index("ix_ai_usage_events_channel_id", "channel_id"),
        Index("ix_ai_usage_events_conversation_id", "conversation_id"),
        Index("ix_ai_usage_events_created_at", "created_at"),
        Index("ix_ai_usage_events_request_id", "request_id"),
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
