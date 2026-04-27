"""
Config Resolver

Resuelve la configuración final para el PromptBuilder según el tipo de usuario.
No accede a DB, no llama servicios externos, no muta el config original.
"""

BASE_KEYS = ("identity", "tone", "rules", "objectives", "data_collection")


def get_sections_by_type(config: dict, user_type: str) -> dict:
    """
    Combina la base config con los overrides del tipo de usuario.

    Args:
        config: Config completa del canal (config_jsonb). Debe contener las keys
                base (identity, tone, rules, objectives, data_collection) y
                opcionalmente "user_type_config" con overrides por tipo.
        user_type: Tipo del usuario actual (e.g. "premium", "guest"). Si no existe
                   en user_type_config se usa "default".

    Returns:
        Nuevo dict con base config + overrides aplicados, listo para PromptBuilder.
        Las keys de type_config pisan las de base config.
    """
    base = {k: config[k] for k in BASE_KEYS if k in config}

    user_types = config.get("user_type_config", {})
    type_config = user_types.get(user_type) or user_types.get("default") or {}

    return {**base, **type_config}
