from conftest import register


def admin_client(client):
    assert register(client, "admin_user", "admin@example.com").status_code == 201
    from app.database import session_scope
    from app.models import User

    with session_scope(client.app.state.database_url) as db:
        db.query(User).filter_by(username="admin_user").update({"role": "admin"})
        db.commit()
    return client


def problem_payload(**overrides):
    payload = {
        "title": "Sum A + B",
        "statement": "Compute the sum.",
        "input": "Two integers.",
        "output": "Their sum.",
        "difficulty": "easy",
        "time_limit_ms": 1000,
        "published": True,
        "tags": ["math"],
        "test_cases": [
            {"input": "1 2", "output": "3", "is_sample": True},
            {"input": "4 5", "output": "9", "is_sample": False},
        ],
    }
    payload.update(overrides)
    return payload


def test_student_cannot_use_admin_routes(client):
    assert register(client).status_code == 201
    response = client.get("/api/admin/dashboard")
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_published_filter_problem_filters_and_hidden_case_redaction(client):
    admin = admin_client(client)
    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    public = admin.post("/api/admin/problems", json=problem_payload()).json()
    assert admin.post(
        "/api/admin/problems", json=problem_payload(title="Secret", published=False, difficulty="hard", tags=[])
    ).status_code == 201
    admin.post("/api/auth/logout")

    listing = client.get("/api/problems", params={"keyword": "sum", "difficulty": "easy", "tag": "math"})
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [public["id"]]
    assert client.get("/api/problems", params={"difficulty": "hard"}).json()["total"] == 0
    detail = client.get(f"/api/problems/{public['id']}")
    assert detail.status_code == 200
    assert detail.json()["test_cases"] == [{"input": "1 2", "output": "3", "is_sample": True, "position": 1}]


def test_public_problem_tag_filter_matches_legacy_tag_regardless_of_case(client):
    from app.database import session_scope
    from app.models import Problem, ProblemTag, Tag, TestCase

    with session_scope(client.app.state.database_url) as db:
        legacy_tag = Tag(name="BFS")
        problem = Problem(
            title="Legacy breadth-first search",
            statement="Find the shortest path.",
            input_markdown="A graph.",
            output_markdown="The distance.",
            difficulty="easy",
            time_limit_ms=1000,
            published=True,
        )
        problem.tags = [ProblemTag(tag=legacy_tag)]
        problem.test_cases = [TestCase(position=1, input_data="1\n", output_data="1\n", is_sample=True)]
        db.add(problem)
        db.commit()
        problem_id = problem.id

    for tag in ("BFS", "bfs"):
        response = client.get("/api/problems", params={"tag": tag})
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["items"]] == [problem_id]


def test_admin_problem_assignment_reuses_legacy_tag_regardless_of_case(client):
    from app.database import session_scope
    from app.models import Tag

    admin = admin_client(client)
    with session_scope(client.app.state.database_url) as db:
        legacy_tag = Tag(name="BFS")
        db.add(legacy_tag)
        db.commit()
        legacy_tag_id = legacy_tag.id

    response = admin.post("/api/admin/problems", json=problem_payload(tags=["bfs"]))
    assert response.status_code == 201
    assert response.json()["tags"] == ["BFS"]
    with session_scope(client.app.state.database_url) as db:
        assert [tag.id for tag in db.query(Tag).order_by(Tag.id)] == [legacy_tag_id]


def test_admin_tag_create_and_update_reject_legacy_case_variants(client):
    from app.database import session_scope
    from app.models import Tag

    admin = admin_client(client)
    with session_scope(client.app.state.database_url) as db:
        legacy_tag = Tag(name="BFS")
        editable_tag = Tag(name="graphs")
        db.add_all([legacy_tag, editable_tag])
        db.commit()
        editable_tag_id = editable_tag.id

    updated = admin.patch(f"/api/admin/tags/{editable_tag_id}", json={"name": "bfs"})
    assert updated.status_code == 409
    assert updated.json()["code"] == "tag_taken"
    created = admin.post("/api/admin/tags", json={"name": "bfs"})
    assert created.status_code == 409
    assert created.json()["code"] == "tag_taken"


def test_seed_tag_reuses_legacy_case_variant(client):
    from app.database import session_scope
    from app.models import Tag
    from app.seed import _tag

    with session_scope(client.app.state.database_url) as db:
        legacy_tag = Tag(name="BFS")
        db.add(legacy_tag)
        db.commit()
        assert _tag(db, "bfs").id == legacy_tag.id
        assert db.query(Tag).count() == 1


def test_case_variant_tags_are_reused_deterministically_without_duplicate_public_results(client):
    from app import unique_tags
    from app.database import session_scope
    from app.models import Problem, ProblemTag, Tag
    from app.seed import _tag

    def published_problem(title, tags):
        problem = Problem(
            title=title,
            statement="Find a path.",
            input_markdown="A graph.",
            output_markdown="The distance.",
            difficulty="easy",
            time_limit_ms=1000,
            published=True,
        )
        problem.tags = [ProblemTag(tag=tag) for tag in tags]
        return problem

    with session_scope(client.app.state.database_url) as db:
        upper_bfs = Tag(name="BFS")
        lower_bfs = Tag(name="bfs")
        math = Tag(name="math")
        editable = Tag(name="graphs")
        first_problem = published_problem("Two legacy BFS tags", [upper_bfs, lower_bfs])
        second_problem = published_problem("One lower BFS tag", [lower_bfs])
        db.add_all([upper_bfs, lower_bfs, math, editable, first_problem, second_problem])
        db.commit()
        upper_bfs_id = upper_bfs.id
        math_id = math.id
        editable_id = editable.id
        first_problem_id = first_problem.id
        second_problem_id = second_problem.id
        original_tags = [(tag.id, tag.name) for tag in db.query(Tag).order_by(Tag.id)]

        assert [tag.id for tag in unique_tags(db, ["math", "bfs", "BFS"])] == [math_id, upper_bfs_id]
        assert _tag(db, "bfs").id == upper_bfs_id

    first_page = client.get("/api/problems", params={"tag": "bfs", "page_size": 1, "page": 1}).json()
    second_page = client.get("/api/problems", params={"tag": "bfs", "page_size": 1, "page": 2}).json()
    assert first_page["total"] == 2
    assert [item["id"] for item in first_page["items"]] == [first_problem_id]
    assert [item["id"] for item in second_page["items"]] == [second_problem_id]

    admin = admin_client(client)
    created = admin.post("/api/admin/problems", json=problem_payload(title="Reuse one BFS tag", tags=["bfs"]))
    assert created.status_code == 201
    assert created.json()["tags"] == ["BFS"]
    assert admin.post("/api/admin/tags", json={"name": "bfs"}).status_code == 409
    assert admin.patch(f"/api/admin/tags/{editable_id}", json={"name": "bfs"}).status_code == 409

    with session_scope(client.app.state.database_url) as db:
        assert [(tag.id, tag.name) for tag in db.query(Tag).order_by(Tag.id)] == original_tags
        assert [tag_id for tag_id, in db.query(ProblemTag.tag_id).filter_by(problem_id=created.json()["id"])] == [upper_bfs_id]


def test_admin_crud_and_revision_changes_only_for_judging_data(client):
    admin = admin_client(client)
    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    created = admin.post("/api/admin/problems", json=problem_payload()).json()
    assert created["revision"] == 1

    statement_edit = admin.patch(
        f"/api/admin/problems/{created['id']}", json={"title": "Sum two numbers", "tags": ["math"]}
    )
    assert statement_edit.status_code == 200
    assert statement_edit.json()["revision"] == 1

    limit_edit = admin.patch(f"/api/admin/problems/{created['id']}", json={"time_limit_ms": 2000})
    assert limit_edit.status_code == 200
    assert limit_edit.json()["revision"] == 2

    case_edit = admin.patch(
        f"/api/admin/problems/{created['id']}",
        json={"test_cases": [{"input": "7 8", "output": "15", "is_sample": False}]},
    )
    assert case_edit.status_code == 200
    assert case_edit.json()["revision"] == 3
    assert case_edit.json()["test_cases"][0]["output"] == "15"


def test_problem_update_rejects_empty_or_explicit_null_fields(client):
    from fastapi.testclient import TestClient

    admin = admin_client(client)
    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    problem_id = admin.post("/api/admin/problems", json=problem_payload()).json()["id"]

    with TestClient(client.app, raise_server_exceptions=False) as no_raise_client:
        no_raise_client.cookies.update(client.cookies)
        empty = no_raise_client.patch(f"/api/admin/problems/{problem_id}", json={})
        null_title = no_raise_client.patch(f"/api/admin/problems/{problem_id}", json={"title": None})

    for response in (empty, null_title):
        assert response.status_code == 422
        assert response.json()["code"] == "validation_error"
        assert response.json()["field_errors"]


def test_deleting_a_problem_referenced_by_a_submission_returns_standard_conflict(client):
    from fastapi.testclient import TestClient

    admin = admin_client(client)
    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    problem_id = admin.post("/api/admin/problems", json=problem_payload()).json()["id"]
    from app.database import session_scope
    from app.models import Submission, User

    with session_scope(client.app.state.database_url) as db:
        user_id = db.query(User.id).filter_by(username="admin_user").scalar()
        db.add(Submission(user_id=user_id, problem_id=problem_id, source="print(1)", language="python", status="queued"))
        db.commit()

    with TestClient(client.app, raise_server_exceptions=False) as no_raise_client:
        no_raise_client.cookies.update(client.cookies)
        response = no_raise_client.delete(f"/api/admin/problems/{problem_id}")

    assert response.status_code == 409
    assert response.json() == {"code": "conflict", "message": "Resource is still referenced"}


def test_problem_filters_pagination_and_anonymous_solved_semantics(client):
    admin = admin_client(client)
    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    first = admin.post("/api/admin/problems", json=problem_payload(title="Sum one")).json()
    second = admin.post("/api/admin/problems", json=problem_payload(title="Sum two")).json()
    admin.post("/api/auth/logout")
    assert register(client, "student_user", "student@example.com").status_code == 201

    from app.database import session_scope
    from app.models import Submission, User

    with session_scope(client.app.state.database_url) as db:
        user_id = db.query(User.id).filter_by(username="student_user").scalar()
        db.add(Submission(user_id=user_id, problem_id=first["id"], source="int main(){}", language="cpp17", status="AC", problem_revision=1))
        db.commit()

    combined = client.get("/api/problems", params={"keyword": "sum", "difficulty": "easy", "tag": "math", "page": 1, "page_size": 1})
    assert combined.json()["total"] == 2
    assert [item["id"] for item in combined.json()["items"]] == [first["id"]]
    assert [item["id"] for item in client.get("/api/problems", params={"solved": True}).json()["items"]] == [first["id"]]
    assert [item["id"] for item in client.get("/api/problems", params={"solved": False}).json()["items"]] == [second["id"]]

    client.post("/api/auth/logout")
    assert client.get("/api/problems", params={"solved": True}).json()["total"] == 0
    assert client.get("/api/problems", params={"solved": False}).json()["total"] == 2


def test_tag_crud_and_admin_user_submission_dashboard_success_paths(client):
    admin = admin_client(client)
    tag = admin.post("/api/admin/tags", json={"name": "graphs"}).json()
    assert admin.get("/api/admin/tags").json()[0]["id"] == tag["id"]
    assert admin.patch(f"/api/admin/tags/{tag['id']}", json={"name": "graph-theory"}).json()["name"] == "graph-theory"
    assert admin.delete(f"/api/admin/tags/{tag['id']}").status_code == 204

    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    problem = admin.post("/api/admin/problems", json=problem_payload()).json()
    from app.database import session_scope
    from app.models import Submission, User

    with session_scope(client.app.state.database_url) as db:
        user_id = db.query(User.id).filter_by(username="admin_user").scalar()
        submission = Submission(user_id=user_id, problem_id=problem["id"], source="print(3)", language="python", status="queued")
        db.add(submission)
        db.commit()
        submission_id = submission.id

    users = admin.get("/api/admin/users")
    submission = admin.get(f"/api/admin/submissions/{submission_id}")
    dashboard = admin.get("/api/admin/dashboard")
    assert users.status_code == 200 and users.json()["total"] == 1
    assert submission.json()["source"] == "print(3)"
    assert dashboard.json() == {"users": 1, "problems": 1, "submissions": 1}


def test_problem_crud_success_paths(client):
    admin = admin_client(client)
    assert admin.post("/api/admin/tags", json={"name": "math"}).status_code == 201
    created = admin.post("/api/admin/problems", json=problem_payload()).json()

    assert [problem["id"] for problem in admin.get("/api/admin/problems").json()] == [created["id"]]
    assert admin.get(f"/api/admin/problems/{created['id']}").json()["title"] == "Sum A + B"
    assert admin.patch(f"/api/admin/problems/{created['id']}", json={"published": False}).status_code == 200
    assert admin.delete(f"/api/admin/problems/{created['id']}").status_code == 204
    assert admin.get("/api/admin/problems").json() == []


def test_concurrent_duplicate_tag_creations_return_a_standard_conflict(client):
    from concurrent.futures import ThreadPoolExecutor

    from fastapi.testclient import TestClient

    admin_client(client)

    def create_once():
        with TestClient(client.app, raise_server_exceptions=False) as race_client:
            race_client.cookies.update(client.cookies)
            return race_client.post("/api/admin/tags", json={"name": "race-tag"})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _index: create_once(), range(2)))

    assert sorted(response.status_code for response in responses) == [201, 409]
    assert next(response for response in responses if response.status_code == 409).json()["code"] == "tag_taken"
