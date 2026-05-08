from abc import ABC, abstractmethod
from typing import Any, Optional

from app.schemas.internal.normalized_message import NormalizedMessage

class MessageProvider(ABC):
    @abstractmethod
    def normalize_incoming_payload(self, channel_id: str, payload: dict[str, Any]) -> NormalizedMessage:
        pass

    @abstractmethod
    def send_text(
        self,
        channel: str,
        to: str,
        content: str,
        *,
        reply_to_message_id: Optional[str] = None,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        pass

    @abstractmethod
    def send_media(
        self,
        channel: str,
        to: str,
        media_url: str,
        caption: str = None,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        pass

    @abstractmethod
    def reply_to_message(
        self,
        channel: str,
        to: str,
        content: str,
        reply_to_id: str,
        *,
        channel_external_id: Optional[str] = None,
        channel_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        pass
