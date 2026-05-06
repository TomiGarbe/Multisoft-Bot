import logging
import uuid
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant_id
from app.interfaces.messaging.message_provider import MessageProvider
from app.models.channel import Channel
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.providers.provider_factory import get_message_provider
from app.repositories.message_repository import MessageRepository
from app.schemas.internal.normalized_message import NormalizedMessage
from app.schemas.message import MessageResponse, MessageSendRequest
from app.services.realtime_service import event_bus

logger = logging.getLogger(__name__)


def _ensure_message_id_value(message: object) -> str:
    message_id = getattr(message, "external_message_id", None)
    if isinstance(message, dict):
        message_id = message.get("external_message_id")
    message_id = str(message_id).strip() if message_id is not None else ""
    if not message_id:
        message_id = str(uuid.uuid4())
        if isinstance(message, dict):
            message["external_message_id"] = message_id
        else:
            setattr(message, "external_message_id", message_id)
    return message_id


def _serialize_message(message: Message) -> MessageResponse:
    return MessageResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        direction=message.direction,
        sender_type=message.sender_type,
        message_type=message.message_type,
        content=message.content_text,
        status=message.status,
        provider_message_id=message.provider_message_id,
        created_at=message.created_at,
    )


class MessageService:
    def __init__(
        self,
        db: Session,
        provider_resolver: Callable[[str], MessageProvider] = get_message_provider,
    ) -> None:
        self.db = db
        self.repository = MessageRepository(db)
        self.provider_resolver = provider_resolver

    def ensure_message_id(self, message: object) -> str:
        return _ensure_message_id_value(message)

    def get_or_create_conversation(self, normalized: NormalizedMessage) -> Optional[Conversation]:
        tenant_id = get_current_tenant_id()
        channel_uuid = uuid.UUID(normalized.channel_id)

        channel = self.repository.get_channel_by_id_and_tenant(channel_uuid, tenant_id)
        if not channel:
            logger.error("Channel not found or outside tenant scope: %s", normalized.channel_id)
            return None

        contact_id = self._resolve_or_create_contact_id(channel, normalized)
        thread = self._get_or_create_thread(channel, normalized)
        conversation = self.repository.get_open_conversation_by_thread(thread.id, tenant_id)
        if conversation:
            return conversation

        conversation = self.repository.create_conversation(tenant_id=channel.tenant_id, thread_id=thread.id)
        if contact_id:
            self.repository.create_contact_usage(contact_id=contact_id, conversation_id=conversation.id)

        self.repository.commit()
        self.repository.refresh(conversation)
        return conversation

    def save_inbound_message(self, conversation: Conversation, normalized: NormalizedMessage) -> Optional[Message]:
        external_message_id = self.ensure_message_id(normalized)
        channel_uuid = uuid.UUID(normalized.channel_id)

        duplicate = self.repository.get_message_by_provider_id(
            channel_id=channel_uuid,
            provider_message_id=external_message_id,
            tenant_id=conversation.tenant_id,
        )
        if duplicate:
            logger.info("Duplicate ignored: channel=%s id=%s", normalized.channel_id, external_message_id)
            return None

        contact_id = self._lookup_contact_id(channel_uuid, normalized.sender_external_id, conversation.tenant_id)

        message = Message(
            conversation_id=conversation.id,
            tenant_id=conversation.tenant_id,
            channel_id=channel_uuid,
            sender_contact_id=contact_id,
            direction="inbound",
            sender_type="contact",
            message_type=normalized.message_type,
            content_text=normalized.content,
            provider_message_id=external_message_id,
            status="received",
            is_group=normalized.is_group,
            group_id=normalized.group_id,
            is_status=normalized.is_status,
            sender_external_id=normalized.sender_external_id,
            sender_name=normalized.sender_name,
            provider_timestamp=normalized.timestamp,
            has_media=normalized.has_media,
            raw_payload=normalized.raw_payload,
        )
        self.repository.create_message(message)
        self.repository.touch_conversation_last_message(conversation)
        self.repository.commit()
        self.repository.refresh(message)
        self._publish_new_message_event(message)
        return message

    def save_outbound_message(
        self,
        conversation: Conversation,
        content: str,
        attachments: Optional[list] = None,
        raw_payload: Optional[dict] = None,
    ) -> Message:
        thread = self.repository.get_thread_by_id_and_tenant(conversation.chat_thread_id, conversation.tenant_id)
        if thread is None:
            raise ValueError(f"Chat thread not found: {conversation.chat_thread_id}")

        message = Message(
            conversation_id=conversation.id,
            tenant_id=conversation.tenant_id,
            channel_id=thread.channel_id,
            direction="outbound",
            sender_type="bot",
            message_type="media" if attachments else "text",
            content_text=content,
            provider_message_id=str(uuid.uuid4()),
            status="pending",
            has_media=bool(attachments),
            raw_payload=raw_payload,
        )
        self.repository.create_message(message)
        self.repository.commit()
        self.repository.refresh(message)
        self._publish_new_message_event(message)
        return message

    def dispatch_to_channel(
        self,
        conversation: Conversation,
        message: Message,
        attachments: Optional[list] = None,
        reply_to_id: Optional[str] = None,
    ) -> dict:
        thread = self.repository.get_thread_by_id_and_tenant(conversation.chat_thread_id, conversation.tenant_id)
        if thread is None:
            raise ValueError(f"Chat thread not found: {conversation.chat_thread_id}")

        channel = self.repository.get_channel_by_id_and_tenant(thread.channel_id, conversation.tenant_id)
        if channel is None:
            raise ValueError(f"Channel not found: {thread.channel_id}")

        provider = self.provider_resolver(channel.type)
        to = thread.external_chat_id
        content = message.content_text or ""

        if reply_to_id:
            result = provider.reply_to_message(str(channel.id), to, content, reply_to_id)
        elif attachments:
            media_url = attachments[0].get("url", "")
            result = provider.send_media(str(channel.id), to, media_url, content or None)
        else:
            result = provider.send_text(str(channel.id), to, content)

        self.repository.update_message(
            message,
            provider_message_id=result.get("provider_message_id"),
            status=result.get("status", "sent"),
        )
        self.repository.touch_conversation_last_message(conversation)
        self.repository.commit()
        self.repository.refresh(message)
        return result

    def create_inbound_message(self, normalized: NormalizedMessage) -> Optional[Message]:
        conversation = self.get_or_create_conversation(normalized)
        if not conversation:
            return None
        return self.save_inbound_message(conversation, normalized)

    def send_message(
        self,
        data: MessageSendRequest,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> dict:
        tenant_id = tenant_id or get_current_tenant_id()
        conversation = self.repository.get_conversation_by_id_and_tenant(data.conversation_id, tenant_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {data.conversation_id}")

        message = self.save_outbound_message(
            conversation,
            data.content,
            attachments=data.attachments,
            raw_payload=data.model_dump(),
        )
        return self.dispatch_to_channel(
            conversation,
            message,
            attachments=data.attachments,
            reply_to_id=data.reply_to_id,
        )

    def list_messages(
        self,
        conversation_id: uuid.UUID,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> list[MessageResponse]:
        tenant_id = tenant_id or get_current_tenant_id()
        conversation = self.repository.get_conversation_by_id_and_tenant(conversation_id, tenant_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")
        messages = self.repository.list_messages(conversation_id=conversation_id, tenant_id=tenant_id)
        return [self._to_response(m) for m in messages]

    def get_contact_by_id(self, contact_id: uuid.UUID) -> Optional[Contact]:
        return self.repository.get_contact_by_id(contact_id)

    def get_contact_by_id_and_tenant(self, contact_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Contact]:
        return self.repository.get_contact_by_id_and_tenant(contact_id, tenant_id)

    def ensure_contact_current_type(self, contact_id: uuid.UUID, default_type: str) -> Optional[Contact]:
        contact = self.repository.get_contact_by_id(contact_id)
        if not contact:
            return None
        if contact.current_type is None:
            contact.current_type = default_type
            self.repository.commit()
            self.repository.refresh(contact)
        return contact

    def apply_contact_current_type(self, contact_id: uuid.UUID, user_type: str) -> Optional[Contact]:
        contact = self.repository.get_contact_by_id(contact_id)
        if not contact:
            return None
        contact.current_type = user_type
        self.repository.commit()
        self.repository.refresh(contact)
        return contact

    def increment_contact_usage(self, contact_id: uuid.UUID, conversation_id: uuid.UUID) -> Optional[int]:
        usage = self.repository.get_contact_usage_by_conversation(conversation_id)
        if usage is None:
            usage = self.repository.create_contact_usage(contact_id=contact_id, conversation_id=conversation_id)
        usage.bot_message_count += 1
        self.repository.commit()
        self.repository.refresh(usage)
        return usage.bot_message_count

    def set_conversation_mode(self, conversation: Conversation, mode: str) -> None:
        conversation.mode = mode
        self.repository.commit()
        self.repository.refresh(conversation)

    def _resolve_or_create_contact_id(self, channel: Channel, normalized: NormalizedMessage) -> Optional[uuid.UUID]:
        if not normalized.sender_external_id:
            return None

        identity = self.repository.get_contact_identity(channel.type, normalized.sender_external_id)
        if identity:
            return identity.contact_id

        contact = self.repository.create_contact(
            tenant_id=channel.tenant_id,
            name=normalized.sender_name,
            phone=normalized.sender_external_id if channel.type in ("whatsapp", "sms") else None,
        )
        self.repository.create_contact_identity(
            contact_id=contact.id,
            channel_type=channel.type,
            external_id=normalized.sender_external_id,
        )
        return contact.id

    def _get_or_create_thread(self, channel: Channel, normalized: NormalizedMessage):
        external_chat_id = normalized.group_id if normalized.is_group else normalized.sender_external_id
        thread = self.repository.get_thread_by_channel_and_external_chat(
            channel_id=channel.id,
            external_chat_id=external_chat_id,
            tenant_id=channel.tenant_id,
        )
        if thread:
            return thread

        return self.repository.create_thread(
            tenant_id=channel.tenant_id,
            channel_id=channel.id,
            external_chat_id=external_chat_id,
            thread_type="group" if normalized.is_group else "direct",
            is_group=normalized.is_group,
        )

    def _lookup_contact_id(
        self,
        channel_id: uuid.UUID,
        external_id: Optional[str],
        tenant_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        if not external_id:
            return None

        channel = self.repository.get_channel_by_id_and_tenant(channel_id, tenant_id)
        if not channel:
            return None

        identity = self.repository.get_contact_identity(channel.type, external_id)
        return identity.contact_id if identity else None

    def _to_response(self, message: Message) -> MessageResponse:
        return _serialize_message(message)

    def _publish_new_message_event(self, message: Message) -> None:
        serialized = self._to_response(message).model_dump(mode="json")
        event_bus.publish(
            "new_message",
            {
                "type": "new_message",
                "conversation_id": str(message.conversation_id),
                "message": serialized,
            },
        )


# Backward-compatible wrappers

def ensure_message_id(message: object) -> str:
    return _ensure_message_id_value(message)


def get_or_create_conversation(db: Session, normalized: NormalizedMessage) -> Optional[Conversation]:
    return MessageService(db).get_or_create_conversation(normalized)


def save_inbound_message(db: Session, conversation: Conversation, normalized: NormalizedMessage) -> Optional[Message]:
    return MessageService(db).save_inbound_message(conversation, normalized)


def save_outbound_message(
    db: Session,
    conversation: Conversation,
    content: str,
    attachments: Optional[list] = None,
    raw_payload: Optional[dict] = None,
) -> Message:
    return MessageService(db).save_outbound_message(conversation, content, attachments, raw_payload)


def dispatch_to_channel(
    db: Session,
    conversation: Conversation,
    message: Message,
    attachments: Optional[list] = None,
    reply_to_id: Optional[str] = None,
) -> dict:
    return MessageService(db).dispatch_to_channel(conversation, message, attachments, reply_to_id)


def create_inbound_message(db: Session, normalized: NormalizedMessage) -> Optional[Message]:
    return MessageService(db).create_inbound_message(normalized)


def send_message(db: Session, data: dict) -> dict:
    request = MessageSendRequest(**data)
    return MessageService(db).send_message(request)


def get_messages(db: Session, conversation_id: uuid.UUID) -> list[dict]:
    messages = MessageService(db).list_messages(conversation_id)
    return [m.model_dump(mode="json") for m in messages]


def get_contact(db: Session, contact_id: uuid.UUID) -> Optional[Contact]:
    return MessageService(db).get_contact_by_id(contact_id)


def get_contact_by_tenant(db: Session, contact_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Contact]:
    return MessageService(db).get_contact_by_id_and_tenant(contact_id, tenant_id)


def ensure_contact_current_type(db: Session, contact_id: uuid.UUID, default_type: str) -> Optional[Contact]:
    return MessageService(db).ensure_contact_current_type(contact_id, default_type)


def apply_contact_current_type(db: Session, contact_id: uuid.UUID, user_type: str) -> Optional[Contact]:
    return MessageService(db).apply_contact_current_type(contact_id, user_type)


def increment_contact_usage(db: Session, contact_id: uuid.UUID, conversation_id: uuid.UUID) -> Optional[int]:
    return MessageService(db).increment_contact_usage(contact_id, conversation_id)


def set_conversation_mode(db: Session, conversation: Conversation, mode: str) -> None:
    MessageService(db).set_conversation_mode(conversation, mode)


def serialize_message(message: Message) -> dict:
    return _serialize_message(message).model_dump(mode="json")
