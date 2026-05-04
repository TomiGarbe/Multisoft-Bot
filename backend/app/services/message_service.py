import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.contact import Contact, ContactIdentity
from app.models.conversation import ChatThread, Conversation, Message
from app.models.metrics import ContactUsage
from app.providers.provider_factory import get_message_provider
from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.realtime_service import event_bus

logger = logging.getLogger(__name__)


def ensure_message_id(message) -> str:
    """Return a non-empty string message id, generating a UUID when missing."""
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


def get_or_create_conversation(
    db: Session,
    normalized: NormalizedMessage,
) -> Optional[Conversation]:
    """Resolve channel/contact/thread and return the open conversation, creating it if missing."""
    channel_uuid = uuid.UUID(normalized.channel_id)

    channel = db.query(Channel).filter(Channel.id == channel_uuid).first()
    if not channel:
        logger.error("Channel not found: %s", normalized.channel_id)
        return None

    contact_id = _resolve_or_create_contact_id(db, channel, normalized)
    thread = _get_or_create_thread(db, channel, normalized)

    conversation = db.query(Conversation).filter(
        Conversation.chat_thread_id == thread.id,
        Conversation.status == "open",
    ).first()
    if conversation:
        return conversation

    now = datetime.now(timezone.utc)
    conversation = Conversation(
        tenant_id=channel.tenant_id,
        chat_thread_id=thread.id,
        status="open",
        mode="ai",
        started_at=now,
        last_message_at=now,
    )
    db.add(conversation)
    db.flush()
    if contact_id:
        db.add(ContactUsage(
            contact_id=contact_id,
            conversation_id=conversation.id,
            bot_message_count=0,
        ))
        db.flush()
    db.commit()
    db.refresh(conversation)
    return conversation


def save_inbound_message(
    db: Session,
    conversation: Conversation,
    normalized: NormalizedMessage,
) -> Optional[Message]:
    """Persist an inbound Message. Returns None on dedup hit."""
    external_message_id = ensure_message_id(normalized)
    channel_uuid = uuid.UUID(normalized.channel_id)

    if db.query(Message).filter(
        Message.channel_id == channel_uuid,
        Message.provider_message_id == external_message_id,
    ).first():
        logger.info(
            "Duplicate ignored: channel=%s id=%s",
            normalized.channel_id, external_message_id,
        )
        return None

    contact_id = _lookup_contact_id(db, channel_uuid, normalized.sender_external_id)

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
    db.add(message)
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)
    _publish_new_message_event(message)
    return message


def save_outbound_message(
    db: Session,
    conversation: Conversation,
    content: str,
    attachments: Optional[list] = None,
    raw_payload: Optional[dict] = None,
) -> Message:
    """Persist an outbound bot Message in 'pending' status."""
    thread = db.query(ChatThread).filter(ChatThread.id == conversation.chat_thread_id).first()
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
    db.add(message)
    db.commit()
    db.refresh(message)
    _publish_new_message_event(message)
    return message


def dispatch_to_channel(
    db: Session,
    conversation: Conversation,
    message: Message,
    attachments: Optional[list] = None,
    reply_to_id: Optional[str] = None,
) -> dict:
    """Send a previously-saved outbound Message via its channel provider."""
    thread = db.query(ChatThread).filter(ChatThread.id == conversation.chat_thread_id).first()
    channel = db.query(Channel).filter(Channel.id == thread.channel_id).first()

    provider = get_message_provider(channel.type)
    to = thread.external_chat_id
    content = message.content_text or ""

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


def create_inbound_message(db: Session, normalized: NormalizedMessage) -> Optional[Message]:
    """Backward-compatible helper used by webhook flows: resolve conversation + save inbound."""
    conversation = get_or_create_conversation(db, normalized)
    if not conversation:
        return None
    return save_inbound_message(db, conversation, normalized)


def send_message(db: Session, data: dict) -> dict:
    """Backward-compatible API wrapper: save outbound + dispatch."""
    conversation_id = uuid.UUID(str(data["conversation_id"]))
    content = data.get("content", "")
    attachments = data.get("attachments") or []
    reply_to_id = data.get("reply_to_id")

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise ValueError(f"Conversation not found: {conversation_id}")

    message = save_outbound_message(
        db, conversation, content, attachments=attachments, raw_payload=data,
    )
    return dispatch_to_channel(
        db, conversation, message, attachments=attachments, reply_to_id=reply_to_id,
    )


def get_messages(db: Session, conversation_id: uuid.UUID) -> list:
    logger.warning("Fetching messages for conversation: %s", conversation_id)
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    logger.warning("Found %d messages for conversation: %s", len(messages), conversation_id)
    return [serialize_message(m) for m in messages]


# ---------- Internals ----------

def _resolve_or_create_contact_id(
    db: Session,
    channel: Channel,
    normalized: NormalizedMessage,
) -> Optional[uuid.UUID]:
    if not normalized.sender_external_id:
        return None
    identity = db.query(ContactIdentity).filter(
        ContactIdentity.channel_type == channel.type,
        ContactIdentity.external_id == normalized.sender_external_id,
    ).first()
    if identity:
        return identity.contact_id

    contact = Contact(
        tenant_id=channel.tenant_id,
        name=normalized.sender_name,
        phone=normalized.sender_external_id if channel.type in ("whatsapp", "sms") else None,
    )
    db.add(contact)
    db.flush()
    db.add(ContactIdentity(
        contact_id=contact.id,
        channel_type=channel.type,
        external_id=normalized.sender_external_id,
    ))
    db.flush()
    return contact.id


def _get_or_create_thread(
    db: Session,
    channel: Channel,
    normalized: NormalizedMessage,
) -> ChatThread:
    external_chat_id = normalized.group_id if normalized.is_group else normalized.sender_external_id
    thread = db.query(ChatThread).filter(
        ChatThread.channel_id == channel.id,
        ChatThread.external_chat_id == external_chat_id,
    ).first()
    if thread:
        return thread
    thread = ChatThread(
        tenant_id=channel.tenant_id,
        channel_id=channel.id,
        external_chat_id=external_chat_id,
        type="group" if normalized.is_group else "direct",
        is_group=normalized.is_group,
    )
    db.add(thread)
    db.flush()
    return thread


def _lookup_contact_id(
    db: Session,
    channel_id: uuid.UUID,
    external_id: Optional[str],
) -> Optional[uuid.UUID]:
    if not external_id:
        return None
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        return None
    identity = db.query(ContactIdentity).filter(
        ContactIdentity.channel_type == channel.type,
        ContactIdentity.external_id == external_id,
    ).first()
    return identity.contact_id if identity else None


def serialize_message(message: Message) -> dict:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "direction": message.direction,
        "sender_type": message.sender_type,
        "message_type": message.message_type,
        "content": message.content_text,
        "status": message.status,
        "provider_message_id": message.provider_message_id,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def _publish_new_message_event(message: Message) -> None:
    event_bus.publish(
        "new_message",
        {
            "type": "new_message",
            "conversation_id": str(message.conversation_id),
            "message": serialize_message(message),
        },
    )
