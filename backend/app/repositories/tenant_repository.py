import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tenant, User
from app.models.auth import TenantUser


def get_by_id(db: Session, tenant_id: uuid.UUID) -> Optional[Tenant]:
    return db.get(Tenant, tenant_id)


def get_all(db: Session) -> list[Tenant]:
    stmt = select(Tenant)
    return db.execute(stmt).scalars().all()


def get_all_by_user(db: Session, user: User) -> list[Tenant]:
    stmt = (
        select(Tenant)
        .join(TenantUser, TenantUser.tenant_id == Tenant.id)
        .where(TenantUser.user_id == user.id, TenantUser.tenant_id.is_not(None))
        .distinct()
        .order_by(Tenant.name.asc())
    )
    return db.execute(stmt).scalars().all()


def get_all_active_for_backdoor(db: Session) -> list[Tenant]:
    stmt = select(Tenant)
    return db.execute(stmt).scalars().all()


def get_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    stmt = select(Tenant).where(Tenant.slug == slug)
    return db.execute(stmt).scalar_one_or_none()


def get_by_slug_excluding_id(
    db: Session,
    *,
    slug: str,
    tenant_id: uuid.UUID,
) -> Optional[Tenant]:
    stmt = select(Tenant).where(Tenant.slug == slug, Tenant.id != tenant_id)
    return db.execute(stmt).scalar_one_or_none()


def create(
    db: Session,
    *,
    name: str,
    slug: str,
    description: Optional[str] = None,
    industry: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Tenant:
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
    return tenant


def update(db: Session, tenant: Tenant, **kwargs) -> Tenant:
    for key, value in kwargs.items():
        setattr(tenant, key, value)
    return tenant


def delete(db: Session, tenant: Tenant) -> Tenant:
    # Soft-delete current behavior: mark as inactive.
    tenant.is_active = False
    return tenant


def flush(db: Session) -> None:
    db.flush()


def commit(db: Session) -> None:
    db.commit()


def refresh(db: Session, tenant: Tenant) -> None:
    db.refresh(tenant)


def rollback(db: Session) -> None:
    db.rollback()
