from __future__ import annotations

from replykey.logging_setup import setup_logging


def test_privacy_logger_drops_keys_chat_text_and_generated_content(tmp_path) -> None:
    logger = setup_logging(tmp_path)

    logger.event(
        "generation_failed",
        code="timeout",
        http_status=504,
        api_key="sk-top-secret",
        source_text="这是复制的聊天原文",
        draft="这是生成的回复内容",
    )
    logger.close()

    text = (tmp_path / "replykey.log").read_text(encoding="utf-8")
    assert "generation_failed" in text
    assert "timeout" in text
    assert "504" in text
    assert "sk-top-secret" not in text
    assert "这是复制的聊天原文" not in text
    assert "这是生成的回复内容" not in text
