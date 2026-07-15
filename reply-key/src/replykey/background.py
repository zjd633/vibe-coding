from __future__ import annotations

from concurrent.futures import Future
import itertools
import threading
from typing import Any, Callable


class DaemonTaskExecutor:
    """Minimal executor whose running requests cannot keep ReplyKey alive on exit."""

    def __init__(self, thread_name_prefix: str = "ReplyKeyTask") -> None:
        self._thread_name_prefix = thread_name_prefix
        self._counter = itertools.count(1)
        self._lock = threading.Lock()
        self._closed = False
        self._futures: set[Future[Any]] = set()
        self._threads: set[threading.Thread] = set()

    def submit(
        self, function: Callable[..., Any], /, *args: Any, **kwargs: Any
    ) -> Future[Any]:
        future: Future[Any] = Future()
        thread: threading.Thread

        def run() -> None:
            try:
                if not future.set_running_or_notify_cancel():
                    return
                try:
                    result = function(*args, **kwargs)
                except BaseException as exc:
                    future.set_exception(exc)
                else:
                    future.set_result(result)
            finally:
                with self._lock:
                    self._futures.discard(future)
                    self._threads.discard(thread)

        with self._lock:
            if self._closed:
                raise RuntimeError("executor has been shut down")
            thread = threading.Thread(
                target=run,
                name=f"{self._thread_name_prefix}-{next(self._counter)}",
                daemon=True,
            )
            self._futures.add(future)
            self._threads.add(thread)
            thread.start()
        return future

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        with self._lock:
            self._closed = True
            futures = tuple(self._futures)
            threads = tuple(self._threads)
        if cancel_futures:
            for future in futures:
                future.cancel()
        if wait:
            current = threading.current_thread()
            for thread in threads:
                if thread is not current:
                    thread.join()
