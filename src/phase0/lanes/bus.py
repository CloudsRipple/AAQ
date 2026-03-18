from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LaneEvent:
    event_type: str
    source_lane: str
    payload: dict[str, Any]
    trace_id: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    @classmethod
    def from_payload(cls, *, event_type: str, source_lane: str, payload: dict[str, Any]) -> "LaneEvent":
        trace_id = _stable_trace_id(event_type=event_type, source_lane=source_lane, payload=payload)
        return cls(
            event_type=event_type,
            source_lane=source_lane,
            payload=payload,
            trace_id=trace_id,
        )


class InMemoryLaneBus:
    def __init__(self, dedup_capacity: int = 2048) -> None:
        self._dedup_capacity = max(1, dedup_capacity)
        self._seen_trace_ids: set[str] = set()
        self._seen_order = deque()
        self._queues: dict[str, list[LaneEvent]] = {}
        self._consumer_offsets: dict[str, dict[str, int]] = {}

    def publish(self, channel: str, event: LaneEvent) -> bool:
        if event.trace_id in self._seen_trace_ids:
            return False
        self._seen_trace_ids.add(event.trace_id)
        self._seen_order.append(event.trace_id)
        if len(self._seen_order) > self._dedup_capacity:
            expired = self._seen_order.popleft()
            self._seen_trace_ids.discard(expired)
        queue = self._queues.setdefault(channel, [])
        queue.append(event)
        if len(queue) > self._dedup_capacity:
            queue.pop(0)
            channel_offsets = self._consumer_offsets.get(channel, {})
            for consumer_id, offset in list(channel_offsets.items()):
                channel_offsets[consumer_id] = max(0, offset - 1)
        return True

    def consume(self, channel: str) -> list[LaneEvent]:
        return self.consume_for(channel, "__default__")

    def consume_for(self, channel: str, consumer_id: str) -> list[LaneEvent]:
        queue = self._queues.get(channel, [])
        channel_offsets = self._consumer_offsets.setdefault(channel, {})
        offset = channel_offsets.get(consumer_id, 0)
        if offset >= len(queue):
            return []
        events = queue[offset:]
        channel_offsets[consumer_id] = len(queue)
        return events

    async def apublish(self, channel: str, event: LaneEvent) -> bool:
        return await asyncio.to_thread(self.publish, channel, event)

    async def aconsume(self, channel: str) -> list[LaneEvent]:
        return await asyncio.to_thread(self.consume, channel)

    async def aconsume_for(self, channel: str, consumer_id: str) -> list[LaneEvent]:
        return await asyncio.to_thread(self.consume_for, channel, consumer_id)


class AsyncEventBus:
    """
    A Pub/Sub event bus using asyncio.Queue supporting topics.
    Provides backpressure warning when a subscriber's queue is full.
    """

    def __init__(self, max_queue_size: int = 100) -> None:
        self.max_queue_size = max_queue_size
        self._subscribers: dict[str, set[asyncio.Queue[Any]]] = {}

    def publish(self, topic: str, event: Any) -> None:
        """
        Publish an event to a specific topic.
        Logs a backpressure warning if a queue is full.
        """
        if topic not in self._subscribers:
            return
        
        for queue in list(self._subscribers[topic]):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"AsyncEventBus backpressure: queue full for topic '{topic}', dropping event.")

    def subscribe(self, topic: str) -> asyncio.Queue[Any]:
        """
        Subscribe to a topic. Returns an asyncio.Queue.
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
        
        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=self.max_queue_size)
        self._subscribers[topic].add(queue)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue[Any]) -> None:
        """
        Unsubscribe a queue from a topic.
        """
        if topic in self._subscribers:
            self._subscribers[topic].discard(queue)
            if not self._subscribers[topic]:
                del self._subscribers[topic]


def _stable_trace_id(event_type: str, source_lane: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "event_type": event_type,
            "source_lane": source_lane,
            "payload": payload,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return sha256(raw.encode("utf-8")).hexdigest()[:24]


def _json_default(value: object) -> object:
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())
    return str(value)
