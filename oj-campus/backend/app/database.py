from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import secrets
import sqlite3
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///") or database_url.endswith(":memory:"):
        return None
    return Path(database_url.removeprefix("sqlite:///"))


TASK2_SCHEMA_VERSION = 3
SUBMISSION_COLUMNS = {
    "problem_revision", "runtime_ms", "failed_case", "details", "judging_started_at",
}
SUBMISSION_FOREIGN_KEYS = {
    ("user_id", "users", "id", "RESTRICT"),
    ("problem_id", "problems", "id", "RESTRICT"),
}
ACTIVITY_FOREIGN_KEYS = {
    ("user_id", "users", "id", "CASCADE"),
    ("problem_id", "problems", "id", "CASCADE"),
}


def _foreign_keys(conn: sqlite3.Connection, table: str) -> set[tuple[str, str, str, str]]:
    return {(row[3], row[2], row[4], row[6]) for row in conn.execute(f"PRAGMA foreign_key_list({table})")}


def _indexes(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA index_list({table})")}


def _has_unique_index(conn: sqlite3.Connection, table: str, columns: tuple[str, ...]) -> bool:
    for index in conn.execute(f"PRAGMA index_list({table})"):
        if index[2] and tuple(row[2] for row in conn.execute(f"PRAGMA index_info({index[1]})")) == columns:
            return True
    return False


def _has_submission_checks(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='submissions'"
    ).fetchone()
    normalized = "".join((row[0] if row and row[0] else "").upper().split())
    return (
        "CHECK(LANGUAGEIN('CPP17'))" in normalized
        and "CHECK(STATUSIN('PENDING','JUDGING','AC','WA','CE','RE','TLE','OLE','SE'))" in normalized
    )


def _migration_state(conn: sqlite3.Connection) -> tuple[bool, bool, bool]:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "submissions" not in tables:
        return False, False, False
    submission_columns = {row[1] for row in conn.execute("PRAGMA table_info(submissions)")}
    submission_indexes = _indexes(conn, "submissions")
    needs_submissions = (
        not SUBMISSION_COLUMNS <= submission_columns
        or _foreign_keys(conn, "submissions") != SUBMISSION_FOREIGN_KEYS
        or not {"ix_submissions_status", "ix_submissions_judging_started_at"} <= submission_indexes
        or not _has_submission_checks(conn)
    )
    needs_activity = False
    if "user_activities" in tables:
        activity_columns = {row[1] for row in conn.execute("PRAGMA table_info(user_activities)")}
        activity_indexes = _indexes(conn, "user_activities")
        needs_activity = (
            "activity_date" not in activity_columns
            or _foreign_keys(conn, "user_activities") != ACTIVITY_FOREIGN_KEYS
            or "ix_user_activities_activity_date" not in activity_indexes
            or not _has_unique_index(conn, "user_activities", ("user_id", "activity_date"))
        )
    return True, needs_submissions, needs_activity


def _backup_locked_database(conn: sqlite3.Connection, path: Path) -> Path:
    suffix = f"{datetime.now():%Y%m%d%H%M%S%f}-{secrets.token_hex(4)}"
    backup = path.with_name(f"{path.name}.pre-task2-{suffix}.bak")
    backup.write_bytes(conn.serialize())
    return backup


def _legacy_submission_value(row: sqlite3.Row, column: str, default=None):
    return row[column] if column in row.keys() else default


def _rebuild_submissions(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM submissions").fetchall()
    conn.execute("ALTER TABLE submissions RENAME TO submissions_legacy_task2")
    conn.execute(
        """CREATE TABLE submissions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        problem_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        language TEXT NOT NULL CONSTRAINT submission_language CHECK(language IN ('cpp17')),
        status TEXT NOT NULL CONSTRAINT submission_status CHECK(status IN ('PENDING','JUDGING','AC','WA','CE','RE','TLE','OLE','SE')),
        problem_revision INTEGER NOT NULL DEFAULT 1,
        runtime_ms INTEGER,
        failed_case INTEGER,
        details TEXT,
        judging_started_at DATETIME,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE RESTRICT
        )"""
    )
    allowed = {"PENDING", "JUDGING", "AC", "WA", "CE", "RE", "TLE", "OLE", "SE"}
    for row in rows:
        old_language = row["language"]
        old_status = row["status"]
        if old_language == "cpp17" and old_status == "queued":
            status = "PENDING"
        elif old_language == "cpp17" and old_status in allowed:
            status = old_status
        else:
            status = "SE"
        conn.execute(
            """INSERT INTO submissions(
            id,user_id,problem_id,source,language,status,problem_revision,runtime_ms,
            failed_case,details,judging_started_at,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row["id"], row["user_id"], row["problem_id"], row["source"], "cpp17", status,
                _legacy_submission_value(row, "problem_revision", 1),
                _legacy_submission_value(row, "runtime_ms"),
                _legacy_submission_value(row, "failed_case"),
                _legacy_submission_value(row, "details"),
                _legacy_submission_value(row, "judging_started_at"),
                row["created_at"],
            ),
        )
    conn.execute("DROP TABLE submissions_legacy_task2")
    conn.execute("CREATE INDEX ix_submissions_status ON submissions(status)")
    conn.execute("CREATE INDEX ix_submissions_judging_started_at ON submissions(judging_started_at)")
    conn.row_factory = None


def _rebuild_user_activities(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM user_activities").fetchall()
    conn.execute("ALTER TABLE user_activities RENAME TO user_activities_legacy_task2")
    conn.execute(
        """CREATE TABLE user_activities (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        problem_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        activity_date DATE NOT NULL,
        updated_at DATETIME NOT NULL,
        CONSTRAINT uq_activity_user_day UNIQUE(user_id, activity_date),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
        )"""
    )
    for row in rows:
        if "activity_date" in row.keys():
            day = row["activity_date"]
        else:
            day = conn.execute("SELECT date(?, 'localtime')", (row["updated_at"],)).fetchone()[0]
        day = day or datetime.now().date().isoformat()
        conn.execute(
            """INSERT OR IGNORE INTO user_activities(
            id,user_id,problem_id,status,activity_date,updated_at
            ) VALUES(?,?,?,?,?,?)""",
            (row["id"], row["user_id"], row["problem_id"], row["status"], day, row["updated_at"]),
        )
    conn.execute("DROP TABLE user_activities_legacy_task2")
    conn.execute("CREATE INDEX ix_user_activities_activity_date ON user_activities(activity_date)")
    conn.row_factory = None


def migrate_sqlite(database_url: str) -> bool:
    """Apply the Task 2 SQLite migration under one exclusive, re-checked lock."""
    path = _sqlite_path(database_url)
    if path is None or not path.exists():
        return False
    with sqlite3.connect(path, timeout=10, isolation_level=None) as conn:
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN EXCLUSIVE")
        has_submissions, needs_submissions, needs_activity = _migration_state(conn)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if not has_submissions:
            conn.rollback()
            return False
        if version >= TASK2_SCHEMA_VERSION and not needs_submissions and not needs_activity:
            conn.rollback()
            return False
        if needs_submissions or needs_activity:
            _backup_locked_database(conn, path)
        if needs_submissions:
            _rebuild_submissions(conn)
        if needs_activity:
            _rebuild_user_activities(conn)
        conn.execute(f"PRAGMA user_version={TASK2_SCHEMA_VERSION}")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise sqlite3.IntegrityError("foreign key check failed after migration")
        conn.commit()
    return True


def make_engine(database_url: str) -> Engine:
    migrate_sqlite(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine_options = {"connect_args": connect_args}
    if database_url == "sqlite:///:memory:":
        engine_options["poolclass"] = StaticPool
    engine = create_engine(database_url, **engine_options)

    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def configure_sqlite(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            if database_url != "sqlite:///:memory:" and ":memory:" not in database_url:
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def session_factory(database_url: str) -> sessionmaker[OrmSession]:
    return sessionmaker(bind=make_engine(database_url), autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(database_url: str) -> Iterator[OrmSession]:
    factory = session_factory(database_url)
    session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def default_database_url() -> str:
    path = Path(__file__).resolve().parents[1] / "data" / "oj-campus.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.resolve().as_posix()}"
