import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.contact import Contact, ContactIdentity
from app.models.conversation import ChatThread, Conversation, Message, MessageAttachment
from app.models.metrics import ContactUsage
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_conversation_by_id_and_tenant(self, conversation_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_channel_by_id_and_tenant(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Channel]:
        stmt = select(Channel).where(Channel.id == channel_id, Channel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_thread_by_id_and_tenant(self, thread_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[ChatThread]:
        stmt = select(ChatThread).where(ChatThread.id == thread_id, ChatThread.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_thread_by_channel_and_external_chat(
        self,
        channel_id: uuid.UUID,
        external_chat_id: Optional[str],
        tenant_id: uuid.UUID,
    ) -> Optional[ChatThread]:
        stmt = select(ChatThread).where(
            ChatThread.channel_id == channel_id,
            ChatThread.external_chat_id == external_chat_id,
            ChatThread.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_thread(
        self,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        external_chat_id: Optional[str],
        thread_type: str,
        is_group: bool,
    ) -> ChatThread:
        thread = ChatThread(
            tenant_id=tenant_id,
            channel_id=channel_id,
            external_chat_id=external_chat_id,
            type=thread_type,
            is_group=is_group,
        )
        self.db.add(thread)
        self.db.flush()
        return thread

    def get_open_conversation_by_thread(self, thread_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.chat_thread_id == thread_id,
            Conversation.tenant_id == tenant_id,
            Conversation.status == "open",
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_conversation(self, tenant_id: uuid.UUID, thread_id: uuid.UUID) -> Conversation:
        now = datetime.now(timezone.utc)
        conversation = Conversation(
            tenant_id=tenant_id,
            chat_thread_id=thread_id,
            status="open",
            mode="ai",
            started_at=now,
            last_message_at=now,
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def create_contact_usage(self, contact_id: uuid.UUID, conversation_id: uuid.UUID) -> ContactUsage:
        usage = ContactUsage(
            contact_id=contact_id,
            conversation_id=conversation_id,
            bot_message_count=0,
        )
        self.db.add(usage)
        self.db.flush()
        return usage

    def get_contact_usage_by_conversation(self, conversation_id: uuid.UUID) -> Optional[ContactUsage]:
        stmt = select(ContactUsage).where(ContactUsage.conversation_id == conversation_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_contact_identity(self, channel_type: str, external_id: str) -> Optional[ContactIdentity]:
        stmt = select(ContactIdentity).where(
            ContactIdentity.channel_type == channel_type,
            ContactIdentity.external_id == external_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_contact_by_id(self, contact_id: uuid.UUID) -> Optional[Contact]:
        stmt = select(Contact).where(Contact.id == contact_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_contact_by_id_and_tenant(self, contact_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Contact]:
        stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_contact(self, tenant_id: uuid.UUID, name: Optional[str], phone: Optional[str]) -> Contact:
        contact = Contact(tenant_id=tenant_id, name=name, phone=phone)
        self.db.add(contact)
        self.db.flush()
        return contact

    def create_contact_identity(self, contact_id: uuid.UUID, channel_type: str, external_id: str) -> ContactIdentity:
        identity = ContactIdentity(
            contact_id=contact_id,
            channel_type=channel_type,
            external_id=external_id,
        )
        self.db.add(identity)
        self.db.flush()
        return identity

    def get_message_by_provider_id(
        self,
        channel_id: uuid.UUID,
        provider_message_id: str,
        tenant_id: uuid.UUID,
    ) -> Optional[Message]:
        stmt = select(Message).where(
            Message.channel_id == channel_id,
            Message.provider_message_id == provider_message_id,
            Message.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, message_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Message]:
        stmt = select(Message).where(Message.id == message_id, Message.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_conversation(self, conversation_id: uuid.UUID, tenant_id: uuid.UUID) -> list[Message]:
        return self.list_messages(conversation_id=conversation_id, tenant_id=tenant_id)

    def create_message(self, message: Message) -> Message:
        self.db.add(message)
        return message

    def create(self, message: Message) -> Message:
        return self.create_message(message)

    def update_message(self, message: Message, **kwargs: object) -> Message:
        for key, value in kwargs.items():
            setattr(message, key, value)
        return message

    def update(self, message: Message, **kwargs: object) -> Message:
        return self.update_message(message, **kwargs)

    def touch_conversation_last_message(self, conversation: Conversation) -> None:
        conversation.last_message_at = datetime.now(timezone.utc)

    def save_attachment(
        self,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        attachment_type: str,
        file_data: bytes,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_extension: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        metadata_jsonb: Optional[dict] = None,
    ) -> MessageAttachment:
        attachment = MessageAttachment(
            message_id=message_id,
            tenant_id=tenant_id,
            attachment_type=attachment_type,
            file_data=file_data,
            file_name=file_name,
            mime_type=mime_type,
            file_extension=file_extension,
            file_size_bytes=file_size_bytes,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            metadata_jsonb=metadata_jsonb,
        )
        self.db.add(attachment)
        return attachment

    def list_messages(self, conversation_id: uuid.UUID, tenant_id: uuid.UUID) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.tenant_id == tenant_id)
            .order_by(Message.created_at.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)

    def rollback(self) -> None:
        self.db.rollback()
