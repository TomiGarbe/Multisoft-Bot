from sqlalchemy import String, ForeignKey, Text, Integer, BigInteger, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid
from datetime import datetime
from typing import List, Optional, Any


class ChatThread(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Representa un chat o conversación a nivel de thread.
    Puede ser un chat directo (1:1 con un contacto) o un grupo (múltiples contactos).
    """
    __tablename__ = "chat_threads"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    external_chat_id: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "direct" | "group"
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("channel_id", "external_chat_id", name="uq_chat_threads_channel_external"),
        Index("ix_chat_threads_tenant_channel", "tenant_id", "channel_id"),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="chat_threads")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="chat_threads")
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="chat_thread", cascade="all, delete-orphan"
    )


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    chat_thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False
    )
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="conversations")
    chat_thread: Mapped["ChatThread"] = relationship("ChatThread", back_populates="conversations")
    assigned_user: Mapped[Optional["User"]] = relationship("User")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    sender_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    direction: Mapped[str] = mapped_column(String(30), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(30), nullable=False)
    message_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    metadata_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    group_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sender_external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    has_media: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_payload: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("channel_id", "provider_message_id", name="uq_messages_channel_provider_id"),
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    tenant: Mapped["Tenant"] = relationship("Tenant")
    channel: Mapped["Channel"] = relationship("Channel")
    sender_contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="messages")
    attachments: Mapped[List["MessageAttachment"]] = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )


class MessageAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "message_attachments"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    attachment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    file_extension: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_data: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_jsonb: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="attachments")
    tenant: Mapped["Tenant"] = relationship("Tenant")