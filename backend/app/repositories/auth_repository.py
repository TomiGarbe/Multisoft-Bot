from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from app.models import Permission, RefreshToken, User
from app.models.auth import Role, RolePermission, TenantUser, UserPermission
from app.models.channel import Channel
from app.models.config import ChannelBotConfig
from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository


class AuthRepository(BaseRepository):
    def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return super().get_by_id(User, user_id)

    def create_refresh_token(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token)
        return refresh_token

    def get_refresh_token(self, user_id: uuid.UUID) -> list[RefreshToken]:
        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(RefreshToken.created_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_refresh_tokens_by_user(self, user_id: uuid.UUID) -> list[RefreshToken]:
        return self.get_refresh_token(user_id)

    def revoke_refresh_token(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(timezone.utc)

    def revoke_all_user_refresh_tokens(self, user_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        tokens = self.get_refresh_token(user_id)
        for token in tokens:
            token.revoked_at = now
        return len(tokens)

    def get_tenant_user_link(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[TenantUser]:
        stmt = (
            select(TenantUser)
            .where(TenantUser.user_id == user_id, TenantUser.tenant_id == tenant_id)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_default_tenant_user_link(self, user_id: uuid.UUID) -> Optional[TenantUser]:
        stmt = (
            select(TenantUser)
            .where(TenantUser.user_id == user_id, TenantUser.tenant_id.is_not(None))
            .order_by(TenantUser.created_at.asc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def user_has_tenant_scope(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        stmt = select(TenantUser.id).where(TenantUser.user_id == user_id, TenantUser.tenant_id == tenant_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def has_tenant_user_link(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        stmt = select(TenantUser.id).where(TenantUser.user_id == user_id, TenantUser.tenant_id == tenant_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def get_conversation_tenant_id(self, conversation_id: uuid.UUID) -> Optional[uuid.UUID]:
        stmt = select(Conversation.tenant_id).where(Conversation.id == conversation_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_channel_tenant_id(self, channel_id: uuid.UUID) -> Optional[uuid.UUID]:
        stmt = select(Channel.tenant_id).where(Channel.id == channel_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_channel_config_tenant_id(self, channel_config_id: uuid.UUID) -> Optional[uuid.UUID]:
        stmt = select(ChannelBotConfig.tenant_id).where(ChannelBotConfig.id == channel_config_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_permission_codes(self) -> set[str]:
        stmt = select(Permission.code)
        return set(self.db.execute(stmt).scalars().all())

    def get_global_role_permission_codes(self, role_name: str) -> set[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .where(Role.tenant_id.is_(None), Role.name == role_name)
        )
        return set(self.db.execute(stmt).scalars().all())

    def get_user_with_type(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_tenant_user_with_permissions(self, tenant_user_id: uuid.UUID) -> Optional[TenantUser]:
        stmt = (
            select(TenantUser)
            .where(TenantUser.id == tenant_user_id)
            .options(
                joinedload(TenantUser.user),
                joinedload(TenantUser.role)
                .joinedload(Role.role_permissions)
                .joinedload(RolePermission.permission),
                joinedload(TenantUser.user_permissions)
                .joinedload(UserPermission.permission),
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)

    def cleanup_expired_refresh_tokens(self) -> int:
        stmt = delete(RefreshToken).where(
            (RefreshToken.expires_at <= datetime.now(timezone.utc))
            | (RefreshToken.revoked_at.is_not(None))
        )
        result = self.db.execute(stmt)
        return int(result.rowcount or 0)

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)

    def rollback(self) -> None:
        self.db.rollback()
