import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user as _get_current_user_model
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.auth_service import AuthService


router = APIRouter(tags=["auth"])


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
