from __future__ import annotations

import threading

from replykey.background import DaemonTaskExecutor


def test_background_task_runs_on_daemon_thread() -> None:
    executor = DaemonTaskExecutor(thread_name_prefix="ReplyKeyTest")

    future = executor.submit(lambda: threading.current_thread().daemon)

    assert future.result(timeout=1) is True
    executor.shutdown(wait=True)
