from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog

from replykey.app import ReplyKeyRuntime
from replykey.config import AppConfig
from replykey.models import ReplyDraft
from replykey.ui.theme import configure_application


class FakeConfigStore:
    def __init__(self) -> None:
        self.config = AppConfig()
        self.saved = []

    def load(self):
        return self.config

    def save(self, config):
        self.config = config
        self.saved.append(config)


class FakeCredentials:
    def get_api_key(self):
        return "local-key"

    def set_api_key(self, value):
        return None


class FakeStartup:
    def __init__(self) -> None:
        self.values = []

    def is_enabled(self):
        return False

    def set_enabled(self, value):
        self.values.append(value)


class FakeInspector:
    def capture_wechat_target(self):
        return None

    def target_still_valid(self, target):
        return False

    def is_foreground(self, hwnd):
        return False


class FakeClipboard:
    def read_text(self):
        return ""

    def write_text(self, text):
        return None


class FakeKeyboard:
    def paste(self):
        raise AssertionError("paste should not run in this wiring test")


class FakeHotkey:
    def __init__(self, callback) -> None:
        self.callback = callback
        self.started = []
        self.stop_calls = 0

    def start(self, value):
        self.started.append(value)

    def stop(self):
        self.stop_calls += 1


class FakeSettings(QObject):
    settings_saved = Signal(object)

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.reload_calls = 0
        self.show_calls = 0

    def reload(self):
        self.reload_calls += 1

    def showNormal(self):
        self.show_calls += 1

    def raise_(self):
        return None

    def activateWindow(self):
        return None

    def close(self):
        return None


class FakeTray:
    def __init__(self, **kwargs) -> None:
        self.callbacks = kwargs
        self.statuses = []
        self.startup_checked = []
        self.hidden = False

    def show_status(self, status):
        self.statuses.append(status)

    def set_startup_checked(self, value):
        self.startup_checked.append(value)

    def hide(self):
        self.hidden = True


class FakeGuard(QObject):
    activation_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.closed = False

    def close(self):
        self.closed = True


class AcceptPrivacy:
    def exec(self):
        return QDialog.DialogCode.Accepted


def test_runtime_starts_hotkey_accepts_privacy_and_applies_saved_hotkey(qtbot, qapp) -> None:
    store = FakeConfigStore()
    startup = FakeStartup()
    guard = FakeGuard()
    hotkeys = []
    trays = []
    settings = []

    def hotkey_factory(callback):
        service = FakeHotkey(callback)
        hotkeys.append(service)
        return service

    def tray_factory(**kwargs):
        tray = FakeTray(**kwargs)
        trays.append(tray)
        return tray

    def settings_factory(**kwargs):
        window = FakeSettings(**kwargs)
        settings.append(window)
        return window

    runtime = ReplyKeyRuntime(
        app=qapp,
        guard=guard,
        config_store=store,
        credential_store=FakeCredentials(),
        startup_manager=startup,
        inspector=FakeInspector(),
        clipboard=FakeClipboard(),
        keyboard=FakeKeyboard(),
        provider_factory=lambda config, key: object(),
        hotkey_factory=hotkey_factory,
        tray_factory=tray_factory,
        settings_factory=settings_factory,
        privacy_dialog_factory=AcceptPrivacy,
    )

    runtime.start()
    assert hotkeys[0].started == []
    qtbot.waitUntil(lambda: bool(store.saved), timeout=1000)

    assert hotkeys[0].started == ["Ctrl+Alt+R"]
    assert store.saved[-1].privacy_notice_accepted

    updated = replace(store.saved[-1], hotkey="Ctrl+Shift+K")
    settings[0].settings_saved.emit(updated)
    assert hotkeys[0].started[-1] == "Ctrl+Shift+K"

    trays[0].callbacks["on_pause"](True)
    assert runtime.controller.paused
    guard.activation_requested.emit()
    assert settings[0].show_calls == 1

    runtime.cleanup()
    assert hotkeys[0].stop_calls >= 1
    assert trays[0].hidden
    assert guard.closed


def test_theme_uses_segoe_ui(qapp) -> None:
    configure_application(qapp)

    assert qapp.font().family() == "Segoe UI"
