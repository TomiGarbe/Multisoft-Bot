import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
logger = logging.getLogger(__name__)


def _pretty_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        return str(value)


@router.post("/{channel_id}")
async def receive_webhook(
    channel_id: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    auth_ctx: WebhookAuthContext = Depends(require_webhook_auth),
):
    _ = channel_id
    raw_body = await request.body()
    headers = dict(request.headers)
    logger.warning("[WEBHOOK][HEADERS] %s", _pretty_json(headers))
    logger.warning("[WEBHOOK][RAW] %s", raw_body.decode("utf-8", errors="replace"))
    logger.warning("[WEBHOOK][PARSED] %s", _pretty_json(payload))
    logger.warning(
        "[WEBHOOK][META] content_type=%s user_agent=%s path=%s",
        request.headers.get("content-type"),
        request.headers.get("user-agent"),
        str(request.url.path),
    )

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
