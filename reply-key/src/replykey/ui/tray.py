from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..controller import ControllerStatus


class TrayController(QObject):
    def __init__(
        self,
        *,
        on_settings: Callable[[], None],
        on_pause: Callable[[bool], None],
        on_clear: Callable[[], None],
        on_startup: Callable[[bool], None],
        on_exit: Callable[[], None],
        startup_enabled: bool,
        icon: QIcon | None = None,
        tray_icon=None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_settings = on_settings
        self._on_pause = on_pause
        self._on_clear = on_clear
        self._on_startup = on_startup
        self._on_exit = on_exit
        self.tray_icon = tray_icon or QSystemTrayIcon(self)
        self.menu = QMenu()

        self.settings_action = QAction("设置", self)
        self.settings_action.triggered.connect(self._on_settings)
        self.menu.addAction(self.settings_action)

        self.pause_action = QAction("暂停热键", self)
        self.pause_action.setCheckable(True)
        self.pause_action.toggled.connect(self._on_pause)
        self.menu.addAction(self.pause_action)

        self.clear_action = QAction("清空会话", self)
        self.clear_action.triggered.connect(self._on_clear)
        self.menu.addAction(self.clear_action)

        self.startup_action = QAction("开机启动", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(startup_enabled)
        self.startup_action.toggled.connect(self._on_startup)
        self.menu.addAction(self.startup_action)

        self.menu.addSeparator()
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self._on_exit)
        self.menu.addAction(self.exit_action)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.setToolTip("ReplyKey 微信回复助手")
        self.tray_icon.setIcon(icon or QIcon())
        activated = getattr(self.tray_icon, "activated", None)
        if activated is not None:
            activated.connect(self._activated)
        self.tray_icon.show()

    def _activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_settings()

    def show_status(self, status: ControllerStatus) -> None:
        icon_map = {
            "success": QSystemTrayIcon.MessageIcon.Information,
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "error": QSystemTrayIcon.MessageIcon.Critical,
        }
        self.tray_icon.showMessage(
            "ReplyKey",
            status.message,
            icon_map.get(status.level, QSystemTrayIcon.MessageIcon.Information),
            4000,
        )

    def set_startup_checked(self, checked: bool) -> None:
        blocked = self.startup_action.blockSignals(True)
        self.startup_action.setChecked(checked)
        self.startup_action.blockSignals(blocked)

    def hide(self) -> None:
        self.tray_icon.hide()

