from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RefreshToken, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthResult


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuthRepository(db)

    def login(self, email: str, password: str) -> Optional[AuthResult]:
        user = self.authenticate_user(email, password)
        if not user:
            return None
        if not user.is_active:
            raise PermissionError("User account is inactive")

        try:
            self.repository.update_last_login(user)
            access_token = self.create_access_token(
                user.id,
                user.email,
                is_backdoor=user.is_backdoor,
                user_type=user.user_type.value,
            )
            refresh_token = self.create_refresh_token(user.id)
            self.repository.commit()
            return AuthResult(access_token=access_token, refresh_token=refresh_token)
        except Exception:
            self.repository.rollback()
            raise

    def refresh(self, token: str) -> Optional[AuthResult]:
        payload = verify_token(token)
        if payload is None:
            return None

        user_id_str = payload.get("user_id")
        if not user_id_str:
            return None

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            return None

        user = self.repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None

        stored_refresh_token = self._find_valid_refresh_token(user_id, token)
        if stored_refresh_token is None:
            return None

        try:
            self.repository.revoke_refresh_token(stored_refresh_token)
            new_refresh_token = self.create_refresh_token(user.id)
            access_token = self.create_access_token(
                user.id,
                user.email,
                is_backdoor=user.is_backdoor,
                user_type=user.user_type.value,
            )
            self.repository.commit()
            return AuthResult(access_token=access_token, refresh_token=new_refresh_token)
        except Exception:
            self.repository.rollback()
            raise

    def logout(self, token: str) -> bool:
        payload = verify_token(token)
        if payload is None:
            return False

        user_id_str = payload.get("user_id")
        if not user_id_str:
            return False

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            return False

        stored_refresh_token = self._find_valid_refresh_token(user_id, token)
        if stored_refresh_token is None:
            return False

        try:
            self.repository.revoke_refresh_token(stored_refresh_token)
            self.repository.commit()
            return True
        except Exception:
            self.repository.rollback()
            raise

    def cleanup_refresh_tokens(self) -> int:
        try:
            deleted = self.repository.cleanup_expired_refresh_tokens()
            self.repository.commit()
            return deleted
        except Exception:
            self.repository.rollback()
            raise

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.repository.get_user_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash or ""):
            return None

        return user

    def create_access_token(
        self,
        user_id: uuid.UUID,
        email: str,
        is_backdoor: bool = False,
        user_type: str = "USER",
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        return create_access_token(
            user_id=user_id,
            email=email,
            is_backdoor=is_backdoor,
            user_type=user_type,
            expires_delta=expires_delta,
        )

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        token_string = jwt.encode(
            {
                "user_id": str(user_id),
                "exp": datetime.now(timezone.utc) + timedelta(days=30),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        self.repository.create_refresh_token(
            user_id=user_id,
            token_hash=hash_password(token_string),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        return token_string

    def _find_valid_refresh_token(self, user_id: uuid.UUID, token: str) -> Optional[RefreshToken]:
        for refresh_token in self.repository.get_refresh_token(user_id):
            if verify_password(token, refresh_token.token_hash):
                return refresh_token
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    is_backdoor: bool = False,
    user_type: str = "USER",
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {
        "user_id": str(user_id),
        "email": email,
        "is_backdoor": is_backdoor,
        "user_type": user_type,
        "exp": expire,
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    return AuthService(db).authenticate_user(email=email, password=password)


def create_refresh_token(db: Session, user_id: uuid.UUID) -> str:
    service = AuthService(db)
    try:
        token = service.create_refresh_token(user_id=user_id)
        service.repository.commit()
        return token
    except Exception:
        service.repository.rollback()
        raise
