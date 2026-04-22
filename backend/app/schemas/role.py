from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
