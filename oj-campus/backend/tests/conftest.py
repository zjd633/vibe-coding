import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Test modules import ``app.*`` during collection, which initializes the
# module-level FastAPI app. Isolate that import before it can open the demo DB.
PYTEST_DATABASE_URL = "sqlite:///:memory:"
os.environ["OJ_DATABASE_URL"] = PYTEST_DATABASE_URL


def pytest_sessionstart(session):
    assert os.environ.get("OJ_DATABASE_URL") == PYTEST_DATABASE_URL


@pytest.fixture()
def client(tmp_path: Path):
    from app import create_app

    application = create_app(f"sqlite:///{tmp_path / 'oj-campus.db'}")
    with TestClient(application) as test_client:
        yield test_client


def register(client, username="alice", email="alice@example.com", password="correct-horse-battery"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "display_name": "Alice",
            "password": password,
        },
    )
