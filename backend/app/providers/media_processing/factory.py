from __future__ import annotations

from app.interfaces.media import MediaProcessingProvider
from app.providers.media_processing.local_provider import LocalMediaProcessingProvider


def get_media_processing_provider(provider_name: str | None = None) -> MediaProcessingProvider:
    _ = provider_name
    return LocalMediaProcessingProvider()
