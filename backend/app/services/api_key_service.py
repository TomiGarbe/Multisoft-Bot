import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import ApiKey
from app.repositories.api_key_repository import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreatedResponse, ApiKeyResponse, MachineIdentity


_API_KEY_PREFIX_LEN = 20
_API_KEY_FORMAT_PREFIX = "msb_sk_"
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ApiKeyService:
    def __init__(self, db: Session) -> None:
        self.repository = ApiKeyRepository(db)

    def list_api_keys(self, tenant_id: uuid.UUID) -> list[ApiKeyResponse]:
        return [self._to_response(entity) for entity in self.repository.list_by_tenant(tenant_id)]

    def create_api_key(
        self,
        tenant_id: uuid.UUID,
        name: str,
        channel_id: Optional[uuid.UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> ApiKeyCreatedResponse:
        if not self.repository.tenant_exists(tenant_id):
            raise LookupError("Tenant not found")

        if channel_id and not self.repository.channel_belongs_to_tenant(channel_id, tenant_id):
            raise LookupError("Channel not found for tenant")

        expires_at = self._normalize_datetime(expires_at)
        if expires_at and expires_at <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")

        raw_key = self._generate_raw_api_key()
        key_prefix = self._extract_key_prefix(raw_key)
        hashed_key = _pwd_context.hash(raw_key)

        entity = ApiKey(
            tenant_id=tenant_id,
            channel_id=channel_id,
            name=name,
            key_prefix=key_prefix,
            hashed_key=hashed_key,
            is_active=True,
            expires_at=expires_at,
        )

        try:
            self.repository.create(entity)
            self.repository.commit()
            self.repository.refresh(entity)
        except Exception:
            self.repository.rollback()
            raise

        return ApiKeyCreatedResponse(**self._to_response(entity).model_dump(), api_key=raw_key)

    def revoke_api_key(self, tenant_id: uuid.UUID, api_key_id: uuid.UUID) -> bool:
        entity = self.repository.get_by_id_and_tenant(api_key_id, tenant_id)
        if not entity:
            return False

        try:
            self.repository.deactivate(entity)
            self.repository.commit()
            return True
        except Exception:
            self.repository.rollback()
            raise

    def authenticate_bearer_token(
        self,
        raw_api_key: str,
        tenant_id: Optional[uuid.UUID] = None,
        channel_id: Optional[uuid.UUID] = None,
        touch_last_used: bool = True,
    ) -> Optional[MachineIdentity]:
        try:
            key_prefix = self._extract_key_prefix(raw_api_key)
        except ValueError:
            return None

        entity = self.repository.get_by_prefix(key_prefix)
        if entity is None:
            return None

        if not _pwd_context.verify(raw_api_key, entity.hashed_key):
            return None
        if not entity.is_active:
            return None
        if entity.expires_at and entity.expires_at <= datetime.now(timezone.utc):
            return None
        if tenant_id and entity.tenant_id != tenant_id:
            return None
        if channel_id and entity.channel_id and entity.channel_id != channel_id:
            return None

        if touch_last_used:
            try:
                self.repository.update_last_used(entity)
                self.repository.commit()
            except Exception:
                self.repository.rollback()
                raise

        return MachineIdentity(
            api_key_id=entity.id,
            tenant_id=entity.tenant_id,
            channel_id=entity.channel_id,
            name=entity.name,
        )

    def resolve_and_validate_channel_for_identity(
        self,
        identity: MachineIdentity,
        raw_channel_id: str,
    ) -> uuid.UUID:
        try:
            channel_id = uuid.UUID(str(raw_channel_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel_id")

        channel = self.repository.get_channel_by_id_and_tenant(channel_id, identity.tenant_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

        if identity.channel_id and identity.channel_id != channel_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key not allowed for this channel")

        return channel_id

    def require_valid_bearer_token(
        self,
        raw_api_key: str,
        tenant_id: Optional[uuid.UUID] = None,
        channel_id: Optional[uuid.UUID] = None,
    ) -> MachineIdentity:
        identity = self.authenticate_bearer_token(
            raw_api_key=raw_api_key,
            tenant_id=tenant_id,
            channel_id=channel_id,
        )
        if identity is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return identity

    def _to_response(self, entity: ApiKey) -> ApiKeyResponse:
        return ApiKeyResponse(
            id=entity.id,
            tenant_id=entity.tenant_id,
            channel_id=entity.channel_id,
            name=entity.name,
            key_prefix=entity.key_prefix,
            is_active=entity.is_active,
            created_at=entity.created_at,
            last_used_at=entity.last_used_at,
            expires_at=entity.expires_at,
        )

    @staticmethod
    def _generate_raw_api_key() -> str:
        return f"{_API_KEY_FORMAT_PREFIX}{secrets.token_urlsafe(32)}"

    @staticmethod
    def _extract_key_prefix(raw_api_key: str) -> str:
        if not raw_api_key.startswith(_API_KEY_FORMAT_PREFIX):
            raise ValueError("Invalid API key format")
        return raw_api_key[:_API_KEY_PREFIX_LEN]

    @staticmethod
    def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
