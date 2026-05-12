from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.integration_auth import require_webhook_auth
from app.db.session import get_db
from app.schemas.api_key import WebhookAuthContext
from app.services.inbound.webhook_dispatcher import WebhookJob, webhook_dispatcher
from app.services.inbound.webhook_handler import (
    resolve_webhook_channel_and_provider,
    validate_minimal_webhook_payload,
)

router = APIRouter(tags=["webhooks"])


@router.post("/{channel_id}")
async def receive_webhook(
    channel_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    auth_ctx: WebhookAuthContext = Depends(require_webhook_auth),
):
    _ = channel_id

    try:
        safe_payload = validate_minimal_webhook_payload(payload)
        _, provider_name = resolve_webhook_channel_and_provider(
            db,
            channel_id=auth_ctx.channel_id,
            tenant_id=auth_ctx.tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    webhook_dispatcher.enqueue(
        WebhookJob(
            tenant_id=auth_ctx.tenant_id,
            channel_id=auth_ctx.channel_id,
            provider_name=provider_name,
            payload=safe_payload,
        )
    )
    return {"status": "ok"}
