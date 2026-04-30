import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.api.routes.auth import get_current_user
from app.db.session import get_db
import app.services.conversation_service as conversation_service
from app.models.conversation import Conversation
from app.services.bot_config_service import BotConfigService
from app.services.conversation.mode_service import InvalidBotConfigError, disable_ai, enable_ai

router = APIRouter(tags=["conversations"])


class ConversationModeUpdateRequest(BaseModel):
    mode: Literal["ai", "human"]


class ConversationModeUpdateResponse(BaseModel):
    id: str
    mode: Literal["ai", "human"]


@router.get("/")
async def read_conversations(
    #current_user: tuple[uuid.UUID, str] = Depends(get_current_user),
    #_: None = Depends(require_permission("conversations.read")),
    db: Session = Depends(get_db),
):
    #user_id = current_user[0]
    return conversation_service.get_conversations(db, user_id=None)


@router.patch("/{id}/mode", response_model=ConversationModeUpdateResponse)
async def update_conversation_mode(
    id: uuid.UUID,
    payload: ConversationModeUpdateRequest,
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {id}",
        )

    if payload.mode == "ai":
        channel_config = BotConfigService.get_channel_config(
            db,
            conversation.chat_thread.channel_id,
        )
        try:
            enable_ai(db, conversation, channel_config)
        except InvalidBotConfigError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Config incompleta",
            )
    else:
        disable_ai(db, conversation)

    return ConversationModeUpdateResponse(id=str(conversation.id), mode=conversation.mode)
