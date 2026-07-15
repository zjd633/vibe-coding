from __future__ import annotations

import pytest

from replykey.windows import (
    ForegroundTarget,
    Win32WindowInspector,
    is_wechat_executable,
)


@pytest.mark.parametrize(
    "name", ["Weixin.exe", "weixin.EXE", "WeChat.exe", "WECHAT.EXE"]
)
def test_only_current_and_legacy_wechat_executables_are_allowed(name: str) -> None:
    assert is_wechat_executable(name)


@pytest.mark.parametrize(
    "name", ["wechatweb.exe", "WeChatApp.exe", "chrome.exe", "", "Weixin.exe.bak"]
)
def test_similar_or_unrelated_process_names_are_rejected(name: str) -> None:
    assert not is_wechat_executable(name)


class FakeWindowApi:
    def __init__(self) -> None:
        self.foreground = 101
        self.live = {101}
        self.names = {101: "Weixin.exe"}

    def get_foreground_window(self) -> int:
        return self.foreground

    def is_window(self, hwnd: int) -> bool:
        return hwnd in self.live

    def process_name(self, hwnd: int) -> str:
        return self.names.get(hwnd, "")


def test_capture_records_foreground_wechat_handle_and_process() -> None:
    inspector = Win32WindowInspector(api=FakeWindowApi())

    target = inspector.capture_wechat_target()

    assert target == ForegroundTarget(hwnd=101, process_name="Weixin.exe")


def test_non_wechat_foreground_is_not_captured() -> None:
    api = FakeWindowApi()
    api.names[101] = "notepad.exe"

    assert Win32WindowInspector(api=api).capture_wechat_target() is None


def test_revalidation_rejects_dead_or_reused_window_handles() -> None:
    api = FakeWindowApi()
    inspector = Win32WindowInspector(api=api)
    target = ForegroundTarget(hwnd=101, process_name="Weixin.exe")

    api.live.clear()
    assert not inspector.target_still_valid(target)

    api.live.add(101)
    api.names[101] = "notepad.exe"
    assert not inspector.target_still_valid(target)


def test_foreground_check_compares_exact_recorded_handle() -> None:
    api = FakeWindowApi()
    inspector = Win32WindowInspector(api=api)

    assert inspector.is_foreground(101)
    api.foreground = 202
    assert not inspector.is_foreground(101)

