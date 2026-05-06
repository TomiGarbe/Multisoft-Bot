import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api_key import MachineIdentity, WebhookAuthContext
from app.services.api_key_service import ApiKeyService


machine_security = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(machine_security),
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
) -> MachineIdentity:
    """
    Machine auth boundary (API Keys via Bearer token).
    Separated from user JWT/permission flow.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parsed_tenant_id: Optional[uuid.UUID] = None
    if tenant_id:
        try:
            parsed_tenant_id = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Tenant-Id")

    service = ApiKeyService(db)
    return service.require_valid_bearer_token(credentials.credentials, tenant_id=parsed_tenant_id)


async def require_webhook_auth(
    channel_id: str = Path(...),
    api_key_identity: MachineIdentity = Depends(require_api_key),
    x_webhook_signature: Optional[str] = Header(default=None, alias="X-Webhook-Signature"),
    db: Session = Depends(get_db),
) -> WebhookAuthContext:
    """
    Webhook/integration auth boundary.
    Intentionally separated from user JWT/permission flow.
    """
    channel_uuid = ApiKeyService(db).resolve_and_validate_channel_for_identity(
        identity=api_key_identity,
        raw_channel_id=channel_id,
    )

    # TODO: implement provider-specific signature validation.
    _ = x_webhook_signature
    return WebhookAuthContext(
        api_key=api_key_identity,
        tenant_id=api_key_identity.tenant_id,
        channel_id=channel_uuid,
        provider_signature=x_webhook_signature,
    )
