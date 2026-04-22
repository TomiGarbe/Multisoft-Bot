from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.services.auth_service import hash_password


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def create_user(
    db: Session, name: str, email: str, password: str, is_active: bool = True
) -> User:
    """Create a new user."""
    hashed_password = hash_password(password)
    user = User(
        name=name,
        email=email,
        password_hash=hashed_password,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: uuid.UUID, **kwargs) -> Optional[User]:
    """Update user."""
    user = db.get(User, user_id)
    if not user:
        return None

    if "password" in kwargs and kwargs["password"]:
        kwargs["password_hash"] = hash_password(kwargs.pop("password"))

    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    """Delete user."""
    user = db.get(User, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users."""
    stmt = select(User).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()
