from __future__ import annotations

from dataclasses import replace
import threading
from typing import Callable
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config import AppConfig
from ..hotkey import HotkeySyntaxError, parse_hotkey
from ..provider import ProviderError


class _ConnectionBridge(QObject):
    completed = Signal(bool, str)


class SettingsWindow(QDialog):
    settings_saved = Signal(object)

    def __init__(
        self,
        *,
        config_store,
        credential_store,
        startup_manager,
        connection_tester: Callable[[AppConfig, str], object],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("ReplyKey 微信回复助手 · 设置")
        self.setMinimumWidth(520)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self._config_store = config_store
        self._credential_store = credential_store
        self._startup_manager = startup_manager
        self._connection_tester = connection_tester
        self._loaded_config = self._config_store.load()
        self._connection_bridge = _ConnectionBridge(self)
        self._connection_bridge.completed.connect(self._finish_connection_test)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        title = QLabel("ReplyKey 设置")
        title.setObjectName("settingsTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        root.addWidget(title)
        subtitle = QLabel("复制微信消息后按热键，草稿只会进入输入框，必须由你手动发送。")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("settingsSubtitle")
        root.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        self.form_layout = QVBoxLayout(content)
        self.form_layout.setContentsMargins(0, 0, 8, 0)
        self.form_layout.setSpacing(8)

        self.api_base_edit = QLineEdit()
        self.api_base_edit.setAccessibleName("API Base URL")
        self.api_base_edit.setPlaceholderText("https://api.openai.com/v1")
        self.api_base_error = self._add_field("API Base URL", self.api_base_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setAccessibleName("API Key")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("保存在 Windows 凭据存储中")
        self.api_key_error = self._add_field("API Key", self.api_key_edit)
        self.show_key_checkbox = QCheckBox("显示 API Key")
        self.show_key_checkbox.toggled.connect(self._toggle_key_visibility)
        self.form_layout.addWidget(self.show_key_checkbox)

        self.model_edit = QLineEdit()
        self.model_edit.setAccessibleName("模型名称")
        self.model_edit.setPlaceholderText("gpt-5.6-luna")
        self.model_error = self._add_field("模型名称", self.model_edit)

        self.tone_combo = QComboBox()
        self.tone_combo.setAccessibleName("回复语气")
        self.tone_combo.addItems(["自动判断", "亲切自然", "简洁直接", "礼貌专业", "幽默轻松"])
        self._add_field("回复语气", self.tone_combo)

        self.length_combo = QComboBox()
        self.length_combo.setAccessibleName("回复长度")
        self.length_combo.addItems(["简短", "适中", "详细"])
        self._add_field("回复长度", self.length_combo)

        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setAccessibleName("全局热键")
        self.hotkey_edit.setPlaceholderText("Ctrl+Alt+R")
        self.hotkey_error = self._add_field("全局热键", self.hotkey_edit)

        self.startup_checkbox = QCheckBox("登录 Windows 后自动启动")
        self.startup_checkbox.setAccessibleName("开机启动")
        self.form_layout.addSpacing(4)
        self.form_layout.addWidget(self.startup_checkbox)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.connection_status = QLabel("")
        self.connection_status.setWordWrap(True)
        self.connection_status.setObjectName("connectionStatus")
        root.addWidget(self.connection_status)

        self.general_error = QLabel("")
        self.general_error.setWordWrap(True)
        self.general_error.setStyleSheet("color: #c62828;")
        root.addWidget(self.general_error)

        buttons = QHBoxLayout()
        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self._start_connection_test)
        buttons.addWidget(self.test_button)
        buttons.addStretch(1)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        self.save_button = QPushButton("保存")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._save)
        buttons.addWidget(self.save_button)
        root.addLayout(buttons)

        self.reload()

    def _add_field(self, label_text: str, widget: QWidget) -> QLabel:
        label = QLabel(label_text)
        label.setBuddy(widget)
        label.setStyleSheet("font-weight: 600; margin-top: 6px;")
        self.form_layout.addWidget(label)
        self.form_layout.addWidget(widget)
        error = QLabel("")
        error.setWordWrap(True)
        error.setStyleSheet("color: #c62828; font-size: 12px;")
        self.form_layout.addWidget(error)
        return error

    def reload(self) -> None:
        self._loaded_config = self._config_store.load()
        config = self._loaded_config
        self.api_base_edit.setText(config.api_base_url)
        self.model_edit.setText(config.model)
        self.hotkey_edit.setText(config.hotkey)
        self.tone_combo.setCurrentText(config.tone)
        self.length_combo.setCurrentText(config.reply_length)
        self.startup_checkbox.setChecked(config.launch_at_startup)
        try:
            self.api_key_edit.setText(self._credential_store.get_api_key())
        except Exception:
            self.api_key_edit.clear()
            self.api_key_error.setText("无法读取 Windows 凭据，请重新填写 API Key。")

    def _toggle_key_visibility(self, visible: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self.api_key_edit.setEchoMode(mode)

    def _validated_config(self) -> AppConfig | None:
        self.api_base_error.clear()
        self.api_key_error.clear()
        self.model_error.clear()
        self.hotkey_error.clear()
        self.general_error.clear()
        valid = True

        base_url = self.api_base_edit.text().strip().rstrip("/")
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            self.api_base_error.setText("请输入以 http:// 或 https:// 开头的完整接口地址。")
            valid = False

        model = self.model_edit.text().strip()
        if not model:
            self.model_error.setText("请输入模型名称。")
            valid = False

        try:
            hotkey = parse_hotkey(self.hotkey_edit.text()).normalized
        except HotkeySyntaxError as exc:
            self.hotkey_error.setText(str(exc))
            valid = False
            hotkey = self._loaded_config.hotkey

        if not valid:
            return None
        return replace(
            self._loaded_config,
            api_base_url=base_url,
            model=model,
            hotkey=hotkey,
            tone=self.tone_combo.currentText(),
            reply_length=self.length_combo.currentText(),
            launch_at_startup=self.startup_checkbox.isChecked(),
        )

    @Slot()
    def _save(self) -> None:
        config = self._validated_config()
        if config is None:
            return
        try:
            self._credential_store.set_api_key(self.api_key_edit.text())
            self._startup_manager.set_enabled(config.launch_at_startup)
            self._config_store.save(config)
        except Exception:
            self.general_error.setText("保存失败，请检查 Windows 凭据或启动项权限。")
            return
        self._loaded_config = config
        self.settings_saved.emit(config)
        self.accept()

    @Slot()
    def _start_connection_test(self) -> None:
        config = self._validated_config()
        if config is None:
            return
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.api_key_error.setText("请先填写 API Key，再测试连接。")
            return
        self.test_button.setEnabled(False)
        self.connection_status.setStyleSheet("color: #52606d;")
        self.connection_status.setText("正在测试连接…")

        def run() -> None:
            try:
                self._connection_tester(config, api_key)
            except ProviderError as exc:
                self._connection_bridge.completed.emit(False, exc.user_message)
            except Exception:
                self._connection_bridge.completed.emit(
                    False, "连接测试失败，请检查接口地址、模型和网络。"
                )
            else:
                self._connection_bridge.completed.emit(True, "连接成功")

        threading.Thread(target=run, name="ReplyKeyConnectionTest", daemon=True).start()

    @Slot(bool, str)
    def _finish_connection_test(self, succeeded: bool, message: str) -> None:
        self.test_button.setEnabled(True)
        color = "#1b7f46" if succeeded else "#c62828"
        self.connection_status.setStyleSheet(f"color: {color};")
        self.connection_status.setText(message)


class PrivacyDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("首次使用说明")
        self.setModal(True)
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        heading = QLabel("使用前请了解")
        heading.setStyleSheet("font-size: 19px; font-weight: 600;")
        layout.addWidget(heading)
        self.notice_label = QLabel(
            "你复制的聊天内容和最近的内存会话将发送到你配置的 API 服务，用于生成一条回复草稿。\n\n"
            "ReplyKey 不读取微信聊天数据库，不保存聊天记录，也不会自动发送微信消息。草稿进入输入框后，必须由你检查并手动发送。"
        )
        self.notice_label.setWordWrap(True)
        layout.addWidget(self.notice_label)
        buttons = QDialogButtonBox()
        accept = buttons.addButton("我已了解，继续", QDialogButtonBox.ButtonRole.AcceptRole)
        reject = buttons.addButton("退出", QDialogButtonBox.ButtonRole.RejectRole)
        accept.clicked.connect(self.accept)
        reject.clicked.connect(self.reject)
        layout.addWidget(buttons)

