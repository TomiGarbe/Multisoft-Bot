from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class MediaResolutionResult:
    download_url: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MediaResolver(ABC):
    @abstractmethod
    def resolve(self, *, provider_media_id: str, metadata: dict[str, Any]) -> Optional[MediaResolutionResult]:
        pass

