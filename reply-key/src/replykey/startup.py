from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol
import winreg


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
ENTRY_NAME = "ReplyKey"


class StartupRegistry(Protocol):
    def read(self, name: str) -> str | None: ...

    def write(self, name: str, value: str) -> None: ...

    def delete(self, name: str) -> None: ...


class StartupManager:
    def __init__(self, registry: StartupRegistry | None = None) -> None:
        self._registry = registry or CurrentUserRunRegistry()

    @staticmethod
    def command_for(executable: Path | str) -> str:
        return f'"{Path(executable)}" --background'

    def enable(self, executable: Path | str | None = None) -> None:
        path = Path(executable) if executable is not None else current_executable_path()
        self._registry.write(ENTRY_NAME, self.command_for(path))

    def disable(self) -> None:
        self._registry.delete(ENTRY_NAME)

    def is_enabled(self, executable: Path | str | None = None) -> bool:
        path = Path(executable) if executable is not None else current_executable_path()
        return self._registry.read(ENTRY_NAME) == self.command_for(path)

    def set_enabled(self, enabled: bool, executable: Path | str | None = None) -> None:
        if enabled:
            self.enable(executable)
        else:
            self.disable()


def current_executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


class CurrentUserRunRegistry:
    def read(self, name: str) -> str | None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value)
        except FileNotFoundError:
            return None

    def write(self, name: str, value: str) -> None:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    def delete(self, name: str) -> None:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            return
