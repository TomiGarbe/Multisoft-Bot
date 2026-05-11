from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import TenantContext, get_current_tenant_context
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.services.usage_service import UsageService

router = APIRouter(tags=["analytics"])


@router.get("/usage/totals")
async def get_usage_totals(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: None = Depends(require_permission("analytics.read")),
):
    usage_service = UsageService(db)
    if tenant_context.scope == "global":
        return {
            "scope": "global",
            "totals": usage_service.get_global_totals(start_date=start_date, end_date=end_date),
        }

    if tenant_context.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant scope required")
    return {
        "scope": "tenant",
        "tenant_id": str(tenant_context.tenant_id),
        "totals": usage_service.get_tenant_totals(
            tenant_id=tenant_context.tenant_id,
            start_date=start_date,
            end_date=end_date,
        ),
    }


@router.get("/usage/series")
async def get_usage_series(
    granularity: str = Query(default="day", pattern="^(day|month)$"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: None = Depends(require_permission("analytics.read")),
):
    usage_service = UsageService(db)
    if granularity == "month":
        tenant_fn = usage_service.get_tenant_monthly_usage
        global_fn = usage_service.get_global_monthly_usage
    else:
        tenant_fn = usage_service.get_tenant_daily_usage
        global_fn = usage_service.get_global_daily_usage

    if tenant_context.scope == "global":
        return {
            "scope": "global",
            "granularity": granularity,
            "series": global_fn(start_date=start_date, end_date=end_date),
        }

    if tenant_context.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant scope required")
    return {
        "scope": "tenant",
        "tenant_id": str(tenant_context.tenant_id),
        "granularity": granularity,
        "series": tenant_fn(
            tenant_id=tenant_context.tenant_id,
            start_date=start_date,
            end_date=end_date,
        ),
    }


@router.get("/business/summary")
async def get_business_summary(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: None = Depends(require_permission("analytics.read")),
):
    usage_service = UsageService(db)

    if tenant_context.scope == "global":
        totals = usage_service.get_global_totals(start_date=start_date, end_date=end_date)
        contacts = usage_service.get_contacts_summary()
        tokens_by_tenant = usage_service.get_token_usage_by_tenant(start_date=start_date, end_date=end_date)
        return {
            "scope": "global",
            "contacts": contacts,
            "tokens": {
                "total_tokens": totals.get("total_tokens", 0),
                "by_tenant": tokens_by_tenant,
            },
        }

    if tenant_context.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant scope required")

    totals = usage_service.get_tenant_totals(
        tenant_id=tenant_context.tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    contacts = usage_service.get_contacts_summary(tenant_id=tenant_context.tenant_id)
    tokens_by_channel = usage_service.get_token_usage_by_channel(
        tenant_id=tenant_context.tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    conversion_flows = usage_service.get_configured_conversion_flows(tenant_id=tenant_context.tenant_id)
    return {
        "scope": "tenant",
        "tenant_id": str(tenant_context.tenant_id),
        "contacts": contacts,
        "tokens": {
            "total_tokens": totals.get("total_tokens", 0),
            "by_channel": tokens_by_channel,
        },
        "conversions": {
            "flows": [
                {
                    "from_type": item["from_type"],
                    "to_type": item["to_type"],
                    "count": 0,
                    "rate": 0,
                }
                for item in conversion_flows
            ]
        },
    }
