import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserType


class UserRoleSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None


class UserPermissionSummary(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class TenantSummary(BaseModel):
    id: uuid.UUID
    name: str


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role_id: Optional[uuid.UUID] = None
    permissions: list[uuid.UUID] = Field(default_factory=list)
    is_active: bool = True
    is_backdoor: bool = False
    user_type: Optional[UserType] = None
    tenant_id: Optional[uuid.UUID] = None
    tenant_ids: list[uuid.UUID] = Field(default_factory=list)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role_id: Optional[uuid.UUID] = None
    permissions: Optional[list[uuid.UUID]] = None
    is_active: Optional[bool] = None
    is_backdoor: Optional[bool] = None
    user_type: Optional[UserType] = None
    tenant_id: Optional[uuid.UUID] = None
    tenant_ids: Optional[list[uuid.UUID]] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    user_type: UserType
    is_backdoor: bool = False
    is_active: bool = True
    tenant_id: Optional[uuid.UUID] = None
    tenant_ids: list[uuid.UUID] = Field(default_factory=list)
    tenant: Optional[TenantSummary] = None
    role: Optional[UserRoleSummary] = None
    permissions: list[UserPermissionSummary] = Field(default_factory=list)

    model_config = {"from_attributes": True}
