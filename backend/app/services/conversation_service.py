import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.models.conversation import Conversation, Message
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ContactChatResponse, ConversationResponse
from app.services.auth.access_service import can_access_tenant_resource
from app.services.channel_config_service import ChannelConfigService
from app.services.conversation.mode_service import InvalidChannelConfigError
from app.services.conversation.lifecycle_service import ConversationLifecycleService
from app.services.conversation.guards import is_config_valid
from app.services.realtime_service import event_bus


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ConversationRepository(db)

    def _build_response(self, conversation: Conversation) -> ConversationResponse:
        channel = conversation.chat_thread.channel if conversation.chat_thread else None
        channel_config = channel.config_jsonb if channel and isinstance(channel.config_jsonb, dict) else {}
        channel_provider = channel_config.get("provider") if isinstance(channel_config.get("provider"), str) else None
        channel_config_id = self.repository.get_active_channel_config_id_by_channel_id(
            conversation.chat_thread.channel_id
        )
        return ConversationResponse(
            id=conversation.id,
            tenant_id=conversation.tenant_id,
            chat_thread_id=conversation.chat_thread_id,
            channel_id=conversation.chat_thread.channel_id,
            channel_name=channel.name if channel else None,
            channel_type=channel.type if channel else None,
            channel_provider=channel_provider,
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
    ) -> list[ContactChatResponse]:
        if user_id is None or tenant_id is None:
            return []

        conversations = self.repository.get_all_by_tenant(tenant_id)
        return [self._build_response(c) for c in conversations]

    def get_contact_chats(
        self,
        user_id: Optional[uuid.UUID] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> list[ConversationResponse]:
        if user_id is None or tenant_id is None:
            return []

        conversations = self.repository.get_all_by_tenant(tenant_id)
        channel_type_keys_cache: dict[uuid.UUID, tuple[set[str], str | None]] = {}
        by_contact: dict[uuid.UUID, list[Conversation]] = {}
        thread_to_contact: dict[uuid.UUID, uuid.UUID] = {}
        mapped_conversation_ids: set[uuid.UUID] = set()
        for conversation in conversations:
            contact = self.repository.get_contact_for_conversation(conversation.id)
            if contact is None:
                continue
            by_contact.setdefault(contact.id, []).append(conversation)
            thread_to_contact[conversation.chat_thread_id] = contact.id
            mapped_conversation_ids.add(conversation.id)

        for conversation in conversations:
            if conversation.id in mapped_conversation_ids:
                continue
            mapped_contact_id = thread_to_contact.get(conversation.chat_thread_id)
            if mapped_contact_id is None:
                continue
            by_contact.setdefault(mapped_contact_id, []).append(conversation)

        items: list[ContactChatResponse] = []
        touched_contacts = False
        for contact_id, rows in by_contact.items():
            rows.sort(
                key=lambda c: (
                    c.last_message_at or c.started_at,
                    c.started_at,
                ),
                reverse=True,
            )
            latest = rows[0]
            active = next((c for c in rows if c.status == "open"), latest)
            contact = self.repository.get_contact_for_conversation(latest.id)
            channel_id = latest.chat_thread.channel_id if latest.chat_thread else None
            normalized_type: str | None = None
            if contact and channel_id:
                normalized_type = self._normalize_contact_type(contact.current_type, channel_id, channel_type_keys_cache)
                if normalized_type != contact.current_type:
                    contact.current_type = normalized_type
                    touched_contacts = True
            latest_message = self.repository.get_latest_message_for_conversation(latest.id)
            conversation_ids = [row.id for row in rows]
            messages_count_stmt = select(func.count(Message.id)).where(Message.conversation_id.in_(conversation_ids))
            messages_count = int(self.db.execute(messages_count_stmt).scalar() or 0)
            items.append(
                ContactChatResponse(
                    contact_id=contact_id,
                    contact_name=(contact.name if contact else None),
                    contact_phone=(contact.phone if contact else None),
                    contact_current_type=(normalized_type if contact else None),
                    active_conversation_id=active.id,
                    active_conversation_status=active.status,
                    active_conversation_mode=active.mode,  # type: ignore[arg-type]
                    channel_id=latest.chat_thread.channel_id if latest.chat_thread else None,
                    channel_name=latest.chat_thread.channel.name if latest.chat_thread and latest.chat_thread.channel else None,
                    channel_type=latest.chat_thread.channel.type if latest.chat_thread and latest.chat_thread.channel else None,
                    channel_provider=(
                        latest.chat_thread.channel.config_jsonb.get("provider")
                        if latest.chat_thread and latest.chat_thread.channel and isinstance(latest.chat_thread.channel.config_jsonb, dict)
                        else None
                    ),
                    channel_config_id=(
                        self.repository.get_active_channel_config_id_by_channel_id(latest.chat_thread.channel_id)
                        if latest.chat_thread
                        else None
                    ),
                    last_message_at=latest.last_message_at or latest.started_at,
                    last_message=(latest_message.content_text if latest_message else None),
                    unread_count=0,
                    conversations_count=len(rows),
                    messages_count=messages_count,
                )
            )

        items.sort(key=lambda c: c.last_message_at, reverse=True)
        if touched_contacts:
            self.db.commit()
        return items

    def set_contact_type(
        self,
        contact_id: uuid.UUID,
        type_key: str,
        tenant_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> str | None:
        contact = self.repository.get_contact_by_id_and_tenant(contact_id, tenant_id)
        if contact is None:
            raise LookupError(f"Contact not found: {contact_id}")
        if user is not None and not can_access_tenant_resource(self.db, user, contact.tenant_id):
            raise LookupError(f"Contact not found: {contact_id}")

        channel_id = self.repository.get_latest_channel_id_for_contact(contact_id, tenant_id)
        if channel_id is None:
            raise LookupError(f"No channel context found for contact: {contact_id}")
        resolved_type_key = self._normalize_contact_type(type_key, channel_id, {})
        contact.current_type = resolved_type_key
        self.db.commit()

        event_bus.publish(
            "contact_type_updated",
            {
                "type": "contact_type_updated",
                "contact_id": str(contact.id),
                "type_key": resolved_type_key,
            },
            tenant_id=contact.tenant_id,
        )
        return resolved_type_key

    def _normalize_contact_type(
        self,
        type_key: str | None,
        channel_id: uuid.UUID,
        cache: dict[uuid.UUID, tuple[set[str], str | None]],
    ) -> str | None:
        if channel_id in cache:
            available_keys, configured_default = cache[channel_id]
        else:
            available_keys: set[str] = set()
            configured_default: str | None = None
            try:
                config = ChannelConfigService.get_channel_config(self.db, channel_id)
                raw = config.user_types_jsonb if isinstance(config.user_types_jsonb, dict) else {}
                if isinstance(raw, dict):
                    maybe_default = raw.get("default_type")
                    configured_default = maybe_default.strip() if isinstance(maybe_default, str) and maybe_default.strip() else None
                    raw_types = raw.get("types")
                    if isinstance(raw_types, list):
                        for item in raw_types:
                            if not isinstance(item, dict):
                                continue
                            key = item.get("key")
                            if isinstance(key, str) and key.strip():
                                available_keys.add(key.strip())
            except Exception:
                available_keys = set()
                configured_default = None
            cache[channel_id] = (available_keys, configured_default)

        candidate = type_key.strip() if isinstance(type_key, str) and type_key.strip() else None
        if candidate == "default":
            candidate = "nuevo"
        if candidate and candidate in available_keys:
            return candidate
        if "nuevo" in available_keys:
            return "nuevo"
        if configured_default and configured_default in available_keys:
            return configured_default
        if available_keys:
            return sorted(available_keys)[0]
        return candidate

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

        previous_conversation_id = conversation.id
        previous_mode = conversation.mode
        lifecycle = ConversationLifecycleService(self.db)
        if mode == "ai":
            channel_config = ChannelConfigService.get_channel_config(self.db, conversation.chat_thread.channel_id)
            if not is_config_valid(channel_config):
                raise InvalidChannelConfigError("Config incompleta")
            conversation = lifecycle.switch_mode_with_new_session(
                conversation=conversation,
                target_mode="ai",
                resolution="manual_ai_reactivation",
            )
        else:
            conversation = lifecycle.switch_mode_with_new_session(
                conversation=conversation,
                target_mode="human",
                resolution="human_handoff",
            )

        contact = self.repository.get_contact_for_conversation(conversation.id) or self.repository.get_contact_for_conversation(
            previous_conversation_id
        )
        event_bus.publish(
            "conversation_changed",
            {
                "type": "conversation_changed",
                "contact_id": str(contact.id) if contact else None,
                "old_conversation_id": str(previous_conversation_id),
                "new_conversation_id": str(conversation.id),
                "old_mode": previous_mode,
                "mode": conversation.mode,
            },
            tenant_id=conversation.tenant_id,
        )

        return conversation


def get_conversations(
    db: Session,
    user_id: Optional[uuid.UUID] = None,
    tenant_id: Optional[uuid.UUID] = None,
) -> list[ConversationResponse]:
    return ConversationService(db).get_conversations(user_id=user_id, tenant_id=tenant_id)
