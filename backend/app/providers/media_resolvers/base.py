from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

from app.interfaces.media import MediaResolutionResult, MediaResolver

logger = logging.getLogger(__name__)


class UrlLikeMediaResolver(MediaResolver):
    source_name = "provider_media_id_url"

    def resolve(self, *, provider_media_id: str, metadata: dict) -> Optional[MediaResolutionResult]:
        if self._is_valid_url(provider_media_id):
            logger.warning(
                "[MULTIMEDIA][RESOLVER] provider_media_id_resolved resolver=%s strategy=id_as_url",
                self.__class__.__name__,
            )
            return MediaResolutionResult(download_url=provider_media_id, source=self.source_name)
        logger.warning(
            "[MULTIMEDIA][RESOLVER] provider_media_id_unresolved resolver=%s",
            self.__class__.__name__,
        )
        return None

    @staticmethod
    def _is_valid_url(value: str) -> bool:
        try:
            parsed = urlparse(value)
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        except Exception:
            return False
