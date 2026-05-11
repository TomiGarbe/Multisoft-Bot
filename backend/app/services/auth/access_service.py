import uuid
from typing import Optional
import logging

from sqlalchemy.orm import Session

from app.models import User
from app.models.user import UserType
from app.models.auth import TenantUser
from app.repositories.auth_repository import AuthRepository
from app.services.auth.permission_service import get_user_permissions

logger = logging.getLogger(__name__)


def is_super_admin(user: User) -> bool:
    return user.user_type == UserType.BACKDOOR or user.is_backdoor


def get_tenant_user_link(db: Session, user_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[TenantUser]:
    return AuthRepository(db).get_tenant_user_link(user_id=user_id, tenant_id=tenant_id)


def get_default_tenant_user_link(db: Session, user_id: uuid.UUID) -> Optional[TenantUser]:
    return AuthRepository(db).get_default_tenant_user_link(user_id=user_id)


def can_access_tenant(db: Session, user: User, tenant_id: uuid.UUID) -> bool:
    repository = AuthRepository(db)

    if is_super_admin(user):
        logger.debug("AUTH access bypass: user=%s tenant=%s", user.id, tenant_id)
        return True

    if user.user_type == UserType.ADMINISTRADOR:
        return repository.user_has_tenant_scope(user_id=user.id, tenant_id=tenant_id)

    return repository.has_tenant_user_link(user_id=user.id, tenant_id=tenant_id)


def get_effective_permissions(
    db: Session,
    user: User,
    tenant_id: Optional[uuid.UUID] = None,
) -> set[str]:
    if is_super_admin(user):
        return get_user_permissions(db, user_id=user.id)

    tenant_user: Optional[TenantUser] = None
    if tenant_id is not None:
        tenant_user = get_tenant_user_link(db, user.id, tenant_id)
    if tenant_user is None:
        tenant_user = get_default_tenant_user_link(db, user.id)
    if tenant_user is None:
        return set()

    return get_user_permissions(db, tenant_user_id=tenant_user.id, user_id=user.id)


def can_access_tenant_resource(db: Session, user: User, tenant_id: uuid.UUID) -> bool:
    return can_access_tenant(db, user, tenant_id)


def can_operate_on_tenant_target(user: User, current_tenant_id: uuid.UUID, target_tenant_id: uuid.UUID) -> bool:
    if is_super_admin(user):
        return True
    return current_tenant_id == target_tenant_id


def can_access_conversation(db: Session, user: User, conversation_id: uuid.UUID) -> bool:
    conversation_tenant_id = AuthRepository(db).get_conversation_tenant_id(conversation_id=conversation_id)
    if conversation_tenant_id is None:
        return False
    return can_access_tenant_resource(db, user, conversation_tenant_id)


def can_access_channel(db: Session, user: User, channel_id: uuid.UUID) -> bool:
    channel_tenant_id = AuthRepository(db).get_channel_tenant_id(channel_id=channel_id)
    if channel_tenant_id is None:
        return False
    return can_access_tenant_resource(db, user, channel_tenant_id)


def can_access_channel_config(db: Session, user: User, channel_config_id: uuid.UUID) -> bool:
    channel_config_tenant_id = AuthRepository(db).get_channel_config_tenant_id(channel_config_id=channel_config_id)
    if channel_config_tenant_id is None:
        return False
    return can_access_tenant_resource(db, user, channel_config_tenant_id)

