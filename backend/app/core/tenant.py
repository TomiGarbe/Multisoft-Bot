import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

_DEFAULT_DEV_TENANT_ID = "00000000-0000-0000-0000-000000000001"
_current_tenant_id_ctx: ContextVar[Optional[uuid.UUID]] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id() -> uuid.UUID:
    """
    Legacy helper kept only for backward compatibility.
    New code must use explicit tenant context via request dependencies.
    """
    context_tenant_id = _current_tenant_id_ctx.get()
    if context_tenant_id is not None:
        return context_tenant_id

    raw_tenant_id = os.getenv("MULTISOFT_CURRENT_TENANT_ID", _DEFAULT_DEV_TENANT_ID)
    return uuid.UUID(str(raw_tenant_id))


@contextmanager
def tenant_scope(tenant_id: uuid.UUID) -> Iterator[None]:
    token = _current_tenant_id_ctx.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant_id_ctx.reset(token)
