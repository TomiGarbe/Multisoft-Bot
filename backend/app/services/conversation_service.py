import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import User
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationResponse
from app.services.auth.access_service import can_access_tenant_resource
from app.services.channel_config_service import ChannelConfigService
from app.services.conversation.mode_service import InvalidChannelConfigError, disable_ai, enable_ai


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

    def get_conversations(
        self,
        user_id: Optional[uuid.UUID] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> list[ConversationResponse]:
        if user_id is None or tenant_id is None:
            return []

        conversations = self.repository.get_all_by_tenant(tenant_id)
        return [self._build_response(c) for c in conversations]

    def set_mode(
        self,
        conversation_id: uuid.UUID,
        mode: str,
        tenant_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> Conversation:
        conversation = self.repository.get_by_id_and_tenant(conversation_id, tenant_id)
        if conversation is None:
            raise LookupError(f"Conversation not found: {conversation_id}")
        if user is not None and not can_access_tenant_resource(self.db, user, conversation.tenant_id):
            raise LookupError(f"Conversation not found: {conversation_id}")

        if mode == "ai":
            channel_config = ChannelConfigService.get_channel_config(
                self.db,
                conversation.chat_thread.channel_id,
            )
            try:
                enable_ai(self.db, conversation, channel_config)
            except InvalidChannelConfigError as exc:
                raise ValueError("Config incompleta") from exc
        else:
            disable_ai(self.db, conversation)

        return conversation


def get_conversations(
    db: Session,
    user_id: Optional[uuid.UUID] = None,
    tenant_id: Optional[uuid.UUID] = None,
) -> list[ConversationResponse]:
    return ConversationService(db).get_conversations(user_id=user_id, tenant_id=tenant_id)
