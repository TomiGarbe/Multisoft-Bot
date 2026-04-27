"""
Procesador de mensajes inbound con integración de IA.

Responsable de orquestar el flujo completo:
1. Obtener/crear conversación
2. Obtener últimos mensajes (excluyendo el actual para evitar duplicación en prompt)
3. Obtener config del canal (channel_id → ChannelBotConfig → config_jsonb)
4. Obtener user_memory del contacto (Contact.metadata_jsonb)
5. Construir prompt
6. Llamar IA
7. Loggear (prompt + response, incluso en fallback)
8. Retornar respuesta (real o fallback)
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.repositories.ai.ai_log_repository import AILogRepository
from app.services.ai.ai_service import AIService
from app.services.ai.out_of_scope_detector import is_out_of_scope
from app.services.ai.prompt_builder import PromptBuilder
from app.services.bot_config_service import BotConfigService
import app.services.message_service as message_service
from app.services.conversation.guards import is_human_mode

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = "No pude procesar tu mensaje en este momento, ¿podés intentar nuevamente?"


class MessageProcessor:

    def __init__(self):
        self.ai_service = AIService()
        self.prompt_builder = PromptBuilder()
        self.ai_log_repository = AILogRepository()

    async def process_inbound_message(
        self,
        db: Session,
        message: Message,
        incoming_text: str,
    ) -> Optional[str]:
        try:
            # 1. Obtener conversación
            conversation = self._get_conversation(db, message.conversation_id)
            if not conversation:
                logger.error("Conversation not found: %s", message.conversation_id)
                return None

            # 2. Validar modo humano
            if is_human_mode({"id": str(conversation.id), "status": conversation.status}):
                logger.info("Human mode enabled for conversation: %s", conversation.id)
                return None

            # 3. Obtener últimos mensajes excluyendo el actual (evita duplicación en prompt)
            messages = self._get_messages(db, message.conversation_id, message.id)
            mapped_messages = self._map_messages(messages)

            # 4. Obtener config: channel_id → ChannelBotConfig (activo) → config_jsonb
            config = BotConfigService.get_active_channel_config(db, message.channel_id)
            if not config:
                logger.error("No active bot config found for channel: %s", message.channel_id)
                return None

            # 5. Fallback desde config["behavior"] si es dict, sino default
            behavior = config.get("behavior")
            fallback_message = (
                (behavior.get("fallback_message") if isinstance(behavior, dict) else None)
                or _DEFAULT_FALLBACK
            )

            # 6. Obtener datos del contacto: user_memory y user_type
            contact = self._get_contact(db, message.sender_contact_id)
            user_memory = self._extract_user_memory(contact)
            user_type = self._extract_user_type(contact)

            # 6.1. Límite de mensajes del bot
            bot_messages = sum(1 for m in mapped_messages if m["role"] == "assistant")
            channel_settings = config.get("settings", {})
            max_bot_messages = channel_settings.get("max_bot_messages", 999) if isinstance(channel_settings, dict) else 999

            if bot_messages >= max_bot_messages:
                logger.warning(
                    "Bot message limit (%d) reached for conversation: %s — flagging for human",
                    max_bot_messages,
                    conversation.id,
                )
                try:
                    conversation.status = "needs_human"
                    db.commit()
                except Exception:
                    logger.exception("Failed to flag conversation for human: %s", conversation.id)
                return fallback_message

            # 7. Construir prompt
            prompt = self.prompt_builder.build(
                config=config,
                messages=mapped_messages,
                user_memory=user_memory,
                current_message=incoming_text,
                user_type=user_type,
            )
            if not prompt:
                logger.warning("Empty prompt generated for conversation: %s", conversation.id)
                return None

            # 8. Llamar IA — si falla, response queda en None
            try:
                response = await self.ai_service.generate(prompt)
            except Exception:
                logger.exception("AI generation failed for conversation: %s", conversation.id)
                response = None

            # 8.1. Loggear siempre (incluso si response es None o fallback)
            try:
                await self.ai_log_repository.create_log(db, {
                    "tenant_id": message.tenant_id,
                    "channel_id": message.channel_id,
                    "contact_id": message.sender_contact_id,
                    "conversation_id": conversation.id,
                    "prompt": prompt,
                    "response": response,
                    "provider": "ollama",
                    "model": settings.OLLAMA_MODEL,
                })
            except Exception:
                logger.exception("Failed to save AI log for conversation: %s", conversation.id)

            # 8.2. Fallback si respuesta vacía o None
            if not response or not response.strip():
                logger.warning(
                    "Empty AI response for conversation: %s — using fallback",
                    conversation.id,
                )
                response = fallback_message

            # 8.3. Reemplazar respuesta fuera de scope
            elif is_out_of_scope(response):
                unsupported_message = (
                    channel_settings.get("unsupported_content_message")
                    if isinstance(channel_settings, dict)
                    else None
                ) or "No puedo ayudarte con eso."
                logger.warning(
                    "Out-of-scope AI response for conversation: %s — using unsupported_content_message",
                    conversation.id,
                )
                response = unsupported_message

            # 9. Actualizar user_type si el objetivo tiene on_completion
            self._apply_user_type_on_completion(db, contact, config)

            logger.info("Response ready for conversation: %s", conversation.id)
            return response

        except Exception:
            logger.exception(
                "Error processing inbound message for conversation: %s",
                message.conversation_id,
            )
            return None

    # ========== MÉTODOS PRIVADOS ==========

    def _get_conversation(self, db: Session, conversation_id: uuid.UUID) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def _get_messages(
        self,
        db: Session,
        conversation_id: uuid.UUID,
        exclude_id: uuid.UUID,
    ) -> list[dict]:
        """
        Devuelve los últimos 10 mensajes de la conversación, excluyendo el mensaje
        actual (ya guardado en DB) para evitar duplicación en el prompt.
        """
        messages = message_service.get_messages(db, conversation_id)
        messages = [m for m in messages if m["id"] != str(exclude_id)]
        return messages[-10:]

    def _map_messages(self, messages: list[dict]) -> list[dict]:
        """
        Mapea mensajes al formato de prompt_builder.

        sender_type="contact"         → role="user"
        sender_type="assistant"/"bot" → role="assistant"
        """
        mapped = []
        for msg in messages:
            sender_type = msg.get("sender_type", "").lower()
            content = msg.get("content", "").strip() if msg.get("content") else ""
            if not content:
                continue
            if sender_type == "contact":
                role = "user"
            elif sender_type in ("assistant", "bot"):
                role = "assistant"
            else:
                logger.warning("Unknown sender_type '%s' — skipping message", sender_type)
                continue
            mapped.append({"role": role, "content": content})
        return mapped

    def _get_contact(
        self,
        db: Session,
        contact_id: Optional[uuid.UUID],
    ) -> Optional[Contact]:
        if not contact_id:
            return None
        return db.query(Contact).filter(Contact.id == contact_id).first()

    def _extract_user_memory(self, contact: Optional[Contact]) -> Optional[dict]:
        if not contact or not isinstance(contact.metadata_jsonb, dict):
            return None
        return contact.metadata_jsonb or None

    def _extract_user_type(self, contact: Optional[Contact]) -> str:
        if not contact or not isinstance(contact.metadata_jsonb, dict):
            return "default"
        return contact.metadata_jsonb.get("user_type") or "default"

    def _apply_user_type_on_completion(
        self,
        db: Session,
        contact: Optional[Contact],
        config: dict,
    ) -> None:
        if not contact:
            return
        try:
            objective = config.get("objective", {})
            if not isinstance(objective, dict):
                return
            on_completion = objective.get("on_completion")
            if not on_completion:
                return
            metadata = contact.metadata_jsonb or {}
            metadata["user_type"] = on_completion
            contact.metadata_jsonb = metadata
            db.commit()
            logger.info(
                "Updated user_type to '%s' for contact: %s",
                on_completion,
                contact.id,
            )
        except Exception:
            logger.exception("Failed to update user_type for contact: %s", contact.id)
