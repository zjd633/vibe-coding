from __future__ import annotations

import pytest

from replykey.clipboard import ClipboardError, Win32Clipboard


class FakeClipboardApi:
    def __init__(self, open_results: list[bool] | None = None) -> None:
        self.open_results = list(open_results or [True])
        self.text = "你好，世界"
        self.close_calls = 0

    def open(self) -> bool:
        return self.open_results.pop(0) if self.open_results else False

    def close(self) -> None:
        self.close_calls += 1

    def read_unicode(self) -> str:
        return self.text

    def write_unicode(self, text: str) -> None:
        self.text = text


def test_clipboard_retries_busy_open_and_reads_unicode() -> None:
    api = FakeClipboardApi([False, False, True])
    sleeps: list[float] = []
    clipboard = Win32Clipboard(api=api, attempts=4, retry_delay=0.01, sleeper=sleeps.append)

    assert clipboard.read_text() == "你好，世界"
    assert sleeps == [0.01, 0.01]
    assert api.close_calls == 1


def test_clipboard_writes_unicode_and_always_closes() -> None:
    api = FakeClipboardApi()
    clipboard = Win32Clipboard(api=api)

    clipboard.write_text("草稿：晚点见")

    assert api.text == "草稿：晚点见"
    assert api.close_calls == 1


def test_clipboard_busy_failure_has_safe_chinese_error() -> None:
    api = FakeClipboardApi([False, False])
    clipboard = Win32Clipboard(api=api, attempts=2, retry_delay=0, sleeper=lambda _: None)

    with pytest.raises(ClipboardError) as caught:
        clipboard.read_text()

    assert "剪贴板" in str(caught.value)

