"""Repeatable local demonstration data for OJ Campus."""
from __future__ import annotations

import os
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import func, select

from .database import default_database_url, make_engine, session_scope
from .models import Base, Problem, ProblemTag, Submission, Tag, TestCase, User, UserActivity
from .security import hash_password
from .seed_catalog import PROBLEMS


DEMO_PASSWORD = "ojcampus-demo"

_LEGACY_GRID_TITLE = "网格最小路径和"
_LEGACY_GRID_OLD_METADATA = (
    "只能向右或向下走，求左上到右下的最小路径和。",
    "第一行 n m，随后 n 行 m 个非负整数。",
    "输出最小路径和。",
    "hard",
    1000,
    True,
    1,
)
_LEGACY_GRID_OLD_TAGS = ("动态规划", "网格")
_LEGACY_GRID_OLD_CASES = (
    (1, "2 3\n1 3 1\n1 5 1\n", "6\n", True),
    (2, "3 2\n1 2\n1 1\n4 2\n", "6\n", False),
)


def _tag(db, name: str) -> Tag:
    tag = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()).order_by(Tag.id))
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


def _user(db, username: str, email: str, display_name: str, role: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username, email=email, display_name=display_name, password_hash=hash_password(DEMO_PASSWORD), role=role)
        db.add(user)
        db.flush()
    return user


def _repair_legacy_grid_path_answer(db) -> None:
    """Repair only the untouched built-in row that shipped with one wrong answer."""
    candidates = db.scalars(
        select(Problem).where(Problem.title == _LEGACY_GRID_TITLE).order_by(Problem.id)
    ).all()
    for problem in candidates:
        metadata = (
            problem.statement,
            problem.input_markdown,
            problem.output_markdown,
            problem.difficulty,
            problem.time_limit_ms,
            problem.published,
            problem.revision,
        )
        tags = Counter(link.tag.name for link in problem.tags)
        cases = tuple(
            (case.position, case.input_data, case.output_data, case.is_sample)
            for case in problem.test_cases
        )
        if (
            metadata != _LEGACY_GRID_OLD_METADATA
            or tags != Counter(_LEGACY_GRID_OLD_TAGS)
            or cases != _LEGACY_GRID_OLD_CASES
        ):
            continue
        problem.test_cases[1].output_data = "5\n"
        problem.revision += 1


def _matches_seed_problem(problem: Problem, data) -> bool:
    metadata = (
        problem.title,
        problem.statement,
        problem.input_markdown,
        problem.output_markdown,
        problem.difficulty,
        problem.time_limit_ms,
        problem.published,
        problem.revision,
    )
    expected_metadata = (
        data.title,
        data.statement,
        data.input_text,
        data.output_text,
        data.difficulty,
        data.time_limit_ms,
        True,
        1,
    )
    tags = Counter(link.tag.name for link in problem.tags)
    cases = tuple(
        (case.position, case.input_data, case.output_data, case.is_sample)
        for case in problem.test_cases
    )
    expected_cases = tuple(
        (position, case.input_data, case.output_data, case.is_sample)
        for position, case in enumerate(data.cases, start=1)
    )
    return metadata == expected_metadata and tags == Counter(data.tags) and cases == expected_cases


def seed_database(database_url: str | None = None) -> None:
    """Create or complete the local demo dataset without duplicating its rows."""
    database_url = database_url or os.environ.get("OJ_DATABASE_URL") or default_database_url()
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        admin = _user(db, "demo_admin", "admin@oj-campus.local", "演示管理员", "admin")
        student = _user(db, "demo_student", "student@oj-campus.local", "演示学生", "student")
        _repair_legacy_grid_path_answer(db)
        demo_by_title: dict[str, Problem] = {}
        for data in PROBLEMS:
            candidates = db.scalars(
                select(Problem).where(Problem.title == data.title).order_by(Problem.id)
            ).all()
            if not candidates:
                problem = Problem(
                    title=data.title,
                    statement=data.statement,
                    input_markdown=data.input_text,
                    output_markdown=data.output_text,
                    difficulty=data.difficulty,
                    time_limit_ms=data.time_limit_ms,
                    published=True,
                )
                problem.tags = [ProblemTag(tag=_tag(db, name)) for name in data.tags]
                problem.test_cases = [TestCase(position=index, input_data=case.input_data, output_data=case.output_data,
                                               is_sample=case.is_sample)
                                      for index, case in enumerate(data.cases, start=1)]
                db.add(problem)
                db.flush()
                demo_by_title[data.title] = problem
            elif len(candidates) == 1 and _matches_seed_problem(candidates[0], data):
                demo_by_title[data.title] = candidates[0]
        # Fixed source strings make these records deterministic and prevent a second seed from adding more.
        historical = (
            (student, "两数之和", "AC"),
            (student, "奇偶判断", "WA"),
            (admin, "最大公约数", "AC"),
        )
        for user, title, status in historical:
            problem = demo_by_title.get(title)
            if problem is None:
                continue
            existing = db.scalar(select(Submission).where(Submission.user_id == user.id, Submission.problem_id == problem.id, Submission.status == status))
            if existing is None:
                db.add(Submission(user_id=user.id, problem_id=problem.id, source="#include <iostream>\nint main(){return 0;}",
                                  language="cpp17", status=status, problem_revision=problem.revision, runtime_ms=1 if status == "AC" else None,
                                  failed_case=1 if status == "WA" else None))
        for offset, title in enumerate(("两数之和", "奇偶判断", "区间求和")):
            problem = demo_by_title.get(title)
            if problem is None:
                continue
            activity_date = date.today() - timedelta(days=2 - offset)
            existing = db.scalar(select(UserActivity).where(
                UserActivity.user_id == student.id,
                UserActivity.activity_date == activity_date,
            ))
            if existing is None:
                db.add(UserActivity(user_id=student.id, problem_id=problem.id, status="attempted", activity_date=activity_date))
        db.commit()


def main() -> None:
    seed_database()
    print("OJ Campus demo data is ready (100 problems, demo_admin and demo_student).")


if __name__ == "__main__":
    main()
