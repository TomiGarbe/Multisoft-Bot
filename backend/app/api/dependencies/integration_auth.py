import uuid
import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, Path, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api_key import MachineIdentity, WebhookAuthContext
from app.services.api_key_service import ApiKeyService


machine_security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def _safe_key_tag(raw_api_key: Optional[str]) -> str:
    if not raw_api_key:
        return "none"
    if raw_api_key.startswith("msb_sk_") and len(raw_api_key) >= 20:
        return f"{raw_api_key[:20]}..."
    return f"{raw_api_key[:8]}..."


async def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(machine_security),
    api_key: Optional[str] = Query(default=None, alias="api_key"),
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
) -> MachineIdentity:
    """
    Machine auth boundary (API Keys via Bearer token).
    Separated from user JWT/permission flow.
    """
    raw_api_key: Optional[str] = None
    auth_source: Optional[str] = None

    if credentials is not None and credentials.scheme.lower() == "bearer":
        raw_api_key = credentials.credentials
        auth_source = "header"
    elif api_key:
        raw_api_key = api_key
        auth_source = "query"

    if raw_api_key is None:
        logger.warning("Machine auth failed source=none reason=missing_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key (Bearer token or api_key query param)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parsed_tenant_id: Optional[uuid.UUID] = None
    if tenant_id:
        try:
            parsed_tenant_id = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Tenant-Id")

    service = ApiKeyService(db)
    try:
        identity = service.require_valid_bearer_token(raw_api_key, tenant_id=parsed_tenant_id)
    except HTTPException:
        logger.warning(
            "Machine auth failed source=%s key=%s",
            auth_source,
            _safe_key_tag(raw_api_key),
        )
        raise

    logger.info(
        "Machine auth success source=%s tenant_id=%s key=%s",
        auth_source,
        identity.tenant_id,
        _safe_key_tag(raw_api_key),
    )
    return identity


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
