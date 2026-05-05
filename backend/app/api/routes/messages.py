import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.message import MessageResponse, MessageSendRequest, MessageSendResponse
from app.services.message_service import MessageService

router = APIRouter(tags=["messages"])


@router.post("/send", response_model=MessageSendResponse)
async def send_message_endpoint(
    request: MessageSendRequest,
    #_: None = Depends(require_permission("messages.send")),
    db: Session = Depends(get_db),
):
    service = MessageService(db)
    service.send_message(request)
    return MessageSendResponse(status="sent")


@router.get("/{conversation_id}", response_model=list[MessageResponse])
async def get_messages_endpoint(
    conversation_id: uuid.UUID,
    #_: None = Depends(require_permission("messages.read")),
    db: Session = Depends(get_db),
):
    service = MessageService(db)
    return service.list_messages(conversation_id)
