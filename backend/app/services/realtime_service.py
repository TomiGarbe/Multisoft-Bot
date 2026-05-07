import asyncio
import json
import uuid
from typing import Any


class RealtimeEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[asyncio.Queue[str], uuid.UUID] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, tenant_id: uuid.UUID) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers[queue] = tenant_id
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        async with self._lock:
            self._subscribers.pop(queue, None)

    def publish(self, event_name: str, payload: dict[str, Any], tenant_id: uuid.UUID) -> None:
        frame = f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"
        for queue, subscriber_tenant_id in tuple(self._subscribers.items()):
            if subscriber_tenant_id == tenant_id:
                queue.put_nowait(frame)


event_bus = RealtimeEventBus()
