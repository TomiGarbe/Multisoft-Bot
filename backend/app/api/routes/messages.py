import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.message import MessageResponse, MessageSendRequest, MessageSendResponse
from app.services.message_service import MessageService

router = APIRouter(tags=["messages"])


@router.post("/send", response_model=MessageSendResponse)
async def send_message_endpoint(
    request: MessageSendRequest,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.send")),
):
    service = MessageService(db)
    try:
        service.send_message(request, tenant_id=current_tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return MessageSendResponse(status="sent")


@router.get("/{conversation_id}", response_model=list[MessageResponse])
async def get_messages_endpoint(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    service = MessageService(db)
    try:
        return service.list_messages(conversation_id, tenant_id=current_tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
