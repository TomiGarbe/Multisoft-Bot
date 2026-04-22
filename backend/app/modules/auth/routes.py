from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List

from app.db.session import get_db
from app.modules.auth import schemas, service, dependencies
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return tokens.
    """
    user = service.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = service.create_access_token(user.id, user.email)
    refresh_token = service.create_refresh_token(db, user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh endpoint - generate new access token from refresh token.
    """
    # Verify refresh token
    payload = service.verify_token(request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = service.create_access_token(user.id, user.email)
    new_refresh_token = service.create_refresh_token(db, user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# ==================== User CRUD ====================

@router.get("/users", response_model=List[schemas.UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get all users."""
    users = service.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/users", response_model=schemas.UserResponse)
async def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Create a new user."""
    existing_user = service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = service.create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        is_active=user_data.is_active
    )
    return user


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get user by ID."""
    user = service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Update user."""
    user = service.update_user(db, user_id, **user_data.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Delete user."""
    success = service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# ==================== Role CRUD ====================

@router.get("/roles", response_model=List[schemas.RoleResponse])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get all roles."""
    roles = service.get_roles(db, skip=skip, limit=limit)
    return roles


@router.post("/roles", response_model=schemas.RoleResponse)
async def create_role(
    role_data: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Create a new role."""
    role = service.create_role(
        db,
        name=role_data.name,
        description=role_data.description
    )
    return role


@router.get("/roles/{role_id}", response_model=schemas.RoleResponse)
async def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get role by ID."""
    role = service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.put("/roles/{role_id}", response_model=schemas.RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    role_data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Update role."""
    role = service.update_role(db, role_id, **role_data.model_dump(exclude_unset=True))
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Delete role."""
    success = service.delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )


# ==================== Permission CRUD ====================

@router.get("/permissions", response_model=List[schemas.PermissionResponse])
async def get_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get all permissions."""
    permissions = service.get_permissions(db, skip=skip, limit=limit)
    return permissions


@router.post("/permissions", response_model=schemas.PermissionResponse)
async def create_permission(
    permission_data: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Create a new permission."""
    existing = service.get_permission_by_code(db, permission_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission code already exists"
        )
    
    permission = service.create_permission(
        db,
        code=permission_data.code,
        name=permission_data.name,
        description=permission_data.description
    )
    return permission


@router.get("/permissions/{permission_id}", response_model=schemas.PermissionResponse)
async def get_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get permission by ID."""
    permission = service.get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


@router.put("/permissions/{permission_id}", response_model=schemas.PermissionResponse)
async def update_permission(
    permission_id: uuid.UUID,
    permission_data: schemas.PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Update permission."""
    permission = service.update_permission(db, permission_id, **permission_data.model_dump(exclude_unset=True))
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Delete permission."""
    success = service.delete_permission(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )



@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return tokens.
    """
    user = service.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = service.create_access_token(user.id, user.email)
    refresh_token = service.create_refresh_token(db, user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh endpoint - generate new access token from refresh token.
    """
    # Verify refresh token
    payload = service.verify_token(request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = service.create_access_token(user.id, user.email)
    new_refresh_token = service.create_refresh_token(db, user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# ==================== User CRUD ====================

@router.get("/users", response_model=list[schemas.UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get all users."""
    users = service.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/users", response_model=schemas.UserResponse)
async def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Create a new user."""
    existing_user = service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = service.create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        is_active=user_data.is_active
    )
    return user


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get user by ID."""
    user = service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Update user."""
    user = service.update_user(db, user_id, **user_data.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Delete user."""
    success = service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# ==================== Role CRUD ====================

@router.get("/roles", response_model=list[schemas.RoleResponse])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get all roles."""
    roles = service.get_roles(db, skip=skip, limit=limit)
    return roles


@router.post("/roles", response_model=schemas.RoleResponse)
async def create_role(
    role_data: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Create a new role."""
    role = service.create_role(
        db,
        name=role_data.name,
        description=role_data.description
    )
    return role


@router.get("/roles/{role_id}", response_model=schemas.RoleResponse)
async def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get role by ID."""
    role = service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.put("/roles/{role_id}", response_model=schemas.RoleResponse)
async def update_role(
    role_id: uuid.UUID,
    role_data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Update role."""
    role = service.update_role(db, role_id, **role_data.model_dump(exclude_unset=True))
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Delete role."""
    success = service.delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )


# ==================== Permission CRUD ====================

@router.get("/permissions", response_model=list[schemas.PermissionResponse])
async def get_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get all permissions."""
    permissions = service.get_permissions(db, skip=skip, limit=limit)
    return permissions


@router.post("/permissions", response_model=schemas.PermissionResponse)
async def create_permission(
    permission_data: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Create a new permission."""
    existing = service.get_permission_by_code(db, permission_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission code already exists"
        )
    
    permission = service.create_permission(
        db,
        code=permission_data.code,
        name=permission_data.name,
        description=permission_data.description
    )
    return permission


@router.get("/permissions/{permission_id}", response_model=schemas.PermissionResponse)
async def get_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Get permission by ID."""
    permission = service.get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


@router.put("/permissions/{permission_id}", response_model=schemas.PermissionResponse)
async def update_permission(
    permission_id: uuid.UUID,
    permission_data: schemas.PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Update permission."""
    permission = service.update_permission(db, permission_id, **permission_data.model_dump(exclude_unset=True))
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(dependencies.get_current_user)
):
    """Delete permission."""
    success = service.delete_permission(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
