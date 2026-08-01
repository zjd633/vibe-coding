from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _problem_snapshot(db, problem_id):
    from app.models import Problem, ProblemTag, Submission, Tag, TestCase

    problem = db.get(Problem, problem_id)
    return {
        "problem": (
            problem.id,
            problem.title,
            problem.statement,
            problem.input_markdown,
            problem.output_markdown,
            problem.difficulty,
            problem.time_limit_ms,
            problem.published,
            problem.revision,
            problem.created_at,
            problem.updated_at,
        ),
        "tags": tuple(
            db.execute(
                select(ProblemTag.tag_id, Tag.name)
                .join(Tag, ProblemTag.tag_id == Tag.id)
                .where(ProblemTag.problem_id == problem_id)
                .order_by(ProblemTag.tag_id)
            ).all()
        ),
        "cases": tuple(
            db.execute(
                select(
                    TestCase.id,
                    TestCase.position,
                    TestCase.input_data,
                    TestCase.output_data,
                    TestCase.is_sample,
                )
                .where(TestCase.problem_id == problem_id)
                .order_by(TestCase.position)
            ).all()
        ),
        "submissions": tuple(
            db.execute(
                select(
                    Submission.id,
                    Submission.user_id,
                    Submission.problem_id,
                    Submission.source,
                    Submission.language,
                    Submission.status,
                    Submission.problem_revision,
                    Submission.runtime_ms,
                    Submission.failed_case,
                    Submission.details,
                    Submission.judging_started_at,
                    Submission.created_at,
                )
                .where(Submission.problem_id == problem_id)
                .order_by(Submission.id)
            ).all()
        ),
    }


def _add_exact_old_grid(db, *, with_submission=False):
    from app.models import Problem, ProblemTag, Submission, Tag, TestCase, User

    tags = []
    for name in ("动态规划", "网格"):
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    problem = Problem(
        title="网格最小路径和",
        statement="只能向右或向下走，求左上到右下的最小路径和。",
        input_markdown="第一行 n m，随后 n 行 m 个非负整数。",
        output_markdown="输出最小路径和。",
        difficulty="hard",
        time_limit_ms=1000,
        published=True,
        revision=1,
    )
    problem.tags = [ProblemTag(tag=tag) for tag in tags]
    problem.test_cases = [
        TestCase(
            position=1,
            input_data="2 3\n1 3 1\n1 5 1\n",
            output_data="6\n",
            is_sample=True,
        ),
        TestCase(
            position=2,
            input_data="3 2\n1 2\n1 1\n4 2\n",
            output_data="6\n",
            is_sample=False,
        ),
    ]
    db.add(problem)
    db.flush()
    if with_submission:
        owner = User(
            username="legacy_owner",
            email="legacy-owner@example.test",
            display_name="旧库用户",
            password_hash="not-used-by-this-test",
            role="student",
        )
        db.add(owner)
        db.flush()
        db.add(
            Submission(
                user_id=owner.id,
                problem_id=problem.id,
                source="// historical accepted source",
                language="cpp17",
                status="AC",
                problem_revision=1,
                runtime_ms=7,
            )
        )
    return problem


def _add_catalog_problem(db, data):
    from app.models import Problem, ProblemTag, Tag, TestCase

    tags = []
    for name in data.tags:
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    problem = Problem(
        title=data.title,
        statement=data.statement,
        input_markdown=data.input_text,
        output_markdown=data.output_text,
        difficulty=data.difficulty,
        time_limit_ms=data.time_limit_ms,
        published=True,
        revision=1,
    )
    problem.tags = [ProblemTag(tag=tag) for tag in tags]
    problem.test_cases = [
        TestCase(
            position=position,
            input_data=case.input_data,
            output_data=case.output_data,
            is_sample=case.is_sample,
        )
        for position, case in enumerate(data.cases, start=1)
    ]
    db.add(problem)
    db.flush()
    return problem


def test_delivery_scripts_propagate_native_failures_and_dev_launch_is_parameterized():
    setup = (PROJECT_ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")
    test = (PROJECT_ROOT / "scripts" / "test.ps1").read_text(encoding="utf-8")
    dev = (PROJECT_ROOT / "scripts" / "dev.ps1").read_text(encoding="utf-8")

    for script in (setup, test):
        assert "function Invoke-NativeChecked" in script
        assert "$LASTEXITCODE -ne 0" in script
        assert "failed with exit code" in script
    assert "-EncodedCommand" not in dev
    assert "OJ_DATABASE_URL =" not in dev
    assert "ArgumentsJson" not in dev
    assert "-WorkingDirectory $WorkingDirectory" in dev
    assert "inherit OJ_DATABASE_URL" in dev
    assert "function Test-Components" in dev
    assert dev.count("Test-Components $components") >= 2
    assert "has exited with code" in dev
    assert "Stop-ProcessTree" in dev


def test_seed_is_idempotent_and_has_catalog_balanced_runnable_problems(tmp_path):
    from app import local_day
    from app.database import session_scope
    from app.models import Problem, Submission, TestCase, User, UserActivity
    from app.seed_catalog import PROBLEMS
    from app.seed import seed_database

    database_url = f"sqlite:///{tmp_path / 'seed.db'}"
    seed_database(database_url)

    with session_scope(database_url) as db:
        difficulties = dict(db.execute(select(Problem.difficulty, func.count()).group_by(Problem.difficulty)).all())
        assert difficulties == {"easy": 40, "medium": 35, "hard": 25}
        assert db.scalar(select(func.count()).select_from(Problem)) == 100
        assert db.scalar(select(func.count()).select_from(TestCase)) == sum(
            len(problem.cases) for problem in PROBLEMS
        )
        assert all(
            db.scalar(select(func.count()).select_from(Problem).where(Problem.title == problem.title)) == 1
            for problem in PROBLEMS
        )
        assert db.scalar(select(func.count()).select_from(User)) == 2
        assert db.scalar(select(func.count()).select_from(Submission)) >= 3
        historical = set(
            db.execute(
                select(User.username, Problem.title, Submission.status)
                .join(User, Submission.user_id == User.id)
                .join(Problem, Submission.problem_id == Problem.id)
            ).all()
        )
        assert {
            ("demo_student", "两数之和", "AC"),
            ("demo_student", "奇偶判断", "WA"),
            ("demo_admin", "最大公约数", "AC"),
        } <= historical
        student = db.scalar(select(User).where(User.username == "demo_student"))
        activities = db.execute(
            select(UserActivity.activity_date, Problem.title)
            .join(Problem, UserActivity.problem_id == Problem.id)
            .where(UserActivity.user_id == student.id)
            .order_by(UserActivity.activity_date)
        ).all()
        assert activities == [
            (local_day() - timedelta(days=2), "两数之和"),
            (local_day() - timedelta(days=1), "奇偶判断"),
            (local_day(), "区间求和"),
        ]
        for problem in db.scalars(select(Problem)).all():
            cases = db.scalars(select(TestCase).where(TestCase.problem_id == problem.id)).all()
            assert any(case.is_sample for case in cases)
            assert any(not case.is_sample for case in cases)
            assert problem.tags


def test_second_seed_preserves_a_custom_admin_problem_and_catalog_case_counts(tmp_path):
    from app.database import session_scope
    from app.models import Problem, ProblemTag, Tag, TestCase
    from app.seed import seed_database
    from app.seed_catalog import PROBLEMS

    database_url = f"sqlite:///{tmp_path / 'custom-problem.db'}"
    seed_database(database_url)
    catalog_titles = {problem.title for problem in PROBLEMS}
    expected_catalog_cases = sum(len(problem.cases) for problem in PROBLEMS)

    with session_scope(database_url) as db:
        sentinel_tag = Tag(name="custom-admin-sentinel-tag")
        custom = Problem(
            title="管理员自定义 sentinel 题目",
            statement="custom statement sentinel",
            input_markdown="custom input sentinel",
            output_markdown="custom output sentinel",
            difficulty="medium",
            time_limit_ms=4321,
            published=False,
            revision=17,
        )
        custom.tags = [ProblemTag(tag=sentinel_tag)]
        custom.test_cases = [
            TestCase(
                position=7,
                input_data="custom input bytes\n",
                output_data="custom output bytes\n",
                is_sample=False,
            )
        ]
        db.add(custom)
        db.commit()
        custom_id = custom.id

    with session_scope(database_url) as db:
        custom_before = _problem_snapshot(db, custom_id)
        catalog_cases_before = db.scalar(
            select(func.count())
            .select_from(TestCase)
            .join(Problem, TestCase.problem_id == Problem.id)
            .where(Problem.title.in_(catalog_titles))
        )

    seed_database(database_url)

    with session_scope(database_url) as db:
        assert db.scalar(select(func.count()).select_from(Problem)) == 101
        assert all(
            db.scalar(select(func.count()).select_from(Problem).where(Problem.title == title)) == 1
            for title in catalog_titles
        )
        assert db.scalar(
            select(func.count())
            .select_from(TestCase)
            .join(Problem, TestCase.problem_id == Problem.id)
            .where(Problem.title.in_(catalog_titles))
        ) == catalog_cases_before == expected_catalog_cases
        assert _problem_snapshot(db, custom_id) == custom_before


def test_seed_preserves_a_custom_problem_that_collides_with_a_catalog_title(tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base, Problem, ProblemTag, Tag, TestCase
    from app.seed import seed_database
    from app.seed_catalog import PROBLEMS

    database_url = f"sqlite:///{tmp_path / 'title-collision.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        collision = Problem(
            title="Dijkstra 最短路",
            statement="collision statement sentinel",
            input_markdown="collision input sentinel",
            output_markdown="collision output sentinel",
            difficulty="easy",
            time_limit_ms=4999,
            published=False,
            revision=23,
        )
        collision.tags = [ProblemTag(tag=Tag(name="collision-sentinel-tag"))]
        collision.test_cases = [
            TestCase(
                position=9,
                input_data="collision input bytes\n",
                output_data="collision output bytes\n",
                is_sample=False,
            )
        ]
        db.add(collision)
        db.commit()
        collision_id = collision.id

    with session_scope(database_url) as db:
        collision_before = _problem_snapshot(db, collision_id)

    seed_database(database_url)

    catalog_titles = {problem.title for problem in PROBLEMS}
    with session_scope(database_url) as db:
        assert _problem_snapshot(db, collision_id) == collision_before
        assert db.scalar(
            select(func.count()).select_from(Problem).where(Problem.title == "Dijkstra 最短路")
        ) == 1
        assert db.scalar(select(func.count()).select_from(Problem)) == 100
        inserted_titles = set(
            db.scalars(select(Problem.title).where(Problem.id != collision_id)).all()
        )
        assert inserted_titles == catalog_titles - {"Dijkstra 最短路"}


@pytest.mark.parametrize("title", ("两数之和", "奇偶判断", "区间求和", "最大公约数"))
def test_seed_does_not_attach_demo_history_to_custom_historical_title_collision(title, tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base, Problem, ProblemTag, Submission, Tag, TestCase, UserActivity
    from app.seed import seed_database

    database_url = f"sqlite:///{tmp_path / 'historical-title-collision.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        collision = Problem(
            title=title,
            statement="collision statement sentinel",
            input_markdown="collision input sentinel",
            output_markdown="collision output sentinel",
            difficulty="hard",
            time_limit_ms=4999,
            published=False,
            revision=23,
        )
        collision.tags = [ProblemTag(tag=Tag(name="collision-sentinel-tag"))]
        collision.test_cases = [
            TestCase(
                position=9,
                input_data="collision input bytes\n",
                output_data="collision output bytes\n",
                is_sample=False,
            )
        ]
        db.add(collision)
        db.commit()
        collision_id = collision.id

    with session_scope(database_url) as db:
        collision_before = _problem_snapshot(db, collision_id)

    seed_database(database_url)

    with session_scope(database_url) as db:
        assert _problem_snapshot(db, collision_id) == collision_before
        assert db.scalar(
            select(func.count()).select_from(Submission).where(Submission.problem_id == collision_id)
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(UserActivity).where(UserActivity.problem_id == collision_id)
        ) == 0


@pytest.mark.parametrize("title", ("两数之和", "奇偶判断", "区间求和", "最大公约数"))
def test_seed_skips_demo_history_for_every_row_with_a_duplicate_historical_title(title, tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base, Problem, Submission, UserActivity
    from app.seed import seed_database
    from app.seed_catalog import PROBLEMS

    database_url = f"sqlite:///{tmp_path / 'duplicate-historical-title.db'}"
    data = next(problem for problem in PROBLEMS if problem.title == title)
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        duplicates = (_add_catalog_problem(db, data), _add_catalog_problem(db, data))
        db.commit()
        duplicate_ids = tuple(problem.id for problem in duplicates)

    with session_scope(database_url) as db:
        before = {problem_id: _problem_snapshot(db, problem_id) for problem_id in duplicate_ids}

    seed_database(database_url)

    with session_scope(database_url) as db:
        assert db.scalar(
            select(func.count()).select_from(Problem).where(Problem.title == title)
        ) == 2
        assert {problem_id: _problem_snapshot(db, problem_id) for problem_id in duplicate_ids} == before
        assert db.scalar(
            select(func.count()).select_from(Submission).where(Submission.problem_id.in_(duplicate_ids))
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(UserActivity).where(UserActivity.problem_id.in_(duplicate_ids))
        ) == 0


def test_seed_does_not_merge_or_delete_arbitrary_preexisting_duplicate_titles(tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base, Problem, TestCase
    from app.seed import seed_database

    database_url = f"sqlite:///{tmp_path / 'preexisting-duplicates.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        duplicates = []
        for marker in ("first", "second"):
            problem = Problem(
                title="Dijkstra 最短路",
                statement=f"{marker} duplicate statement sentinel",
                input_markdown=f"{marker} duplicate input sentinel",
                output_markdown=f"{marker} duplicate output sentinel",
                difficulty="hard",
                time_limit_ms=1000,
                published=False,
                revision=7,
            )
            problem.test_cases = [
                TestCase(
                    position=1,
                    input_data=f"{marker} duplicate input bytes\n",
                    output_data=f"{marker} duplicate output bytes\n",
                    is_sample=False,
                )
            ]
            db.add(problem)
            duplicates.append(problem)
        db.commit()
        duplicate_ids = tuple(problem.id for problem in duplicates)

    with session_scope(database_url) as db:
        before = {problem_id: _problem_snapshot(db, problem_id) for problem_id in duplicate_ids}

    seed_database(database_url)

    with session_scope(database_url) as db:
        assert db.scalar(
            select(func.count()).select_from(Problem).where(Problem.title == "Dijkstra 最短路")
        ) == 2
        assert {problem_id: _problem_snapshot(db, problem_id) for problem_id in duplicate_ids} == before


def test_nine_problem_database_migrates_insert_only_and_preserves_admin_edits(monkeypatch, tmp_path):
    import app.seed as seed
    from app.database import session_scope
    from app.models import Problem, ProblemTag, Submission, Tag, TestCase
    from app.seed_catalog import PROBLEMS

    database_url = f"sqlite:///{tmp_path / 'nine-to-one-hundred.db'}"
    full_catalog = PROBLEMS
    legacy_catalog = tuple(problem for problem in full_catalog if problem.legacy)
    assert len(legacy_catalog) == 9
    monkeypatch.setattr(seed, "PROBLEMS", legacy_catalog)
    seed.seed_database(database_url)

    with session_scope(database_url) as db:
        edited = db.scalar(select(Problem).where(Problem.title == "两数之和"))
        edited.statement = "administrator sentinel statement"
        edited.input_markdown = "administrator sentinel input markdown"
        edited.output_markdown = "administrator sentinel output markdown"
        edited.time_limit_ms = 4321
        edited.published = False
        edited.revision = 19
        sentinel_tag = Tag(name="administrator-sentinel-tag")
        edited.tags = [ProblemTag(tag=sentinel_tag)]
        edited.test_cases = [
            TestCase(
                position=11,
                input_data="administrator sentinel case input\n",
                output_data="administrator sentinel case output\n",
                is_sample=False,
            )
        ]
        historical = db.scalar(
            select(Submission).where(Submission.problem_id == edited.id).order_by(Submission.id)
        )
        assert historical is not None
        db.commit()
        legacy_ids = tuple(db.scalars(select(Problem.id).order_by(Problem.id)).all())

    with session_scope(database_url) as db:
        protected_before = {problem_id: _problem_snapshot(db, problem_id) for problem_id in legacy_ids}

    monkeypatch.setattr(seed, "PROBLEMS", full_catalog)
    seed.seed_database(database_url)

    with session_scope(database_url) as db:
        assert {problem_id: _problem_snapshot(db, problem_id) for problem_id in legacy_ids} == protected_before
        assert db.scalar(select(func.count()).select_from(Problem)) == 100
        assert set(db.scalars(select(Problem.title)).all()) == {problem.title for problem in full_catalog}
        assert db.scalar(select(func.count()).select_from(Problem).where(Problem.id.not_in(legacy_ids))) == 91


def test_seed_repairs_the_exact_old_grid_once_and_preserves_history(tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base
    from app.seed import seed_database

    database_url = f"sqlite:///{tmp_path / 'legacy-grid-repair.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        old_grid = _add_exact_old_grid(db, with_submission=True)
        db.commit()
        old_grid_id = old_grid.id

    with session_scope(database_url) as db:
        before = _problem_snapshot(db, old_grid_id)

    seed_database(database_url)

    with session_scope(database_url) as db:
        after = _problem_snapshot(db, old_grid_id)

    expected_problem = list(before["problem"])
    expected_problem[8] = 2
    expected_problem[10] = after["problem"][10]
    expected_cases = list(before["cases"])
    corrected_hidden = list(expected_cases[1])
    corrected_hidden[3] = "5\n"
    expected_cases[1] = tuple(corrected_hidden)
    assert after == {
        **before,
        "problem": tuple(expected_problem),
        "cases": tuple(expected_cases),
    }
    assert after["submissions"] == before["submissions"]
    assert after["submissions"][0][6] == 1
    assert after["problem"][10] >= before["problem"][10]

    seed_database(database_url)

    with session_scope(database_url) as db:
        assert _problem_snapshot(db, old_grid_id) == after


def test_seed_repairs_the_exact_old_grid_when_tag_ids_reverse_the_expected_order(tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base, Tag
    from app.seed import seed_database

    database_url = f"sqlite:///{tmp_path / 'legacy-grid-reversed-tag-ids.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        db.add(Tag(name="网格"))
        db.flush()
        db.add(Tag(name="动态规划"))
        db.flush()
        old_grid = _add_exact_old_grid(db)
        db.commit()
        old_grid_id = old_grid.id

    with session_scope(database_url) as db:
        before = _problem_snapshot(db, old_grid_id)
        assert tuple(name for _tag_id, name in before["tags"]) == ("网格", "动态规划")

    seed_database(database_url)

    with session_scope(database_url) as db:
        after = _problem_snapshot(db, old_grid_id)

    expected_problem = list(before["problem"])
    expected_problem[8] = 2
    expected_problem[10] = after["problem"][10]
    expected_cases = list(before["cases"])
    corrected_hidden = list(expected_cases[1])
    corrected_hidden[3] = "5\n"
    expected_cases[1] = tuple(corrected_hidden)
    assert after == {
        **before,
        "problem": tuple(expected_problem),
        "cases": tuple(expected_cases),
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "revision",
        "statement",
        "input_markdown",
        "output_markdown",
        "difficulty",
        "published",
        "time_limit_ms",
        "tag_replacement",
        "extra_tag",
        "case_position",
        "case_input",
        "case_output",
        "case_is_sample",
        "extra_case",
        "missing_case",
        "non_target_title",
    ],
)
def test_legacy_grid_repair_rejects_every_partial_signature_match(mutation, tmp_path):
    from app.database import make_engine, session_scope
    from app.models import Base, ProblemTag, Tag, TestCase
    from app.seed import seed_database

    database_url = f"sqlite:///{tmp_path / f'grid-guard-{mutation}.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        old_grid = _add_exact_old_grid(db)
        if mutation == "revision":
            old_grid.revision = 2
        elif mutation == "statement":
            old_grid.statement += " sentinel"
        elif mutation == "input_markdown":
            old_grid.input_markdown += " sentinel"
        elif mutation == "output_markdown":
            old_grid.output_markdown += " sentinel"
        elif mutation == "difficulty":
            old_grid.difficulty = "medium"
        elif mutation == "published":
            old_grid.published = False
        elif mutation == "time_limit_ms":
            old_grid.time_limit_ms = 1001
        elif mutation == "tag_replacement":
            old_grid.tags = [ProblemTag(tag=Tag(name="replacement-sentinel-tag"))]
        elif mutation == "extra_tag":
            old_grid.tags.append(ProblemTag(tag=Tag(name="extra-sentinel-tag")))
        elif mutation == "case_position":
            old_grid.test_cases[1].position = 3
        elif mutation == "case_input":
            old_grid.test_cases[1].input_data += "sentinel\n"
        elif mutation == "case_output":
            old_grid.test_cases[1].output_data = "999\n"
        elif mutation == "case_is_sample":
            old_grid.test_cases[1].is_sample = True
        elif mutation == "extra_case":
            old_grid.test_cases.append(
                TestCase(position=3, input_data="extra\n", output_data="extra\n", is_sample=False)
            )
        elif mutation == "missing_case":
            db.delete(old_grid.test_cases[1])
        elif mutation == "non_target_title":
            old_grid.title = "非目标网格 sentinel"
        else:  # pragma: no cover - the parametrization is exhaustive
            raise AssertionError(mutation)
        db.commit()
        old_grid_id = old_grid.id

    with session_scope(database_url) as db:
        before = _problem_snapshot(db, old_grid_id)

    seed_database(database_url)

    with session_scope(database_url) as db:
        assert _problem_snapshot(db, old_grid_id) == before


def test_seed_rolls_back_all_staged_rows_when_tag_creation_fails(monkeypatch, tmp_path):
    import app.seed as seed
    from app.database import make_engine, session_scope
    from app.models import Problem, ProblemTag, Submission, Tag, TestCase, User, UserActivity

    database_url = f"sqlite:///{tmp_path / 'fresh-seed-rollback.db'}"
    original_tag = seed._tag

    def fail_after_a_problem_was_flushed(db, name):
        tag = original_tag(db, name)
        if db.scalar(select(func.count()).select_from(Problem)) >= 3:
            raise RuntimeError("sentinel tag failure after several problem flushes")
        return tag

    monkeypatch.setattr(seed, "_tag", fail_after_a_problem_was_flushed)
    with pytest.raises(RuntimeError, match="sentinel tag failure"):
        seed.seed_database(database_url)

    engine = make_engine(database_url)
    assert {
        "users",
        "tags",
        "problems",
        "problem_tags",
        "test_cases",
        "submissions",
        "user_activities",
    } <= set(inspect(engine).get_table_names())
    with session_scope(database_url) as db:
        for model in (User, Tag, Problem, ProblemTag, TestCase, Submission, UserActivity):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_seed_rolls_back_a_staged_legacy_grid_repair_when_later_tag_creation_fails(monkeypatch, tmp_path):
    import app.seed as seed
    from app.database import make_engine, session_scope
    from app.models import Base

    database_url = f"sqlite:///{tmp_path / 'repair-rollback.db'}"
    Base.metadata.create_all(make_engine(database_url))
    with session_scope(database_url) as db:
        old_grid = _add_exact_old_grid(db)
        db.commit()
        old_grid_id = old_grid.id

    with session_scope(database_url) as db:
        before = _problem_snapshot(db, old_grid_id)

    original_tag = seed._tag

    def fail_after_repair_was_staged(db, name):
        original_tag(db, name)
        raise RuntimeError("sentinel failure after repair")

    monkeypatch.setattr(seed, "_tag", fail_after_repair_was_staged)
    with pytest.raises(RuntimeError, match="sentinel failure after repair"):
        seed.seed_database(database_url)

    with session_scope(database_url) as db:
        assert _problem_snapshot(db, old_grid_id) == before
        assert _problem_snapshot(db, old_grid_id)["problem"][8] == 1
        assert _problem_snapshot(db, old_grid_id)["cases"][1][3] == "6\n"


def test_seed_main_reports_the_final_100_problem_catalog(monkeypatch, capsys):
    import app.seed as seed

    monkeypatch.setattr(seed, "seed_database", lambda: None)
    seed.main()

    assert "100 problems" in capsys.readouterr().out


def test_readme_describes_the_100_problem_catalog_and_security_boundary():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "内置目录共 100 道中文题" in readme
    assert "40 简单" in readme
    assert "35 中等" in readme
    assert "25 困难" in readme
    assert "不是安全沙箱" in readme
    assert "受信任的本地教学代码" in readme
    assert "绝不能接收不受信任的代码" in readme
    assert "绝不能部署到公网" in readme
    assert "多租户服务" in readme


def test_problem_bank_design_uses_the_accurate_legacy_and_easy_coverage_terms():
    design = (
        PROJECT_ROOT / "docs" / "superpowers" / "specs" / "2026-07-28-problem-bank-expansion-design.md"
    ).read_text(encoding="utf-8")

    assert "简单模拟 7 道" in design
    assert "扩充前的 9 道演示题" in design
    assert "函数与简单模拟" not in design
    assert "当前 9 道演示题" not in design


def test_playwright_problem_probe_uses_same_origin_api_path():
    campus_spec = (PROJECT_ROOT / "frontend" / "e2e" / "campus.spec.ts").read_text(encoding="utf-8")
    assert "page.request.get('/api/problems/1')" in campus_spec
    assert "http://127.0.0.1:8000/api/problems/1" not in campus_spec


def test_static_spa_fallback_serves_build_but_never_shadows_api(monkeypatch, tmp_path):
    from app import create_app
    from starlette import responses as starlette_responses

    original_guess_type = starlette_responses.guess_type

    def registry_hostile_guess_type(url, strict=True):
        if str(url).lower().endswith(".js"):
            return "text/plain", None
        return original_guess_type(url, strict=strict)

    monkeypatch.setattr(starlette_responses, "guess_type", registry_hostile_guess_type)

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<main>OJ Campus build</main>", encoding="utf-8")
    (dist / "asset.js").write_text("console.log('asset')", encoding="utf-8")
    app = create_app(f"sqlite:///{tmp_path / 'static.db'}", frontend_dist=dist)
    with TestClient(app) as client:
        assert client.get("/problems/42").text == "<main>OJ Campus build</main>"
        asset = client.get("/asset.js")
        assert asset.text == "console.log('asset')"
        assert asset.headers["content-type"].split(";", 1)[0] == "application/javascript"
        api = client.get("/api/not-a-route")
    assert api.status_code == 404
    assert api.json()["code"] == "not_found"


def test_missing_frontend_build_has_clear_response(tmp_path):
    from app import create_app

    app = create_app(f"sqlite:///{tmp_path / 'missing-build.db'}", frontend_dist=tmp_path / "missing")
    with TestClient(app) as client:
        response = client.get("/dashboard")
    assert response.status_code == 503
    assert response.json()["code"] == "frontend_build_missing"


def test_application_uses_configured_database_url(monkeypatch, tmp_path):
    from app import create_app

    database_url = f"sqlite:///{tmp_path / 'configured.db'}"
    monkeypatch.setenv("OJ_DATABASE_URL", database_url)
    app = create_app(frontend_dist=tmp_path / "missing")
    assert app.state.database_url == database_url
