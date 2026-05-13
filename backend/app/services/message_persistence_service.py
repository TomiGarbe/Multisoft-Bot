from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message
from app.repositories.message_repository import MessageRepository


class MessagePersistenceService:
    def __init__(self, db: Session) -> None:
        self.repository = MessageRepository(db)

    def save_message(self, message: Message, conversation: Conversation | None = None) -> Message:
        self.repository.create_message(message)
        if conversation is not None:
            self.repository.touch_conversation_last_message(conversation)
        self.repository.commit()
        self.repository.refresh(message)
        return message
