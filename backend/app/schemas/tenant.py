from pydantic import BaseModel, field_validator
from typing import Optional
import uuid

from app.core.timezones import is_supported_tenant_timezone


class TenantCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    industry: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not is_supported_tenant_timezone(value):
            raise ValueError("Unsupported timezone. Use one of the allowed IANA tenant timezones.")
        return value


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    industry: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not is_supported_tenant_timezone(value):
            raise ValueError("Unsupported timezone. Use one of the allowed IANA tenant timezones.")
        return value


class TenantTimezoneOption(BaseModel):
    value: str
    label: str


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    industry: Optional[str] = None
    timezone: Optional[str] = None
    branding_jsonb: Optional[dict] = None
    features_jsonb: Optional[dict] = None

    model_config = {"from_attributes": True}
