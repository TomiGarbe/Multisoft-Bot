import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr
from app.schemas.tenant import TenantResponse
from app.schemas.user import UserResponse


class AuthResult(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: uuid.UUID
    email: str
    is_backdoor: bool = False
    tenant_id: Optional[uuid.UUID] = None


class AuthContextResponse(BaseModel):
    user: UserResponse
    tenants: list[TenantResponse]
    is_global_access: bool
