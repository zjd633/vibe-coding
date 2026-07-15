from __future__ import annotations

import uuid

from replykey.single_instance import SingleInstanceGuard


def test_second_instance_notifies_first_and_does_not_acquire(qtbot) -> None:
    name = f"ReplyKey-test-{uuid.uuid4()}"
    first = SingleInstanceGuard(name)
    second = SingleInstanceGuard(name)

    assert first.acquire()
    with qtbot.waitSignal(first.activation_requested, timeout=2000):
        assert not second.acquire()

    assert first.is_primary
    assert not second.is_primary
    second.close()
    first.close()
