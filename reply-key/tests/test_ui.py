from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QLineEdit, QVBoxLayout

from replykey.config import AppConfig
from replykey.models import ReplyDraft
from replykey.ui.settings import PrivacyDialog, SettingsWindow
from replykey.ui.tray import TrayController


class FakeConfigStore:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self.saved: list[AppConfig] = []

    def load(self) -> AppConfig:
        return self.config

    def save(self, config: AppConfig) -> None:
        self.config = config
        self.saved.append(config)


class FakeCredentialStore:
    def __init__(self, key: str = "") -> None:
        self.key = key
        self.saved: list[str] = []

    def get_api_key(self) -> str:
        return self.key

    def set_api_key(self, key: str) -> None:
        self.key = key.strip()
        self.saved.append(key.strip())


class FakeStartupManager:
    def __init__(self) -> None:
        self.enabled_values: list[bool] = []

    def set_enabled(self, enabled: bool) -> None:
        self.enabled_values.append(enabled)


def make_settings(qtbot, *, config=None, key="", tester=None):
    config_store = FakeConfigStore(config)
    credentials = FakeCredentialStore(key)
    startup = FakeStartupManager()
    window = SettingsWindow(
        config_store=config_store,
        credential_store=credentials,
        startup_manager=startup,
        connection_tester=tester or (lambda config, api_key: ReplyDraft("连接成功")),
    )
    qtbot.addWidget(window)
    return window, config_store, credentials, startup


def test_settings_has_labeled_single_column_fields_and_masked_key(qtbot) -> None:
    window, *_ = make_settings(qtbot, key="secret")

    assert window.api_base_edit.accessibleName() == "API Base URL"
    assert window.api_key_edit.accessibleName() == "API Key"
    assert window.model_edit.accessibleName() == "模型名称"
    assert window.hotkey_edit.accessibleName() == "全局热键"
    assert window.api_key_edit.echoMode() == QLineEdit.EchoMode.Password
    assert isinstance(window.form_layout, QVBoxLayout)


def test_invalid_hotkey_shows_inline_error_and_does_not_save(qtbot) -> None:
    window, config_store, credentials, _ = make_settings(qtbot, key="secret")
    window.hotkey_edit.setText("Ctrl+Alt")

    window.save_button.click()

    assert window.hotkey_error.text()
    assert config_store.saved == []
    assert credentials.saved == []


def test_save_separates_secret_from_json_config_and_updates_startup(qtbot) -> None:
    window, config_store, credentials, startup = make_settings(qtbot, key="old")
    window.api_base_edit.setText("https://compatible.example/v1/")
    window.api_key_edit.setText("new-secret")
    window.model_edit.setText("provider-model")
    window.hotkey_edit.setText("Ctrl+Shift+K")
    window.startup_checkbox.setChecked(True)

    with qtbot.waitSignal(window.settings_saved, timeout=1000) as signal:
        window.save_button.click()

    saved = signal.args[0]
    assert saved.api_base_url == "https://compatible.example/v1"
    assert saved.model == "provider-model"
    assert saved.hotkey == "Ctrl+Shift+K"
    assert credentials.saved == ["new-secret"]
    assert config_store.saved == [saved]
    assert startup.enabled_values == [True]


def test_connection_test_runs_minimal_tester_and_reports_inline_success(qtbot) -> None:
    calls = []

    def tester(config, api_key):
        calls.append((config, api_key))
        return ReplyDraft("连接成功")

    window, *_ = make_settings(qtbot, key="local-key", tester=tester)

    window.test_button.click()
    qtbot.waitUntil(lambda: window.connection_status.text() == "连接成功", timeout=2000)

    assert calls[0][1] == "local-key"
    assert calls[0][0].model == "gpt-5.6-luna"
    assert window.test_button.isEnabled()


def test_privacy_dialog_explicitly_discloses_api_transfer_and_manual_send(qtbot) -> None:
    dialog = PrivacyDialog()
    qtbot.addWidget(dialog)

    text = dialog.notice_label.text()
    assert "发送到你配置的 API 服务" in text
    assert "不会自动发送" in text


class FakeTrayIcon:
    def __init__(self) -> None:
        self.menu = None
        self.messages = []
        self.visible = False

    def setContextMenu(self, menu) -> None:
        self.menu = menu

    def setToolTip(self, text: str) -> None:
        self.tooltip = text

    def setIcon(self, icon) -> None:
        self.icon = icon

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def showMessage(self, *args) -> None:
        self.messages.append(args)


def test_tray_actions_wire_settings_pause_clear_startup_and_exit(qapp) -> None:
    calls = []
    icon = FakeTrayIcon()
    tray = TrayController(
        on_settings=lambda: calls.append("settings"),
        on_pause=lambda value: calls.append(("pause", value)),
        on_clear=lambda: calls.append("clear"),
        on_startup=lambda value: calls.append(("startup", value)),
        on_exit=lambda: calls.append("exit"),
        startup_enabled=False,
        tray_icon=icon,
    )

    tray.settings_action.trigger()
    tray.pause_action.trigger()
    tray.clear_action.trigger()
    tray.startup_action.trigger()
    tray.exit_action.trigger()

    assert calls == [
        "settings",
        ("pause", True),
        "clear",
        ("startup", True),
        "exit",
    ]
    assert icon.visible
