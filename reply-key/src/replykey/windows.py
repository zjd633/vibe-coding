from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


WECHAT_EXECUTABLES = frozenset({"weixin.exe", "wechat.exe"})


def is_wechat_executable(process_name: str) -> bool:
    return Path(process_name).name.casefold() in WECHAT_EXECUTABLES


@dataclass(frozen=True, slots=True)
class ForegroundTarget:
    hwnd: int
    process_name: str


class WindowApi(Protocol):
    def get_foreground_window(self) -> int: ...

    def is_window(self, hwnd: int) -> bool: ...

    def process_name(self, hwnd: int) -> str: ...


class Win32WindowInspector:
    def __init__(self, api: WindowApi | None = None) -> None:
        self._api = api or CtypesWindowApi()

    def capture_wechat_target(self) -> ForegroundTarget | None:
        hwnd = self._api.get_foreground_window()
        if not hwnd or not self._api.is_window(hwnd):
            return None
        process_name = self._api.process_name(hwnd)
        if not is_wechat_executable(process_name):
            return None
        return ForegroundTarget(hwnd=hwnd, process_name=Path(process_name).name)

    def target_still_valid(self, target: ForegroundTarget) -> bool:
        if not target.hwnd or not self._api.is_window(target.hwnd):
            return False
        current_name = Path(self._api.process_name(target.hwnd)).name
        return (
            is_wechat_executable(current_name)
            and current_name.casefold() == target.process_name.casefold()
        )

    def is_foreground(self, hwnd: int) -> bool:
        return bool(hwnd) and self._api.get_foreground_window() == hwnd


class CtypesWindowApi:
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def __init__(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.IsWindow.argtypes = [wintypes.HWND]
        self._user32.IsWindow.restype = wintypes.BOOL
        self._user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL

    def get_foreground_window(self) -> int:
        return int(self._user32.GetForegroundWindow() or 0)

    def is_window(self, hwnd: int) -> bool:
        return bool(self._user32.IsWindow(hwnd))

    def process_name(self, hwnd: int) -> str:
        process_id = wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if not process_id.value:
            return ""
        handle = self._kernel32.OpenProcess(
            self.PROCESS_QUERY_LIMITED_INFORMATION, False, process_id.value
        )
        if not handle:
            return ""
        try:
            capacity = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(capacity.value)
            if not self._kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(capacity)
            ):
                return ""
            return Path(buffer.value).name
        finally:
            self._kernel32.CloseHandle(handle)

