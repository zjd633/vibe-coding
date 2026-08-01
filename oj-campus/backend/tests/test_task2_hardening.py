from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from conftest import register


def _published_problem(client):
    from test_submissions import make_problem

    return make_problem(client)


def _create_submission(client, problem_id: int, source: str = "int main(){}"):
    return client.post(
        "/api/submissions",
        json={"problem_id": problem_id, "language": "cpp17", "source": source},
    )


def test_cross_user_owner_detail_is_forbidden(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_id = _create_submission(client, problem["id"]).json()["id"]
    client.post("/api/auth/logout")
    assert register(client, "bob", "bob@example.com").status_code == 201

    response = client.get(f"/api/submissions/{submission_id}")

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_owner_detail_uses_generic_safe_diagnostic(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_id = _create_submission(client, problem["id"]).json()["id"]
    from app.database import session_scope
    from app.models import Submission

    with session_scope(client.app.state.database_url) as db:
        submission = db.get(Submission, submission_id)
        submission.status = "CE"
        submission.details = r"C:\private\oj-123\source.cpp: secret compiler diagnostic"
        db.commit()

    detail = client.get(f"/api/submissions/{submission_id}").json()

    assert detail["details"] == "Compilation failed / 编译失败"


def test_admin_detail_shows_sanitized_database_diagnostic(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_id = _create_submission(client, problem["id"]).json()["id"]
    sanitized = "source.cpp: error: expected ';'"
    from app.database import session_scope
    from app.models import Submission

    with session_scope(client.app.state.database_url) as db:
        submission = db.get(Submission, submission_id)
        submission.status = "CE"
        submission.details = sanitized
        db.commit()
    client.post("/api/auth/logout")
    assert client.post(
        "/api/auth/login",
        json={"username": "admin_user", "password": "correct-horse-battery"},
    ).status_code == 200

    detail = client.get(f"/api/admin/submissions/{submission_id}").json()

    assert detail["details"] == sanitized


def test_four_concurrent_creates_cap_outstanding_and_upsert_one_activity(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    cookies = dict(client.cookies)

    def create_once(_index):
        with TestClient(client.app, raise_server_exceptions=False) as race_client:
            race_client.cookies.update(cookies)
            return _create_submission(race_client, problem["id"])

    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(create_once, range(4)))

    assert sorted(response.status_code for response in responses) == [201, 201, 201, 429]
    from app.database import session_scope
    from app.models import Submission, UserActivity

    with session_scope(client.app.state.database_url) as db:
        assert db.query(Submission).filter(Submission.status.in_(("PENDING", "JUDGING"))).count() == 3
        assert db.query(UserActivity).count() == 1


def test_two_concurrent_claims_cannot_claim_the_same_submission(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_id = _create_submission(client, problem["id"]).json()["id"]
    from app.judge import claim_one

    with ThreadPoolExecutor(max_workers=2) as executor:
        claimed = list(executor.map(lambda _index: claim_one(client.app.state.database_url), range(2)))

    assert sorted(claimed, key=lambda value: value is None) == [submission_id, None]


def test_broken_pipe_execution_becomes_se_and_clears_judging_timestamp(client, monkeypatch):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_id = _create_submission(client, problem["id"]).json()["id"]
    import app.judge as judge

    monkeypatch.setattr(judge, "run_submission", lambda *_args, **_kwargs: (_ for _ in ()).throw(BrokenPipeError("closed")))
    assert judge.process_one(client.app.state.database_url) == submission_id
    from app.database import session_scope
    from app.models import Submission

    with session_scope(client.app.state.database_url) as db:
        submission = db.get(Submission, submission_id)
        assert submission.status == "SE"
        assert submission.judging_started_at is None


def test_missing_claimed_submission_is_not_dereferenced(monkeypatch, tmp_path):
    import app.judge as judge
    from app.database import make_engine
    from app.models import Base

    database_url = f"sqlite:///{(tmp_path / 'missing.db').as_posix()}"
    Base.metadata.create_all(make_engine(database_url))
    monkeypatch.setattr(judge, "claim_one", lambda _database_url: 999)

    assert judge.process_one(database_url) == 999


def test_result_commit_exception_marks_se_and_worker_processes_later_task(client, monkeypatch):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    first = _create_submission(client, problem["id"]).json()["id"]
    second = _create_submission(client, problem["id"]).json()["id"]
    import app.judge as judge
    from app.models import Submission
    from sqlalchemy.orm import Session as SqlAlchemySession

    monkeypatch.setattr(judge, "run_submission", lambda *_args, **_kwargs: judge.JudgeResult("AC", 3, None))
    original_commit = SqlAlchemySession.commit
    failed = False

    def fail_first_result_commit(session):
        nonlocal failed
        if not failed and any(isinstance(item, Submission) and item.status == "AC" for item in session.dirty):
            failed = True
            raise RuntimeError("simulated result commit failure")
        return original_commit(session)

    monkeypatch.setattr(SqlAlchemySession, "commit", fail_first_result_commit)

    judge.run_worker(client.app.state.database_url, max_iterations=2, poll_seconds=0)

    from app.database import session_scope

    with session_scope(client.app.state.database_url) as db:
        assert db.get(Submission, first).status == "SE"
        assert db.get(Submission, first).judging_started_at is None
        assert db.get(Submission, second).status == "AC"


def test_worker_loop_logs_failed_iteration_and_continues(monkeypatch, caplog):
    import app.judge as judge

    calls = []

    def flaky_process(*_args, **_kwargs):
        calls.append(len(calls) + 1)
        if len(calls) == 1:
            raise RuntimeError("iteration failed")
        return 42

    monkeypatch.setattr(judge, "recover_stale_judging", lambda _url: 0)
    monkeypatch.setattr(judge, "process_one", flaky_process)

    judge.run_worker("sqlite:///unused.db", max_iterations=2, poll_seconds=0)

    assert calls == [1, 2]
    assert "iteration failed" in caplog.text


def test_worker_retries_failed_initial_recovery_then_processes_work(monkeypatch, caplog):
    import app.judge as judge

    recovery_calls = []
    processed = []
    sleeps = []

    def flaky_recovery(_database_url):
        recovery_calls.append(len(recovery_calls) + 1)
        if len(recovery_calls) == 1:
            raise RuntimeError("transient recovery database failure")
        return 1

    monkeypatch.setattr(judge, "recover_stale_judging", flaky_recovery)
    monkeypatch.setattr(judge, "process_one", lambda *_args, **_kwargs: processed.append(42) or 42)
    monkeypatch.setattr(judge.time, "sleep", lambda seconds: sleeps.append(seconds))

    judge.run_worker("sqlite:///unused.db", max_iterations=2, poll_seconds=0.25)

    assert recovery_calls == [1, 2]
    assert processed == [42]
    assert sleeps == [0.25]
    assert "transient recovery database failure" in caplog.text


def test_application_and_worker_startup_emit_chinese_security_warning(tmp_path, monkeypatch, caplog):
    import app
    import app.judge as judge

    warning = "Windows 子进程执行不是安全沙箱，仅允许运行受信任的本地代码，绝不能对公网开放"
    with caplog.at_level("WARNING"):
        app.create_app(f"sqlite:///{(tmp_path / 'warning.db').as_posix()}")
    assert warning in caplog.text

    caplog.clear()
    monkeypatch.setattr(judge, "recover_stale_judging", lambda _database_url: 0)
    monkeypatch.setattr(judge, "process_one", lambda *_args, **_kwargs: None)
    with caplog.at_level("WARNING"):
        judge.run_worker("sqlite:///unused.db", max_iterations=1, poll_seconds=0)
    assert warning in caplog.text


def test_run_closes_job_and_reaps_process_when_wait_raises(tmp_path, monkeypatch):
    import app.judge as judge

    class FakeJob:
        closed = False

        def terminate(self):
            process.kill()

        def close(self):
            self.closed = True
            process.kill()

    class FakeProcess:
        pid = 12345
        returncode = None
        stdin = None
        _handle = 1
        killed = False

        def __init__(self):
            stdout_read, stdout_write = os.pipe()
            stderr_read, stderr_write = os.pipe()
            os.close(stdout_write)
            os.close(stderr_write)
            self.stdout = os.fdopen(stdout_read, "rb")
            self.stderr = os.fdopen(stderr_read, "rb")

        def resume(self):
            return None

        def wait(self, timeout=None):
            if not self.killed:
                raise RuntimeError("simulated wait failure")
            self.returncode = -9
            return self.returncode

        def poll(self):
            return self.returncode

        def kill(self):
            self.killed = True
            self.returncode = -9

    process = FakeProcess()
    job = FakeJob()
    monkeypatch.setattr(judge.psutil, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(judge, "_create_windows_job", lambda _process: job)
    monkeypatch.setattr(judge, "_record_descendants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        judge,
        "_kill_recorded_processes",
        lambda target, _descendants, _lock, include_parent, job=None: target.kill() if include_parent else None,
    )

    with pytest.raises(RuntimeError, match="simulated wait failure"):
        judge._run(["ignored"], tmp_path, 1)

    assert job.closed
    assert process.killed


def test_windows_job_close_failure_keeps_handle_for_retry(monkeypatch):
    import app.judge as judge

    class FakeKernel:
        def __init__(self):
            self.close_results = iter((False, True))
            self.closed = []

        def CloseHandle(self, handle):
            self.closed.append(handle)
            return next(self.close_results)

    kernel = FakeKernel()
    job = judge._WindowsJob(kernel, 77)

    with pytest.raises(OSError, match=r"CloseHandle\(job\) failed"):
        job.close()
    assert job._handle == 77

    job.close()
    assert job._handle is None
    assert kernel.closed == [77, 77]


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object close retry regression")
def test_run_retries_job_close_and_leaves_no_handle_or_live_process(tmp_path, monkeypatch):
    import app.judge as judge

    class FakeKernel:
        def __init__(self):
            self.close_results = iter((False, True))
            self.closed = []

        def CloseHandle(self, handle):
            self.closed.append(handle)
            return next(self.close_results)

    class FakeProcess:
        pid = 987654
        _handle = 1
        stdin = None

        def __init__(self):
            self.returncode = None
            self.resumed = False
            self.wait_calls = 0
            stdout_read, stdout_write = os.pipe()
            stderr_read, stderr_write = os.pipe()
            os.close(stdout_write)
            os.close(stderr_write)
            self.stdout = os.fdopen(stdout_read, "rb")
            self.stderr = os.fdopen(stderr_read, "rb")

        def resume(self):
            self.resumed = True

        def wait(self, timeout=None):
            self.wait_calls += 1
            self.returncode = 0
            return 0

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    kernel = FakeKernel()
    job = judge._WindowsJob(kernel, 90)
    process = FakeProcess()
    monkeypatch.setattr(judge.psutil, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(judge, "_create_windows_job", lambda _process: job)
    monkeypatch.setattr(judge, "_record_descendants", lambda *_args, **_kwargs: None)

    result = judge._run(["ignored"], tmp_path, 1)

    assert result.returncode == 0
    assert process.resumed
    assert process.poll() == 0
    assert process.wait_calls >= 1
    assert kernel.closed == [90, 90]
    assert job._handle is None


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object close failure regression")
def test_run_final_job_close_failure_kills_tree_and_preserves_cleanup_error(tmp_path, monkeypatch):
    import app.judge as judge

    class FakeKernel:
        def __init__(self):
            self.closed = []

        def CloseHandle(self, handle):
            self.closed.append(handle)
            return False

    class FakeProcess:
        pid = 987655
        _handle = 1
        stdin = None

        def __init__(self):
            self.returncode = None
            stdout_read, stdout_write = os.pipe()
            stderr_read, stderr_write = os.pipe()
            os.close(stdout_write)
            os.close(stderr_write)
            self.stdout = os.fdopen(stdout_read, "rb")
            self.stderr = os.fdopen(stderr_read, "rb")

        def resume(self):
            return None

        def wait(self, timeout=None):
            self.returncode = 0
            return 0

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    kernel = FakeKernel()
    job = judge._WindowsJob(kernel, 91)
    process = FakeProcess()
    kill_calls = []
    tree_alive = True

    def kill_tree(_process, _descendants, _lock, include_parent, job=None):
        nonlocal tree_alive
        kill_calls.append(include_parent)
        if include_parent:
            tree_alive = False

    monkeypatch.setattr(judge.psutil, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(judge, "_create_windows_job", lambda _process: job)
    monkeypatch.setattr(judge, "_record_descendants", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(judge, "_kill_recorded_processes", kill_tree)

    with pytest.raises(OSError, match=r"CloseHandle\(job\) failed"):
        judge._run(["ignored"], tmp_path, 1)

    assert kernel.closed == [91, 91, 91]
    assert job._handle == 91
    assert True in kill_calls
    assert not tree_alive


@pytest.mark.skipif(os.name != "nt", reason="Windows ctypes Job Object regression")
def test_windows_job_creation_cleanup_preserves_original_error_and_retries_close(monkeypatch):
    import ctypes
    import app.judge as judge

    class FakeFunction:
        def __init__(self, values):
            self.values = iter(values)
            self.calls = []

        def __call__(self, *args):
            self.calls.append(args)
            return next(self.values)

    class FakeKernel:
        def __init__(self):
            self.CreateJobObjectW = FakeFunction([88])
            self.SetInformationJobObject = FakeFunction([False])
            self.AssignProcessToJobObject = FakeFunction([True])
            self.TerminateJobObject = FakeFunction([True])
            self.CloseHandle = FakeFunction([False, True])

    kernel = FakeKernel()
    monkeypatch.setattr(ctypes, "WinDLL", lambda *_args, **_kwargs: kernel)

    with pytest.raises(OSError, match="SetInformationJobObject failed"):
        judge._create_windows_job(SimpleNamespace(_handle=123))

    assert [call[0] for call in kernel.CloseHandle.calls] == [88, 88]


@pytest.mark.skipif(os.name != "nt", reason="Windows suspended-process fallback regression")
def test_windows_job_failure_warns_and_falls_back_to_psutil_execution(tmp_path, monkeypatch, caplog):
    import app.judge as judge

    monkeypatch.setattr(
        judge,
        "_create_windows_job",
        lambda _process: (_ for _ in ()).throw(OSError("job assignment unavailable")),
    )

    with caplog.at_level("WARNING"):
        result = judge._run([sys.executable, "-c", "print('fallback-ok')"], tmp_path, 5)

    assert result.returncode == 0
    assert result.stdout.strip() == b"fallback-ok"
    assert "weaker containment" in caplog.text
    assert "较弱" in caplog.text


def test_child_closing_stdin_uses_return_code_instead_of_system_error(tmp_path):
    import app.judge as judge

    compiler = Path(os.environ.get("OJ_GPP_PATH", judge.GPP_PATH))
    if not compiler.is_file():
        pytest.skip(f"g++ not found: {compiler}")
    large_input = "x" * (2 * 1024 * 1024)

    accepted = judge.run_submission("int main(){return 0;}", [(large_input, "")], 2000, tmp_path, str(compiler))
    runtime_error = judge.run_submission("int main(){return 7;}", [(large_input, "")], 2000, tmp_path, str(compiler))

    assert accepted.status == "AC"
    assert runtime_error.status == "RE"


def test_stdout_overflow_immediately_terminates_and_is_ole(tmp_path):
    import app.judge as judge

    compiler = Path(os.environ.get("OJ_GPP_PATH", judge.GPP_PATH))
    if not compiler.is_file():
        pytest.skip(f"g++ not found: {compiler}")
    source = (
        "#include <iostream>\n#include <windows.h>\n"
        "int main(){for(int i=0;i<1048577;i++)std::cout<<'x';std::cout.flush();Sleep(5000);}"
    )

    result = judge.run_submission(source, [("", "")], 10_000, tmp_path, str(compiler))

    assert result.status == "OLE"
    assert result.runtime_ms is not None
    # The child sleeps for 5s after overflow, so runtime below 3s proves immediate termination.
    assert result.runtime_ms < 3000


def test_stderr_over_cap_is_truncated_without_changing_verdict(tmp_path):
    import app.judge as judge

    compiler = Path(os.environ.get("OJ_GPP_PATH", judge.GPP_PATH))
    if not compiler.is_file():
        pytest.skip(f"g++ not found: {compiler}")
    source = "#include <iostream>\nint main(){for(int i=0;i<20000;i++)std::cerr<<'e';}"

    result = judge.run_submission(source, [("", "")], 2000, tmp_path, str(compiler))

    assert result.status == "AC"
    assert result.details == ""


def test_compiler_stdout_and_stderr_are_independently_capped(tmp_path):
    import app.judge as judge

    result = judge._run(
        [sys.executable, "-c", "import sys; sys.stdout.write('o'*20000); sys.stderr.write('e'*20000)"],
        tmp_path,
        5,
        stdout_limit=judge.STDERR_LIMIT,
    )

    assert len(result.stdout) <= judge.STDERR_LIMIT
    assert len(result.stderr) <= judge.STDERR_LIMIT
    assert result.stdout_overflow
    assert result.stderr_truncated


def test_compile_timeout_is_ce_with_safe_bilingual_message(tmp_path, monkeypatch):
    import app.judge as judge

    timed_out = SimpleNamespace(
        stdout=b"",
        stderr=b"secret",
        returncode=None,
        timed_out=True,
        overflow=False,
        stdout_overflow=False,
        stderr_truncated=False,
        elapsed_ms=15_000,
    )
    monkeypatch.setattr(judge, "_run", lambda *_args, **_kwargs: timed_out)

    result = judge.run_submission("int main(){}", [], 1000, tmp_path, "g++")

    assert result.status == "CE"
    assert result.details == "Compilation timed out / 编译超时"


def test_missing_compiler_is_system_error(tmp_path):
    from app.judge import run_submission

    result = run_submission("int main(){}", [], 1000, tmp_path, r"Z:\missing\g++.exe")

    assert result.status == "SE"


def test_runtime_excludes_deliberately_delayed_compile_time(tmp_path, monkeypatch):
    import app.judge as judge

    results = iter(
        [
            SimpleNamespace(stdout=b"", stderr=b"", returncode=0, timed_out=False, overflow=False,
                            stdout_overflow=False, stderr_truncated=False, elapsed_ms=5_000),
            SimpleNamespace(stdout=b"ok", stderr=b"", returncode=0, timed_out=False, overflow=False,
                            stdout_overflow=False, stderr_truncated=False, elapsed_ms=7),
        ]
    )
    monkeypatch.setattr(judge, "_run", lambda *_args, **_kwargs: next(results))

    result = judge.run_submission("int main(){}", [("", "ok")], 1000, tmp_path, "g++")

    assert result.status == "AC"
    assert result.runtime_ms == 7


def test_first_failing_case_ordinal_is_retained(tmp_path, monkeypatch):
    import app.judge as judge

    results = iter(
        [
            SimpleNamespace(stdout=b"", stderr=b"", returncode=0, timed_out=False, overflow=False,
                            stdout_overflow=False, stderr_truncated=False, elapsed_ms=100),
            SimpleNamespace(stdout=b"one", stderr=b"", returncode=0, timed_out=False, overflow=False,
                            stdout_overflow=False, stderr_truncated=False, elapsed_ms=2),
            SimpleNamespace(stdout=b"wrong", stderr=b"", returncode=0, timed_out=False, overflow=False,
                            stdout_overflow=False, stderr_truncated=False, elapsed_ms=3),
        ]
    )
    monkeypatch.setattr(judge, "_run", lambda *_args, **_kwargs: next(results))

    result = judge.run_submission("int main(){}", [("", "one"), ("", "two"), ("", "three")], 1000, tmp_path, "g++")

    assert result.status == "WA"
    assert result.failed_case == 2
    assert result.runtime_ms == 5


def test_worker_startup_requeues_stale_fresh_and_null_judging_rows(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_ids = [_create_submission(client, problem["id"]).json()["id"] for _ in range(3)]
    from app.database import session_scope
    from app.judge import recover_stale_judging
    from app.models import Submission, utcnow

    with session_scope(client.app.state.database_url) as db:
        started_values = [utcnow() - timedelta(minutes=6), utcnow(), None]
        for submission_id, started_at in zip(submission_ids, started_values, strict=True):
            submission = db.get(Submission, submission_id)
            submission.status = "JUDGING"
            submission.judging_started_at = started_at
        db.commit()

    assert recover_stale_judging(client.app.state.database_url) == 3
    with session_scope(client.app.state.database_url) as db:
        for submission_id in submission_ids:
            submission = db.get(Submission, submission_id)
            assert submission.status == "PENDING"
            assert submission.judging_started_at is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process-tree regression")
def test_normal_parent_exit_still_terminates_background_descendant_and_removes_temp(tmp_path):
    import app.judge as judge

    compiler = Path(os.environ.get("OJ_GPP_PATH", judge.GPP_PATH))
    if not compiler.is_file():
        pytest.skip(f"g++ not found: {compiler}")
    source = r'''
#include <windows.h>
#include <string>
int main(int argc, char**) {
    if (argc > 1) {
        HANDLE file = CreateFileA("locked.txt", GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
        Sleep(5000);
        if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
        return 0;
    }
    char executable[MAX_PATH];
    GetModuleFileNameA(nullptr, executable, MAX_PATH);
    std::string command = "\"" + std::string(executable) + "\" child";
    STARTUPINFOA startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION child{};
    if (!CreateProcessA(nullptr, command.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW, nullptr, nullptr, &startup, &child)) return 2;
    CloseHandle(child.hThread);
    CloseHandle(child.hProcess);
    return 0;
}
'''

    for _attempt in range(5):
        result = judge.run_submission(source, [("", "")], 2000, tmp_path, str(compiler))
        assert result.status == "AC"
        assert not list(tmp_path.iterdir())


def test_local_date_activity_streak_handles_consecutive_days_and_gap(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    assert _create_submission(client, problem["id"]).status_code == 201
    from app import local_day
    from app.database import session_scope
    from app.models import User, UserActivity

    today = local_day()
    with session_scope(client.app.state.database_url) as db:
        user_id = db.query(User.id).filter_by(username="alice").scalar()
        db.add(UserActivity(user_id=user_id, problem_id=problem["id"], activity_date=today - timedelta(days=1)))
        db.commit()
    assert client.get("/api/dashboard").json()["current_streak"] == 2

    with session_scope(client.app.state.database_url) as db:
        db.query(UserActivity).filter(UserActivity.activity_date == today - timedelta(days=1)).delete()
        db.add(UserActivity(user_id=user_id, problem_id=problem["id"], activity_date=today - timedelta(days=2)))
        db.commit()
    assert client.get("/api/dashboard").json()["current_streak"] == 1


def test_obsolete_revision_ac_does_not_count_solved_or_rank_but_rate_is_lifetime(client):
    problem, admin = _published_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    submission_id = _create_submission(client, problem["id"]).json()["id"]
    from app.database import session_scope
    from app.models import Problem, Submission

    with session_scope(client.app.state.database_url) as db:
        db.get(Submission, submission_id).status = "AC"
        db.get(Problem, problem["id"]).revision += 1
        db.commit()

    dashboard = client.get("/api/dashboard").json()
    leaderboard = client.get("/api/leaderboard").json()
    alice = next(row for row in leaderboard["items"] if row["username"] == "alice")

    assert dashboard["solved_count"] == 0
    assert dashboard["acceptance_rate"] == 1.0
    assert alice["solved"] == 0
    assert dashboard["rank"] == leaderboard["current_user_position"]


def test_leaderboard_orders_solved_desc_attempts_asc_username_asc(client):
    problem, admin = _published_problem(client)
    from app.database import session_scope
    from app.models import Submission, User
    from app.security import hash_password

    with session_scope(client.app.state.database_url) as db:
        users = {}
        for username in ("alpha", "beta", "zebra"):
            user = User(username=username, email=f"{username}@example.com", display_name=username,
                        password_hash=hash_password("correct-horse-battery"))
            db.add(user)
            db.flush()
            users[username] = user.id
        for username in ("alpha", "beta", "zebra"):
            db.add(Submission(user_id=users[username], problem_id=problem["id"], source="int main(){}",
                              language="cpp17", status="AC", problem_revision=problem["revision"]))
        db.add(Submission(user_id=users["alpha"], problem_id=problem["id"], source="int main(){}",
                          language="cpp17", status="WA", problem_revision=problem["revision"]))
        db.commit()

    rows = client.get("/api/leaderboard").json()["items"]
    solved_rows = [row for row in rows if row["solved"] == 1]

    assert [row["username"] for row in solved_rows] == ["beta", "zebra", "alpha"]
    assert [row["attempts"] for row in solved_rows] == [1, 1, 2]
