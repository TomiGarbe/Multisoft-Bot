from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User, RefreshToken, Role, Permission
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "user_id": str(user_id),
        "email": email,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    return encoded_jwt


def create_refresh_token(db: Session, user_id: uuid.UUID) -> str:
    """Create a refresh token and store it in database."""
    from datetime import datetime
    
    token_string = jwt.encode(
        {
            "user_id": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=30)
        },
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_password(token_string),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(refresh_token)
    db.commit()
    
    return token_string


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
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


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, name: str, email: str, password: str, is_active: bool = True) -> User:
    """Create a new user."""
    hashed_password = hash_password(password)
    user = User(
        name=name,
        email=email,
        password_hash=hashed_password,
        is_active=is_active
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


# ==================== Role Functions ====================

def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    """Get role by ID."""
    return db.get(Role, role_id)


def create_role(db: Session, name: str, description: Optional[str] = None, tenant_id: Optional[uuid.UUID] = None) -> Role:
    """Create a new role."""
    role = Role(
        tenant_id=tenant_id,
        name=name,
        description=description,
        is_system=False
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role_id: uuid.UUID, **kwargs) -> Optional[Role]:
    """Update role."""
    role = db.get(Role, role_id)
    if not role:
        return None
    
    for key, value in kwargs.items():
        if hasattr(role, key) and value is not None:
            setattr(role, key, value)
    
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: uuid.UUID) -> bool:
    """Delete role."""
    role = db.get(Role, role_id)
    if not role:
        return False
    db.delete(role)
    db.commit()
    return True


def get_roles(db: Session, skip: int = 0, limit: int = 100):
    """Get all roles."""
    stmt = select(Role).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


# ==================== Permission Functions ====================

def get_permission_by_id(db: Session, permission_id: uuid.UUID) -> Optional[Permission]:
    """Get permission by ID."""
    return db.get(Permission, permission_id)


def get_permission_by_code(db: Session, code: str) -> Optional[Permission]:
    """Get permission by code."""
    stmt = select(Permission).where(Permission.code == code)
    return db.execute(stmt).scalar_one_or_none()


def create_permission(db: Session, code: str, name: str, description: Optional[str] = None) -> Permission:
    """Create a new permission."""
    permission = Permission(
        code=code,
        name=name,
        description=description
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def update_permission(db: Session, permission_id: uuid.UUID, **kwargs) -> Optional[Permission]:
    """Update permission."""
    permission = db.get(Permission, permission_id)
    if not permission:
        return None
    
    for key, value in kwargs.items():
        if hasattr(permission, key) and value is not None:
            setattr(permission, key, value)
    
    db.commit()
    db.refresh(permission)
    return permission


def delete_permission(db: Session, permission_id: uuid.UUID) -> bool:
    """Delete permission."""
    permission = db.get(Permission, permission_id)
    if not permission:
        return False
    db.delete(permission)
    db.commit()
    return True


def get_permissions(db: Session, skip: int = 0, limit: int = 100):
    """Get all permissions."""
    stmt = select(Permission).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()
