from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.integration_auth import require_webhook_auth
from app.core.tenant import tenant_scope
from app.db.session import get_db
from app.schemas.api_key import WebhookAuthContext
from app.services.inbound.webhook_handler import handle_webhook

router = APIRouter(tags=["webhooks"])


@router.post("/{channel_id}")
async def receive_webhook(
    channel_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    auth_ctx: WebhookAuthContext = Depends(require_webhook_auth),
):
    with tenant_scope(auth_ctx.tenant_id):
        await handle_webhook(db, str(auth_ctx.channel_id), payload)
    return {"status": "ok"}
