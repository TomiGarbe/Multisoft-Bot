from abc import ABC, abstractmethod


class MessageProvider(ABC):

    @abstractmethod
    def send_text(self, channel: str, to: str, content: str) -> None:
        pass

    @abstractmethod
    def send_media(self, channel: str, to: str, media_url: str, caption: str = None) -> None:
        pass

    @abstractmethod
    def reply_to_message(self, channel: str, to: str, content: str, reply_to_id: str) -> None:
        pass
