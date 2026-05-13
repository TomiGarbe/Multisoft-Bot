from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.schemas.internal.message_enums import (
    MediaProcessingCapability,
    MediaProcessingStatus,
    ProcessedArtifactStorageBackend,
)


class AttachmentProcessingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "attachment_processing_jobs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message_attachments.id", ondelete="CASCADE"), nullable=False
    )
    capability: Mapped[MediaProcessingCapability] = mapped_column(
        Enum(MediaProcessingCapability, name="media_processing_capability_enum", native_enum=False),
        nullable=False,
    )
    status: Mapped[MediaProcessingStatus] = mapped_column(
        Enum(MediaProcessingStatus, name="media_processing_status_enum", native_enum=False),
        nullable=False,
        default=MediaProcessingStatus.PENDING,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    attachment: Mapped["MessageAttachment"] = relationship("MessageAttachment")
    tenant: Mapped["Tenant"] = relationship("Tenant")

    __table_args__ = (
        Index("ix_attachment_processing_jobs_attachment_id", "attachment_id"),
        Index("ix_attachment_processing_jobs_tenant_status", "tenant_id", "status"),
        Index("ix_attachment_processing_jobs_capability", "capability"),
    )


class ProcessedArtifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "processed_artifacts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message_attachments.id", ondelete="CASCADE"), nullable=False
    )
    capability: Mapped[MediaProcessingCapability] = mapped_column(
        Enum(MediaProcessingCapability, name="media_processing_capability_enum", native_enum=False),
        nullable=False,
    )
    storage_backend: Mapped[ProcessedArtifactStorageBackend] = mapped_column(
        Enum(ProcessedArtifactStorageBackend, name="processed_artifact_storage_backend_enum", native_enum=False),
        nullable=False,
        default=ProcessedArtifactStorageBackend.INLINE_JSON,
    )
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    payload_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    payload_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    attachment: Mapped["MessageAttachment"] = relationship("MessageAttachment")
    tenant: Mapped["Tenant"] = relationship("Tenant")

    __table_args__ = (
        Index("ix_processed_artifacts_attachment_id", "attachment_id"),
        Index("ix_processed_artifacts_tenant_capability", "tenant_id", "capability"),
    )
