from pathlib import Path


def test_default_database_is_kept_inside_backend_data_directory():
    from app.database import default_database_url

    database_url = default_database_url()

    assert Path(database_url.removeprefix("sqlite:///")) == Path(__file__).parents[1] / "data" / "oj-campus.db"


def test_in_memory_application_reuses_its_single_engine():
    from fastapi.testclient import TestClient

    from app import create_app

    application = create_app("sqlite:///:memory:")
    with TestClient(application) as memory_client:
        response = memory_client.post(
            "/api/auth/register",
            json={
                "username": "memory_user",
                "email": "memory@example.com",
                "display_name": "Memory User",
                "password": "correct-horse-battery",
            },
        )

    assert response.status_code == 201
