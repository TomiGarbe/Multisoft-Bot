"""
Único punto de entrada para mensajes entrantes (cualquier canal).

Flujo (orden estricto, sin saltos):
    1. is_bot         → si es eco del propio bot, cortar
    2. conversation   → get_or_create
    3. inbound save   → SIEMPRE (dedup por provider_message_id)
    4. config         → resolver del canal
    5. AI gate        → should_use_ai(conv, config)
    6. context        → últimos 15 + user_type + memoria
    7. prompt         → PromptBuilder
    8. AI             → AIService.generate_for_conversation
    9. outbound save  → SIEMPRE antes de despachar
   10. dispatch       → enviar al canal vía provider

No hay otro punto que orqueste estos pasos: cualquier otro flujo (HTTP, webhook,
test) debe entrar por aquí para garantizar consistencia y trazabilidad.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.channel_config_service import ChannelConfigService
from app.services.conversation.guards import should_use_ai
from app.services.inbound.message_processor import MessageProcessor
import app.services.message_service as message_service

logger = logging.getLogger(__name__)

_processor = MessageProcessor()


async def handle_incoming_message(db: Session, message: NormalizedMessage, tenant_id: uuid.UUID) -> None:
    # 1. Cortar si el mensaje proviene del propio bot (echo).
    if message.is_bot:
        logger.info("Skipping bot echo: channel=%s id=%s", message.channel_id, message.external_message_id)
        return

    # 2. Obtener o crear la conversación.
    conversation = message_service.get_or_create_conversation_with_tenant(db, message, tenant_id=tenant_id)
    if not conversation:
        return

    # 3. Guardar el mensaje inbound SIEMPRE (dedup vía UNIQUE channel+provider_id).
    inbound = message_service.save_inbound_message(db, conversation, message)
    if not inbound:
        # Duplicado ya persistido: no procesar de nuevo (evita doble respuesta).
        return

    # 4. Resolver la config del canal.
    channel_config = ChannelConfigService.get_active_channel_config(
        db, inbound.channel_id,
    )
    if not channel_config:
        logger.info("No active config for channel: %s", inbound.channel_id)
        return

    # 5. Gate IA: modo "ai" + config válida.
    if not should_use_ai(conversation, channel_config):
        logger.info("AI disabled for conversation: %s", conversation.id)
        return

    # 6 + 7. Construir contexto y prompt.
    prompt = _processor.build_prompt_for_conversation(db, conversation, channel_config, inbound)
    if not prompt:
        return

    # 8. Llamar a IA (incluye logging, fallback, out-of-scope, límite de mensajes).
    ai_response = await _processor.generate_response(
        db,
        conversation=conversation,
        channel_config=channel_config,
        prompt=prompt,
        contact_id=inbound.sender_contact_id,
        tenant_id=inbound.tenant_id,
        channel_id=inbound.channel_id,
        message_id=inbound.id,
        request_id=inbound.provider_message_id,
    )
    if not ai_response:
        return

    # 9. Guardar la respuesta SIEMPRE antes de despachar.
    outbound = message_service.save_outbound_message(db, conversation, ai_response)

    # 10. Enviar al canal.
    try:
        message_service.dispatch_to_channel(db, conversation, outbound)
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to dispatch outbound message %s for conversation %s",
            outbound.id, conversation.id,
        )
