from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time
from typing import Callable


@dataclass(frozen=True, slots=True)
class Interaction:
    inbound: str
    draft: str


class ConversationSession:
    def __init__(
        self,
        max_interactions: int = 8,
        timeout_seconds: float = 30 * 60,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_interactions < 1:
            raise ValueError("max_interactions must be positive")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._interactions: deque[Interaction] = deque(maxlen=max_interactions)
        self._timeout_seconds = float(timeout_seconds)
        self._clock = clock
        self._last_activity: float | None = None
        self._lock = threading.RLock()

    def append_success(self, inbound: str, draft: str) -> None:
        with self._lock:
            self._expire_if_idle()
            self._interactions.append(Interaction(inbound=inbound, draft=draft))
            self._last_activity = self._clock()

    def messages(self) -> list[dict[str, str]]:
        with self._lock:
            self._expire_if_idle()
            result: list[dict[str, str]] = []
            for interaction in self._interactions:
                result.append({"role": "user", "content": interaction.inbound})
                result.append({"role": "assistant", "content": interaction.draft})
            return result

    def touch(self) -> None:
        with self._lock:
            self._expire_if_idle()
            self._last_activity = self._clock()

    def clear(self) -> None:
        with self._lock:
            self._interactions.clear()
            self._last_activity = None

    def __len__(self) -> int:
        with self._lock:
            self._expire_if_idle()
            return len(self._interactions)

    def _expire_if_idle(self) -> None:
        if self._last_activity is None:
            return
        if self._clock() - self._last_activity >= self._timeout_seconds:
            self.clear()
