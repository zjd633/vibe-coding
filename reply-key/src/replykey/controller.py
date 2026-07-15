from __future__ import annotations

from dataclasses import dataclass
import hashlib
import threading
import time
from typing import Any, Callable, Literal, Protocol

from .background import DaemonTaskExecutor
from .clipboard import ClipboardError
from .config import AppConfig
from .paste import PasteError, PasteResult
from .prompting import build_chat_messages
from .provider import ProviderError
from .session import ConversationSession
from .windows import ForegroundTarget


class Provider(Protocol):
    def generate(self, messages: list[dict[str, str]]): ...


@dataclass(frozen=True, slots=True)
class ControllerStatus:
    code: str
    message: str
    level: Literal["info", "success", "warning", "error"] = "info"


class ReplyController:
    def __init__(
        self,
        *,
        inspector: Any,
        clipboard: Any,
        provider_factory: Callable[[AppConfig, str], Provider],
        config_supplier: Callable[[], AppConfig],
        api_key_supplier: Callable[[], str],
        session: ConversationSession,
        paste_coordinator: Any,
        status_callback: Callable[[ControllerStatus], None],
        executor: Any | None = None,
        clock: Callable[[], float] = time.monotonic,
        duplicate_window_seconds: float = 2.0,
    ) -> None:
        self._inspector = inspector
        self._clipboard = clipboard
        self._provider_factory = provider_factory
        self._config_supplier = config_supplier
        self._api_key_supplier = api_key_supplier
        self._session = session
        self._paste_coordinator = paste_coordinator
        self._status_callback = status_callback
        self._executor = executor or DaemonTaskExecutor(
            thread_name_prefix="ReplyKeyGenerate"
        )
        self._clock = clock
        self._duplicate_window_seconds = duplicate_window_seconds
        self._state_lock = threading.Lock()
        self._delivery_lock = threading.Lock()
        self._busy = False
        self._paused = False
        self._closed = False
        self._last_success_signature: tuple[int, bytes] | None = None
        self._last_success_time = float("-inf")

    @property
    def busy(self) -> bool:
        with self._state_lock:
            return self._busy

    @property
    def paused(self) -> bool:
        with self._state_lock:
            return self._paused

    def set_paused(self, paused: bool) -> None:
        with self._state_lock:
            self._paused = bool(paused)

    def clear_session(self) -> None:
        self._session.clear()
        self._emit("session_cleared", "会话上下文已清空。", "success")

    def trigger(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            paused = self._paused
            busy = self._busy
        if paused:
            self._emit("paused", "热键已暂停。", "warning")
            return
        if busy:
            self._emit("busy", "正在生成，请稍候。", "info")
            return

        target: ForegroundTarget | None = self._inspector.capture_wechat_target()
        if target is None:
            self._emit(
                "not_wechat", "请先在桌面微信中复制对方消息，再按热键。", "warning"
            )
            return
        try:
            copied_text = self._clipboard.read_text().strip()
        except ClipboardError as exc:
            self._emit("clipboard_error", str(exc), "error")
            return
        except Exception:
            self._emit("clipboard_error", "无法读取剪贴板，请稍后重试。", "error")
            return
        if not copied_text:
            self._emit("empty_clipboard", "剪贴板中没有可回复的文字。", "warning")
            return

        try:
            config = self._config_supplier()
            api_key = self._api_key_supplier().strip()
        except Exception:
            self._emit("settings_error", "无法读取设置，请打开设置页检查。", "error")
            return
        if not api_key:
            self._emit("missing_key", "请先在设置中填写 API Key。", "warning")
            return

        signature = self._signature(target, copied_text)
        now = self._clock()
        rejected_code: str | None = None
        with self._state_lock:
            if self._busy:
                rejected_code = "busy"
            elif (
                signature == self._last_success_signature
                and now - self._last_success_time < self._duplicate_window_seconds
            ):
                rejected_code = "duplicate"
            else:
                self._busy = True
        if rejected_code == "busy":
            self._emit("busy", "正在生成，请稍候。", "info")
            return
        if rejected_code == "duplicate":
            self._emit("duplicate", "已处理相同内容，请勿重复触发。", "info")
            return

        self._session.touch()
        history = self._session.messages()
        self._emit("generating", "正在生成回复草稿…", "info")
        try:
            self._executor.submit(
                self._generate_and_deliver,
                target,
                copied_text,
                history,
                config,
                api_key,
                signature,
            )
        except Exception:
            with self._state_lock:
                self._busy = False
            self._emit("internal_error", "无法启动生成任务，请重试。", "error")

    def close(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            self._closed = True
            self._paused = True
        # If delivery already began, let that short clipboard transaction finish.
        # Otherwise this barrier makes a completed request observe the closed flag.
        with self._delivery_lock:
            pass
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            self._executor.shutdown(wait=False)

    def _generate_and_deliver(
        self,
        target: ForegroundTarget,
        copied_text: str,
        history: list[dict[str, str]],
        config: AppConfig,
        api_key: str,
        signature: tuple[int, bytes],
    ) -> None:
        generated = False
        try:
            with self._state_lock:
                if self._closed:
                    return
            messages = build_chat_messages(
                copied_text,
                history,
                config.tone,
                config.reply_length,
            )
            provider = self._provider_factory(config, api_key)
            draft = provider.generate(messages)
            with self._delivery_lock:
                with self._state_lock:
                    if self._closed:
                        return
                self._session.append_success(copied_text, draft.text)
                generated = True
                result: PasteResult = self._paste_coordinator.deliver(
                    target, draft.text
                )
            if result.action == "pasted":
                self._emit(
                    "pasted", "草稿已粘贴到微信输入框，请确认后手动发送。", "success"
                )
            else:
                self._emit(
                    "copied",
                    "窗口已切换，草稿仅复制到剪贴板，未自动粘贴。",
                    "warning",
                )
        except ProviderError as exc:
            self._emit("provider_error", exc.user_message, "error")
        except (PasteError, ClipboardError) as exc:
            self._emit("paste_error", str(exc), "error")
        except Exception:
            self._emit("unexpected_error", "生成失败，请检查设置后重试。", "error")
        finally:
            with self._state_lock:
                if generated:
                    self._last_success_signature = signature
                    self._last_success_time = self._clock()
                self._busy = False

    @staticmethod
    def _signature(target: ForegroundTarget, copied_text: str) -> tuple[int, bytes]:
        digest = hashlib.sha256(copied_text.encode("utf-8", errors="replace")).digest()
        return target.hwnd, digest

    def _emit(
        self,
        code: str,
        message: str,
        level: Literal["info", "success", "warning", "error"] = "info",
    ) -> None:
        with self._state_lock:
            if self._closed:
                return
        try:
            self._status_callback(ControllerStatus(code, message, level))
        except Exception:
            return
