import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.schemas.conversation import (
    ConversationModeUpdateRequest,
    ConversationModeUpdateResponse,
    ConversationResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(tags=["conversations"])


@router.get("/", response_model=list[ConversationResponse])
async def read_conversations(
    #current_user: tuple[uuid.UUID, str] = Depends(get_current_user),
    #_: None = Depends(require_permission("conversations.read")),
    db: Session = Depends(get_db),
):
    #user_id = current_user[0]
    service = ConversationService(db)
    return service.get_conversations(user_id=None)


@router.patch("/{id}/mode", response_model=ConversationModeUpdateResponse)
async def update_conversation_mode(
    id: uuid.UUID,
    payload: ConversationModeUpdateRequest,
    db: Session = Depends(get_db),
):
    service = ConversationService(db)
    try:
        conversation = service.set_mode(id, payload.mode)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ConversationModeUpdateResponse(id=str(conversation.id), mode=conversation.mode)
