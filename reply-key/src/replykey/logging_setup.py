from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from typing import Any


_ALLOWED_FIELDS = {"code", "status", "http_status", "duration_ms", "version"}
_EVENT_PATTERN = re.compile(r"^[a-z0-9_.-]{1,64}$")


def default_log_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    root = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return root / "ReplyKey" / "logs"


class PrivacyLogger:
    def __init__(self, logger: logging.Logger, handler: logging.Handler) -> None:
        self._logger = logger
        self._handler = handler

    def event(self, event: str, **metadata: Any) -> None:
        safe_event = event if _EVENT_PATTERN.fullmatch(event) else "invalid_event"
        payload: dict[str, Any] = {"event": safe_event}
        for key in _ALLOWED_FIELDS:
            if key not in metadata:
                continue
            value = metadata[key]
            if isinstance(value, (int, float, bool)) or value is None:
                payload[key] = value
            elif isinstance(value, str):
                payload[key] = value.replace("\r", " ").replace("\n", " ")[:80]
        self._logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def close(self) -> None:
        self._handler.flush()
        self._logger.removeHandler(self._handler)
        self._handler.close()


class NullPrivacyLogger:
    def event(self, event: str, **metadata: Any) -> None:
        return

    def close(self) -> None:
        return


def setup_logging(log_dir: Path | str | None = None) -> PrivacyLogger:
    directory = Path(log_dir) if log_dir is not None else default_log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "replykey.log"
    logger = logging.getLogger(f"replykey.{path.resolve()}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for existing in list(logger.handlers):
        logger.removeHandler(existing)
        existing.close()
    handler = RotatingFileHandler(
        path, maxBytes=512 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return PrivacyLogger(logger, handler)
