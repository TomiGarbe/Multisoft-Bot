from typing import Any, Union

from app.services.config_validation import get_config_validation_status


def is_human_mode(conversation: Union[object, dict]) -> bool:
    """Returns True if the conversation is in human mode (AI should not respond)."""
    if isinstance(conversation, dict):
        return conversation.get("mode") == "human"
    return getattr(conversation, "mode", "ai") == "human"


def is_config_valid(channel_config: Any) -> bool:
    """
    Valida que la config tenga los campos minimos para ejecutar la IA.
    La fuente de verdad es get_config_validation_status().
    """
    if channel_config is None:
        return False

    config = _get_field(channel_config, "config_jsonb")
    status = get_config_validation_status(config)
    return bool(status.get("is_valid"))


def should_use_ai(conversation: Any, channel_config: Any) -> bool:
    """
    Decide si la IA debe ejecutarse para esta conversacion.
    Retorna True solo si la conversacion esta en modo "ai" y la config es valida.
    """
    if _get_field(conversation, "mode") != "ai":
        return False

    return is_config_valid(channel_config)


def _get_field(source: Any, key: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)
