from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from app.interfaces.media import MediaResolutionResult, MediaResolver


class UrlLikeMediaResolver(MediaResolver):
    source_name = "provider_media_id_url"

    def resolve(self, *, provider_media_id: str, metadata: dict) -> Optional[MediaResolutionResult]:
        if self._is_valid_url(provider_media_id):
            return MediaResolutionResult(download_url=provider_media_id, source=self.source_name)
        return None

    @staticmethod
    def _is_valid_url(value: str) -> bool:
        try:
            parsed = urlparse(value)
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        except Exception:
            return False

