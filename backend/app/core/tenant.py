import os
import uuid

_DEFAULT_DEV_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def get_current_tenant_id() -> uuid.UUID:
    """
    Centralized tenant resolver for development and transitional phases.
    Uses MULTISOFT_CURRENT_TENANT_ID when present, otherwise falls back
    to a fixed development tenant id.
    """
    raw_tenant_id = os.getenv("MULTISOFT_CURRENT_TENANT_ID", _DEFAULT_DEV_TENANT_ID)
    return uuid.UUID(str(raw_tenant_id))
