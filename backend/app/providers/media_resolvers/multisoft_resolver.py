from __future__ import annotations

import logging
from typing import Optional

from app.interfaces.media import MediaResolutionResult
from app.providers.media_resolvers.base import UrlLikeMediaResolver

logger = logging.getLogger(__name__)


class MultisoftMediaResolver(UrlLikeMediaResolver):
    source_name = "multisoft_media_resolver"

    def resolve(self, *, provider_media_id: str, metadata: dict) -> Optional[MediaResolutionResult]:
        provider_media_url = metadata.get("provider_media_url")
        if isinstance(provider_media_url, str) and provider_media_url.strip():
            logger.warning(
                "[MULTIMEDIA][RESOLVER] provider_media_id_resolved resolver=%s strategy=metadata_provider_media_url",
                self.__class__.__name__,
            )
            return MediaResolutionResult(
                download_url=provider_media_url.strip(),
                source=self.source_name,
                metadata={"resolved_from": "metadata.provider_media_url"},
            )
        return super().resolve(provider_media_id=provider_media_id, metadata=metadata)
