from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
import subprocess
import sys

import psutil
import pytest
from sqlalchemy import func, select

from app.database import session_scope
from app.judge import process_one
from app.models import Problem, Submission, User
from app.seed import seed_database
from reference_seed_solutions import REFERENCE_SOLUTIONS


REPRESENTATIVE_TITLES = (
    "长方形周长与面积",
    "闰年判断",
    "质数判断",
    "数组循环右移",
    "回文字符串",
    "日期的下一天",
    "二分查找首次出现",
    "区间和查询",
    "后缀表达式求值",
    "迷宫最短路",
    "活动选择",
    "零一背包",
    "Dijkstra 最短路",
    "编辑距离",
    "N 皇后计数",
    "并查集连通性",
    "LRU 缓存模拟",
    "带括号表达式求值",
)


def test_reference_solutions_cover_representatives_exactly():
    assert set(REFERENCE_SOLUTIONS) == set(REPRESENTATIVE_TITLES)
    assert len(REFERENCE_SOLUTIONS) == len(REPRESENTATIVE_TITLES)


@pytest.fixture(scope="module")
def compiler() -> str:
    configured = os.environ.get("OJ_GPP_PATH", "").strip()
    path = Path(configured) if configured else Path(r"E:\mingw64\bin\g++.exe")
    if not path.is_file():
        pytest.skip(f"g++ unavailable at configured path: {path}")
    return str(path.resolve())


@pytest.fixture(scope="module")
def seeded_database_url(tmp_path_factory: pytest.TempPathFactory):
    database_root = tmp_path_factory.mktemp("seed-catalog-worker-db")
    database_path = database_root / "seed-catalog-worker.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    seed_database(database_url)
    yield database_url
    assert database_path.is_file()


@pytest.fixture()
def judge_temp_root(tmp_path: Path):
    assert not list(tmp_path.iterdir())
    yield tmp_path
    assert not list(tmp_path.iterdir())


def _live_descendants(parent: psutil.Process) -> dict[int, psutil.Process]:
    try:
        descendants = parent.children(recursive=True)
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return {}
    live: dict[int, psutil.Process] = {}
    for descendant in descendants:
        try:
            if descendant.is_running() and descendant.status() != psutil.STATUS_ZOMBIE:
                live[descendant.pid] = descendant
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return live


def _submission_ids_for_title(database_url: str, title: str) -> set[int]:
    with session_scope(database_url) as db:
        return set(
            db.scalars(
                select(Submission.id)
                .join(Problem, Problem.id == Submission.problem_id)
                .where(Problem.title == title)
            ).all()
        )


def _remove_new_nonterminal_rows(
    database_url: str,
    title: str,
    submission_ids_before: set[int],
) -> None:
    with session_scope(database_url) as db:
        rows = db.scalars(
            select(Submission)
            .join(Problem, Problem.id == Submission.problem_id)
            .where(
                Problem.title == title,
                Submission.status.in_(("PENDING", "JUDGING")),
            )
        ).all()
        for row in rows:
            if row.id not in submission_ids_before:
                db.delete(row)
        db.commit()


def _exercise_seeded_problem_through_worker(
    title: str,
    compiler: str,
    seeded_database_url: str,
    judge_temp_root: Path,
    worker: Callable[..., int | None],
) -> None:
    source = REFERENCE_SOLUTIONS[title]
    with session_scope(seeded_database_url) as db:
        pending_count = db.scalar(
            select(func.count()).select_from(Submission).where(Submission.status == "PENDING")
        )
        assert pending_count == 0
        student = db.scalar(select(User).where(User.username == "demo_student"))
        problem = db.scalar(select(Problem).where(Problem.title == title))
        assert student is not None
        assert problem is not None
        current_revision = problem.revision
        submission = Submission(
            user_id=student.id,
            problem_id=problem.id,
            source=source,
            language="cpp17",
            status="PENDING",
            problem_revision=current_revision,
        )
        db.add(submission)
        db.commit()
        submission_id = submission.id

    pytest_process = psutil.Process()
    descendant_pids_before = set(_live_descendants(pytest_process))
    try:
        processed_id = worker(
            seeded_database_url,
            compiler=compiler,
            temp_root=judge_temp_root,
        )
        assert processed_id == submission_id

        with session_scope(seeded_database_url) as db:
            persisted = db.get(Submission, submission_id)
            assert persisted is not None
            assert persisted.status == "AC"
            assert persisted.failed_case is None
            assert persisted.judging_started_at is None
            assert persisted.problem_revision == current_revision
            assert persisted.runtime_ms is not None

        assert not list(judge_temp_root.iterdir())
    finally:
        try:
            new_descendants = [
                descendant
                for pid, descendant in _live_descendants(pytest_process).items()
                if pid not in descendant_pids_before
            ]
            _gone, alive = psutil.wait_procs(new_descendants, timeout=0.5)
            live_new_pids = []
            for descendant in alive:
                try:
                    if descendant.is_running() and descendant.status() != psutil.STATUS_ZOMBIE:
                        live_new_pids.append(descendant.pid)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
            assert live_new_pids == [], f"new live child processes remain: {live_new_pids}"
        finally:
            with session_scope(seeded_database_url) as db:
                exact_submission = db.get(Submission, submission_id)
                if exact_submission is not None and exact_submission.status in ("PENDING", "JUDGING"):
                    db.delete(exact_submission)
                    db.commit()


def test_worker_failure_before_claim_does_not_poison_shared_database(
    compiler: str,
    seeded_database_url: str,
    judge_temp_root: Path,
):
    title = "长方形周长与面积"
    submission_ids_before = _submission_ids_for_title(seeded_database_url, title)

    def fail_before_claim(*_args, **_kwargs):
        raise RuntimeError("worker failed before claim")

    try:
        with pytest.raises(RuntimeError, match="worker failed before claim"):
            _exercise_seeded_problem_through_worker(
                title,
                compiler,
                seeded_database_url,
                judge_temp_root,
                fail_before_claim,
            )
        with session_scope(seeded_database_url) as db:
            poisoned = db.scalar(
                select(func.count())
                .select_from(Submission)
                .where(Submission.status.in_(("PENDING", "JUDGING")))
            )
            assert poisoned == 0
    finally:
        _remove_new_nonterminal_rows(
            seeded_database_url,
            title,
            submission_ids_before,
        )


def test_child_leak_check_runs_when_worker_raises(
    compiler: str,
    seeded_database_url: str,
    judge_temp_root: Path,
):
    title = "闰年判断"
    submission_ids_before = _submission_ids_for_title(seeded_database_url, title)
    leaked_processes: list[subprocess.Popen] = []

    def leak_child_then_fail(*_args, **_kwargs):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
        )
        leaked_processes.append(child)
        raise RuntimeError("worker failed after leaking child")

    try:
        with pytest.raises(AssertionError, match="new live child"):
            _exercise_seeded_problem_through_worker(
                title,
                compiler,
                seeded_database_url,
                judge_temp_root,
                leak_child_then_fail,
            )
    finally:
        for child in leaked_processes:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        _remove_new_nonterminal_rows(
            seeded_database_url,
            title,
            submission_ids_before,
        )


@pytest.mark.parametrize("title", REPRESENTATIVE_TITLES)
def test_seeded_problem_is_accepted_through_worker(
    title: str,
    compiler: str,
    seeded_database_url: str,
    judge_temp_root: Path,
):
    _exercise_seeded_problem_through_worker(
        title,
        compiler,
        seeded_database_url,
        judge_temp_root,
        process_one,
    )
