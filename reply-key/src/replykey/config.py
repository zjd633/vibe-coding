from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_HOTKEY = "Ctrl+Alt+R"


@dataclass(frozen=True, slots=True)
class AppConfig:
    api_base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    hotkey: str = DEFAULT_HOTKEY
    tone: str = "自动判断"
    reply_length: str = "适中"
    session_timeout_minutes: int = 30
    request_timeout_seconds: float = 30.0
    launch_at_startup: bool = False
    privacy_notice_accepted: bool = False

    def __post_init__(self) -> None:
        base_url = str(self.api_base_url or "").strip().rstrip("/") or DEFAULT_BASE_URL
        model = str(self.model or "").strip() or DEFAULT_MODEL
        hotkey = str(self.hotkey or "").strip() or DEFAULT_HOTKEY
        tone = str(self.tone or "").strip() or "自动判断"
        reply_length = str(self.reply_length or "").strip() or "适中"
        timeout_minutes = _positive_int(self.session_timeout_minutes, 30)
        request_timeout = _positive_float(self.request_timeout_seconds, 30.0)

        object.__setattr__(self, "api_base_url", base_url)
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "hotkey", hotkey)
        object.__setattr__(self, "tone", tone)
        object.__setattr__(self, "reply_length", reply_length)
        object.__setattr__(self, "session_timeout_minutes", timeout_minutes)
        object.__setattr__(self, "request_timeout_seconds", request_timeout)
        object.__setattr__(self, "launch_at_startup", bool(self.launch_at_startup))
        object.__setattr__(self, "privacy_notice_accepted", bool(self.privacy_notice_accepted))


def _positive_int(value: object, fallback: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return fallback
    return parsed if parsed > 0 else fallback


def _positive_float(value: object, fallback: float) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return fallback
    return parsed if parsed > 0 else fallback


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    root = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return root / "ReplyKey" / "config.json"


class ConfigStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_config_path()

    def load(self) -> AppConfig:
        try:
            data: Any = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return AppConfig()
            allowed = {field.name for field in fields(AppConfig)}
            values = {key: value for key, value in data.items() if key in allowed}
            return AppConfig(**values)
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n"
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, self.path)

