import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import default_database_url, make_engine, session_factory
from .errors import AppError
from .judge import WINDOWS_SANDBOX_WARNING
from .models import Base, Problem, ProblemTag, Session, Submission, Tag, TestCase, User, UserActivity, utcnow
from .schemas import LoginRequest, PasswordUpdate, ProblemCreate, ProblemUpdate, ProfileUpdate, RegisterRequest, SubmissionCreate, TagInput
from .security import hash_password, is_expired, new_session_token, session_expiry, token_digest, verify_password


LOGGER = logging.getLogger(__name__)


def user_data(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email, "display_name": user.display_name,
            "role": user.role, "is_active": user.is_active, "created_at": user.created_at}


def tag_data(tag: Tag) -> dict:
    return {"id": tag.id, "name": tag.name, "created_at": tag.created_at}


def case_data(case: TestCase) -> dict:
    return {"input": case.input_data, "output": case.output_data, "is_sample": case.is_sample, "position": case.position}


def normalized_tag_name(name: str) -> str:
    return name.strip().lower()


def matching_tag_query(name: str):
    return select(Tag).where(func.lower(Tag.name) == normalized_tag_name(name)).order_by(Tag.id)


def submission_data(submission: Submission, view: str = "public") -> dict:
    data = {"id": submission.id, "user_id": submission.user_id, "problem_id": submission.problem_id,
            "problem_revision": submission.problem_revision, "language": submission.language, "status": submission.status,
            "runtime_ms": submission.runtime_ms, "created_at": submission.created_at}
    if view in {"owner", "admin"}:
        data["failed_case"] = submission.failed_case
        data["source"] = submission.source
    if view == "owner":
        data["details"] = {
            "CE": "Compilation failed / 编译失败",
            "RE": "Runtime error",
            "TLE": "Time limit exceeded / 超出时间限制",
            "OLE": "Output limit exceeded / 超出输出限制",
            "SE": "Judge system error / 评测系统错误",
        }.get(submission.status)
    elif view == "admin":
        data["details"] = submission.details
    return data


def local_day(value: datetime | None = None) -> date:
    return date.today() if value is None else value.astimezone().date()


def problem_data(problem: Problem, include_cases: bool = False, public: bool = False) -> dict:
    data = {"id": problem.id, "title": problem.title, "statement": problem.statement,
            "input": problem.input_markdown, "output": problem.output_markdown, "difficulty": problem.difficulty,
            "time_limit_ms": problem.time_limit_ms, "published": problem.published, "revision": problem.revision,
            "created_at": problem.created_at, "updated_at": problem.updated_at,
            "tags": [item.tag.name for item in problem.tags]}
    if include_cases:
        cases = problem.test_cases
        if public:
            cases = [case for case in cases if case.is_sample]
        data["test_cases"] = [case_data(case) for case in cases]
    return data


def unique_tags(db: OrmSession, names: list[str]) -> list[Tag]:
    normalized = []
    for name in names:
        name = normalized_tag_name(name)
        if name and name not in normalized:
            normalized.append(name)
    tags = [db.scalar(matching_tag_query(name)) for name in normalized]
    missing = [name for name, tag in zip(normalized, tags) if tag is None]
    if missing:
        raise AppError(422, "invalid_tag", f"unknown tag: {missing[0]}", {"tags": "contains an unknown tag"})
    return [tag for tag in tags if tag is not None]


def replace_cases(problem: Problem, cases, db: OrmSession | None = None) -> None:
    problem.test_cases.clear()
    if db is not None:
        # Flush deletions before reusing (problem_id, position) unique keys.
        db.flush()
    problem.test_cases.extend(TestCase(position=index, input_data=case.input, output_data=case.output, is_sample=case.is_sample)
                              for index, case in enumerate(cases, start=1))


def create_app(database_url: str | None = None, frontend_dist: Path | str | None = None) -> FastAPI:
    LOGGER.warning(WINDOWS_SANDBOX_WARNING)
    database_url = database_url or os.environ.get("OJ_DATABASE_URL") or default_database_url()
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    app = FastAPI(title="OJ Campus API")
    app.state.database_url = database_url
    app.state.engine = engine

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, error: AppError):
        data = {"code": error.code, "message": error.message}
        if error.field_errors:
            data["field_errors"] = error.field_errors
        return JSONResponse(status_code=error.status_code, content=data)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_request: Request, _error: IntegrityError):
        return JSONResponse(status_code=409, content={"code": "conflict", "message": "Resource conflicts with existing data"})

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, _error: Exception):
        return JSONResponse(status_code=500, content={"code": "internal_error", "message": "Internal server error"})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, error: RequestValidationError):
        field_errors = {}
        for item in error.errors():
            location = [str(part) for part in item["loc"] if part not in {"body", "query", "path"}]
            field_errors[".".join(location) or "request"] = item["msg"]
        return JSONResponse(status_code=422, content={"code": "validation_error", "message": "Request validation failed", "field_errors": field_errors})

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, error: StarletteHTTPException):
        codes = {404: "not_found", 405: "method_not_allowed"}
        return JSONResponse(status_code=error.status_code, content={"code": codes.get(error.status_code, "http_error"), "message": str(error.detail)})

    def get_db():
        db = factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    Db = Annotated[OrmSession, Depends(get_db)]

    def current_user(db: Db, oj_session: str | None = Cookie(default=None)) -> User:
        if not oj_session:
            raise AppError(401, "authentication_required", "Authentication is required")
        session = db.scalar(select(Session).where(Session.token_hash == token_digest(oj_session)))
        if session is None or is_expired(session.expires_at):
            if session is not None:
                db.delete(session)
                db.commit()
            raise AppError(401, "authentication_required", "Session is invalid or expired")
        user = db.get(User, session.user_id)
        if user is None or not user.is_active:
            raise AppError(401, "authentication_required", "Session user is unavailable")
        return user

    def optional_user(response: Response, db: Db, oj_session: str | None = Cookie(default=None)) -> User | None:
        if not oj_session:
            return None
        session = db.scalar(select(Session).where(Session.token_hash == token_digest(oj_session)))
        if session is None or is_expired(session.expires_at):
            if session is not None:
                db.delete(session)
            response.delete_cookie("oj_session", httponly=True, samesite="lax")
            return None
        user = db.get(User, session.user_id)
        if user is None or not user.is_active:
            db.delete(session)
            response.delete_cookie("oj_session", httponly=True, samesite="lax")
            return None
        return user

    def admin_user(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role != "admin":
            raise AppError(403, "forbidden", "Administrator role is required")
        return user

    def set_session(response: Response, db: OrmSession, user: User) -> None:
        token = new_session_token()
        db.add(Session(token_hash=token_digest(token), user_id=user.id, expires_at=session_expiry()))
        response.set_cookie("oj_session", token, httponly=True, samesite="lax", secure=False, max_age=7 * 24 * 60 * 60)

    def flush_or_conflict(db: OrmSession, code: str, message: str, field_errors: dict[str, str] | None = None) -> None:
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise AppError(409, code, message, field_errors)

    @app.post("/api/auth/register", status_code=201)
    def register(payload: RegisterRequest, response: Response, db: Db):
        if db.scalar(select(User.id).where(User.username == payload.username)) is not None:
            raise AppError(409, "username_taken", "Username is already in use", {"username": "already in use"})
        if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
            raise AppError(409, "email_taken", "Email is already in use", {"email": "already in use"})
        user = User(username=payload.username, email=payload.email, display_name=payload.display_name,
                    password_hash=hash_password(payload.password))
        db.add(user)
        flush_or_conflict(db, "registration_conflict", "Username or email is already in use")
        set_session(response, db, user)
        return user_data(user)

    @app.post("/api/auth/login")
    def login(payload: LoginRequest, response: Response, db: Db):
        username = payload.username.strip().lower()
        user = db.scalar(select(User).where(User.username == username))
        if user is None or not user.is_active or not verify_password(user.password_hash, payload.password):
            raise AppError(401, "invalid_credentials", "Invalid username or password")
        set_session(response, db, user)
        return user_data(user)

    @app.post("/api/auth/logout", status_code=204)
    def logout(response: Response, db: Db, oj_session: str | None = Cookie(default=None)):
        if oj_session:
            session = db.scalar(select(Session).where(Session.token_hash == token_digest(oj_session)))
            if session:
                db.delete(session)
        response.delete_cookie("oj_session", httponly=True, samesite="lax")
        response.status_code = 204
        return response

    @app.get("/api/auth/me")
    def me(user: Annotated[User, Depends(current_user)]):
        return user_data(user)

    @app.get("/api/auth/session")
    def session_state(user: Annotated[User | None, Depends(optional_user)]):
        """Return the current user or null without turning anonymous startup into a browser error."""
        return user_data(user) if user is not None else None

    @app.patch("/api/auth/profile")
    def update_profile(payload: ProfileUpdate, user: Annotated[User, Depends(current_user)], db: Db):
        if payload.email is not None and payload.email != user.email:
            if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
                raise AppError(409, "email_taken", "Email is already in use", {"email": "already in use"})
            user.email = payload.email
        if payload.display_name is not None:
            user.display_name = payload.display_name
        return user_data(user)

    @app.patch("/api/auth/password", status_code=204)
    def update_password(payload: PasswordUpdate, user: Annotated[User, Depends(current_user)], db: Db):
        if not verify_password(user.password_hash, payload.current_password):
            raise AppError(400, "invalid_credentials", "Current password is incorrect")
        user.password_hash = hash_password(payload.new_password)
        db.query(Session).filter(Session.user_id == user.id).delete(synchronize_session=False)
        return Response(status_code=204)

    @app.get("/api/problems")
    def list_problems(db: Db, user: Annotated[User | None, Depends(optional_user)], page: int = 1, page_size: int = 20,
                      keyword: str | None = None, difficulty: str | None = None, tag: str | None = None, solved: bool | None = None):
        if page < 1 or not 1 <= page_size <= 100:
            raise AppError(422, "validation_error", "Invalid pagination", {"page": "must be >= 1", "page_size": "must be 1-100"})
        query = select(Problem).options(joinedload(Problem.tags).joinedload(ProblemTag.tag)).where(Problem.published.is_(True))
        if keyword:
            query = query.where(Problem.title.ilike(f"%{keyword.strip()}%"))
        if difficulty:
            if difficulty not in {"easy", "medium", "hard"}:
                raise AppError(422, "validation_error", "Invalid difficulty", {"difficulty": "must be easy, medium, or hard"})
            query = query.where(Problem.difficulty == difficulty)
        if tag:
            query = query.where(Problem.tags.any(ProblemTag.tag.has(func.lower(Tag.name) == normalized_tag_name(tag))))
        if solved is not None:
            if user is None and solved:
                return {"items": [], "page": page, "page_size": page_size, "total": 0}
            if user is not None:
                accepted_ids = select(Submission.problem_id).join(Problem).where(
                    Submission.user_id == user.id, Submission.status == "AC", Submission.problem_revision == Problem.revision)
                query = query.where(Problem.id.in_(accepted_ids) if solved else Problem.id.not_in(accepted_ids))
        total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
        problems = db.scalars(query.order_by(Problem.id).offset((page - 1) * page_size).limit(page_size)).unique().all()
        return {"items": [problem_data(problem) for problem in problems], "page": page, "page_size": page_size, "total": total}

    @app.get("/api/problems/{problem_id}")
    def get_problem(problem_id: int, db: Db):
        problem = db.scalar(select(Problem).options(joinedload(Problem.tags).joinedload(ProblemTag.tag), joinedload(Problem.test_cases))
                            .where(Problem.id == problem_id, Problem.published.is_(True)))
        if problem is None:
            raise AppError(404, "not_found", "Problem was not found")
        return problem_data(problem, include_cases=True, public=True)

    @app.post("/api/submissions", status_code=201)
    def create_submission(payload: SubmissionCreate, user: Annotated[User, Depends(current_user)], db: Db):
        db.commit()
        db.execute(text("BEGIN IMMEDIATE"))
        problem = db.get(Problem, payload.problem_id)
        if problem is None or not problem.published:
            raise AppError(404, "not_found", "Problem was not found")
        outstanding = db.scalar(select(func.count()).select_from(Submission).where(
            Submission.user_id == user.id, Submission.status.in_(("PENDING", "JUDGING")))) or 0
        if outstanding >= 3:
            raise AppError(429, "outstanding_limit", "At most three submissions may be waiting for judgment")
        submission = Submission(user_id=user.id, problem_id=problem.id, source=payload.source, language=payload.language,
                                status="PENDING", problem_revision=problem.revision)
        db.add(submission)
        today = local_day()
        db.execute(text("INSERT OR IGNORE INTO user_activities(user_id, problem_id, status, activity_date, updated_at) VALUES (:user_id, :problem_id, 'attempted', :day, :now)"),
                   {"user_id": user.id, "problem_id": problem.id, "day": today, "now": utcnow()})
        db.flush()
        return submission_data(submission, "owner")

    @app.get("/api/submissions")
    def list_my_submissions(user: Annotated[User, Depends(current_user)], db: Db, page: int = 1, page_size: int = 20):
        if page < 1 or not 1 <= page_size <= 100:
            raise AppError(422, "validation_error", "Invalid pagination")
        query = select(Submission).where(Submission.user_id == user.id)
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = db.scalars(query.order_by(Submission.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [submission_data(item) for item in items], "page": page, "page_size": page_size, "total": total}

    @app.get("/api/submissions/public")
    def list_public_submissions(db: Db, page: int = 1, page_size: int = 20):
        if page < 1 or not 1 <= page_size <= 100:
            raise AppError(422, "validation_error", "Invalid pagination")
        query = select(Submission)
        total = db.scalar(select(func.count()).select_from(Submission)) or 0
        items = db.scalars(query.order_by(Submission.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [submission_data(item) for item in items], "page": page, "page_size": page_size, "total": total}

    @app.get("/api/submissions/{submission_id}")
    def get_own_submission(submission_id: int, user: Annotated[User, Depends(current_user)], db: Db):
        submission = db.get(Submission, submission_id)
        if submission is None:
            raise AppError(404, "not_found", "Submission was not found")
        if submission.user_id != user.id and user.role != "admin":
            raise AppError(403, "forbidden", "Submission is not owned by current user")
        return submission_data(submission, "admin" if user.role == "admin" else "owner")

    def current_revision_ac_query():
        return select(Submission.user_id, Submission.problem_id).join(Problem).where(
            Submission.status == "AC", Submission.problem_revision == Problem.revision).distinct()

    @app.get("/api/dashboard")
    def student_dashboard(user: Annotated[User, Depends(current_user)], db: Db):
        solved = db.scalar(select(func.count()).select_from(current_revision_ac_query().where(Submission.user_id == user.id).subquery())) or 0
        history = select(Submission.id).where(Submission.user_id == user.id)
        attempts = db.scalar(select(func.count()).select_from(history.subquery())) or 0
        accepted = db.scalar(select(func.count()).select_from(history.where(Submission.status == "AC").subquery())) or 0
        ranked = leaderboard_rows(db)
        position = next((index for index, row in enumerate(ranked, start=1) if row["user_id"] == user.id), None)
        dates = {item.activity_date for item in db.scalars(select(UserActivity).where(UserActivity.user_id == user.id))}
        streak = 0
        cursor = local_day()
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        solved_ids = select(Submission.problem_id).join(Problem).where(Submission.user_id == user.id, Submission.status == "AC", Submission.problem_revision == Problem.revision)
        unsolved = db.scalars(select(Problem).where(Problem.published.is_(True), Problem.id.not_in(solved_ids)).order_by(Problem.id).limit(3)).all()
        recent = db.scalars(select(Submission).where(Submission.user_id == user.id).order_by(Submission.id.desc()).limit(10)).all()
        return {"solved_count": solved, "acceptance_rate": (accepted / attempts if attempts else 0.0), "rank": position,
                "current_streak": streak, "recent_submissions": [submission_data(item, "owner") for item in recent],
                "unsolved_problems": [problem_data(item) for item in unsolved]}

    def leaderboard_rows(db: OrmSession) -> list[dict]:
        users = db.scalars(select(User).where(User.is_active.is_(True))).all()
        solved = dict(db.execute(select(Submission.user_id, func.count(func.distinct(Submission.problem_id))).join(Problem).where(
            Submission.status == "AC", Submission.problem_revision == Problem.revision).group_by(Submission.user_id)).all())
        attempts = dict(db.execute(select(Submission.user_id, func.count()).group_by(Submission.user_id)).all())
        rows = [{"user_id": item.id, "username": item.username, "display_name": item.display_name,
                 "solved": solved.get(item.id, 0), "attempts": attempts.get(item.id, 0)} for item in users]
        return sorted(rows, key=lambda row: (-row["solved"], row["attempts"], row["username"]))

    @app.get("/api/leaderboard")
    def leaderboard(user: Annotated[User | None, Depends(optional_user)], db: Db):
        rows = leaderboard_rows(db)
        position = next((index for index, row in enumerate(rows, start=1) if user and row["user_id"] == user.id), None)
        return {"items": rows, "current_user_position": position}

    @app.post("/api/admin/tags", status_code=201)
    def create_tag(payload: TagInput, _admin: Annotated[User, Depends(admin_user)], db: Db):
        if db.scalar(matching_tag_query(payload.name)) is not None:
            raise AppError(409, "tag_taken", "Tag already exists", {"name": "already in use"})
        tag = Tag(name=payload.name)
        db.add(tag)
        flush_or_conflict(db, "tag_taken", "Tag already exists", {"name": "already in use"})
        return tag_data(tag)

    @app.get("/api/admin/tags")
    def list_tags(_admin: Annotated[User, Depends(admin_user)], db: Db):
        return [tag_data(tag) for tag in db.scalars(select(Tag).order_by(Tag.name))]

    @app.patch("/api/admin/tags/{tag_id}")
    def update_tag(tag_id: int, payload: TagInput, _admin: Annotated[User, Depends(admin_user)], db: Db):
        tag = db.get(Tag, tag_id)
        if tag is None:
            raise AppError(404, "not_found", "Tag was not found")
        existing = db.scalar(matching_tag_query(payload.name).where(Tag.id != tag_id))
        if existing is not None:
            raise AppError(409, "tag_taken", "Tag already exists", {"name": "already in use"})
        tag.name = payload.name
        flush_or_conflict(db, "tag_taken", "Tag already exists", {"name": "already in use"})
        return tag_data(tag)

    @app.delete("/api/admin/tags/{tag_id}", status_code=204)
    def delete_tag(tag_id: int, _admin: Annotated[User, Depends(admin_user)], db: Db):
        tag = db.get(Tag, tag_id)
        if tag is None:
            raise AppError(404, "not_found", "Tag was not found")
        if db.scalar(select(ProblemTag).where(ProblemTag.tag_id == tag_id)) is not None:
            raise AppError(409, "tag_in_use", "Tag is assigned to a problem")
        db.delete(tag)
        return Response(status_code=204)

    @app.post("/api/admin/problems", status_code=201)
    def create_problem(payload: ProblemCreate, _admin: Annotated[User, Depends(admin_user)], db: Db):
        problem = Problem(title=payload.title, statement=payload.statement, input_markdown=payload.input, output_markdown=payload.output,
                          difficulty=payload.difficulty, time_limit_ms=payload.time_limit_ms, published=payload.published, revision=1)
        problem.tags = [ProblemTag(tag=tag) for tag in unique_tags(db, payload.tags)]
        replace_cases(problem, payload.test_cases)
        db.add(problem)
        flush_or_conflict(db, "conflict", "Problem conflicts with existing data")
        return problem_data(problem, include_cases=True)

    @app.get("/api/admin/problems")
    def admin_list_problems(_admin: Annotated[User, Depends(admin_user)], db: Db):
        problems = db.scalars(select(Problem).options(joinedload(Problem.tags).joinedload(ProblemTag.tag), joinedload(Problem.test_cases)).order_by(Problem.id)).unique()
        return [problem_data(problem, include_cases=True) for problem in problems]

    @app.get("/api/admin/problems/{problem_id}")
    def admin_get_problem(problem_id: int, _admin: Annotated[User, Depends(admin_user)], db: Db):
        problem = db.scalar(select(Problem).options(joinedload(Problem.tags).joinedload(ProblemTag.tag), joinedload(Problem.test_cases)).where(Problem.id == problem_id))
        if problem is None:
            raise AppError(404, "not_found", "Problem was not found")
        return problem_data(problem, include_cases=True)

    @app.patch("/api/admin/problems/{problem_id}")
    @app.put("/api/admin/problems/{problem_id}")
    def update_problem(problem_id: int, payload: ProblemUpdate, _admin: Annotated[User, Depends(admin_user)], db: Db):
        problem = db.scalar(select(Problem).options(joinedload(Problem.tags).joinedload(ProblemTag.tag), joinedload(Problem.test_cases)).where(Problem.id == problem_id))
        if problem is None:
            raise AppError(404, "not_found", "Problem was not found")
        changes = payload.model_fields_set
        for field, attribute in [("title", "title"), ("statement", "statement"), ("input", "input_markdown"), ("output", "output_markdown"),
                                 ("difficulty", "difficulty"), ("published", "published")]:
            if field in changes:
                setattr(problem, attribute, getattr(payload, field))
        revision_changed = False
        if "time_limit_ms" in changes and payload.time_limit_ms != problem.time_limit_ms:
            problem.time_limit_ms = payload.time_limit_ms
            revision_changed = True
        if "tags" in changes:
            problem.tags = [ProblemTag(tag=tag) for tag in unique_tags(db, payload.tags or [])]
        if "test_cases" in changes:
            old_cases = [(case.input_data, case.output_data, case.is_sample) for case in problem.test_cases]
            new_cases = [(case.input, case.output, case.is_sample) for case in (payload.test_cases or [])]
            if old_cases != new_cases:
                replace_cases(problem, payload.test_cases or [], db)
                revision_changed = True
        if revision_changed:
            problem.revision += 1
        flush_or_conflict(db, "conflict", "Problem conflicts with existing data")
        return problem_data(problem, include_cases=True)

    @app.delete("/api/admin/problems/{problem_id}", status_code=204)
    def delete_problem(problem_id: int, _admin: Annotated[User, Depends(admin_user)], db: Db):
        problem = db.get(Problem, problem_id)
        if problem is None:
            raise AppError(404, "not_found", "Problem was not found")
        db.delete(problem)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise AppError(409, "conflict", "Resource is still referenced")
        return Response(status_code=204)

    @app.get("/api/admin/users")
    def list_users(_admin: Annotated[User, Depends(admin_user)], db: Db, page: int = 1, page_size: int = 20):
        if page < 1 or not 1 <= page_size <= 100:
            raise AppError(422, "validation_error", "Invalid pagination")
        total = db.scalar(select(func.count()).select_from(User)) or 0
        users = db.scalars(select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [user_data(user) for user in users], "page": page, "page_size": page_size, "total": total}

    @app.get("/api/admin/submissions/{submission_id}")
    def get_submission(submission_id: int, _admin: Annotated[User, Depends(admin_user)], db: Db):
        submission = db.get(Submission, submission_id)
        if submission is None:
            raise AppError(404, "not_found", "Submission was not found")
        return submission_data(submission, "admin")

    @app.get("/api/admin/submissions")
    def admin_list_submissions(_admin: Annotated[User, Depends(admin_user)], db: Db):
        return [submission_data(item, "admin") for item in db.scalars(select(Submission).order_by(Submission.id.desc()))]

    @app.get("/api/admin/dashboard")
    def dashboard(_admin: Annotated[User, Depends(admin_user)], db: Db):
        return {"users": db.scalar(select(func.count()).select_from(User)) or 0,
                "problems": db.scalar(select(func.count()).select_from(Problem)) or 0,
                "submissions": db.scalar(select(func.count()).select_from(Submission)) or 0}

    configured_dist = frontend_dist or os.environ.get("OJ_FRONTEND_DIST")
    dist = Path(configured_dist) if configured_dist else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    dist = dist.resolve()
    index = dist / "index.html"

    @app.middleware("http")
    async def frontend_fallback(request: Request, call_next):
        """Serve the built SPA only after routing has established a non-API 404.

        Middleware avoids a greedy route swallowing API routes added by embedding/tests.
        """
        response = await call_next(request)
        path = request.url.path.lstrip("/")
        if request.method != "GET" or response.status_code != 404 or path == "api" or path.startswith("api/"):
            return response
        if not index.is_file():
            return JSONResponse(
                status_code=503,
                content={"code": "frontend_build_missing", "message": "Frontend build is missing; run npm run build in frontend."},
            )
        candidate = (dist / path).resolve()
        if candidate.is_file() and dist in candidate.parents:
            if candidate.suffix.lower() == ".js":
                return FileResponse(candidate, media_type="application/javascript")
            return FileResponse(candidate)
        return FileResponse(index)

    return app


app = create_app()
