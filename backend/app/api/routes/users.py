import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.models.user import UserType
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user, delete_user, get_global_users, get_users, update_user


router = APIRouter(tags=["users"])


@router.get("", response_model=list[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.read")),
):
    return get_users(db, skip=skip, limit=limit, current_user_id=None)


@router.get("/global", response_model=list[UserResponse])
async def read_global_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.read")),
):
    return get_global_users(db, skip=skip, limit=limit)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.create")),
):
    try:
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
            tenant_id=user_data.tenant_id,
            tenant_ids=user_data.tenant_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.delete")),
):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


