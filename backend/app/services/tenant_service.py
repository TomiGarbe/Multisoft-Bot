import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Tenant, User
from app.repositories import tenant_repository
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


def get_tenants(db: Session, user: Optional[User] = None) -> list[TenantResponse]:
    tenants = _resolve_tenants_for_user_scope(db, user)
    return [_build_tenant_response(t) for t in tenants]


def _resolve_tenants_for_user_scope(db: Session, user: Optional[User]) -> list[Tenant]:
    # DEV: bypass user filtering must remain for current compatibility.
    if user is None:
        return tenant_repository.get_all(db)
    if not user.is_active:
        return []
    if user.is_backdoor:
        return tenant_repository.get_all_active_for_backdoor(db)
    return tenant_repository.get_all_by_user(db, user)


def create_tenant(
    db: Session,
    name: str,
    slug: str,
    description: Optional[str] = None,
    industry: Optional[str] = None,
    timezone: Optional[str] = None,
):
    existing = tenant_repository.get_by_slug(db, slug)
    if existing is not None:
        raise ValueError("Slug already exists")

    try:
        tenant = tenant_repository.create(
            db,
            name=name,
            slug=slug,
            description=description,
            industry=industry,
            timezone=timezone,
        )
        tenant_repository.commit(db)
        tenant_repository.refresh(db, tenant)
        return tenant
    except Exception:
        tenant_repository.rollback(db)
        raise


def update_tenant(
    db: Session,
    tenant_id: uuid.UUID,
    **kwargs,
):
    tenant = tenant_repository.get_by_id(db, tenant_id)

    if tenant is None:
        raise LookupError("Tenant not found")

    # Keep protected fields behavior unchanged.
    kwargs.pop("branding_jsonb", None)
    kwargs.pop("features_jsonb", None)

    if "slug" in kwargs and kwargs["slug"]:
        existing = tenant_repository.get_by_slug_excluding_id(
            db,
            slug=kwargs["slug"],
            tenant_id=tenant_id,
        )
        if existing is not None:
            raise ValueError("Slug already exists")

    try:
        tenant_repository.update(db, tenant, **kwargs)
        tenant_repository.commit(db)
        tenant_repository.refresh(db, tenant)
        return tenant
    except Exception:
        tenant_repository.rollback(db)
        raise


def delete_tenant(db: Session, tenant_id: uuid.UUID) -> bool:
    try:
        tenant = tenant_repository.get_by_id(db, tenant_id)
        if tenant is None:
            return False

        tenant_repository.delete(db, tenant)
        tenant_repository.commit(db)
        return True
    except Exception:
        tenant_repository.rollback(db)
        raise
