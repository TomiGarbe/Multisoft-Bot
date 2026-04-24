from app.providers.provider_factory import get_ai_provider
from app.services.conversation.guards import is_human_mode


def process_message(conversation: dict, messages: list) -> str | None:
    if is_human_mode(conversation):
        return None

    ai = get_ai_provider()
    response = ai.generate_response(conversation, messages)
    return response
