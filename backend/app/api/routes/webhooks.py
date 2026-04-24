from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.inbound.webhook_handler import handle_webhook

router = APIRouter(tags=["webhooks"])


@router.post("/{channel_id}")
async def receive_webhook(channel_id: str, payload: dict, db: Session = Depends(get_db)):
    handle_webhook(db, channel_id, payload)
    return {"status": "ok"}
