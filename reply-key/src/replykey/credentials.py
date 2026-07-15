from __future__ import annotations

from typing import Protocol
import uuid

import keyring


SERVICE_NAME = "ReplyKey"
ACCOUNT_NAME = "chat-completions-api-key"


class KeyringBackend(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...

    def set_password(self, service: str, username: str, password: str) -> None: ...

    def delete_password(self, service: str, username: str) -> None: ...


class CredentialError(RuntimeError):
    """A secret-store operation failed without exposing secret material."""


class CredentialStore:
    def __init__(self, backend: KeyringBackend | None = None) -> None:
        self._backend = backend or keyring

    def get_api_key(self) -> str:
        try:
            return self._backend.get_password(SERVICE_NAME, ACCOUNT_NAME) or ""
        except Exception as exc:
            raise CredentialError("无法访问 Windows 凭据存储。") from exc

    def set_api_key(self, api_key: str) -> None:
        normalized = api_key.strip()
        try:
            if normalized:
                self._backend.set_password(SERVICE_NAME, ACCOUNT_NAME, normalized)
                return
            if self._backend.get_password(SERVICE_NAME, ACCOUNT_NAME) is not None:
                self._backend.delete_password(SERVICE_NAME, ACCOUNT_NAME)
        except Exception as exc:
            raise CredentialError("无法保存 Windows 凭据。") from exc


def verify_credential_backend(
    *,
    backend: KeyringBackend | None = None,
    service: str | None = None,
    token: str | None = None,
) -> None:
    """Round-trip a disposable value for packaged-build acceptance checks."""

    selected_backend = backend or keyring
    unique_id = uuid.uuid4().hex
    probe_service = service or f"{SERVICE_NAME}.PackageSelfTest.{unique_id}"
    probe_token = token or f"temporary-{unique_id}"
    probe_account = "temporary-probe"
    written = False
    try:
        selected_backend.set_password(probe_service, probe_account, probe_token)
        written = True
        if selected_backend.get_password(probe_service, probe_account) != probe_token:
            raise CredentialError("Windows 凭据存储自检未能读回临时值。")
    finally:
        if written:
            selected_backend.delete_password(probe_service, probe_account)
