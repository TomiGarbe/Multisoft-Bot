from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCatalogEntry:
    value: str
    label: str


MESSAGE_PROVIDER_CATALOG: tuple[ProviderCatalogEntry, ...] = (
    ProviderCatalogEntry(value="multisoft", label="Multisoft"),
    ProviderCatalogEntry(value="web", label="Webchat"),
)

MESSAGE_PROVIDER_VALUES: set[str] = {entry.value for entry in MESSAGE_PROVIDER_CATALOG}

# Backward-compat aliases for existing data.
MESSAGE_PROVIDER_ALIASES: dict[str, str] = {
    "evolution": "multisoft",
    "meta": "multisoft",
    "twilio": "multisoft",
    "internal": "web",
}

# Which providers are valid per channel type.
CHANNEL_TYPE_PROVIDER_MAP: dict[str, set[str]] = {
    "whatsapp": {"multisoft"},
    "web": {"web"},
    "instagram": {"multisoft"},
}


def normalize_provider_value(provider: str | None) -> str:
    normalized = (provider or "").strip().lower()
    if not normalized:
        return ""
    return MESSAGE_PROVIDER_ALIASES.get(normalized, normalized)


def is_supported_provider_for_channel_type(channel_type: str, provider: str) -> bool:
    normalized_type = (channel_type or "").strip().lower()
    allowed = CHANNEL_TYPE_PROVIDER_MAP.get(normalized_type, set())
    return provider in allowed

