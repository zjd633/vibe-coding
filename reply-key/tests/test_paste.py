from __future__ import annotations

import pytest

from replykey.paste import (
    VK_RETURN,
    PasteCoordinator,
    PasteError,
    paste_key_events,
)
from replykey.windows import ForegroundTarget


class FakeInspector:
    def __init__(self, foreground_values: list[bool], valid: bool = True) -> None:
        self.foreground_values = list(foreground_values)
        self.valid = valid

    def target_still_valid(self, target: ForegroundTarget) -> bool:
        return self.valid

    def is_foreground(self, hwnd: int) -> bool:
        if len(self.foreground_values) > 1:
            return self.foreground_values.pop(0)
        return self.foreground_values[0]


class FakeClipboard:
    def __init__(self, text: str) -> None:
        self.text = text
        self.writes: list[str] = []

    def read_text(self) -> str:
        return self.text

    def write_text(self, text: str) -> None:
        self.text = text
        self.writes.append(text)


class FailingRestoreClipboard(FakeClipboard):
    def write_text(self, text: str) -> None:
        if text == "原消息":
            raise RuntimeError("clipboard is locked")
        super().write_text(text)


class FakeKeyboard:
    def __init__(self, error: Exception | None = None) -> None:
        self.paste_calls = 0
        self.error = error

    def paste(self) -> None:
        self.paste_calls += 1
        if self.error:
            raise self.error


TARGET = ForegroundTarget(101, "Weixin.exe")


def test_same_wechat_window_pastes_then_restores_original_clipboard() -> None:
    clipboard = FakeClipboard("原消息")
    keyboard = FakeKeyboard()
    coordinator = PasteCoordinator(
        FakeInspector([True, True]), clipboard, keyboard, sleeper=lambda _: None
    )

    result = coordinator.deliver(TARGET, "AI 草稿")

    assert result.action == "pasted"
    assert keyboard.paste_calls == 1
    assert clipboard.writes == ["AI 草稿", "原消息"]
    assert clipboard.text == "原消息"


def test_switched_window_only_copies_draft_and_never_pastes() -> None:
    clipboard = FakeClipboard("原消息")
    keyboard = FakeKeyboard()
    coordinator = PasteCoordinator(
        FakeInspector([False]), clipboard, keyboard, sleeper=lambda _: None
    )

    result = coordinator.deliver(TARGET, "AI 草稿")

    assert result.action == "copied"
    assert keyboard.paste_calls == 0
    assert clipboard.text == "AI 草稿"


def test_switch_after_clipboard_write_still_prevents_paste() -> None:
    clipboard = FakeClipboard("原消息")
    keyboard = FakeKeyboard()
    coordinator = PasteCoordinator(
        FakeInspector([True, False]), clipboard, keyboard, sleeper=lambda _: None
    )

    result = coordinator.deliver(TARGET, "AI 草稿")

    assert result.action == "copied"
    assert keyboard.paste_calls == 0
    assert clipboard.text == "AI 草稿"


def test_keyboard_failure_restores_clipboard_and_is_mapped() -> None:
    clipboard = FakeClipboard("原消息")
    coordinator = PasteCoordinator(
        FakeInspector([True, True]),
        clipboard,
        FakeKeyboard(RuntimeError("input failed")),
        sleeper=lambda _: None,
    )

    with pytest.raises(PasteError):
        coordinator.deliver(TARGET, "AI 草稿")

    assert clipboard.text == "原消息"


def test_keyboard_and_restore_failure_reports_clipboard_was_not_restored() -> None:
    clipboard = FailingRestoreClipboard("原消息")
    coordinator = PasteCoordinator(
        FakeInspector([True, True]),
        clipboard,
        FakeKeyboard(RuntimeError("input failed")),
        sleeper=lambda _: None,
    )

    with pytest.raises(PasteError, match="无法恢复"):
        coordinator.deliver(TARGET, "AI 草稿")

    assert clipboard.text == "AI 草稿"


def test_real_paste_event_sequence_has_no_enter_key() -> None:
    events = paste_key_events()

    assert events
    assert all(event.virtual_key != VK_RETURN for event in events)
