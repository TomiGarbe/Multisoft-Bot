from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant, get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.bot_action import (
    BotActionCreate,
    BotActionEnabledUpdate,
    BotActionListResponse,
    BotActionResponse,
    BotActionTestRequest,
    BotActionTestResponse,
    BotActionUpdate,
)
from app.services.bot_actions import ActionExecutionError, ActionExecutionService
from app.services.bot_action_service import BotActionService

router = APIRouter(tags=["bot-actions"])


@router.get("", response_model=list[BotActionListResponse])
async def list_bot_actions(
    enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    channel_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.read")),
):
    return BotActionService(db).list_actions(
        tenant_id=current_tenant_id,
        enabled=enabled,
        search=search,
        channel_id=channel_id,
    )


@router.get("/{id}", response_model=BotActionResponse)
async def get_bot_action(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.read")),
):
    try:
        return BotActionService(db).get_action(tenant_id=current_tenant_id, action_id=id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("", response_model=BotActionResponse, status_code=status.HTTP_201_CREATED)
async def create_bot_action(
    payload: BotActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.create")),
):
    try:
        return BotActionService(db).create_action(
            tenant_id=current_tenant_id,
            user_id=current_user.id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{id}", response_model=BotActionResponse)
async def update_bot_action(
    id: uuid.UUID,
    payload: BotActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.update")),
):
    try:
        return BotActionService(db).update_action(
            tenant_id=current_tenant_id,
            action_id=id,
            user_id=current_user.id,
            payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot_action(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.delete")),
):
    try:
        BotActionService(db).delete_action(tenant_id=current_tenant_id, action_id=id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{id}/enabled", response_model=BotActionResponse)
async def set_bot_action_enabled(
    id: uuid.UUID,
    payload: BotActionEnabledUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.update")),
):
    try:
        return BotActionService(db).set_enabled(
            tenant_id=current_tenant_id,
            action_id=id,
            user_id=current_user.id,
            payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{id}/test", response_model=BotActionTestResponse)
async def test_bot_action(
    id: uuid.UUID,
    payload: BotActionTestRequest,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("bot_actions.update")),
):
    try:
        result = await ActionExecutionService(db).execute_test_action(
            tenant_id=current_tenant_id,
            action_id=id,
            variables=payload.variables,
        )
        return BotActionTestResponse.model_validate(result)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ActionExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.code)

