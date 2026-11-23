from __future__ import annotations

import threading
import time
from collections.abc import Callable


class SchedulerService:
    def __init__(self):
        self._jobs: list[tuple[int, Callable[[], None], float]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def add_interval(self, seconds: int, func: Callable[[], None]) -> None:
        self._jobs.append((seconds, func, 0.0))

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="UCtorrentScheduler")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            now = time.time()
            updated = []
            for interval, func, last_run in self._jobs:
                if now - last_run >= interval:
                    try:
                        func()
                    finally:
                        last_run = now
                updated.append((interval, func, last_run))
            self._jobs = updated
            self._stop.wait(1)

