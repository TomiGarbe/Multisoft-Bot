from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import uuid


class TenantWallet(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenant_wallets"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    balance_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    consumed_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="wallet")
