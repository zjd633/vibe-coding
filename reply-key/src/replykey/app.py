from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog

from .clipboard import Win32Clipboard
from .config import AppConfig, ConfigStore
from .controller import ControllerStatus, ReplyController
from .credentials import CredentialStore
from .hotkey import HotkeyRegistrationError, HotkeyService
from .logging_setup import NullPrivacyLogger, setup_logging
from .paste import PasteCoordinator, Win32KeyboardPaster
from .provider import ChatCompletionProvider
from .session import ConversationSession
from .single_instance import SingleInstanceGuard
from .startup import StartupManager
from .ui.settings import PrivacyDialog, SettingsWindow
from .ui.theme import configure_application
from .ui.tray import TrayController
from .windows import Win32WindowInspector


class _RuntimeSignals(QObject):
    hotkey_triggered = Signal()
    status = Signal(object)


def resource_path(relative: str) -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    root = Path(bundled_root) if bundled_root else Path(__file__).resolve().parents[2]
    return root / relative


def create_provider(config: AppConfig, api_key: str) -> ChatCompletionProvider:
    return ChatCompletionProvider(
        api_base_url=config.api_base_url,
        api_key=api_key,
        model=config.model,
        timeout_seconds=config.request_timeout_seconds,
    )


class ReplyKeyRuntime(QObject):
    def __init__(
        self,
        *,
        app: QApplication,
        guard,
        config_store=None,
        credential_store=None,
        startup_manager=None,
        inspector=None,
        clipboard=None,
        keyboard=None,
        provider_factory: Callable[[AppConfig, str], object] = create_provider,
        hotkey_factory=HotkeyService,
        tray_factory=TrayController,
        settings_factory=SettingsWindow,
        privacy_dialog_factory=PrivacyDialog,
        event_logger=None,
    ) -> None:
        super().__init__()
        self.app = app
        self.guard = guard
        self.config_store = config_store if config_store is not None else ConfigStore()
        self.credential_store = (
            credential_store if credential_store is not None else CredentialStore()
        )
        self.startup_manager = (
            startup_manager if startup_manager is not None else StartupManager()
        )
        self.inspector = inspector if inspector is not None else Win32WindowInspector()
        self.clipboard = clipboard if clipboard is not None else Win32Clipboard()
        self.keyboard = keyboard if keyboard is not None else Win32KeyboardPaster()
        self.provider_factory = provider_factory
        self.privacy_dialog_factory = privacy_dialog_factory
        self.event_logger = event_logger if event_logger is not None else NullPrivacyLogger()
        self.config = self.config_store.load()
        self._cleaned = False

        self.signals = _RuntimeSignals(self)
        self.session = ConversationSession(
            max_interactions=8,
            timeout_seconds=self.config.session_timeout_minutes * 60,
        )
        self.paste_coordinator = PasteCoordinator(
            self.inspector, self.clipboard, self.keyboard
        )
        self.controller = ReplyController(
            inspector=self.inspector,
            clipboard=self.clipboard,
            provider_factory=self.provider_factory,
            config_supplier=lambda: self.config,
            api_key_supplier=self.credential_store.get_api_key,
            session=self.session,
            paste_coordinator=self.paste_coordinator,
            status_callback=self.signals.status.emit,
        )

        self.hotkey = hotkey_factory(self.signals.hotkey_triggered.emit)
        icon = QIcon(str(resource_path("assets/replykey.svg")))
        startup_enabled = self._startup_enabled()
        self.tray = tray_factory(
            on_settings=self.show_settings,
            on_pause=self._set_paused,
            on_clear=self.controller.clear_session,
            on_startup=self._set_startup,
            on_exit=self.shutdown,
            startup_enabled=startup_enabled,
            icon=icon,
        )
        self.settings_window = settings_factory(
            config_store=self.config_store,
            credential_store=self.credential_store,
            startup_manager=self.startup_manager,
            connection_tester=self._test_connection,
        )

        self.signals.hotkey_triggered.connect(self._handle_hotkey)
        self.signals.status.connect(self.tray.show_status)
        self.settings_window.settings_saved.connect(self._apply_settings)
        self.guard.activation_requested.connect(self.show_settings)
        self.app.aboutToQuit.connect(self.cleanup)

    def start(self) -> None:
        if not self.config.privacy_notice_accepted:
            QTimer.singleShot(0, self._show_privacy_notice)
            return
        self._start_hotkey()

    def _start_hotkey(self) -> None:
        try:
            self.hotkey.start(self.config.hotkey)
        except HotkeyRegistrationError as exc:
            self._status("hotkey_error", str(exc), "error")
            QTimer.singleShot(0, self.show_settings)
        else:
            self._status("ready", f"ReplyKey 已就绪：{self.config.hotkey}", "success")

    @Slot()
    def _handle_hotkey(self) -> None:
        self.controller.trigger()

    @Slot(object)
    def _apply_settings(self, new_config: AppConfig) -> None:
        old_config = self.config
        if new_config.hotkey != old_config.hotkey:
            try:
                self.hotkey.start(new_config.hotkey)
            except HotkeyRegistrationError as exc:
                try:
                    self.hotkey.start(old_config.hotkey)
                except HotkeyRegistrationError:
                    pass
                rolled_back = replace(new_config, hotkey=old_config.hotkey)
                self.config_store.save(rolled_back)
                self.config = rolled_back
                self.settings_window.reload()
                self._status("hotkey_error", str(exc), "error")
                return
        self.config = new_config
        self.tray.set_startup_checked(new_config.launch_at_startup)
        self._status("settings_saved", "设置已保存并生效。", "success")

    @Slot(bool)
    def _set_paused(self, paused: bool) -> None:
        self.controller.set_paused(paused)
        if paused:
            self._status("paused", "热键已暂停。", "warning")
        else:
            self._status("resumed", "热键已恢复。", "success")

    @Slot(bool)
    def _set_startup(self, enabled: bool) -> None:
        try:
            self.startup_manager.set_enabled(enabled)
            self.config = replace(self.config, launch_at_startup=enabled)
            self.config_store.save(self.config)
        except Exception:
            self.tray.set_startup_checked(not enabled)
            self._status("startup_error", "无法更新开机启动设置。", "error")
            return
        self._status(
            "startup_updated",
            "已开启开机启动。" if enabled else "已关闭开机启动。",
            "success",
        )

    @Slot()
    def show_settings(self) -> None:
        self.settings_window.reload()
        self.settings_window.showNormal()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _show_privacy_notice(self) -> None:
        dialog = self.privacy_dialog_factory()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.shutdown()
            return
        self.config = replace(self.config, privacy_notice_accepted=True)
        self.config_store.save(self.config)
        self._start_hotkey()

    def _test_connection(self, config: AppConfig, api_key: str):
        provider = self.provider_factory(config, api_key)
        return provider.test_connection()

    def _startup_enabled(self) -> bool:
        try:
            return bool(self.startup_manager.is_enabled())
        except Exception:
            return self.config.launch_at_startup

    def _status(self, code: str, message: str, level: str = "info") -> None:
        self.event_logger.event("status", code=code, status=level)
        self.signals.status.emit(ControllerStatus(code, message, level))

    @Slot()
    def cleanup(self) -> None:
        if self._cleaned:
            return
        self._cleaned = True
        self.hotkey.stop()
        self.controller.close()
        self.tray.hide()
        self.settings_window.close()
        self.guard.close()
        self.event_logger.event("application_stopped")
        self.event_logger.close()

    @Slot()
    def shutdown(self) -> None:
        self.cleanup()
        self.app.quit()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ReplyKey")
    app.setOrganizationName("ReplyKey")
    app.setQuitOnLastWindowClosed(False)
    configure_application(app)
    app.setWindowIcon(QIcon(str(resource_path("assets/replykey.svg"))))

    guard = SingleInstanceGuard()
    if not guard.acquire():
        return 0
    event_logger = setup_logging()
    event_logger.event("application_started", version="0.1.0")
    runtime = ReplyKeyRuntime(app=app, guard=guard, event_logger=event_logger)
    runtime.start()
    return app.exec()
