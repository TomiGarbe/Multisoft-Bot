from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.bot_action import BotActionListResponse, ChannelActionReplaceRequest
from app.services.bot_action_service import BotActionService

router = APIRouter(tags=["channel-bot-config-actions"])


@router.get("/{id}/actions", response_model=list[BotActionListResponse])
async def get_channel_assigned_actions(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("channel_config.read")),
):
    try:
        return BotActionService(db).get_channel_actions(
            tenant_id=current_tenant_id,
            channel_bot_config_id=id,
        )
    except LookupError as exc:
        detail = str(exc)
        status_code = status.HTTP_403_FORBIDDEN if detail == "cross_tenant_access" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=detail)


@router.put("/{id}/actions", response_model=list[BotActionListResponse])
async def replace_channel_assigned_actions(
    id: uuid.UUID,
    payload: ChannelActionReplaceRequest,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("channel_config.update")),
):
    try:
        return BotActionService(db).replace_channel_actions(
            tenant_id=current_tenant_id,
            channel_bot_config_id=id,
            action_ids=payload.action_ids,
        )
    except LookupError as exc:
        detail = str(exc)
        status_code = status.HTTP_403_FORBIDDEN if detail == "cross_tenant_access" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=detail)
