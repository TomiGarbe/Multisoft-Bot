from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RemainingQuota(BaseModel):
    tokens_daily: Optional[int] = None
    tokens_monthly: Optional[int] = None
    requests_daily: Optional[int] = None
    requests_monthly: Optional[int] = None


class UsageSnapshot(BaseModel):
    total_tokens: int
    request_count: int


class QuotaCheckResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    remaining: RemainingQuota


class TenantQuotaResponse(BaseModel):
    tenant_id: str
    quotas_enabled: bool
    status: QuotaCheckResult


class QuotaStatusResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    remaining_tokens_daily: Optional[int] = None
    remaining_tokens_monthly: Optional[int] = None
    remaining_requests_daily: Optional[int] = None
    remaining_requests_monthly: Optional[int] = None
