import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant, get_current_user, require_super_admin
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.models.user import UserType
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import (
    create_user,
    delete_user,
    get_global_users,
    get_user_by_id,
    get_users,
    update_user,
)


router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


def _safe_user_payload(payload: UserCreate) -> dict:
    data = payload.model_dump()
    if "password" in data:
        data["password"] = "***"
    return data


@router.get("", response_model=list[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    __: None = Depends(require_permission("users.read")),
):
    return get_users(db, tenant_id=current_tenant_id, skip=skip, limit=limit, current_user_id=None)


@router.get("/global", response_model=list[UserResponse])
async def read_global_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    ___: None = Depends(require_super_admin),
    __: None = Depends(require_permission("users.read")),
):
    return get_global_users(db, skip=skip, limit=limit)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    __: None = Depends(require_permission("users.create")),
):
    safe_payload = _safe_user_payload(user_data)
    logger.info("[USERS][CREATE][REQUEST] payload=%s", safe_payload)
    try:
        final_user_type = user_data.user_type or (UserType.BACKDOOR if user_data.is_backdoor else UserType.USER)
        final_tenant_ids = user_data.tenant_ids or ([] if user_data.tenant_id is None else [user_data.tenant_id])
        inferred_tenant_ids = final_tenant_ids
        if final_user_type == UserType.USER and not inferred_tenant_ids:
            inferred_tenant_ids = [current_tenant_id]

        return create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            role_id=user_data.role_id,
            permissions=user_data.permissions,
            is_active=user_data.is_active,
            is_backdoor=user_data.is_backdoor,
            user_type=user_data.user_type,
            tenant_id=inferred_tenant_ids[0] if inferred_tenant_ids else user_data.tenant_id,
            tenant_ids=inferred_tenant_ids,
        )
    except ValueError as exc:
        logger.warning(
            "[USERS][CREATE][VALIDATION_ERROR] detail=%s role_id=%s permissions=%s tenant_id=%s tenant_ids=%s payload=%s",
            str(exc),
            str(user_data.role_id) if user_data.role_id else None,
            [str(permission_id) for permission_id in user_data.permissions],
            str(user_data.tenant_id) if user_data.tenant_id else None,
            [str(tenant_id) for tenant_id in user_data.tenant_ids],
            safe_payload,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        logger.warning(
            "[USERS][CREATE][FAILED] detail=%s role_id=%s permissions=%s tenant_id=%s tenant_ids=%s payload=%s",
            str(exc),
            str(user_data.role_id) if user_data.role_id else None,
            [str(permission_id) for permission_id in user_data.permissions],
            str(user_data.tenant_id) if user_data.tenant_id else None,
            [str(tenant_id) for tenant_id in user_data.tenant_ids],
            safe_payload,
            exc_info=True,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception(
            "[USERS][CREATE][FAILED] detail=%s role_id=%s permissions=%s tenant_id=%s tenant_ids=%s payload=%s",
            str(exc),
            str(user_data.role_id) if user_data.role_id else None,
            [str(permission_id) for permission_id in user_data.permissions],
            str(user_data.tenant_id) if user_data.tenant_id else None,
            [str(tenant_id) for tenant_id in user_data.tenant_ids],
            safe_payload,
        )
        raise


@router.post("/admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    ___: None = Depends(require_super_admin),
    __: None = Depends(require_permission("users.create_admin")),
):
    try:
        return create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            is_active=user_data.is_active,
            user_type=UserType.ADMINISTRADOR,
            tenant_ids=user_data.tenant_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/backdoor", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_backdoor_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    ___: None = Depends(require_super_admin),
    __: None = Depends(require_permission("users.create_backdoor")),
):
    try:
        return create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            is_active=user_data.is_active,
            user_type=UserType.BACKDOOR,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.update")),
):
    target_user = get_user_by_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target_user.user_type != UserType.USER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        user = update_user(
            db=db,
            user_id=user_id,
            **user_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/global/{user_id}", response_model=UserResponse)
async def update_global_user_endpoint(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    ___: None = Depends(require_super_admin),
    __: None = Depends(require_permission("users.update")),
):
    target_user = get_user_by_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target_user.user_type not in (UserType.ADMINISTRADOR, UserType.BACKDOOR):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Global user not found")

    payload = user_data.model_dump(exclude_unset=True)
    if payload.get("user_type") == UserType.USER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Global user cannot be converted to User")

    try:
        user = update_user(db=db, user_id=user_id, **payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.delete")),
):
    target_user = get_user_by_id(db, user_id)
    if target_user is None or target_user.user_type != UserType.USER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.delete("/global/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ___: None = Depends(require_super_admin),
    __: None = Depends(require_permission("users.delete")),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    target_user = get_user_by_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target_user.user_type not in (UserType.ADMINISTRADOR, UserType.BACKDOOR):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Global user not found")

    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


