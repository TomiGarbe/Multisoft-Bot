"""
AI response builder.

Responsibilities (called by handle_incoming_message after the AI gate has passed):
1. Build prompt and call AI
2. Log the AI interaction (always)
3. Apply fallback / out-of-scope / message-limit rules to the response
4. Track ContactUsage and switch to human mode when the bot limit is reached
5. Apply on_completion to the contact's user_type

This module does NOT save messages or talk to channels; that orchestration
lives in `incoming_message_handler.handle_incoming_message`.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.metrics import ContactUsage
from app.repositories.ai.ai_log_repository import AILogRepository
from app.services.ai.ai_service import AIService
from app.services.ai.out_of_scope_detector import is_out_of_scope
from app.services.ai.prompt_builder import PromptBuilder
from app.services.conversation.context_builder import (
    apply_user_type_on_completion,
    build_conversation_context,
)
from app.services.conversation.guards import should_use_ai
from app.services.conversation.mode_service import disable_ai

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = "No pude procesar tu mensaje en este momento, podes intentar nuevamente?"


class MessageProcessor:

    def __init__(self):
        self.ai_service = AIService()
        self.prompt_builder = PromptBuilder()
        self.ai_log_repository = AILogRepository()

    def build_prompt(self, config: dict, context: dict) -> str:
        return self.prompt_builder.build_prompt(config=config, context=context)

    def build_prompt_for_conversation(
        self,
        db: Session,
        conversation: Conversation,
        channel_config,
        current_message,
    ) -> Optional[str]:
        config = channel_config.config_jsonb or {}
        context = build_conversation_context(db, conversation, current_message, config)
        prompt = self.build_prompt(config, context)
        if not prompt:
            logger.warning("Empty prompt for conversation: %s", conversation.id)
            return None
        return prompt

    async def call_ai(self, prompt: str) -> Optional[str]:
        """Send prompt to provider and return only response text."""
        return await self.ai_service.generate(prompt)

    async def generate_response(
        self,
        db: Session,
        conversation: Conversation,
        channel_config,
        prompt: str,
        contact_id: Optional[uuid.UUID],
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> Optional[str]:
        """Run AI, log it, and apply fallback / out-of-scope / limit rules."""
        config = channel_config.config_jsonb or {}
        channel_settings = channel_config.settings_jsonb or {}

        behavior = config.get("behavior")
        fallback_message = (
            (behavior.get("fallback_message") if isinstance(behavior, dict) else None)
            or _DEFAULT_FALLBACK
        )

        response = None
        if should_use_ai(conversation, channel_config):
            try:
                response = await self.call_ai(prompt)
            except Exception:
                logger.exception("AI generation failed for conversation: %s", conversation.id)
        else:
            logger.info("AI gate blocked execution for conversation: %s", conversation.id)

        await self._log_interaction(
            db,
            tenant_id=tenant_id,
            channel_id=channel_id,
            contact_id=contact_id,
            conversation_id=conversation.id,
            prompt=prompt,
            response=response,
        )

        if not response or not response.strip():
            logger.warning("Empty AI response for conversation: %s - using fallback", conversation.id)
            response = fallback_message
        elif is_out_of_scope(response):
            unsupported = (
                channel_settings.get("unsupported_content_message")
                if isinstance(channel_settings, dict)
                else None
            ) or "No puedo ayudarte con eso."
            logger.warning("Out-of-scope response for conversation: %s", conversation.id)
            response = unsupported

        usage = self._get_or_create_usage(db, contact_id, conversation.id)
        if usage is not None:
            try:
                usage.bot_message_count += 1
                db.commit()
            except Exception:
                logger.exception("Failed to increment bot_message_count for conversation: %s", conversation.id)
                db.rollback()

        max_messages = 999
        limit_message = None
        if isinstance(channel_settings, dict):
            max_messages = channel_settings.get("max_bot_messages", 999)
            limit_message = channel_settings.get("max_bot_messages_message")

        if usage is not None and usage.bot_message_count >= max_messages:
            logger.warning(
                "Bot message limit (%d) reached for conversation: %s - switching to human mode",
                max_messages, conversation.id,
            )
            response = limit_message or fallback_message
            try:
                disable_ai(db, conversation)
            except Exception:
                logger.exception("Failed to set human mode for conversation: %s", conversation.id)
                db.rollback()

        apply_user_type_on_completion(db, contact_id, config)

        logger.info("Response ready for conversation: %s", conversation.id)
        return response

    async def _log_interaction(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        contact_id: Optional[uuid.UUID],
        conversation_id: uuid.UUID,
        prompt: str,
        response: Optional[str],
    ) -> None:
        try:
            await self.ai_log_repository.create_log(db, {
                "tenant_id": tenant_id,
                "channel_id": channel_id,
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "prompt": prompt,
                "response": response,
                "provider": "ollama",
                "model": settings.OLLAMA_MODEL,
            })
        except Exception:
            logger.exception("Failed to save AI log for conversation: %s", conversation_id)

    def _get_or_create_usage(
        self,
        db: Session,
        contact_id: Optional[uuid.UUID],
        conversation_id: uuid.UUID,
    ) -> Optional[ContactUsage]:
        if not contact_id:
            return None
        usage = db.query(ContactUsage).filter(
            ContactUsage.conversation_id == conversation_id,
        ).first()
        if usage:
            return usage
        usage = ContactUsage(
            contact_id=contact_id,
            conversation_id=conversation_id,
            bot_message_count=0,
        )
        db.add(usage)
        try:
            db.commit()
            db.refresh(usage)
        except Exception:
            logger.exception("Failed to create ContactUsage for conversation: %s", conversation_id)
            db.rollback()
            return None
        return usage
