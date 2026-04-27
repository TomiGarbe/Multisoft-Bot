"""
Bot Configuration Service

Handles retrieval of active bot configuration per channel.
Configuration flow: channel_id → ChannelBotConfig (active) → config_jsonb
"""

from typing import Optional, Any
import uuid
from sqlalchemy.orm import Session
from app.models.config import ChannelBotConfig


class BotConfigService:
    """Service for retrieving active bot configurations by channel."""

    @staticmethod
    def get_active_channel_config(
        db: Session,
        channel_id: uuid.UUID,
    ) -> Optional[dict]:
        """
        Get the active bot configuration for a channel.
        
        Args:
            db: Database session
            channel_id: Channel ID to get config for
            
        Returns:
            The config_jsonb dict if active config exists, None otherwise
            
        Raises:
            ValueError: If channel_id is invalid or no active config found
        """
        config = db.query(ChannelBotConfig).filter(
            ChannelBotConfig.channel_id == channel_id,
            ChannelBotConfig.is_active == True,
        ).order_by(
            ChannelBotConfig.version.desc()
        ).first()
        
        if not config:
            return None
            
        return config.config_jsonb

    @staticmethod
    def get_active_channel_config_with_entity(
        db: Session,
        channel_id: uuid.UUID,
    ) -> Optional[ChannelBotConfig]:
        """
        Get the active ChannelBotConfig entity for a channel.
        
        Useful when you need access to metadata (version, created_by, etc.)
        
        Args:
            db: Database session
            channel_id: Channel ID to get config for
            
        Returns:
            The ChannelBotConfig entity if active config exists, None otherwise
        """
        return db.query(ChannelBotConfig).filter(
            ChannelBotConfig.channel_id == channel_id,
            ChannelBotConfig.is_active == True,
        ).order_by(
            ChannelBotConfig.version.desc()
        ).first()

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

    @staticmethod
    def get_config_or_none(
        db: Session,
        channel_id: uuid.UUID,
    ) -> Optional[dict]:
        """
        Get active channel config or None if not found.
        
        Does NOT apply defaults - returns raw config_jsonb or None.
        This is the primary method for config retrieval.
        
        Args:
            db: Database session
            channel_id: Channel ID
            
        Returns:
            config_jsonb dict or None
        """
        return BotConfigService.get_active_channel_config(db, channel_id)
