from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.services.realtime_service import event_bus


class ConversationLifecycleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_open_conversations(self, *, tenant_id: uuid.UUID, thread_id: uuid.UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.chat_thread_id == thread_id,
                Conversation.status == "open",
            )
            .order_by(Conversation.started_at.desc(), Conversation.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def ensure_single_open_conversation(
        self,
        *,
        tenant_id: uuid.UUID,
        thread_id: uuid.UUID,
    ) -> Conversation | None:
        open_rows = self.get_open_conversations(tenant_id=tenant_id, thread_id=thread_id)
        if not open_rows:
            return None
        winner = open_rows[0]
        for duplicate in open_rows[1:]:
            self.close_conversation(duplicate, resolution="deduplicated_open_sessions", commit=False)
        return winner

    def create_conversation(
        self,
        *,
        tenant_id: uuid.UUID,
        thread_id: uuid.UUID,
        mode: str,
    ) -> Conversation:
        now = datetime.now(timezone.utc)
        conversation = Conversation(
            tenant_id=tenant_id,
            chat_thread_id=thread_id,
            status="open",
            mode=mode,
            started_at=now,
            last_message_at=now,
        )
        self.db.add(conversation)
        self.db.flush()
        self._emit_lifecycle_event("conversation_opened", conversation, {"mode": mode})
        return conversation

    def close_conversation(
        self,
        conversation: Conversation,
        *,
        resolution: str,
        commit: bool = True,
    ) -> Conversation:
        if conversation.status != "open":
            return conversation
        now = datetime.now(timezone.utc)
        conversation.status = "closed"
        conversation.closed_at = now
        conversation.last_message_at = conversation.last_message_at or now
        self.db.flush()
        self._emit_lifecycle_event(
            "conversation_closed",
            conversation,
            {"resolution": resolution, "mode": conversation.mode},
        )
        if commit:
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def switch_mode_with_new_session(
        self,
        *,
        conversation: Conversation,
        target_mode: str,
        resolution: str,
    ) -> Conversation:
        if conversation.status != "open":
            return conversation
        if conversation.mode == target_mode:
            return conversation

        self.close_conversation(conversation, resolution=resolution, commit=False)
        opened = self.create_conversation(
            tenant_id=conversation.tenant_id,
            thread_id=conversation.chat_thread_id,
            mode=target_mode,
        )
        self.db.commit()
        self.db.refresh(opened)
        return opened

    def _emit_lifecycle_event(self, event_name: str, conversation: Conversation, extra: dict[str, str]) -> None:
        payload = {
            "type": event_name,
            "conversation_id": str(conversation.id),
            "chat_thread_id": str(conversation.chat_thread_id),
            "status": conversation.status,
            "mode": conversation.mode,
            **extra,
        }
        event_bus.publish(event_name, payload, tenant_id=conversation.tenant_id)
