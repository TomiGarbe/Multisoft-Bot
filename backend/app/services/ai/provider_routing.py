from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings

_SUPPORTED_PROVIDERS = {"ollama", "deepseek", "mock"}


@dataclass(frozen=True)
class AIProviderCapabilities:
    supports_vision: bool
    supports_streaming: bool
    supports_tools: bool


@dataclass(frozen=True)
class AIProviderRoute:
    provider: str
    model: str
    timeout_seconds: float | None
    capabilities: AIProviderCapabilities


def resolve_provider_route(channel_settings: dict[str, Any] | None = None) -> AIProviderRoute:
    settings_jsonb = channel_settings if isinstance(channel_settings, dict) else {}
    provider_candidate = str(settings_jsonb.get("ai_provider") or settings.AI_PROVIDER or "ollama").strip().lower()
    if provider_candidate not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported AI provider: {provider_candidate}. "
            f"Supported providers: {', '.join(sorted(_SUPPORTED_PROVIDERS))}"
        )

    if provider_candidate == "deepseek":
        model = str(settings_jsonb.get("ai_model") or settings.DEEPSEEK_MODEL).strip() or settings.DEEPSEEK_MODEL
        normalized_model = model.lower()
        supports_vision = any(token in normalized_model for token in ("vl", "vision", "v4"))
        return AIProviderRoute(
            provider="deepseek",
            model=model,
            timeout_seconds=settings.DEEPSEEK_TIMEOUT_SECONDS,
            capabilities=AIProviderCapabilities(
                supports_vision=supports_vision,
                supports_streaming=False,
                supports_tools=True,
            ),
        )

    if provider_candidate == "mock":
        return AIProviderRoute(
            provider="mock",
            model="mock",
            timeout_seconds=None,
            capabilities=AIProviderCapabilities(
                supports_vision=False,
                supports_streaming=False,
                supports_tools=False,
            ),
        )

    model = str(settings_jsonb.get("ai_model") or settings.OLLAMA_MODEL).strip() or settings.OLLAMA_MODEL
    normalized_model = model.lower()
    supports_vision = any(token in normalized_model for token in ("vision", "vl", "llava", "qwen2.5vl", "gemma3"))
    return AIProviderRoute(
        provider="ollama",
        model=model,
        timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
        capabilities=AIProviderCapabilities(
            supports_vision=supports_vision,
            supports_streaming=False,
            supports_tools=True,
        ),
    )
