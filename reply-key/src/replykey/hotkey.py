from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import threading
from typing import Callable, Protocol


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID = 0xB001


class HotkeySyntaxError(ValueError):
    pass


class HotkeyRegistrationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Hotkey:
    modifiers: int
    virtual_key: int
    normalized: str


def parse_hotkey(value: str) -> Hotkey:
    tokens = [part.strip() for part in value.split("+") if part.strip()]
    modifier_map = {
        "ctrl": (MOD_CONTROL, "Ctrl"),
        "control": (MOD_CONTROL, "Ctrl"),
        "alt": (MOD_ALT, "Alt"),
        "shift": (MOD_SHIFT, "Shift"),
        "win": (MOD_WIN, "Win"),
        "windows": (MOD_WIN, "Win"),
    }
    modifiers = 0
    names: set[str] = set()
    key_name: str | None = None
    virtual_key: int | None = None
    for token in tokens:
        lowered = token.casefold()
        if lowered in modifier_map:
            flag, name = modifier_map[lowered]
            if name in names:
                raise HotkeySyntaxError("热键包含重复修饰键。")
            modifiers |= flag
            names.add(name)
            continue
        if virtual_key is not None:
            raise HotkeySyntaxError("热键只能包含一个普通按键。")
        upper = token.upper()
        if len(upper) == 1 and upper.isascii() and upper.isalnum():
            virtual_key = ord(upper)
            key_name = upper
        elif upper.startswith("F") and upper[1:].isdigit() and 1 <= int(upper[1:]) <= 12:
            virtual_key = 0x70 + int(upper[1:]) - 1
            key_name = upper
        else:
            raise HotkeySyntaxError("热键包含不支持的按键。")
    if not modifiers or virtual_key is None or key_name is None:
        raise HotkeySyntaxError("热键至少需要一个修饰键和一个普通按键。")
    ordered = [name for name in ("Ctrl", "Alt", "Shift", "Win") if name in names]
    return Hotkey(
        modifiers=modifiers | MOD_NOREPEAT,
        virtual_key=virtual_key,
        normalized="+".join([*ordered, key_name]),
    )


class HotkeyBackend(Protocol):
    def register(self, hotkey: Hotkey) -> bool: ...

    def pump(self, callback: Callable[[], None]) -> None: ...

    def wake(self) -> None: ...

    def unregister(self) -> None: ...


class HotkeyService:
    def __init__(
        self, callback: Callable[[], None], backend: HotkeyBackend | None = None
    ) -> None:
        self._callback = callback
        self._backend = backend or Win32HotkeyBackend()
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._error: HotkeyRegistrationError | None = None
        self._registered = False

    @property
    def running(self) -> bool:
        return bool(self._registered and self._thread and self._thread.is_alive())

    def start(self, value: str) -> None:
        hotkey = parse_hotkey(value)
        self.stop()
        self._ready.clear()
        self._error = None
        self._thread = threading.Thread(
            target=self._run, args=(hotkey,), name="ReplyKeyHotkey", daemon=True
        )
        self._thread.start()
        if not self._ready.wait(timeout=2):
            self.stop()
            raise HotkeyRegistrationError("热键监听启动超时，请重试。")
        if self._error is not None:
            error = self._error
            self._thread.join(timeout=1)
            self._thread = None
            raise error

    def stop(self) -> None:
        thread = self._thread
        if thread and thread.is_alive():
            self._backend.wake()
            thread.join(timeout=2)
        self._thread = None
        self._registered = False

    def _run(self, hotkey: Hotkey) -> None:
        if not self._backend.register(hotkey):
            self._error = HotkeyRegistrationError(
                f"热键 {hotkey.normalized} 已被其他程序占用，请更换后重试。"
            )
            self._ready.set()
            return
        self._registered = True
        self._ready.set()
        try:
            self._backend.pump(self._safe_callback)
        finally:
            self._backend.unregister()
            self._registered = False

    def _safe_callback(self) -> None:
        try:
            self._callback()
        except Exception:
            return


class Win32HotkeyBackend:
    def __init__(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._thread_id = 0

    def register(self, hotkey: Hotkey) -> bool:
        self._thread_id = int(self._kernel32.GetCurrentThreadId())
        message = wintypes.MSG()
        self._user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
        return bool(
            self._user32.RegisterHotKey(
                None, HOTKEY_ID, hotkey.modifiers, hotkey.virtual_key
            )
        )

    def pump(self, callback: Callable[[], None]) -> None:
        message = wintypes.MSG()
        while True:
            result = self._user32.GetMessageW(ctypes.byref(message), None, 0, 0)
            if result <= 0:
                return
            if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                callback()

    def wake(self) -> None:
        if self._thread_id:
            self._user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def unregister(self) -> None:
        self._user32.UnregisterHotKey(None, HOTKEY_ID)
        self._thread_id = 0

