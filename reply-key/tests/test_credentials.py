from __future__ import annotations

import pytest

from replykey.credentials import (
    CredentialError,
    CredentialStore,
    verify_credential_backend,
)


class FakeKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}
        self.calls: list[tuple[str, str, str | None]] = []

    def get_password(self, service: str, account: str) -> str | None:
        self.calls.append(("get", service, account))
        return self.values.get((service, account))

    def set_password(self, service: str, account: str, value: str) -> None:
        self.calls.append(("set", service, account))
        self.values[(service, account)] = value

    def delete_password(self, service: str, account: str) -> None:
        self.calls.append(("delete", service, account))
        self.values.pop((service, account), None)


def test_secret_is_isolated_under_stable_service_and_account() -> None:
    backend = FakeKeyring()
    store = CredentialStore(backend=backend)

    store.set_api_key("sk-local-test")

    assert store.get_api_key() == "sk-local-test"
    assert ("ReplyKey", "chat-completions-api-key") in backend.values


def test_blank_secret_deletes_existing_value() -> None:
    backend = FakeKeyring()
    store = CredentialStore(backend=backend)
    store.set_api_key("secret")

    store.set_api_key("   ")

    assert store.get_api_key() == ""
    assert any(call[0] == "delete" for call in backend.calls)


def test_backend_errors_are_mapped_without_exposing_secret() -> None:
    class BrokenKeyring(FakeKeyring):
        def set_password(self, service: str, account: str, value: str) -> None:
            raise RuntimeError(f"backend failed for {value}")

    store = CredentialStore(backend=BrokenKeyring())

    with pytest.raises(CredentialError) as caught:
        store.set_api_key("top-secret")

    assert "top-secret" not in str(caught.value)


def test_packaged_credential_probe_round_trips_and_removes_temporary_value() -> None:
    backend = FakeKeyring()

    verify_credential_backend(
        backend=backend,
        service="ReplyKey.PackageSelfTest.unit",
        token="temporary-probe",
    )

    assert backend.values == {}
    assert [call[0] for call in backend.calls] == ["set", "get", "delete"]
