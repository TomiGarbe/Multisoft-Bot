import uuid
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Channel, Tenant, User
from app.models.auth import TenantUser
from app.schemas.channel import ChannelResponse


VALID_CHANNEL_TYPES = ["whatsapp", "web", "instagram"]


def _validate_channel_type(channel_type: str) -> None:
    if channel_type not in VALID_CHANNEL_TYPES:
        raise ValueError(f"Invalid channel type. Allowed: {', '.join(VALID_CHANNEL_TYPES)}")


def _build_channel_response(channel: Channel) -> ChannelResponse:
    return ChannelResponse(
        id=channel.id,
        tenant_id=channel.tenant_id,
        type=channel.type,
        name=channel.name,
        external_id=channel.external_id,
        config=channel.config_jsonb,
        is_active=channel.is_active,
    )


def get_channels(db: Session, user: User) -> list[ChannelResponse]:
    """Get channels accessible to the user."""
    if not user.is_active:
        return []
    
    if user.is_backdoor:
        stmt = select(Channel)
    else:
        stmt = (
            select(Channel)
            .join(Tenant, Tenant.id == Channel.tenant_id)
            .join(TenantUser, TenantUser.tenant_id == Tenant.id)
            .where(TenantUser.user_id == user.id)
        )
    
    channels = db.execute(stmt).scalars().all()
    return [_build_channel_response(c) for c in channels]


def create_channel(
    db: Session,
    tenant_id: uuid.UUID,
    type: str,
    name: str,
    external_id: str,
    config: Optional[Dict[str, Any]] = None,
    is_active: bool = True,
) -> ChannelResponse:
    """Create a new channel with validation."""
    # Validate channel type
    _validate_channel_type(type)
    
    # Check if tenant exists
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise LookupError("Tenant not found")
    
    # Check UNIQUE constraint (tenant_id, external_id)
    existing = (
        db.query(Channel)
        .filter(
            Channel.tenant_id == tenant_id,
            Channel.external_id == external_id,
        )
        .first()
    )
    if existing:
        raise ValueError(f"Channel with external_id '{external_id}' already exists for this tenant")
    
    channel = Channel(
        tenant_id=tenant_id,
        type=type,
        name=name,
        external_id=external_id,
        config_jsonb=config,
        is_active=is_active,
    )
    
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    return _build_channel_response(channel)


def update_channel(
    db: Session,
    channel_id: uuid.UUID,
    **kwargs,
) -> ChannelResponse:
    """Update a channel with validation."""
    channel = db.get(Channel, channel_id)
    
    if not channel:
        raise LookupError("Channel not found")
    
    # Validate channel type if provided
    if "type" in kwargs and kwargs["type"]:
        _validate_channel_type(kwargs["type"])
    
    # Check UNIQUE constraint if external_id is being changed
    if "external_id" in kwargs and kwargs["external_id"]:
        existing = (
            db.query(Channel)
            .filter(
                Channel.tenant_id == channel.tenant_id,
                Channel.external_id == kwargs["external_id"],
                Channel.id != channel_id,
            )
            .first()
        )
        if existing:
            raise ValueError(f"Channel with external_id '{kwargs['external_id']}' already exists for this tenant")
    
    # Update only provided fields
    for key, value in kwargs.items():
        if value is not None or (key in ["config"] and key in kwargs):
            if key == "config":
                setattr(channel, "config_jsonb", value)
            else:
                setattr(channel, key, value)
    
    db.commit()
    db.refresh(channel)
    
    return _build_channel_response(channel)


def delete_channel(db: Session, channel_id: uuid.UUID) -> bool:
    """Delete a channel (soft delete by marking is_active=False)."""
    try:
        channel = db.get(Channel, channel_id)
        if channel is None:
            return False
        
        channel.is_active = False
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
