from __future__ import annotations

import threading
import time
from typing import Any


class EventBus:
    def __init__(self, max_events: int = 500):
        self.max_events = max_events
        self._lock = threading.Lock()
        self._seq = 0
        self._events: list[dict[str, Any]] = []

    def publish(self, event: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            self._seq += 1
            item = {
                "id": self._seq,
                "event": event,
                "data": data or {},
                "created_at": time.time(),
            }
            self._events.append(item)
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events :]
            return item.copy()

    def since(self, event_id: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            return [item.copy() for item in self._events if int(item["id"]) > event_id]

    @property
    def last_id(self) -> int:
        with self._lock:
            return self._seq


event_bus = EventBus()
