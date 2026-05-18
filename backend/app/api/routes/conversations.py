import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant, get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.schemas.conversation import (
    ContactTypeUpdateRequest,
    ContactTypeUpdateResponse,
    ContactChatResponse,
    ConversationModeUpdateRequest,
    ConversationModeUpdateResponse,
    ConversationResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
async def read_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("conversations.read")),
):
    service = ConversationService(db)
    return service.get_conversations(user_id=current_user.id, tenant_id=current_tenant_id)


@router.get("/contacts", response_model=list[ContactChatResponse])
async def read_contact_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("conversations.read")),
):
    service = ConversationService(db)
    return service.get_contact_chats(user_id=current_user.id, tenant_id=current_tenant_id)


@router.patch("/{id}/mode", response_model=ConversationModeUpdateResponse)
async def update_conversation_mode(
    id: uuid.UUID,
    payload: ConversationModeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("conversations.update")),
):
    service = ConversationService(db)
    try:
        conversation = service.set_mode(
            id,
            payload.mode,
            tenant_id=current_tenant_id,
            user=current_user,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ConversationModeUpdateResponse(id=str(conversation.id), mode=conversation.mode)


@router.patch("/contacts/{contact_id}/type", response_model=ContactTypeUpdateResponse)
async def update_contact_type(
    contact_id: uuid.UUID,
    payload: ContactTypeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("conversations.update")),
):
    service = ConversationService(db)
    try:
        resolved_type_key = service.set_contact_type(
            contact_id=contact_id,
            type_key=payload.type_key,
            tenant_id=current_tenant_id,
            user=current_user,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ContactTypeUpdateResponse(contact_id=str(contact_id), type_key=resolved_type_key or "")

