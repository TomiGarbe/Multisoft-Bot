"""
Procesador de mensajes inbound con integración de IA.

Flujo completo:
1.  Obtener conversación
2.  Verificar modo (ai/human) — si es "human", salir sin responder
3.  Obtener últimos 15 mensajes (excluyendo el actual)
4.  Obtener ChannelBotConfig (config_jsonb + settings_jsonb)
5.  Resolver user_type desde Contact.current_type
6.  Obtener/sincronizar ContactUsage para la conversación activa
7.  Construir prompt y llamar IA
8.  Incrementar bot_message_count en ContactUsage
9.  Verificar límite: si se alcanzó → respuesta = limit_message, mode = "human"
10. Loggear interacción
11. Aplicar on_completion en contact.current_type
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.models.metrics import ContactUsage
from app.repositories.ai.ai_log_repository import AILogRepository
from app.services.ai.ai_service import AIService
from app.services.ai.out_of_scope_detector import is_out_of_scope
from app.services.ai.prompt_builder import PromptBuilder
from app.services.bot_config_service import BotConfigService
import app.services.message_service as message_service

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

            # 2. Verificar modo — si es "human", la IA no responde
            if conversation.mode == "human":
                logger.info("Human mode active for conversation: %s", conversation.id)
                return None

            # 3. Obtener últimos 15 mensajes excluyendo el actual
            messages = self._get_messages(db, message.conversation_id, message.id)
            mapped_messages = self._map_messages(messages)

            # 4. Obtener config del canal (entidad completa para acceder a settings_jsonb)
            channel_config = BotConfigService.get_active_channel_config_with_entity(
                db, message.channel_id
            )
            if not channel_config:
                logger.error("No active bot config found for channel: %s", message.channel_id)
                return None

            config = channel_config.config_jsonb or {}
            channel_settings = channel_config.settings_jsonb or {}

            # Mensaje de fallback desde behavior
            behavior = config.get("behavior")
            fallback_message = (
                (behavior.get("fallback_message") if isinstance(behavior, dict) else None)
                or _DEFAULT_FALLBACK
            )

            # 5. Obtener contacto y resolver user_type
            contact = self._get_contact(db, message.sender_contact_id)
            default_type = self._resolve_default_type(config)
            self._ensure_contact_type(db, contact, default_type)
            user_type = self._get_valid_contact_type(contact, config, default_type)
            user_memory = self._extract_user_memory(contact)

            # 6. Obtener/sincronizar ContactUsage para esta conversación
            usage = self._get_or_create_usage(db, message.sender_contact_id, conversation.id)

            # 7. Construir prompt y llamar IA
            prompt = self.prompt_builder.build(
                config=config,
                messages=mapped_messages,
                user_memory=user_memory,
                current_message=incoming_text,
                user_type=user_type,
            )
            if not prompt:
                logger.warning("Empty prompt for conversation: %s", conversation.id)
                return None

            try:
                response = await self.ai_service.generate(prompt)
            except Exception:
                logger.exception("AI generation failed for conversation: %s", conversation.id)
                response = None

            # 10. Loggear siempre (incluso si falla)
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

            # Aplicar fallback y out-of-scope
            if not response or not response.strip():
                logger.warning("Empty AI response for conversation: %s — using fallback", conversation.id)
                response = fallback_message
            elif is_out_of_scope(response):
                unsupported = (
                    channel_settings.get("unsupported_content_message")
                    if isinstance(channel_settings, dict)
                    else None
                ) or "No puedo ayudarte con eso."
                logger.warning("Out-of-scope response for conversation: %s", conversation.id)
                response = unsupported

            # 8. Incrementar contador de mensajes del bot
            if usage is not None:
                try:
                    usage.bot_message_count += 1
                    db.commit()
                except Exception:
                    logger.exception("Failed to increment bot_message_count for conversation: %s", conversation.id)
                    db.rollback()

            # 9. Verificar límite de mensajes
            if isinstance(channel_settings, dict):
                max_messages = channel_settings.get("max_bot_messages", 999)
                limit_message = channel_settings.get("max_bot_messages_message")
            else:
                max_messages = 999
                limit_message = None

            if usage is not None and usage.bot_message_count >= max_messages:
                logger.warning(
                    "Bot message limit (%d) reached for conversation: %s — switching to human mode",
                    max_messages,
                    conversation.id,
                )
                response = limit_message or fallback_message
                try:
                    conversation.mode = "human"
                    db.commit()
                except Exception:
                    logger.exception("Failed to set human mode for conversation: %s", conversation.id)
                    db.rollback()

            # 11. Actualizar contact.current_type si el objetivo define on_completion
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
        """Devuelve los últimos 15 mensajes, excluyendo el actual para evitar duplicación."""
        messages = message_service.get_messages(db, conversation_id)
        messages = [m for m in messages if m["id"] != str(exclude_id)]
        return messages[-15:]

    def _map_messages(self, messages: list[dict]) -> list[dict]:
        """Mapea sender_type contact→user / assistant|bot→assistant."""
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

    def _get_or_create_usage(
        self,
        db: Session,
        contact_id: Optional[uuid.UUID],
        conversation_id: uuid.UUID,
    ) -> Optional[ContactUsage]:
        """Obtiene el ContactUsage de la conversación activa, o lo crea si no existe."""
        if not contact_id:
            return None
        usage = db.query(ContactUsage).filter(
            ContactUsage.conversation_id == conversation_id
        ).first()
        if not usage:
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

    def _resolve_default_type(self, config: dict) -> str:
        default_type = config.get("default_type")
        if default_type:
            return default_type
        user_types = config.get("user_type_config", {})
        if isinstance(user_types, dict):
            for type_name, type_config in user_types.items():
                if isinstance(type_config, dict) and type_config.get("is_default"):
                    return type_name
        return "default"

    def _ensure_contact_type(
        self,
        db: Session,
        contact: Optional[Contact],
        default_type: str,
    ) -> None:
        if not contact or contact.current_type is not None:
            return
        try:
            contact.current_type = default_type
            db.commit()
            logger.info("Assigned initial current_type '%s' to contact: %s", default_type, contact.id)
        except Exception:
            logger.exception("Failed to set initial current_type for contact: %s", contact.id)

    def _get_valid_contact_type(
        self,
        contact: Optional[Contact],
        config: dict,
        default_type: str,
    ) -> str:
        if not contact:
            return default_type
        current = contact.current_type or default_type
        user_types = config.get("user_type_config", {})
        if isinstance(user_types, dict) and user_types and current not in user_types:
            logger.warning(
                "Contact type '%s' not in config — using default '%s' for contact: %s",
                current, default_type, contact.id,
            )
            return default_type
        return current

    def _extract_user_memory(self, contact: Optional[Contact]) -> Optional[dict]:
        if not contact or not isinstance(contact.metadata_jsonb, dict):
            return None
        return contact.metadata_jsonb or None

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
            contact.current_type = on_completion
            db.commit()
            logger.info("Updated current_type to '%s' for contact: %s", on_completion, contact.id)
        except Exception:
            logger.exception("Failed to update current_type for contact: %s", contact.id)
