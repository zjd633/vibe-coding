from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import openai
from openai import OpenAI

from .models import ReplyDraft


class ProviderError(RuntimeError):
    def __init__(self, kind: str, user_message: str, *, retryable: bool = True) -> None:
        super().__init__(user_message)
        self.kind = kind
        self.user_message = user_message
        self.retryable = retryable


class ChatCompletionProvider:
    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        client: Any | None = None,
    ) -> None:
        self.api_base_url = api_base_url.strip().rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = float(timeout_seconds)
        self._client = client or OpenAI(
            api_key=api_key,
            base_url=self.api_base_url,
            timeout=self.timeout_seconds,
            max_retries=0,
        )

    def generate(self, messages: Sequence[dict[str, str]]) -> ReplyDraft:
        request_messages = [dict(message) for message in messages]
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=request_messages,
            )
        except openai.APITimeoutError as exc:
            raise ProviderError("timeout", "请求超时，请稍后重试。") from exc
        except openai.AuthenticationError as exc:
            raise ProviderError(
                "authentication",
                "API Key 无效或没有访问该模型的权限，请检查设置。",
                retryable=False,
            ) from exc
        except openai.RateLimitError as exc:
            raise ProviderError(
                "rate_limit", "请求过于频繁或账户额度不足，请稍后重试。"
            ) from exc
        except openai.APIConnectionError as exc:
            raise ProviderError(
                "connection", "无法连接到 API 服务，请检查接口地址和网络。"
            ) from exc
        except openai.APIStatusError as exc:
            status = getattr(exc, "status_code", None)
            suffix = f"（HTTP {status}）" if status else ""
            raise ProviderError(
                "api_status", f"API 服务返回错误{suffix}，请稍后重试。"
            ) from exc
        except openai.OpenAIError as exc:
            raise ProviderError(
                "request", "API 请求失败，请检查服务兼容性后重试。"
            ) from exc
        except Exception as exc:
            raise ProviderError(
                "request", "API 请求未能完成，请检查设置后重试。"
            ) from exc

        return self._extract_draft(response)

    def test_connection(self) -> ReplyDraft:
        return self.generate(
            [{"role": "user", "content": "请只回复四个字：连接成功"}]
        )

    @staticmethod
    def _extract_draft(response: Any) -> ReplyDraft:
        try:
            choices = response.choices
            if not choices:
                raise ValueError("missing choices")
            content = choices[0].message.content
        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(
                "invalid_response", "API 服务没有返回有效回复，请检查兼容性后重试。"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise ProviderError(
                "invalid_response", "API 服务没有返回有效回复，请检查兼容性后重试。"
            )
        return ReplyDraft(content.strip())
