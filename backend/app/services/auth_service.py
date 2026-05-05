from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models import RefreshToken, User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    is_backdoor: bool = False,
    user_type: str = "BUSINESS_USER",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "user_id": str(user_id),
        "email": email,
        "is_backdoor": is_backdoor,
        "user_type": user_type,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(db: Session, user_id: uuid.UUID) -> str:
    """Create a refresh token and store it in database."""
    token_string = jwt.encode(
        {
            "user_id": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_password(token_string),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh_token)
    db.commit()

    return token_string


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        return None

    if not verify_password(password, user.password_hash or ""):
        return None

    return user
