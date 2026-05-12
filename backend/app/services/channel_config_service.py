from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.config import ChannelBotConfig
from app.models.user import User
from app.repositories.channel_config_repository import ChannelConfigRepository
from app.schemas.channel_config import ChannelConfigUpdate
from app.services.auth.access_service import can_access_tenant_resource
from app.services.config_structure import default_config_document, normalize_config_document
from app.services.config_validation import get_config_validation_status


class ChannelConfigService:
    @staticmethod
    def _default_config_jsonb() -> dict[str, Any]:
        return default_config_document()

    @staticmethod
    def _default_user_types_jsonb() -> dict[str, Any]:
        return {
            "default_type": "new",
            "types": [
                {"key": "new", "color": "#d30d0d", "label": "Nuevo", "is_default": True},
                {"key": "interested", "color": "#26cfbb", "label": "Interesado", "is_default": False},
                {"key": "client", "color": "#e164f2", "label": "Cliente", "is_default": False},
            ],
        }

    @staticmethod
    def _default_settings_jsonb() -> dict[str, Any]:
        return {
            "max_bot_messages": 20,
            "max_bot_messages_message": "Te paso con un asesor para ayudarte mejor",
            "human_handoff_reset_hours": 24,
            "quota_exceeded_message": "Llegaste al limite de uso de IA por ahora. Intenta mas tarde.",
            "unsupported_content_message": (
                "Por el momento no puedo escuchar audios, ver fotos o archivos, queres que te pase con un asesor?"
            ),
        }

    @staticmethod
    def create_default_channel_config(
        db: Session,
        channel_id: uuid.UUID,
        *,
        commit: bool = False,
    ) -> ChannelBotConfig:
        repository = ChannelConfigRepository(db)
        existing = repository.get_active_by_channel_id(channel_id)
        if existing:
            return existing

        channel = repository.get_channel_by_id(channel_id)
        if channel is None:
            raise LookupError(f"Channel not found: {channel_id}")

        channel_config = ChannelBotConfig(
            tenant_id=channel.tenant_id,
            channel_id=channel.id,
            is_active=True,
            version=1,
            config_jsonb=ChannelConfigService._default_config_jsonb(),
            user_types_jsonb=ChannelConfigService._default_user_types_jsonb(),
            settings_jsonb=ChannelConfigService._default_settings_jsonb(),
        )
        repository.create(channel_config)
        repository.flush()
        if commit:
            repository.commit()
            repository.refresh(channel_config)
        return channel_config

    @staticmethod
    def get_active_channel_config(db: Session, channel_id: uuid.UUID) -> ChannelBotConfig:
        repository = ChannelConfigRepository(db)
        config = repository.get_active_by_channel_id(channel_id)
        if config:
            return config
        return ChannelConfigService.create_default_channel_config(db, channel_id, commit=True)

    @staticmethod
    def get_channel_config(db: Session, channel_id: uuid.UUID) -> ChannelBotConfig:
        return ChannelConfigService.get_active_channel_config(db, channel_id)

    @staticmethod
    def get_or_create_configs_for_channels(db: Session, channel_ids: list[uuid.UUID]) -> list[ChannelBotConfig]:
        return [ChannelConfigService.get_channel_config(db, channel_id) for channel_id in channel_ids]

    @staticmethod
    def get_channel_config_by_id_and_tenant(
        db: Session,
        config_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user: User | None = None,
    ) -> ChannelBotConfig:
        if user is not None and not can_access_tenant_resource(db, user, tenant_id):
            raise PermissionError("Tenant access denied")

        repository = ChannelConfigRepository(db)
        channel_config = repository.get_by_id_and_tenant(config_id=config_id, tenant_id=tenant_id)
        if channel_config is None:
            raise LookupError(f"Channel config not found: {config_id}")
        channel_config.config_jsonb = normalize_config_document(channel_config.config_jsonb)
        return channel_config

    @staticmethod
    def update_channel_config(
        db: Session,
        config_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: ChannelConfigUpdate,
        user: User | None = None,
    ) -> ChannelBotConfig:
        repository = ChannelConfigRepository(db)
        channel_config = ChannelConfigService.get_channel_config_by_id_and_tenant(
            db=db,
            config_id=config_id,
            tenant_id=tenant_id,
            user=user,
        )

        update_data = payload.model_dump(exclude_unset=True)
        requested_channel_ids = update_data.pop("channel_ids", None)

        target_configs: list[ChannelBotConfig] = [channel_config]
        if requested_channel_ids:
            existing_channel_ids = repository.get_existing_channel_ids_by_tenant(
                requested_channel_ids,
                tenant_id=tenant_id,
            )
            missing_ids = [str(channel_id) for channel_id in requested_channel_ids if channel_id not in existing_channel_ids]
            if missing_ids:
                raise LookupError(f"Channels not found: {', '.join(missing_ids)}")
            target_configs = ChannelConfigService.get_or_create_configs_for_channels(db, requested_channel_ids)

        for target_config in target_configs:
            if "config_jsonb" in update_data:
                target_config.config_jsonb = normalize_config_document(update_data["config_jsonb"])
            if "settings_jsonb" in update_data:
                target_config.settings_jsonb = update_data["settings_jsonb"]
            if "user_types_jsonb" in update_data:
                target_config.user_types_jsonb = update_data["user_types_jsonb"]
            if "is_active" in update_data:
                target_config.is_active = update_data["is_active"]

        try:
            repository.commit()
            repository.refresh(channel_config)
            return channel_config
        except Exception:
            repository.rollback()
            raise

    @staticmethod
    def get_channel_config_status(
        db: Session,
        config_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user: User | None = None,
    ) -> dict[str, Any]:
        channel_config = ChannelConfigService.get_channel_config_by_id_and_tenant(
            db=db,
            config_id=config_id,
            tenant_id=tenant_id,
            user=user,
        )
        return get_config_validation_status(channel_config.config_jsonb)
