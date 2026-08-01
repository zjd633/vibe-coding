from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading
from pathlib import Path

import pytest

from conftest import register


def _create_legacy_task2_database(path: Path, submissions: list[tuple] | None = None) -> None:
    submissions = submissions or [(1, 1, 1, "int main(){}", "cpp17", "queued", "2020-01-01")]
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE users (id INTEGER PRIMARY KEY);
            CREATE TABLE problems (id INTEGER PRIMARY KEY);
            INSERT INTO users VALUES (1);
            INSERT INTO users VALUES (2);
            INSERT INTO problems VALUES (1);
            INSERT INTO problems VALUES (2);
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY, user_id INTEGER, problem_id INTEGER, source TEXT,
                language TEXT, status TEXT, created_at TEXT
            );
            CREATE TABLE user_activities (
                id INTEGER PRIMARY KEY, user_id INTEGER, problem_id INTEGER,
                status TEXT, updated_at TEXT
            );
            INSERT INTO user_activities VALUES (1, 2, 2, 'attempted', '2020-01-01');
            """
        )
        conn.executemany("INSERT INTO submissions VALUES (?,?,?,?,?,?,?)", submissions)


def test_public_submission_never_exposes_private_verdict_fields(client):
    from test_submissions import make_problem
    problem, admin = make_problem(client)
    admin.post("/api/auth/logout")
    register(client)
    created = client.post("/api/submissions", json={"problem_id": problem["id"], "language": "cpp17", "source": "int main(){}"}).json()
    from app.database import session_scope
    from app.models import Problem, Submission
    with session_scope(client.app.state.database_url) as db:
        sub = db.get(Submission, created["id"])
        sub.status, sub.failed_case, sub.details = "RE", 1, "secret stderr"
        db.commit()
    public = client.get("/api/submissions/public").json()["items"][0]
    assert not ({"source", "details", "failed_case"} & public.keys())
    mine = client.get(f"/api/submissions/{created['id']}").json()
    assert mine["details"] == "Runtime error"


def test_migrate_legacy_sqlite_creates_backup_and_legal_status(tmp_path):
    from app.database import migrate_sqlite
    path = tmp_path / "legacy.db"
    _create_legacy_task2_database(
        path,
        [(1, 1, 1, "int main(){}", "python", "queued", "2020-01-01")],
    )
    assert migrate_sqlite(f"sqlite:///{path.as_posix()}")
    assert list(tmp_path.glob("legacy.db.pre-task2-*.bak"))
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT language,status,problem_revision FROM submissions").fetchone()
    assert row == ("cpp17", "SE", 1)
    assert not migrate_sqlite(f"sqlite:///{path.as_posix()}")


def test_migration_preserves_orm_foreign_keys_indexes_and_delete_behavior(tmp_path):
    from app.database import migrate_sqlite

    path = tmp_path / "constraints.db"
    _create_legacy_task2_database(path)

    assert migrate_sqlite(f"sqlite:///{path.as_posix()}")

    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        submission_fks = {
            (row[3], row[2], row[4], row[6])
            for row in conn.execute("PRAGMA foreign_key_list(submissions)")
        }
        activity_fks = {
            (row[3], row[2], row[4], row[6])
            for row in conn.execute("PRAGMA foreign_key_list(user_activities)")
        }
        submission_indexes = {row[1] for row in conn.execute("PRAGMA index_list(submissions)")}
        activity_indexes = {row[1] for row in conn.execute("PRAGMA index_list(user_activities)")}

        assert submission_fks == {
            ("user_id", "users", "id", "RESTRICT"),
            ("problem_id", "problems", "id", "RESTRICT"),
        }
        assert activity_fks == {
            ("user_id", "users", "id", "CASCADE"),
            ("problem_id", "problems", "id", "CASCADE"),
        }
        assert {"ix_submissions_status", "ix_submissions_judging_started_at"} <= submission_indexes
        assert "ix_user_activities_activity_date" in activity_indexes
        unique_activity_indexes = {
            tuple(column[2] for column in conn.execute(f"PRAGMA index_info({row[1]})"))
            for row in conn.execute("PRAGMA index_list(user_activities)")
            if row[2]
        }
        assert ("user_id", "activity_date") in unique_activity_indexes
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        try:
            conn.execute("DELETE FROM users WHERE id=1")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("submission user RESTRICT foreign key was not enforced")
        conn.rollback()
        conn.execute("DELETE FROM users WHERE id=2")
        assert conn.execute("SELECT COUNT(*) FROM user_activities WHERE user_id=2").fetchone()[0] == 0


def test_two_concurrent_migrations_create_one_backup_and_valid_schema(tmp_path):
    from app.database import migrate_sqlite

    path = tmp_path / "concurrent.db"
    _create_legacy_task2_database(path)
    database_url = f"sqlite:///{path.as_posix()}"
    barrier = threading.Barrier(2)

    def migrate_together() -> bool:
        barrier.wait()
        return migrate_sqlite(database_url)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: migrate_together(), range(2)))

    assert sorted(results) == [False, True]
    backups = list(tmp_path.glob("concurrent.db.pre-task2-*.bak"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert backup.execute("SELECT language,status FROM submissions WHERE id=1").fetchone() == ("cpp17", "queued")
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] >= 3
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert {row[1] for row in conn.execute("PRAGMA index_list(submissions)")} >= {
            "ix_submissions_status",
            "ix_submissions_judging_started_at",
        }


def test_migration_rechecks_current_version_shape_for_activity_unique_index(tmp_path):
    from app.database import migrate_sqlite

    path = tmp_path / "shape.db"
    _create_legacy_task2_database(path)
    database_url = f"sqlite:///{path.as_posix()}"
    assert migrate_sqlite(database_url)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript(
            """
            ALTER TABLE user_activities RENAME TO user_activities_with_unique;
            CREATE TABLE user_activities (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                problem_id INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
                status TEXT NOT NULL,
                activity_date DATE NOT NULL,
                updated_at DATETIME NOT NULL
            );
            INSERT INTO user_activities SELECT * FROM user_activities_with_unique;
            DROP TABLE user_activities_with_unique;
            CREATE INDEX ix_user_activities_activity_date ON user_activities(activity_date);
            PRAGMA user_version=3;
            """
        )

    assert migrate_sqlite(database_url)
    with sqlite3.connect(path) as conn:
        unique_indexes = {
            tuple(column[2] for column in conn.execute(f"PRAGMA index_info({row[1]})"))
            for row in conn.execute("PRAGMA index_list(user_activities)")
            if row[2]
        }
    assert ("user_id", "activity_date") in unique_indexes


def test_migration_rechecks_current_version_shape_for_submission_checks(tmp_path):
    from app.database import migrate_sqlite

    path = tmp_path / "missing-checks.db"
    _create_legacy_task2_database(path)
    database_url = f"sqlite:///{path.as_posix()}"
    assert migrate_sqlite(database_url)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript(
            """
            ALTER TABLE submissions RENAME TO submissions_with_checks;
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                problem_id INTEGER NOT NULL REFERENCES problems(id) ON DELETE RESTRICT,
                source TEXT NOT NULL,
                language TEXT NOT NULL,
                status TEXT NOT NULL,
                problem_revision INTEGER NOT NULL DEFAULT 1,
                runtime_ms INTEGER,
                failed_case INTEGER,
                details TEXT,
                judging_started_at DATETIME,
                created_at DATETIME NOT NULL
            );
            INSERT INTO submissions SELECT * FROM submissions_with_checks;
            DROP TABLE submissions_with_checks;
            CREATE INDEX ix_submissions_status ON submissions(status);
            CREATE INDEX ix_submissions_judging_started_at ON submissions(judging_started_at);
            PRAGMA user_version=3;
            """
        )

    assert migrate_sqlite(database_url)
    with sqlite3.connect(path) as conn:
        table_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='submissions'"
        ).fetchone()[0]
        assert "submission_language" in table_sql
        assert "submission_status" in table_sql
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE submissions SET language='python' WHERE id=1")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE submissions SET status='UNKNOWN' WHERE id=1")


def test_legacy_mapping_distinguishes_queued_from_invalid_values(tmp_path):
    from app.database import migrate_sqlite

    path = tmp_path / "mapping.db"
    _create_legacy_task2_database(
        path,
        [
            (1, 1, 1, "one", "cpp17", "queued", "2020-01-01"),
            (2, 1, 1, "two", "python", "queued", "2020-01-01"),
            (3, 1, 1, "three", "cpp17", "mystery", "2020-01-01"),
        ],
    )

    assert migrate_sqlite(f"sqlite:///{path.as_posix()}")
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT id, language, status FROM submissions ORDER BY id").fetchall()

    assert rows == [(1, "cpp17", "PENDING"), (2, "cpp17", "SE"), (3, "cpp17", "SE")]


def test_problem_solved_filter_uses_current_revision_ac(client):
    from test_submissions import make_problem
    problem, admin = make_problem(client)
    admin.post("/api/auth/logout")
    register(client)
    created = client.post("/api/submissions", json={"problem_id": problem["id"], "language": "cpp17", "source": "int main(){}"}).json()
    from app.database import session_scope
    from app.models import Problem, Submission
    with session_scope(client.app.state.database_url) as db:
        db.get(Submission, created["id"]).status = "AC"
        db.commit()
    assert client.get("/api/problems", params={"solved": True}).json()["total"] == 1
    with session_scope(client.app.state.database_url) as db:
        db.get(Problem, problem["id"]).revision += 1
        db.commit()
    assert client.get("/api/problems", params={"solved": True}).json()["total"] == 0
