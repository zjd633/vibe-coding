from __future__ import annotations

import threading

import pytest

from replykey.hotkey import (
    HotkeyRegistrationError,
    HotkeyService,
    HotkeySyntaxError,
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    parse_hotkey,
)


def test_parse_default_hotkey() -> None:
    hotkey = parse_hotkey("ctrl + ALT + r")

    assert hotkey.modifiers == MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
    assert hotkey.virtual_key == ord("R")
    assert hotkey.normalized == "Ctrl+Alt+R"


@pytest.mark.parametrize("value", ["", "Ctrl+Alt", "R", "Ctrl+Nope+R", "Ctrl+R+T"])
def test_invalid_hotkeys_are_rejected(value: str) -> None:
    with pytest.raises(HotkeySyntaxError):
        parse_hotkey(value)


class FakeHotkeyBackend:
    def __init__(self, register_result: bool = True, fire_once: bool = False) -> None:
        self.register_result = register_result
        self.fire_once = fire_once
        self.registered = []
        self.unregister_calls = 0
        self.wake_event = threading.Event()

    def register(self, hotkey) -> bool:
        self.registered.append(hotkey)
        return self.register_result

    def pump(self, callback) -> None:
        if self.fire_once:
            callback()
        self.wake_event.wait(timeout=1)

    def wake(self) -> None:
        self.wake_event.set()

    def unregister(self) -> None:
        self.unregister_calls += 1


def test_registration_conflict_is_reported_without_running_service() -> None:
    backend = FakeHotkeyBackend(register_result=False)
    service = HotkeyService(lambda: None, backend=backend)

    with pytest.raises(HotkeyRegistrationError):
        service.start("Ctrl+Alt+R")

    assert not service.running
    assert backend.unregister_calls == 0


def test_stop_wakes_message_loop_and_unregisters() -> None:
    fired = threading.Event()
    backend = FakeHotkeyBackend(fire_once=True)
    service = HotkeyService(fired.set, backend=backend)

    service.start("Ctrl+Alt+R")
    assert fired.wait(timeout=1)
    service.stop()

    assert not service.running
    assert backend.unregister_calls == 1

