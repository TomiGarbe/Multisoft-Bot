import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
import app.services.message_service as message_service

router = APIRouter(tags=["messages"])


@router.post("/send")
async def send_message_endpoint(
    request: dict,
    _: None = Depends(require_permission("messages.send")),
    db: Session = Depends(get_db),
):
    message_service.send_message(db, request)
    return {"status": "sent"}


@router.get("/{conversation_id}")
async def get_messages_endpoint(
    conversation_id: uuid.UUID,
    _: None = Depends(require_permission("messages.read")),
    db: Session = Depends(get_db),
):
    return message_service.get_messages(db, conversation_id)
