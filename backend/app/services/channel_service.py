import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant_id
from app.models import Channel, User
from app.repositories.channel_repository import ChannelRepository
from app.schemas.channel import ChannelConfigBundleResponse, ChannelResponse
from app.services.bot_config_service import BotConfigService


VALID_CHANNEL_TYPES = ["whatsapp", "web", "instagram"]


class ChannelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ChannelRepository(db)

    def _validate_channel_type(self, channel_type: str) -> None:
        if channel_type not in VALID_CHANNEL_TYPES:
            raise ValueError(f"Invalid channel type. Allowed: {', '.join(VALID_CHANNEL_TYPES)}")

    def _build_channel_response(self, channel: Channel) -> ChannelResponse:
        return ChannelResponse(
            id=channel.id,
            tenant_id=channel.tenant_id,
            type=channel.type,
            name=channel.name,
            external_id=channel.external_id,
            config=channel.config_jsonb,
            is_active=channel.is_active,
        )

    def get_channels(self, user: Optional[User] = None) -> list[ChannelResponse]:
        # DEV compatibility: keep current bypass behavior.
        if user is None:
            channels = self.repository.get_all()
            return [self._build_channel_response(c) for c in channels]

        if not user.is_active:
            return []

        if user.is_backdoor:
            channels = self.repository.get_all()
            return [self._build_channel_response(c) for c in channels]

        channels = self.repository.get_all_by_user_id(user.id)
        return [self._build_channel_response(c) for c in channels]

    def create_channel(
        self,
        tenant_id: uuid.UUID,
        type: str,
        name: str,
        external_id: str,
        config: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
    ) -> ChannelResponse:
        self._validate_channel_type(type)

        if not self.repository.tenant_exists(tenant_id):
            raise LookupError("Tenant not found")

        existing = self.repository.get_by_tenant_and_external_id(tenant_id, external_id)
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

        try:
            self.repository.create(channel)
            self.repository.flush()
            BotConfigService.create_default_channel_config(self.db, channel.id)
            self.repository.commit()
            self.repository.refresh(channel)
            return self._build_channel_response(channel)
        except Exception:
            self.repository.rollback()
            raise

    def update_channel(
        self,
        channel_id: uuid.UUID,
        **kwargs: Any,
    ) -> ChannelResponse:
        tenant_id = get_current_tenant_id()
        channel = self.repository.get_by_id_and_tenant(channel_id, tenant_id)
        if not channel:
            raise LookupError("Channel not found")

        if "type" in kwargs and kwargs["type"]:
            self._validate_channel_type(kwargs["type"])

        if "external_id" in kwargs and kwargs["external_id"]:
            existing = self.repository.get_by_tenant_and_external_id_excluding_id(
                tenant_id=channel.tenant_id,
                external_id=kwargs["external_id"],
                channel_id=channel_id,
            )
            if existing:
                raise ValueError(
                    f"Channel with external_id '{kwargs['external_id']}' already exists for this tenant"
                )

        mapped_updates: dict[str, Any] = {}
        for key, value in kwargs.items():
            if value is not None or (key in ["config"] and key in kwargs):
                if key == "config":
                    mapped_updates["config_jsonb"] = value
                else:
                    mapped_updates[key] = value

        try:
            self.repository.update(channel, **mapped_updates)
            self.repository.commit()
            self.repository.refresh(channel)
            return self._build_channel_response(channel)
        except Exception:
            self.repository.rollback()
            raise

    def delete_channel(self, channel_id: uuid.UUID) -> bool:
        try:
            tenant_id = get_current_tenant_id()
            channel = self.repository.get_by_id_and_tenant(channel_id, tenant_id)
            if channel is None:
                return False

            channel.is_active = False
            self.repository.commit()
            return True
        except Exception:
            self.repository.rollback()
            raise

    def get_channel_config_bundle(self, channel_id: uuid.UUID) -> ChannelConfigBundleResponse:
        tenant_id = get_current_tenant_id()
        channel = self.repository.get_by_id_and_tenant(channel_id, tenant_id)
        if channel is None:
            raise LookupError(f"Channel not found: {channel_id}")

        channel_config = BotConfigService.get_channel_config(self.db, channel_id)
        config = channel_config.config_jsonb
        settings = channel_config.settings_jsonb
        user_types = channel_config.user_types_jsonb

        if not isinstance(config, dict):
            raise ValueError("Config invalida")
        if not isinstance(settings, dict):
            raise ValueError("Settings invalida")
        if not isinstance(user_types, dict):
            raise ValueError("User types invalido")

        return ChannelConfigBundleResponse(
            config=config,
            settings=settings,
            user_types=user_types,
        )


def get_channels(db: Session, user: Optional[User] = None) -> list[ChannelResponse]:
    return ChannelService(db).get_channels(user=user)


def create_channel(
    db: Session,
    tenant_id: uuid.UUID,
    type: str,
    name: str,
    external_id: str,
    config: Optional[Dict[str, Any]] = None,
    is_active: bool = True,
) -> ChannelResponse:
    return ChannelService(db).create_channel(
        tenant_id=tenant_id,
        type=type,
        name=name,
        external_id=external_id,
        config=config,
        is_active=is_active,
    )


def update_channel(db: Session, channel_id: uuid.UUID, **kwargs: Any) -> ChannelResponse:
    return ChannelService(db).update_channel(channel_id=channel_id, **kwargs)


def delete_channel(db: Session, channel_id: uuid.UUID) -> bool:
    return ChannelService(db).delete_channel(channel_id=channel_id)
