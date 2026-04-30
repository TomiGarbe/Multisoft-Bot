"""
Bot Configuration Service

Handles retrieval of active bot configuration per channel.
Configuration flow: channel_id → ChannelBotConfig (active) → config_jsonb
"""

from typing import Any
import uuid
from sqlalchemy.orm import Session
from app.models.config import ChannelBotConfig
from app.models.channel import Channel


class BotConfigService:
    """Service for retrieving active bot configurations by channel."""

    @staticmethod
    def _default_config_jsonb() -> dict[str, Any]:
        return {
            "identity": {
                "role": "assistant",
                "description": "",
                "industry": "",
                "language": "",
            },
            "tone": {
                "tone": "neutral",
                "style_rules": [],
            },
            "rules": {"rules": []},
            "behavior": {},
            "objectives": [],
            "data_collection": [],
            "actions": [],
            "user_type_config": {},
        }

    @staticmethod
    def _default_user_types_jsonb() -> dict[str, Any]:
        return {
            "default_type": "new",
            "types": [
                {
                "key": "new",
                "color": "#d30d0d",
                "label": "Nuevo",
                "is_default": True
                },
                {
                "key": "interested",
                "color": "#26cfbb",
                "label": "Interesado",
                "is_default": False
                },
                {
                "key": "client",
                "color": "#e164f2",
                "label": "Cliente",
                "is_default": False
                }
            ]
        }

    @staticmethod
    def _default_settings_jsonb() -> dict[str, Any]:
        return {
            "max_bot_messages": 20,
            "max_bot_messages_message": "Te paso con un asesor para ayudarte mejor 🙌",
            "human_handoff_reset_hours": 24,
            "unsupported_content_message": "Por el momento no puedo escuchar audios, ver fotos o archivos, queres que te pase con un asesor? 😊"
        }

    @staticmethod
    def create_default_channel_config(
        db: Session,
        channel_id: uuid.UUID,
        *,
        commit: bool = False,
    ) -> ChannelBotConfig:
        """
        Ensure there is an active configuration for the given channel.

        Returns the existing active config if present; otherwise creates a default one.
        """
        existing = db.query(ChannelBotConfig).filter(
            ChannelBotConfig.channel_id == channel_id,
            ChannelBotConfig.is_active == True,
        ).order_by(
            ChannelBotConfig.version.desc()
        ).first()
        if existing:
            return existing

        channel = db.get(Channel, channel_id)
        if not channel:
            raise LookupError(f"Channel not found: {channel_id}")

        channel_config = ChannelBotConfig(
            tenant_id=channel.tenant_id,
            channel_id=channel.id,
            is_active=True,
            version=1,
            config_jsonb=BotConfigService._default_config_jsonb(),
            user_types_jsonb=BotConfigService._default_user_types_jsonb(),
            settings_jsonb=BotConfigService._default_settings_jsonb(),
        )
        db.add(channel_config)
        db.flush()
        if commit:
            db.commit()
            db.refresh(channel_config)
        return channel_config

    @staticmethod
    def get_active_channel_config(
        db: Session,
        channel_id: uuid.UUID,
    ) -> ChannelBotConfig:
        """
        Get the active bot configuration for a channel.
        
        Args:
            db: Database session
            channel_id: Channel ID to get config for
            
        Returns:
            The active ChannelBotConfig entity.
        """
        config = db.query(ChannelBotConfig).filter(
            ChannelBotConfig.channel_id == channel_id,
            ChannelBotConfig.is_active == True,
        ).order_by(
            ChannelBotConfig.version.desc()
        ).first()
        if config:
            return config
        return BotConfigService.create_default_channel_config(db, channel_id, commit=True)

    @staticmethod
    def get_channel_config(
        db: Session,
        channel_id: uuid.UUID,
    ) -> ChannelBotConfig:
        """Alias with fail-safe semantics: never returns null."""
        return BotConfigService.get_active_channel_config(db, channel_id)

    @staticmethod
    def validate_config_structure(config: dict) -> bool:
        """
        Validate that config has the expected structure for PromptBuilder.
        
        Expected keys:
        - identity: str (bot description)
        - tone: str (communication style)
        - rules: list[str] (behavioral rules)
        - conversation: dict (conversation settings)
        - objectives: list[str] (bot goals)
        - data_collection: dict (data handling policies)
        - actions: list (supported actions)
        - user_type_config: dict (user type specific config)
        
        Args:
            config: Configuration dict to validate
            
        Returns:
            True if config has required structure, False otherwise
        """
        if not isinstance(config, dict):
            return False
            
        required_keys = {
            "identity",
            "tone", 
            "rules",
            "conversation",
            "objectives",
            "data_collection",
            "actions",
            "user_type_config",
        }
        
        # Check if all required keys exist and have correct types
        if not all(key in config for key in required_keys):
            return False
            
        # Type validation
        if not isinstance(config.get("identity"), str):
            return False
        if not isinstance(config.get("tone"), str):
            return False
        if not isinstance(config.get("rules"), list):
            return False
        if not isinstance(config.get("conversation"), dict):
            return False
        if not isinstance(config.get("objectives"), list):
            return False
        if not isinstance(config.get("data_collection"), dict):
            return False
        if not isinstance(config.get("actions"), list):
            return False
        if not isinstance(config.get("user_type_config"), dict):
            return False
        return True
