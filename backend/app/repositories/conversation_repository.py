import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.auth import TenantUser
from app.models.config import ChannelBotConfig
from app.models.conversation import Conversation, ChatThread
from app.models.contact import Contact
from app.models.metrics import ContactUsage
from app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        return super().get_by_id(Conversation, conversation_id)

    def get_by_id_and_tenant(
        self,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        ).options(joinedload(Conversation.chat_thread))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(self) -> list[Conversation]:
        stmt = select(Conversation).order_by(Conversation.last_message_at.desc())
        return self.db.execute(stmt).scalars().all()

    def get_all_by_tenant(self, tenant_id: uuid.UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .options(
                joinedload(Conversation.chat_thread).joinedload(ChatThread.channel),
            )
            .where(Conversation.tenant_id == tenant_id)
            .order_by(Conversation.last_message_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_contact_for_conversation(self, conversation_id: uuid.UUID) -> Optional[Contact]:
        stmt = (
            select(Contact)
            .join(ContactUsage, ContactUsage.contact_id == Contact.id)
            .where(ContactUsage.conversation_id == conversation_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_by_tenants(self, tenant_ids: list[uuid.UUID]) -> list[Conversation]:
        if not tenant_ids:
            return []

        stmt = (
            select(Conversation)
            .where(Conversation.tenant_id.in_(tenant_ids))
            .order_by(Conversation.last_message_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_tenant_ids_by_user_id(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(TenantUser.tenant_id).where(TenantUser.user_id == user_id)
        rows = self.db.execute(stmt).scalars().all()
        return [tenant_id for tenant_id in rows if tenant_id is not None]

    def get_active_channel_config_id_by_channel_id(self, channel_id: uuid.UUID) -> Optional[uuid.UUID]:
        stmt = (
            select(ChannelBotConfig.id)
            .where(
                ChannelBotConfig.channel_id == channel_id,
                ChannelBotConfig.is_active.is_(True),
            )
            .order_by(ChannelBotConfig.created_at.desc())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_contact(self, contact_id: uuid.UUID) -> Optional[Conversation]:
        # Placeholder for future contact-conversation mapping without changing current behavior.
        return None

    def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        return conversation

    def update(self, conversation: Conversation, **kwargs: object) -> Conversation:
        for key, value in kwargs.items():
            setattr(conversation, key, value)
        return conversation

    def refresh(self, conversation: Conversation) -> None:
        self.db.refresh(conversation)

    def rollback(self) -> None:
        self.db.rollback()
