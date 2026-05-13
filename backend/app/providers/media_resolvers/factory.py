from __future__ import annotations

from app.interfaces.media import MediaResolver
from app.providers.media_resolvers.mock_resolver import MockMediaResolver
from app.providers.media_resolvers.multisoft_resolver import MultisoftMediaResolver
from app.providers.media_resolvers.web_resolver import WebMediaResolver


def get_media_resolver(provider_name: str | None) -> MediaResolver:
    normalized = (provider_name or "").strip().lower()
    if normalized == "multisoft":
        return MultisoftMediaResolver()
    if normalized == "web":
        return WebMediaResolver()
    if normalized == "mock":
        return MockMediaResolver()
    return UrlFallbackMediaResolver()


class UrlFallbackMediaResolver(WebMediaResolver):
    source_name = "generic_url_media_resolver"

