from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.channel_config_repository import ChannelConfigRepository
from app.repositories import tenant_repository
from app.schemas.internal.message_enums import MediaProcessingCapability


@dataclass(frozen=True)
class MediaCapabilityDecision:
    enabled: bool
    reason: str | None = None


class MediaProcessingFeatureService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.channel_config_repository = ChannelConfigRepository(db)

    def is_capability_enabled(
        self,
        *,
        tenant_id,
        channel_id,
        capability: MediaProcessingCapability,
    ) -> MediaCapabilityDecision:
        if not self._env_enabled(capability):
            return MediaCapabilityDecision(enabled=False, reason="disabled_by_environment")

        tenant = tenant_repository.get_by_id(self.db, tenant_id)
        if tenant and not self._tenant_enabled(tenant.features_jsonb, capability):
            return MediaCapabilityDecision(enabled=False, reason="disabled_by_tenant")

        if channel_id is not None:
            channel_cfg = self._get_active_channel_config(channel_id)
            if channel_cfg is not None and not self._channel_enabled(channel_cfg.settings_jsonb, capability):
                return MediaCapabilityDecision(enabled=False, reason="disabled_by_channel")

        return MediaCapabilityDecision(enabled=True)

    def _get_active_channel_config(self, channel_id):
        return self.channel_config_repository.get_active_by_channel_id(channel_id)

    def _env_enabled(self, capability: MediaProcessingCapability) -> bool:
        mapping = {
            MediaProcessingCapability.TRANSCRIPTION: settings.MEDIA_TRANSCRIPTION_ENABLED,
            MediaProcessingCapability.OCR: settings.MEDIA_OCR_ENABLED,
            MediaProcessingCapability.DOCUMENT_EXTRACTION: settings.MEDIA_DOCUMENT_EXTRACTION_ENABLED,
        }
        return mapping.get(capability, True)

    def _tenant_enabled(self, features_jsonb: Any, capability: MediaProcessingCapability) -> bool:
        if not isinstance(features_jsonb, dict):
            return True
        media = features_jsonb.get("media_processing")
        if not isinstance(media, dict):
            return True
        return self._read_capability_flag(media, capability)

    def _channel_enabled(self, settings_jsonb: Any, capability: MediaProcessingCapability) -> bool:
        if not isinstance(settings_jsonb, dict):
            return True
        media = settings_jsonb.get("media_processing")
        if not isinstance(media, dict):
            return True
        return self._read_capability_flag(media, capability)

    @staticmethod
    def _read_capability_flag(container: dict[str, Any], capability: MediaProcessingCapability) -> bool:
        mapping = {
            MediaProcessingCapability.TRANSCRIPTION: "transcription_enabled",
            MediaProcessingCapability.OCR: "ocr_enabled",
            MediaProcessingCapability.DOCUMENT_EXTRACTION: "document_extraction_enabled",
        }
        key = mapping.get(capability)
        if key is None:
            return True
        value = container.get(key)
        if value is None:
            return True
        return bool(value)
