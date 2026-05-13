from __future__ import annotations

from typing import Optional

from app.interfaces.media import MediaResolutionResult
from app.providers.media_resolvers.base import UrlLikeMediaResolver


class MultisoftMediaResolver(UrlLikeMediaResolver):
    source_name = "multisoft_media_resolver"

    def resolve(self, *, provider_media_id: str, metadata: dict) -> Optional[MediaResolutionResult]:
        provider_media_url = metadata.get("provider_media_url")
        if isinstance(provider_media_url, str) and provider_media_url.strip():
            return MediaResolutionResult(
                download_url=provider_media_url.strip(),
                source=self.source_name,
                metadata={"resolved_from": "metadata.provider_media_url"},
            )
        return super().resolve(provider_media_id=provider_media_id, metadata=metadata)

