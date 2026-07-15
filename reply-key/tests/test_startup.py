from __future__ import annotations

from pathlib import Path

from replykey.startup import StartupManager


class FakeRegistry:
    def __init__(self) -> None:
        self.value: str | None = None

    def read(self, name: str) -> str | None:
        return self.value

    def write(self, name: str, value: str) -> None:
        self.value = value

    def delete(self, name: str) -> None:
        self.value = None


def test_enable_uses_current_user_run_entry_without_admin() -> None:
    registry = FakeRegistry()
    manager = StartupManager(registry=registry)
    executable = Path(r"D:\Portable Apps\ReplyKey\ReplyKey.exe")

    manager.enable(executable)

    assert registry.value == f'"{executable}" --background'
    assert manager.is_enabled(executable)


def test_reenable_after_move_refreshes_path_and_disable_removes_entry() -> None:
    registry = FakeRegistry()
    manager = StartupManager(registry=registry)
    old = Path(r"D:\Old\ReplyKey.exe")
    new = Path(r"E:\New\ReplyKey.exe")

    manager.enable(old)
    assert not manager.is_enabled(new)
    manager.enable(new)
    assert manager.is_enabled(new)
    assert str(old) not in (registry.value or "")

    manager.disable()
    assert registry.value is None
