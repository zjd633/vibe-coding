from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    status_code: int
    code: str
    message: str
    field_errors: dict[str, str] | None = None
