from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import time
from typing import Callable, Literal, Protocol

from .windows import ForegroundTarget


VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


class PasteError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class KeyEvent:
    virtual_key: int
    key_up: bool = False


def paste_key_events() -> tuple[KeyEvent, ...]:
    return (
        KeyEvent(VK_CONTROL),
        KeyEvent(VK_V),
        KeyEvent(VK_V, key_up=True),
        KeyEvent(VK_CONTROL, key_up=True),
    )


class TargetInspector(Protocol):
    def target_still_valid(self, target: ForegroundTarget) -> bool: ...

    def is_foreground(self, hwnd: int) -> bool: ...


class Clipboard(Protocol):
    def read_text(self) -> str: ...

    def write_text(self, text: str) -> None: ...


class KeyboardPaster(Protocol):
    def paste(self) -> None: ...


@dataclass(frozen=True, slots=True)
class PasteResult:
    action: Literal["pasted", "copied"]


class PasteCoordinator:
    def __init__(
        self,
        inspector: TargetInspector,
        clipboard: Clipboard,
        keyboard: KeyboardPaster,
        sleeper: Callable[[float], None] = time.sleep,
        restore_delay: float = 0.08,
    ) -> None:
        self._inspector = inspector
        self._clipboard = clipboard
        self._keyboard = keyboard
        self._sleeper = sleeper
        self._restore_delay = restore_delay

    def deliver(self, target: ForegroundTarget, draft: str) -> PasteResult:
        if not self._safe_to_paste(target):
            self._clipboard.write_text(draft)
            return PasteResult("copied")

        original = self._clipboard.read_text()
        self._clipboard.write_text(draft)
        if not self._safe_to_paste(target):
            return PasteResult("copied")

        try:
            self._keyboard.paste()
            self._sleeper(self._restore_delay)
        except Exception as exc:
            try:
                self._clipboard.write_text(original)
            except Exception as restore_exc:
                raise PasteError(
                    "无法粘贴草稿，且无法恢复原剪贴板内容。"
                ) from restore_exc
            raise PasteError("无法粘贴草稿，原剪贴板内容已恢复。") from exc

        try:
            self._clipboard.write_text(original)
        except Exception as exc:
            raise PasteError("草稿已粘贴，但无法恢复原剪贴板内容。") from exc
        return PasteResult("pasted")

    def _safe_to_paste(self, target: ForegroundTarget) -> bool:
        return self._inspector.target_still_valid(target) and self._inspector.is_foreground(
            target.hwnd
        )


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


class Win32KeyboardPaster:
    def __init__(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)

    def paste(self) -> None:
        events = paste_key_events()
        inputs = (_INPUT * len(events))()
        for index, event in enumerate(events):
            inputs[index].type = INPUT_KEYBOARD
            inputs[index].ki = _KEYBDINPUT(
                wVk=event.virtual_key,
                wScan=self._user32.MapVirtualKeyW(event.virtual_key, 0),
                dwFlags=KEYEVENTF_KEYUP if event.key_up else 0,
                time=0,
                dwExtraInfo=0,
            )
        sent = self._user32.SendInput(len(inputs), inputs, ctypes.sizeof(_INPUT))
        if sent != len(inputs):
            raise PasteError("Windows 未能完成粘贴按键。")
