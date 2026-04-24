import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.api.routes.auth import get_current_user
from app.db.session import get_db
import app.services.conversation_service as conversation_service

router = APIRouter(tags=["conversations"])


@router.get("/")
async def read_conversations(
    current_user: tuple[uuid.UUID, str] = Depends(get_current_user),
    _: None = Depends(require_permission("conversations.read")),
    db: Session = Depends(get_db),
):
    user_id = current_user[0]
    return conversation_service.get_conversations(db, user_id)
