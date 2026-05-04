import asyncio
import json
from typing import Any


class RealtimeEventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        frame = f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"
        for queue in tuple(self._subscribers):
            queue.put_nowait(frame)


event_bus = RealtimeEventBus()

