from abc import ABC, abstractmethod

# Deprecated legacy interface.
# New code should use app.interfaces.ai.ai_interface.AIInterface.

class AIProvider(ABC):

    @abstractmethod
    def generate_response(self, conversation: dict, messages: list) -> str:
        pass
