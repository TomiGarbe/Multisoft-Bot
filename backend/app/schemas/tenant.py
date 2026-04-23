from pydantic import BaseModel
from typing import Optional
import uuid


class TenantCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    industry: Optional[str] = None
    timezone: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    industry: Optional[str] = None
    timezone: Optional[str] = None


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    industry: Optional[str] = None
    timezone: Optional[str] = None

    model_config = {"from_attributes": True}