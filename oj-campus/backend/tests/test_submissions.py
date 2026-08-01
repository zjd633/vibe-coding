from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

import pytest

from conftest import register


def real_gpp() -> str:
    from app.judge import GPP_PATH

    compiler = Path(os.environ.get("OJ_GPP_PATH", GPP_PATH))
    if not compiler.is_file():
        pytest.skip(f"g++ not found: {compiler}")
    return str(compiler)


def make_problem(client, published=True, time_limit_ms=1000):
    from test_problems import admin_client, problem_payload
    admin = admin_client(client)
    admin.post("/api/admin/tags", json={"name": "math"})
    return admin.post("/api/admin/problems", json=problem_payload(published=published, time_limit_ms=time_limit_ms)).json(), admin


def test_submission_creation_tracks_revision_and_redacts_public_data(client):
    problem, admin = make_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    created = client.post("/api/submissions", json={"problem_id": problem["id"], "language": "cpp17", "source": "int main(){}"})
    assert created.status_code == 201
    assert created.json()["status"] == "PENDING"
    assert created.json()["problem_revision"] == 1
    assert client.get(f"/api/submissions/{created.json()['id']}").json()["source"] == "int main(){}"
    public = client.get("/api/submissions").json()["items"][0]
    assert "source" not in public and "details" not in public


def test_submission_rejects_unpublished_invalid_and_more_than_three_outstanding(client):
    hidden, admin = make_problem(client, published=False)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    body = {"problem_id": hidden["id"], "language": "cpp17", "source": "int main(){}"}
    assert client.post("/api/submissions", json=body).status_code == 404
    body["problem_id"] = 99999
    assert client.post("/api/submissions", json=body).status_code == 404
    body["language"] = "python"
    assert client.post("/api/submissions", json=body).status_code == 422
    from app.database import session_scope
    from app.models import Problem
    with session_scope(client.app.state.database_url) as db:
        db.get(Problem, hidden["id"]).published = True
        db.commit()
    body.update(problem_id=hidden["id"], language="cpp17")
    for _ in range(3):
        assert client.post("/api/submissions", json=body).status_code == 201
    assert client.post("/api/submissions", json=body).status_code == 429


def test_normalization_and_worker_verdicts_and_cleanup(tmp_path):
    from app.judge import JudgeResult, normalize_output, run_submission
    assert normalize_output("A  B\r\nX \n\n") == "A  B\nX"
    assert normalize_output("A b") != normalize_output("a b")
    source = "#include <iostream>\nint main(){std::cout << \"ok  \\n\";}"
    result = run_submission(source, [("", "ok\n")], 1000, tmp_path, compiler=real_gpp())
    assert result.status == "AC"
    assert not list(tmp_path.iterdir())
    assert JudgeResult("WA", 1, 1, "").status == "WA"


def test_real_gpp_verdicts_cover_first_failure_categories(tmp_path):
    from app.judge import run_submission
    compiler = real_gpp()
    assert run_submission("not c++", [("", "")], 1000, tmp_path, compiler).status == "CE"
    assert run_submission("int main(){return 4;}", [("", "")], 1000, tmp_path, compiler).status == "RE"
    assert run_submission("#include <iostream>\nint main(){std::cout<<\"wrong\";}", [("", "right")], 1000, tmp_path, compiler).status == "WA"
    assert run_submission("int main(){for(;;);}", [("", "")], 100, tmp_path, compiler).status == "TLE"
    assert run_submission("#include <iostream>\nint main(){for(int i=0;i<1048577;i++)std::cout<<'x';}", [("", "")], 1000, tmp_path, compiler).status == "OLE"
    assert run_submission("int main(){}", [("", "")], 1000, tmp_path, r"Z:\missing\g++.exe").status == "SE"


def test_real_gpp_timeout_uses_psutil_process_tree_termination(tmp_path):
    import app.judge as judge
    assert judge.psutil is not None
    result = judge.run_submission(
        '#include <cstdlib>\nint main(){return std::system("cmd /c ping -n 5 127.0.0.1 > NUL");}',
        [("", "")], 100, tmp_path, compiler=real_gpp(),
    )
    assert result.status == "TLE"


def test_worker_claim_recovery_dashboard_and_leaderboard(client):
    from app.database import session_scope
    from app.judge import process_one, recover_stale_judging
    from app.models import Submission, User, UserActivity

    problem, admin = make_problem(client)
    admin.post("/api/auth/logout")
    assert register(client).status_code == 201
    created = client.post("/api/submissions", json={"problem_id": problem["id"], "language": "cpp17", "source": "#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b;}"})
    assert created.status_code == 201
    assert process_one(client.app.state.database_url, compiler=real_gpp()) == created.json()["id"]
    assert client.get(f"/api/submissions/{created.json()['id']}").json()["status"] == "AC"
    dash = client.get("/api/dashboard").json()
    assert dash["solved_count"] == 1 and dash["current_streak"] >= 1
    board = client.get("/api/leaderboard").json()
    assert board["items"][0]["username"] == "alice" and board["current_user_position"] == 1
    with session_scope(client.app.state.database_url) as db:
        stale = db.get(Submission, created.json()["id"])
        stale.status = "JUDGING"
        stale.judging_started_at = datetime.now(timezone.utc) - timedelta(minutes=6)
        db.commit()
    assert recover_stale_judging(client.app.state.database_url) == 1
