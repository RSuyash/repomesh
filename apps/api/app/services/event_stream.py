from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class StreamSubscriber:
    id: str
    queue: asyncio.Queue[dict[str, Any]]
    recipient_id: str | None
    channel: str | None
    include_broadcast: bool


class EventStreamBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, StreamSubscriber] = {}
        self._lock = asyncio.Lock()

    async def subscribe(
        self,
        *,
        recipient_id: str | None,
        channel: str | None,
        include_broadcast: bool,
    ) -> StreamSubscriber:
        subscriber = StreamSubscriber(
            id=str(uuid.uuid4()),
            queue=asyncio.Queue(maxsize=200),
            recipient_id=recipient_id,
            channel=channel,
            include_broadcast=include_broadcast,
        )
        async with self._lock:
            self._subscribers[subscriber.id] = subscriber
        return subscriber

    async def unsubscribe(self, subscriber_id: str) -> None:
        async with self._lock:
            self._subscribers.pop(subscriber_id, None)

    async def publish(self, event_item: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.values())
        for subscriber in subscribers:
            if not self._matches(subscriber, event_item):
                continue
            try:
                subscriber.queue.put_nowait(event_item)
            except asyncio.QueueFull:
                # Drop oldest event to keep stream live under burst traffic.
                try:
                    subscriber.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    subscriber.queue.put_nowait(event_item)
                except asyncio.QueueFull:
                    continue

    @staticmethod
    def _matches(subscriber: StreamSubscriber, event_item: dict[str, Any]) -> bool:
        event_channel = event_item.get('channel')
        event_recipient = event_item.get('recipient_id')

        if subscriber.channel and subscriber.channel != event_channel:
            return False

        if subscriber.recipient_id:
            if subscriber.include_broadcast:
                return event_recipient in {subscriber.recipient_id, None}
            return event_recipient == subscriber.recipient_id

        return True


event_stream_broker = EventStreamBroker()
