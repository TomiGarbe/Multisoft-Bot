import logging
import uuid
from typing import Any, Callable, Optional
from urllib.parse import urlencode

from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.interfaces.messaging.message_provider import MessageProvider
from app.models.channel import Channel
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.providers.provider_factory import get_message_provider
from app.repositories.message_repository import MessageRepository
from app.schemas.internal.message_enums import AttachmentDownloadStatus, MessageType, StorageBackend
from app.schemas.internal.normalized_message import NormalizedMessage
from app.schemas.internal.attachment_persistence import AttachmentCreate
from app.schemas.internal.outbound_media import OutboundAttachment, OutboundMediaMessage
from app.schemas.message import MessageResponse, MessageSendRequest
from app.services.attachment_service import AttachmentService
from app.services.attachments.attachment_download_dispatcher import (
    AttachmentDownloadJob,
    attachment_download_dispatcher,
)
from app.services.message_persistence_service import MessagePersistenceService
from app.services.realtime_service import event_bus

logger = logging.getLogger(__name__)


def _resolve_channel_provider_name(channel: Channel) -> str:
    if isinstance(channel.config_jsonb, dict):
        provider = channel.config_jsonb.get("provider")
        if isinstance(provider, str) and provider.strip():
            return provider
    # Backward-compatible fallback for old rows without provider.
    if (channel.type or "").strip().lower() == "whatsapp":
        return "multisoft"
    if (channel.type or "").strip().lower() == "web":
        return "web"
    return channel.type


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
        replied_to_message_id=message.replied_to_message_id,
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
        self.attachment_service = AttachmentService(db)
        self.message_persistence = MessagePersistenceService(db)
        self.provider_resolver = provider_resolver

    def ensure_message_id(self, message: object) -> str:
        return _ensure_message_id_value(message)

    def get_or_create_conversation(self, normalized: NormalizedMessage, tenant_id: uuid.UUID) -> Optional[Conversation]:
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
            message_type=normalized.message_type.value,
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
            replied_to_message_id=normalized.replied_to_message_id,
        )
        message = self.message_persistence.save_message(message, conversation)
        self._persist_normalized_attachments(message, normalized)
        self._publish_new_message_event(message)
        return message

    def save_outbound_message(
        self,
        conversation: Conversation,
        content: str,
        attachments: Optional[list[OutboundAttachment]] = None,
        raw_payload: Optional[dict] = None,
        replied_to_message_id: Optional[str] = None,
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
            message_type=MessageType.MEDIA.value if attachments else MessageType.TEXT.value,
            content_text=content,
            provider_message_id=str(uuid.uuid4()),
            status="pending",
            has_media=bool(attachments),
            raw_payload=raw_payload,
            replied_to_message_id=replied_to_message_id,
        )
        message = self.message_persistence.save_message(message, conversation)
        self._persist_outbound_attachments(message, conversation.tenant_id, attachments)
        self._publish_new_message_event(message)
        return message

    def dispatch_to_channel(
        self,
        conversation: Conversation,
        message: Message,
        attachments: Optional[list[OutboundAttachment]] = None,
        reply_to_id: Optional[str] = None,
    ) -> dict:
        thread = self.repository.get_thread_by_id_and_tenant(conversation.chat_thread_id, conversation.tenant_id)
        if thread is None:
            raise ValueError(f"Chat thread not found: {conversation.chat_thread_id}")

        channel = self.repository.get_channel_by_id_and_tenant(thread.channel_id, conversation.tenant_id)
        if channel is None:
            raise ValueError(f"Channel not found: {thread.channel_id}")

        provider_name = _resolve_channel_provider_name(channel)
        provider = self.provider_resolver(provider_name)
        to = thread.external_chat_id
        content = message.content_text or ""

        if reply_to_id:
            result = provider.reply_to_message(
                str(channel.id),
                to,
                content,
                reply_to_id,
                channel_external_id=channel.external_id,
                channel_config=channel.config_jsonb if isinstance(channel.config_jsonb, dict) else None,
            )
        elif attachments:
            resolved_attachments = self._resolve_outbound_attachments(
                message_id=message.id,
                tenant_id=conversation.tenant_id,
                outbound_attachments=attachments,
                channel_config=channel.config_jsonb if isinstance(channel.config_jsonb, dict) else None,
            )
            media_message = OutboundMediaMessage(attachments=resolved_attachments, fallback_text=content or None)
            logger.warning(
                "[MULTIMEDIA][OUTBOUND] dispatch_start provider=%s message_id=%s tenant_id=%s attachments_count=%s",
                provider_name,
                message.id,
                conversation.tenant_id,
                len(attachments),
            )
            result = provider.send_media(
                str(channel.id),
                to,
                media_message,
                channel_external_id=channel.external_id,
                channel_config=channel.config_jsonb if isinstance(channel.config_jsonb, dict) else None,
            )
        else:
            result = provider.send_text(
                str(channel.id),
                to,
                content,
                reply_to_message_id=reply_to_id,
                channel_external_id=channel.external_id,
                channel_config=channel.config_jsonb if isinstance(channel.config_jsonb, dict) else None,
            )

        self.repository.update_message(
            message,
            provider_message_id=result.get("provider_message_id"),
            status=result.get("status", "sent"),
        )
        logger.warning(
            "[MULTIMEDIA][OUTBOUND] dispatch_result provider=%s message_id=%s tenant_id=%s status=%s attachments_count=%s",
            provider_name,
            message.id,
            conversation.tenant_id,
            result.get("status"),
            len(attachments or []),
        )
        self.repository.touch_conversation_last_message(conversation)
        self.repository.commit()
        self.repository.refresh(message)
        return result

    def _resolve_outbound_attachments(
        self,
        *,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        outbound_attachments: list[OutboundAttachment],
        channel_config: Optional[dict[str, Any]],
    ) -> list[OutboundAttachment]:
        persisted = self.attachment_service.list_by_message_id_and_tenant(message_id, tenant_id)
        by_provider_media_id = {str(item.provider_media_id): item for item in persisted if item.provider_media_id}
        unmatched = [item for item in persisted if not item.provider_media_id]
        base_url = self._resolve_public_api_base_url(channel_config)

        resolved: list[OutboundAttachment] = []
        for item in outbound_attachments:
            if item.provider_url:
                logger.warning(
                    "[MULTIMEDIA][OUTBOUND] resolve_attachment message_id=%s strategy=provided_url type=%s provider_media_id=%s",
                    message_id,
                    item.type.value,
                    item.provider_media_id,
                )
                resolved.append(item)
                continue
            if item.provider_media_id and str(item.provider_media_id) in by_provider_media_id:
                db_attachment = by_provider_media_id[str(item.provider_media_id)]
                provider_url = db_attachment.provider_url
                if not provider_url and base_url:
                    provider_url = self._build_internal_download_url(
                        base_url=base_url,
                        attachment_id=db_attachment.id,
                        tenant_id=tenant_id,
                        storage_key=db_attachment.storage_key,
                    )
                logger.warning(
                    "[MULTIMEDIA][OUTBOUND] resolve_attachment message_id=%s strategy=provider_media_id type=%s provider_media_id=%s resolved_url=%s",
                    message_id,
                    item.type.value,
                    item.provider_media_id,
                    bool(provider_url),
                )
                resolved.append(item.model_copy(update={"provider_url": provider_url}))
                continue
            if unmatched:
                db_attachment = unmatched.pop(0)
                provider_url = db_attachment.provider_url
                if not provider_url and base_url:
                    provider_url = self._build_internal_download_url(
                        base_url=base_url,
                        attachment_id=db_attachment.id,
                        tenant_id=tenant_id,
                        storage_key=db_attachment.storage_key,
                    )
                logger.warning(
                    "[MULTIMEDIA][OUTBOUND] resolve_attachment message_id=%s strategy=unmatched_fallback type=%s resolved_url=%s",
                    message_id,
                    item.type.value,
                    bool(provider_url),
                )
                resolved.append(item.model_copy(update={"provider_url": provider_url}))
                continue
            logger.warning(
                "[MULTIMEDIA][OUTBOUND] resolve_attachment message_id=%s strategy=unresolved type=%s provider_media_id=%s",
                message_id,
                item.type.value,
                item.provider_media_id,
            )
            resolved.append(item)
        return resolved

    @staticmethod
    def _resolve_public_api_base_url(channel_config: Optional[dict[str, Any]]) -> Optional[str]:
        if not isinstance(channel_config, dict):
            return None
        for key in ("public_api_base_url", "multimedia_public_base_url", "backend_public_base_url"):
            value = channel_config.get(key)
            if isinstance(value, str) and value.strip():
                return value.rstrip("/")
        return None

    def _build_internal_download_url(
        self,
        *,
        base_url: str,
        attachment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        storage_key: Optional[str],
    ) -> str:
        access_ref = self.attachment_service.generate_access_reference(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            storage_key=storage_key,
            ttl_seconds=300,
        )
        query = urlencode({"access_ref": access_ref})
        return f"{base_url}/api/v1/attachments/{attachment_id}/download?{query}"

    def create_inbound_message(
        self,
        normalized: NormalizedMessage,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> Optional[Message]:
        if tenant_id is None:
            raise ValueError("tenant_id is required for inbound message creation")
        conversation = self.get_or_create_conversation(normalized, tenant_id=tenant_id)
        if not conversation:
            return None
        return self.save_inbound_message(conversation, normalized)

    def send_message(
        self,
        data: MessageSendRequest,
        tenant_id: uuid.UUID,
    ) -> dict:
        logger.warning(
            "[MULTIMEDIA][OUTBOUND] send_message_request tenant_id=%s conversation_id=%s content_len=%s attachments_count=%s attachments=%s",
            tenant_id,
            data.conversation_id,
            len(data.content or ""),
            len(data.attachments or []),
            [
                {
                    "type": item.type.value,
                    "filename": item.filename,
                    "mime_type": item.mime_type,
                    "size_bytes": item.size_bytes,
                    "provider_media_id": item.provider_media_id,
                    "has_provider_url": bool(item.provider_url),
                }
                for item in (data.attachments or [])
            ],
        )
        conversation = self.repository.get_conversation_by_id_and_tenant(data.conversation_id, tenant_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {data.conversation_id}")

        message = self.save_outbound_message(
            conversation,
            data.content,
            attachments=data.attachments,
            raw_payload=data.model_dump(mode="json"),
            replied_to_message_id=data.reply_to_message_id or data.reply_to_id,
        )
        dispatch_result = self.dispatch_to_channel(
            conversation,
            message,
            attachments=data.attachments,
            reply_to_id=data.reply_to_message_id or data.reply_to_id,
        )
        persisted_attachments = self.attachment_service.list_by_message_id_and_tenant(message.id, tenant_id)
        logger.warning(
            "[MULTIMEDIA][OUTBOUND] send_message_persisted tenant_id=%s message_id=%s message_type=%s has_media=%s persisted_attachments_count=%s",
            tenant_id,
            message.id,
            message.message_type,
            message.has_media,
            len(persisted_attachments),
        )
        return dispatch_result

    def list_messages(
        self,
        conversation_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[MessageResponse]:
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

        identity = self.repository.get_contact_identity(
            channel.type,
            normalized.sender_external_id,
            channel.tenant_id,
        )
        if identity:
            return identity.contact_id

        contact = self.repository.create_contact(
            tenant_id=channel.tenant_id,
            name=normalized.sender_name,
            phone=normalized.sender_external_id if channel.type in ("whatsapp", "sms") else None,
        )
        self.repository.create_contact_identity(
            contact_id=contact.id,
            tenant_id=channel.tenant_id,
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

        identity = self.repository.get_contact_identity(channel.type, external_id, tenant_id)
        return identity.contact_id if identity else None

    def _to_response(self, message: Message) -> MessageResponse:
        return _serialize_message(message)

    def _publish_new_message_event(self, message: Message) -> None:
        serialized = jsonable_encoder(self._to_response(message))
        event_bus.publish(
            "new_message",
            {
                "type": "new_message",
                "conversation_id": str(message.conversation_id),
                "message": serialized,
            },
            tenant_id=message.tenant_id,
        )

    def _persist_normalized_attachments(self, message: Message, normalized: NormalizedMessage) -> None:
        if not normalized.attachments:
            return

        logger.warning(
            "[MULTIMEDIA][PERSIST] inbound_attachments_start message_id=%s tenant_id=%s attachments_count=%s",
            message.id,
            message.tenant_id,
            len(normalized.attachments),
        )
        records: list[AttachmentCreate] = []
        for item in normalized.attachments:
            metadata_json = item.metadata.model_dump(mode="json") if item.metadata else {}
            if item.base64_data:
                metadata_json["base64_data"] = item.base64_data
            if item.provider_url:
                metadata_json["provider_url"] = item.provider_url
            if item.provider_media_id:
                metadata_json["provider_media_id"] = item.provider_media_id

            has_source = bool(item.provider_url or item.provider_media_id or item.base64_data)
            records.append(
                AttachmentCreate(
                    message_id=message.id,
                    tenant_id=message.tenant_id,
                    attachment_type=item.type,
                    storage_backend=item.metadata.storage_backend,
                    storage_key=None,
                    provider_media_id=item.provider_media_id,
                    provider_url=item.provider_url,
                    mime_type=item.mime_type,
                    filename=item.filename,
                    extension=item.extension,
                    size_bytes=item.size_bytes,
                    checksum_sha256=item.metadata.checksum_sha256,
                    download_status=(
                        item.metadata.download_status
                        if not has_source
                        else AttachmentDownloadStatus.PENDING
                    ),
                    metadata_json=metadata_json,
                    width=item.width,
                    height=item.height,
                    duration_ms=item.duration_ms,
                    caption=item.caption,
                    provider_timestamp=normalized.timestamp,
                    file_data=None,
                )
            )

        persisted = self.attachment_service.save_attachments_bulk(records)

        self.repository.commit()
        for attachment in persisted:
            logger.warning(
                "[MULTIMEDIA][PERSIST] attachment_saved attachment_id=%s message_id=%s type=%s backend=%s status=%s provider_media_id=%s has_provider_url=%s",
                attachment.id,
                message.id,
                attachment.attachment_type.value,
                attachment.storage_backend.value,
                attachment.download_status.value,
                attachment.provider_media_id,
                bool(attachment.provider_url),
            )
            if attachment.download_status.value != "pending":
                continue
            logger.warning(
                "[MULTIMEDIA][DOWNLOAD] queued attachment_id=%s tenant_id=%s",
                attachment.id,
                message.tenant_id,
            )
            attachment_download_dispatcher.enqueue(
                AttachmentDownloadJob(
                    attachment_id=attachment.id,
                    tenant_id=message.tenant_id,
                )
            )

    def _persist_outbound_attachments(
        self,
        message: Message,
        tenant_id: uuid.UUID,
        attachments: Optional[list[OutboundAttachment]],
    ) -> None:
        if not attachments:
            return

        logger.warning(
            "[MULTIMEDIA][OUTBOUND] persist_attachments_start message_id=%s tenant_id=%s attachments_count=%s",
            message.id,
            tenant_id,
            len(attachments),
        )
        records: list[AttachmentCreate] = []
        for item in attachments:
            metadata_json = dict(item.metadata or {})
            if item.provider_media_id:
                metadata_json["provider_media_id"] = item.provider_media_id
            records.append(
                AttachmentCreate(
                    message_id=message.id,
                    tenant_id=tenant_id,
                    attachment_type=item.type,
                    storage_backend=StorageBackend.PROVIDER,
                    provider_media_id=item.provider_media_id,
                    provider_url=item.provider_url,
                    mime_type=item.mime_type,
                    filename=item.filename,
                    size_bytes=item.size_bytes,
                    caption=item.caption,
                    metadata_json=metadata_json or None,
                    download_status=AttachmentDownloadStatus.NOT_REQUESTED,
                )
            )

        persisted = self.attachment_service.save_attachments_bulk(records)
        for attachment in persisted:
            logger.warning(
                "[MULTIMEDIA][OUTBOUND] attachment_saved attachment_id=%s message_id=%s type=%s provider_media_id=%s has_provider_url=%s",
                attachment.id,
                message.id,
                attachment.attachment_type.value,
                attachment.provider_media_id,
                bool(attachment.provider_url),
            )
        self.repository.commit()


# Backward-compatible wrappers

def ensure_message_id(message: object) -> str:
    return _ensure_message_id_value(message)


def get_or_create_conversation(db: Session, normalized: NormalizedMessage) -> Optional[Conversation]:
    raise ValueError("tenant_id is required for get_or_create_conversation")


def get_or_create_conversation_with_tenant(
    db: Session,
    normalized: NormalizedMessage,
    tenant_id: uuid.UUID,
) -> Optional[Conversation]:
    return MessageService(db).get_or_create_conversation(normalized, tenant_id=tenant_id)


def save_inbound_message(db: Session, conversation: Conversation, normalized: NormalizedMessage) -> Optional[Message]:
    return MessageService(db).save_inbound_message(conversation, normalized)


def save_outbound_message(
    db: Session,
    conversation: Conversation,
    content: str,
    attachments: Optional[list] = None,
    raw_payload: Optional[dict] = None,
    replied_to_message_id: Optional[str] = None,
) -> Message:
    return MessageService(db).save_outbound_message(
        conversation,
        content,
        attachments,
        raw_payload,
        replied_to_message_id,
    )


def dispatch_to_channel(
    db: Session,
    conversation: Conversation,
    message: Message,
    attachments: Optional[list] = None,
    reply_to_id: Optional[str] = None,
) -> dict:
    return MessageService(db).dispatch_to_channel(conversation, message, attachments, reply_to_id)


def create_inbound_message(db: Session, normalized: NormalizedMessage) -> Optional[Message]:
    raise ValueError("tenant_id is required for create_inbound_message")


def create_inbound_message_with_tenant(
    db: Session,
    normalized: NormalizedMessage,
    tenant_id: uuid.UUID,
) -> Optional[Message]:
    return MessageService(db).create_inbound_message(normalized, tenant_id=tenant_id)


def send_message(db: Session, data: dict) -> dict:
    raise ValueError("tenant_id is required for send_message")


def send_message_with_tenant(db: Session, data: dict, tenant_id: uuid.UUID) -> dict:
    request = MessageSendRequest(**data)
    return MessageService(db).send_message(request, tenant_id=tenant_id)


def get_messages(db: Session, conversation_id: uuid.UUID, tenant_id: uuid.UUID) -> list[dict]:
    messages = MessageService(db).list_messages(conversation_id, tenant_id=tenant_id)
    return [jsonable_encoder(m) for m in messages]


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
    return jsonable_encoder(_serialize_message(message))
