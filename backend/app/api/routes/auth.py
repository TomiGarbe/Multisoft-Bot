import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user as _get_current_user_model
from app.db.session import get_db
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthContextResponse, LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.tenant_service import get_tenants
from app.services.auth_service import AuthService
from app.services.user_service import get_user_response_by_id
from app.models.user import UserType


router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)


async def get_current_user(
    user=Depends(_get_current_user_model),
) -> tuple[uuid.UUID, str]:
    """Backward-compatible wrapper that returns (user_id, email)."""
    return user.id, user.email


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        result = auth_service.login(email=credentials.email, password=credentials.password)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": result.token_type,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    result = auth_service.refresh(request.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": result.token_type,
    }


@router.get("/me", response_model=UserResponse)
async def me(
    user=Depends(_get_current_user_model),
    db: Session = Depends(get_db),
):
    try:
        return get_user_response_by_id(db, user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/context", response_model=AuthContextResponse)
async def auth_context(
    user=Depends(_get_current_user_model),
    db: Session = Depends(get_db),
):
    logger.info(
        "[AUTH_CONTEXT] user_id=%s user_type=%s is_backdoor=%s loading_user",
        str(user.id),
        user.user_type.value,
        bool(user.is_backdoor),
    )
    try:
        current_user = get_user_response_by_id(db, user.id)
    except LookupError as exc:
        logger.warning("[AUTH_CONTEXT] user not found user_id=%s detail=%s", str(user.id), str(exc))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[AUTH_CONTEXT] FAILED step=load_user user_id=%s error=%s", str(user.id), str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth context failed") from exc

    logger.info("[AUTH_CONTEXT] loading_user_tenants user_id=%s", str(user.id))
    try:
        allowed_tenants = get_tenants(db, user=user)
        is_global_access = user.user_type == UserType.BACKDOOR
        default_link = AuthRepository(db).get_default_tenant_user_link(user_id=user.id)
        default_tenant = str(default_link.tenant_id) if default_link and default_link.tenant_id else None
        tenant_ids = [str(tenant.id) for tenant in allowed_tenants]

        logger.info(
            "[AUTH_CONTEXT] tenants_found=%s tenant_ids=%s selected_tenant=%s global_access=%s",
            len(allowed_tenants),
            tenant_ids,
            default_tenant,
            is_global_access,
        )
        return AuthContextResponse(
            user=current_user,
            tenants=allowed_tenants,
            is_global_access=is_global_access,
        )
    except Exception as exc:
        logger.exception("[AUTH_CONTEXT] FAILED step=load_tenants user_id=%s error=%s", str(user.id), str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth context failed") from exc
