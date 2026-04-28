from typing import Union


def is_human_mode(conversation: Union[object, dict]) -> bool:
    """Returns True if the conversation is in human mode (AI should not respond)."""
    if isinstance(conversation, dict):
        return conversation.get("mode") == "human"
    return getattr(conversation, "mode", "ai") == "human"
