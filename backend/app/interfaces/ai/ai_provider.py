from abc import ABC, abstractmethod


class AIProvider(ABC):

    @abstractmethod
    def generate_response(self, conversation: dict, messages: list) -> str:
        pass
