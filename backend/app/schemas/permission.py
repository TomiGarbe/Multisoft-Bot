from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
