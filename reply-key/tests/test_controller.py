from __future__ import annotations

from dataclasses import dataclass

import pytest

from replykey.config import AppConfig
from replykey.controller import ControllerStatus, ReplyController
from replykey.models import ReplyDraft
from replykey.paste import PasteResult
from replykey.provider import ProviderError
from replykey.session import ConversationSession
from replykey.windows import ForegroundTarget


TARGET = ForegroundTarget(101, "Weixin.exe")


class FakeInspector:
    def __init__(self, target=TARGET) -> None:
        self.target = target

    def capture_wechat_target(self):
        return self.target


class FakeClipboard:
    def __init__(self, text: str = "在吗") -> None:
        self.text = text

    def read_text(self) -> str:
        return self.text


class FakeProvider:
    def __init__(self, result: str = "在的", error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[list[dict[str, str]]] = []

    def generate(self, messages):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return ReplyDraft(self.result)


class ClosingProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
        self.controller: ReplyController | None = None

    def generate(self, messages):
        self.calls.append(messages)
        assert self.controller is not None
        self.controller.close()
        return ReplyDraft(self.result)


class FakePasteCoordinator:
    def __init__(self, action: str = "pasted") -> None:
        self.action = action
        self.calls: list[tuple[ForegroundTarget, str]] = []

    def deliver(self, target: ForegroundTarget, draft: str) -> PasteResult:
        self.calls.append((target, draft))
        return PasteResult(self.action)  # type: ignore[arg-type]


class ImmediateExecutor:
    def submit(self, function, *args):
        function(*args)

    def shutdown(self, **kwargs):
        return None


class HeldExecutor:
    def __init__(self) -> None:
        self.pending = None

    def submit(self, function, *args):
        self.pending = (function, args)

    def run(self) -> None:
        function, args = self.pending
        function(*args)
        self.pending = None

    def shutdown(self, **kwargs):
        return None


@dataclass
class Harness:
    controller: ReplyController
    provider: FakeProvider
    paste: FakePasteCoordinator
    session: ConversationSession
    statuses: list[ControllerStatus]


def make_harness(
    *,
    target=TARGET,
    clipboard_text="在吗",
    provider: FakeProvider | None = None,
    paste: FakePasteCoordinator | None = None,
    executor=None,
    api_key="local-key",
    clock=lambda: 10.0,
) -> Harness:
    provider = provider or FakeProvider()
    paste = paste or FakePasteCoordinator()
    session = ConversationSession(clock=clock)
    statuses: list[ControllerStatus] = []
    controller = ReplyController(
        inspector=FakeInspector(target),
        clipboard=FakeClipboard(clipboard_text),
        provider_factory=lambda config, key: provider,
        config_supplier=AppConfig,
        api_key_supplier=lambda: api_key,
        session=session,
        paste_coordinator=paste,
        status_callback=statuses.append,
        executor=executor or ImmediateExecutor(),
        clock=clock,
    )
    return Harness(controller, provider, paste, session, statuses)


@pytest.mark.parametrize(
    ("target", "clipboard_text", "expected_code"),
    [(None, "在吗", "not_wechat"), (TARGET, "   ", "empty_clipboard")],
)
def test_invalid_context_never_calls_provider(target, clipboard_text, expected_code) -> None:
    harness = make_harness(target=target, clipboard_text=clipboard_text)

    harness.controller.trigger()

    assert harness.provider.calls == []
    assert harness.statuses[-1].code == expected_code


def test_paused_hotkey_never_reads_or_calls_provider() -> None:
    harness = make_harness()
    harness.controller.set_paused(True)

    harness.controller.trigger()

    assert harness.provider.calls == []
    assert harness.statuses[-1].code == "paused"


def test_missing_api_key_stops_before_provider_call() -> None:
    harness = make_harness(api_key="")

    harness.controller.trigger()

    assert harness.provider.calls == []
    assert harness.statuses[-1].code == "missing_key"


def test_only_one_request_can_be_pending() -> None:
    executor = HeldExecutor()
    harness = make_harness(executor=executor)

    harness.controller.trigger()
    harness.controller.trigger()

    assert harness.controller.busy
    assert harness.provider.calls == []
    assert harness.statuses[-1].code == "busy"

    executor.run()
    assert not harness.controller.busy
    assert len(harness.provider.calls) == 1


def test_immediate_duplicate_after_success_does_not_call_api_again() -> None:
    harness = make_harness(clock=lambda: 10.0)

    harness.controller.trigger()
    harness.controller.trigger()

    assert len(harness.provider.calls) == 1
    assert harness.statuses[-1].code == "duplicate"


def test_provider_failure_preserves_session_and_never_invokes_paste() -> None:
    provider = FakeProvider(error=ProviderError("timeout", "请求超时，请稍后重试。"))
    harness = make_harness(provider=provider)

    harness.controller.trigger()

    assert len(harness.session) == 0
    assert harness.paste.calls == []
    assert harness.statuses[-1].code == "provider_error"
    assert "超时" in harness.statuses[-1].message


def test_success_appends_interaction_and_delivers_to_original_target() -> None:
    harness = make_harness()

    harness.controller.trigger()

    assert harness.session.messages() == [
        {"role": "user", "content": "在吗"},
        {"role": "assistant", "content": "在的"},
    ]
    assert harness.paste.calls == [(TARGET, "在的")]
    assert harness.statuses[-1].code == "pasted"


def test_copy_only_result_reports_window_switch() -> None:
    harness = make_harness(paste=FakePasteCoordinator("copied"))

    harness.controller.trigger()

    assert harness.statuses[-1].code == "copied"
    assert "切换" in harness.statuses[-1].message


def test_close_during_generation_prevents_session_update_and_delivery() -> None:
    provider = ClosingProvider()
    harness = make_harness(provider=provider)
    provider.controller = harness.controller

    harness.controller.trigger()

    assert len(provider.calls) == 1
    assert len(harness.session) == 0
    assert harness.paste.calls == []
    assert harness.statuses[-1].code == "generating"
