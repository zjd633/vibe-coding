from __future__ import annotations

from replykey.session import ConversationSession


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_keeps_only_eight_successful_interactions() -> None:
    session = ConversationSession(max_interactions=8)

    for index in range(10):
        session.append_success(f"消息{index}", f"回复{index}")

    messages = session.messages()
    assert len(messages) == 16
    assert messages[0] == {"role": "user", "content": "消息2"}
    assert messages[-1] == {"role": "assistant", "content": "回复9"}


def test_expires_after_thirty_minutes_without_activity() -> None:
    clock = FakeClock()
    session = ConversationSession(timeout_seconds=30 * 60, clock=clock)
    session.append_success("在吗", "在的")

    clock.advance(30 * 60)

    assert session.messages() == []


def test_touch_keeps_active_session_and_manual_clear_removes_it() -> None:
    clock = FakeClock()
    session = ConversationSession(timeout_seconds=30 * 60, clock=clock)
    session.append_success("A", "B")
    clock.advance(20 * 60)
    session.touch()
    clock.advance(20 * 60)

    assert len(session.messages()) == 2
    session.clear()
    assert session.messages() == []


def test_failed_work_is_not_added_implicitly() -> None:
    session = ConversationSession()

    _ = session.messages()

    assert len(session) == 0

