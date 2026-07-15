from __future__ import annotations

import ctypes
from ctypes import wintypes
import time
from typing import Callable, Protocol, TypeVar


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class ClipboardError(RuntimeError):
    pass


class ClipboardApi(Protocol):
    def open(self) -> bool: ...

    def close(self) -> None: ...

    def read_unicode(self) -> str: ...

    def write_unicode(self, text: str) -> None: ...


T = TypeVar("T")


class Win32Clipboard:
    def __init__(
        self,
        api: ClipboardApi | None = None,
        attempts: int = 6,
        retry_delay: float = 0.02,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api = api or CtypesClipboardApi()
        self._attempts = max(1, attempts)
        self._retry_delay = max(0.0, retry_delay)
        self._sleeper = sleeper

    def read_text(self) -> str:
        return self._while_open(self._api.read_unicode)

    def write_text(self, text: str) -> None:
        self._while_open(lambda: self._api.write_unicode(text))

    def _while_open(self, operation: Callable[[], T]) -> T:
        opened = False
        for attempt in range(self._attempts):
            if self._api.open():
                opened = True
                break
            if attempt + 1 < self._attempts:
                self._sleeper(self._retry_delay)
        if not opened:
            raise ClipboardError("剪贴板正被其他程序占用，请稍后重试。")
        try:
            return operation()
        except ClipboardError:
            raise
        except Exception as exc:
            raise ClipboardError("无法读取或更新剪贴板，请稍后重试。") from exc
        finally:
            self._api.close()


class CtypesClipboardApi:
    def __init__(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._user32.OpenClipboard.argtypes = [wintypes.HWND]
        self._user32.OpenClipboard.restype = wintypes.BOOL
        self._user32.CloseClipboard.restype = wintypes.BOOL
        self._user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
        self._user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
        self._user32.GetClipboardData.argtypes = [wintypes.UINT]
        self._user32.GetClipboardData.restype = wintypes.HANDLE
        self._user32.EmptyClipboard.restype = wintypes.BOOL
        self._user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        self._user32.SetClipboardData.restype = wintypes.HANDLE
        self._kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        self._kernel32.GlobalAlloc.restype = wintypes.HANDLE
        self._kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
        self._kernel32.GlobalLock.restype = ctypes.c_void_p
        self._kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
        self._kernel32.GlobalFree.argtypes = [wintypes.HANDLE]

    def open(self) -> bool:
        return bool(self._user32.OpenClipboard(None))

    def close(self) -> None:
        self._user32.CloseClipboard()

    def read_unicode(self) -> str:
        if not self._user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""
        handle = self._user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        pointer = self._kernel32.GlobalLock(handle)
        if not pointer:
            raise ClipboardError("无法读取剪贴板文本，请重试。")
        try:
            return ctypes.wstring_at(pointer)
        finally:
            self._kernel32.GlobalUnlock(handle)

    def write_unicode(self, text: str) -> None:
        encoded = (text + "\0").encode("utf-16-le")
        handle = self._kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not handle:
            raise ClipboardError("无法分配剪贴板内存。")
        transferred = False
        try:
            pointer = self._kernel32.GlobalLock(handle)
            if not pointer:
                raise ClipboardError("无法写入剪贴板内存。")
            try:
                ctypes.memmove(pointer, encoded, len(encoded))
            finally:
                self._kernel32.GlobalUnlock(handle)
            if not self._user32.EmptyClipboard():
                raise ClipboardError("无法清空剪贴板。")
            if not self._user32.SetClipboardData(CF_UNICODETEXT, handle):
                raise ClipboardError("无法更新剪贴板。")
            transferred = True
        finally:
            if not transferred:
                self._kernel32.GlobalFree(handle)

