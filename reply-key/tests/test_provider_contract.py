from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time

import pytest

from replykey.provider import ChatCompletionProvider, ProviderError


class ContractHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.requests.append(body)  # type: ignore[attr-defined]
        mode = self.server.mode  # type: ignore[attr-defined]
        if mode == "timeout":
            time.sleep(0.2)
        if mode == "401":
            self._json(401, {"error": {"message": "bad key", "type": "auth_error"}})
        elif mode == "429":
            self._json(429, {"error": {"message": "slow down", "type": "rate_limit"}})
        elif mode == "empty":
            self._json(200, completion_payload(""))
        elif mode == "malformed":
            self._json(200, {"id": "chatcmpl-test", "object": "chat.completion", "choices": []})
        else:
            self._json(200, completion_payload("可以，晚点联系。"))

    def _json(self, status: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format: str, *args) -> None:
        return


def completion_payload(content: str) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "local-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }


@contextmanager
def contract_server(mode: str):
    server = ThreadingHTTPServer(("127.0.0.1", 0), ContractHandler)
    server.mode = mode
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def make_provider(server, timeout: float = 1.0) -> ChatCompletionProvider:
    return ChatCompletionProvider(
        api_base_url=f"http://127.0.0.1:{server.server_port}/v1",
        api_key="local-test-key",
        model="local-model",
        timeout_seconds=timeout,
    )


def test_local_contract_success_has_only_generic_body_fields() -> None:
    with contract_server("success") as server:
        draft = make_provider(server).generate([{"role": "user", "content": "你好"}])

    assert draft.text == "可以，晚点联系。"
    assert set(server.requests[0]) == {"model", "messages"}


@pytest.mark.parametrize(
    ("mode", "kind"),
    [("401", "authentication"), ("429", "rate_limit"), ("empty", "invalid_response"), ("malformed", "invalid_response")],
)
def test_local_contract_maps_failures(mode: str, kind: str) -> None:
    with contract_server(mode) as server:
        with pytest.raises(ProviderError) as caught:
            make_provider(server).generate([{"role": "user", "content": "你好"}])

    assert caught.value.kind == kind


def test_local_contract_timeout() -> None:
    with contract_server("timeout") as server:
        with pytest.raises(ProviderError) as caught:
            make_provider(server, timeout=0.05).generate(
                [{"role": "user", "content": "你好"}]
            )

    assert caught.value.kind == "timeout"
