from __future__ import annotations

from types import SimpleNamespace

import httpx
import openai
import pytest

from replykey.provider import ChatCompletionProvider, ProviderError


MESSAGES = [
    {"role": "system", "content": "只回复草稿"},
    {"role": "user", "content": "在吗"},
]


class FakeCompletions:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def completion(content: object):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def provider_for(completions: FakeCompletions) -> ChatCompletionProvider:
    return ChatCompletionProvider(
        api_base_url="https://example.test/v1",
        api_key="not-a-real-key",
        model="compatible-model",
        timeout_seconds=3,
        client=FakeClient(completions),
    )


def test_generate_uses_only_model_and_messages_and_trims_result() -> None:
    completions = FakeCompletions(completion("  好呀，晚点见。  "))
    provider = provider_for(completions)

    draft = provider.generate(MESSAGES)

    assert draft.text == "好呀，晚点见。"
    assert completions.calls == [{"model": "compatible-model", "messages": MESSAGES}]


@pytest.mark.parametrize(
    ("error", "kind", "message_part"),
    [
        (
            openai.APITimeoutError(request=httpx.Request("POST", "https://example.test")),
            "timeout",
            "超时",
        ),
        (
            openai.AuthenticationError(
                "bad key",
                response=httpx.Response(
                    401, request=httpx.Request("POST", "https://example.test")
                ),
                body=None,
            ),
            "authentication",
            "API Key",
        ),
        (
            openai.RateLimitError(
                "slow down",
                response=httpx.Response(
                    429, request=httpx.Request("POST", "https://example.test")
                ),
                body=None,
            ),
            "rate_limit",
            "频繁",
        ),
        (
            openai.APIConnectionError(
                request=httpx.Request("POST", "https://example.test")
            ),
            "connection",
            "连接",
        ),
    ],
)
def test_known_sdk_errors_map_to_retryable_chinese_messages(
    error: Exception, kind: str, message_part: str
) -> None:
    provider = provider_for(FakeCompletions(error=error))

    with pytest.raises(ProviderError) as caught:
        provider.generate(MESSAGES)

    assert caught.value.kind == kind
    assert message_part in caught.value.user_message
    assert str(error) not in caught.value.user_message


@pytest.mark.parametrize("response", [completion(""), completion(None), completion([])])
def test_empty_or_incompatible_content_is_rejected(response) -> None:
    provider = provider_for(FakeCompletions(response))

    with pytest.raises(ProviderError) as caught:
        provider.generate(MESSAGES)

    assert caught.value.kind == "invalid_response"
    assert "有效回复" in caught.value.user_message


def test_missing_choices_is_an_incompatible_response() -> None:
    provider = provider_for(FakeCompletions(SimpleNamespace(choices=[])))

    with pytest.raises(ProviderError) as caught:
        provider.generate(MESSAGES)

    assert caught.value.kind == "invalid_response"


def test_connection_test_is_a_real_minimal_chat_request() -> None:
    completions = FakeCompletions(completion("连接成功"))
    provider = provider_for(completions)

    draft = provider.test_connection()

    assert draft.text == "连接成功"
    assert completions.calls[0]["model"] == "compatible-model"
    assert list(completions.calls[0]) == ["model", "messages"]
    assert len(completions.calls[0]["messages"]) == 1

