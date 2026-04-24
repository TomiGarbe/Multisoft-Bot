import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.contact import Contact, ContactIdentity
from app.models.conversation import ChatThread, Conversation, Message
from app.providers.provider_factory import get_message_provider
from app.schemas.internal.normalized_message import NormalizedMessage

logger = logging.getLogger(__name__)


def create_inbound_message(db: Session, normalized: NormalizedMessage) -> Message | None:
    channel_uuid = uuid.UUID(normalized.channel_id)

    # Dedup by (channel_id, provider_message_id)
    if db.query(Message).filter(
        Message.channel_id == channel_uuid,
        Message.provider_message_id == normalized.external_message_id,
    ).first():
        logger.info("Duplicate ignored: channel=%s id=%s", normalized.channel_id, normalized.external_message_id)
        return None

    channel = db.query(Channel).filter(Channel.id == channel_uuid).first()
    if not channel:
        logger.error("Channel not found: %s", normalized.channel_id)
        return None

    # Resolve or create contact identity
    contact_id = None
    if normalized.sender_external_id:
        identity = db.query(ContactIdentity).filter(
            ContactIdentity.channel_type == channel.type,
            ContactIdentity.external_id == normalized.sender_external_id,
        ).first()
        if identity:
            contact_id = identity.contact_id
        else:
            contact = Contact(
                tenant_id=channel.tenant_id,
                name=normalized.sender_name,
                phone=normalized.sender_external_id if channel.type in ("whatsapp", "sms") else None,
            )
            db.add(contact)
            db.flush()
            identity = ContactIdentity(
                contact_id=contact.id,
                channel_type=channel.type,
                external_id=normalized.sender_external_id,
            )
            db.add(identity)
            db.flush()
            contact_id = contact.id

    # Find or create ChatThread
    external_chat_id = normalized.group_id if normalized.is_group else normalized.sender_external_id
    thread = db.query(ChatThread).filter(
        ChatThread.channel_id == channel.id,
        ChatThread.external_chat_id == external_chat_id,
    ).first()
    if not thread:
        thread = ChatThread(
            tenant_id=channel.tenant_id,
            channel_id=channel.id,
            external_chat_id=external_chat_id,
            type="group" if normalized.is_group else "direct",
            is_group=normalized.is_group,
        )
        db.add(thread)
        db.flush()

    # Find or create open Conversation on this thread
    conversation = db.query(Conversation).filter(
        Conversation.chat_thread_id == thread.id,
        Conversation.status == "open",
    ).first()
    now = datetime.now(timezone.utc)
    if not conversation:
        conversation = Conversation(
            tenant_id=channel.tenant_id,
            chat_thread_id=thread.id,
            status="open",
            started_at=now,
            last_message_at=now,
        )
        db.add(conversation)
        db.flush()

    message = Message(
        conversation_id=conversation.id,
        tenant_id=channel.tenant_id,
        channel_id=channel.id,
        sender_contact_id=contact_id,
        direction="inbound",
        sender_type="contact",
        message_type=normalized.message_type,
        content_text=normalized.content,
        provider_message_id=normalized.external_message_id,
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
    db.add(message)
    conversation.last_message_at = now
    db.commit()
    db.refresh(message)
    return message


def send_message(db: Session, data: dict) -> dict:
    conversation_id = uuid.UUID(str(data["conversation_id"]))
    content = data.get("content", "")
    attachments = data.get("attachments") or []
    reply_to_id = data.get("reply_to_id")

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise ValueError(f"Conversation not found: {conversation_id}")

    thread = db.query(ChatThread).filter(ChatThread.id == conversation.chat_thread_id).first()
    channel = db.query(Channel).filter(Channel.id == thread.channel_id).first()

    message = Message(
        conversation_id=conversation.id,
        tenant_id=conversation.tenant_id,
        channel_id=channel.id,
        direction="outbound",
        sender_type="bot",
        message_type="media" if attachments else "text",
        content_text=content,
        status="pending",
        has_media=bool(attachments),
        raw_payload=data,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    provider = get_message_provider(channel.type)
    to = thread.external_chat_id

    if reply_to_id:
        result = provider.reply_to_message(str(channel.id), to, content, reply_to_id)
    elif attachments:
        media_url = attachments[0].get("url", "")
        result = provider.send_media(str(channel.id), to, media_url, content or None)
    else:
        result = provider.send_text(str(channel.id), to, content)

    message.provider_message_id = result.get("provider_message_id")
    message.status = result.get("status", "sent")
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)
    return result


def get_messages(db: Session, conversation_id: uuid.UUID) -> list:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(m.id),
            "conversation_id": str(m.conversation_id),
            "direction": m.direction,
            "sender_type": m.sender_type,
            "message_type": m.message_type,
            "content": m.content_text,
            "status": m.status,
            "provider_message_id": m.provider_message_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
