import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tenant, User
from app.models.auth import TenantUser
from app.schemas.tenant import TenantResponse


def _build_tenant_response(tenant: Tenant) -> TenantResponse:
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        description=tenant.description,
        is_active=tenant.is_active,
        industry=tenant.industry,
        timezone=tenant.timezone,
        branding_jsonb=tenant.branding_jsonb,
        features_jsonb=tenant.features_jsonb,
    )


def get_tenants(db: Session, user: User) -> list[TenantResponse]:
    if not user.is_active:
        return []
    
    if user.is_backdoor:
        stmt = select(Tenant)
    else:
        stmt = (
            select(Tenant)
            .join(TenantUser, TenantUser.tenant_id == Tenant.id)
            .where(TenantUser.user_id == user.id)
        )
    tenants = db.execute(stmt).scalars().all()
    return [_build_tenant_response(t) for t in tenants]


def create_tenant(
    db: Session,
    name: str,
    slug: str,
    description: Optional[str] = None,
    industry: Optional[str] = None,
    timezone: Optional[str] = None,
):
    existing = db.query(Tenant).filter(Tenant.slug == slug).first()
    if existing:
        raise ValueError("Slug already exists")

    tenant = Tenant(
        name=name,
        slug=slug,
        description=description,
        industry=industry,
        timezone=timezone,
        branding_jsonb=None,
        features_jsonb=None,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant


def update_tenant(
    db: Session,
    tenant_id: uuid.UUID,
    **kwargs,
):
    tenant = db.get(Tenant, tenant_id)

    if not tenant:
        raise LookupError("Tenant not found")

    # Prevent updates to protected fields
    kwargs.pop("branding_jsonb", None)
    kwargs.pop("features_jsonb", None)

    if "slug" in kwargs and kwargs["slug"]:
        existing = (
            db.query(Tenant)
            .filter(Tenant.slug == kwargs["slug"], Tenant.id != tenant_id)
            .first()
        )
        if existing:
            raise ValueError("Slug already exists")

    for key, value in kwargs.items():
        setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)

    return tenant


def delete_tenant(db: Session, tenant_id: uuid.UUID) -> bool:
    try:
        tenant = db.get(Tenant, tenant_id)
        if tenant is None:
            return False

        tenant.is_active = False
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
