import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import TenantContext, get_current_tenant_context
from app.api.dependencies.permissions import require_permission
from app.services.realtime_service import event_bus

router = APIRouter(tags=["realtime"])


@router.get("/events")
async def stream_events(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
    _: None = Depends(require_permission("realtime.read")),
):
    if tenant_context.scope != "tenant" or tenant_context.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant scope required")

    async def event_generator():
        queue = await event_bus.subscribe(tenant_context.tenant_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    yield event
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
