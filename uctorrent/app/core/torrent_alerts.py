from __future__ import annotations


class TorrentAlertBus:
    def __init__(self):
        self.events: list[dict] = []

    def publish(self, event: str, payload: dict) -> None:
        self.events.append({"event": event, "payload": payload})

    def drain(self) -> list[dict]:
        events = self.events[:]
        self.events.clear()
        return events

