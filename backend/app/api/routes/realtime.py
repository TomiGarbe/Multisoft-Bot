import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.realtime_service import event_bus

router = APIRouter(tags=["realtime"])


@router.get("/events")
async def stream_events():
    async def event_generator():
        queue = await event_bus.subscribe()
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

