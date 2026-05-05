import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant_id
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationResponse
from app.services.bot_config_service import BotConfigService
from app.services.conversation.mode_service import InvalidBotConfigError, disable_ai, enable_ai


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ConversationRepository(db)

    def _build_response(self, conversation: Conversation) -> ConversationResponse:
        channel_config_id = self.repository.get_active_channel_config_id_by_channel_id(
            conversation.chat_thread.channel_id
        )
        return ConversationResponse(
            id=conversation.id,
            tenant_id=conversation.tenant_id,
            status=conversation.status,
            mode=conversation.mode,
            channel_config_id=channel_config_id,
            started_at=conversation.started_at,
            last_message_at=conversation.last_message_at,
        )

    def get_conversations(self, user_id: Optional[uuid.UUID] = None) -> list[ConversationResponse]:
        # DEV: keep bypass behavior exactly as before.
        if user_id is None:
            conversations = self.repository.get_all()
            return [self._build_response(c) for c in conversations]

        tenant_ids = self.repository.get_tenant_ids_by_user_id(user_id)
        if not tenant_ids:
            return []

        conversations = self.repository.get_all_by_tenants(tenant_ids)
        return [self._build_response(c) for c in conversations]

    def set_mode(self, conversation_id: uuid.UUID, mode: str) -> Conversation:
        tenant_id = get_current_tenant_id()
        conversation = self.repository.get_by_id_and_tenant(conversation_id, tenant_id)
        if conversation is None:
            conversation = self.repository.get_by_id(conversation_id)
        if conversation is None:
            raise LookupError(f"Conversation not found: {conversation_id}")

        if mode == "ai":
            channel_config = BotConfigService.get_channel_config(
                self.db,
                conversation.chat_thread.channel_id,
            )
            try:
                enable_ai(self.db, conversation, channel_config)
            except InvalidBotConfigError as exc:
                raise ValueError("Config incompleta") from exc
        else:
            disable_ai(self.db, conversation)

        return conversation


def get_conversations(db: Session, user_id: Optional[uuid.UUID] = None) -> list[ConversationResponse]:
    return ConversationService(db).get_conversations(user_id=user_id)
