from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(32), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (CheckConstraint("role IN ('student', 'admin')", name="user_role"),)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    user: Mapped[User] = relationship()


class UserActivity(Base):
    __tablename__ = "user_activities"
    __table_args__ = (UniqueConstraint("user_id", "activity_date", name="uq_activity_user_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="attempted")
    activity_date: Mapped[date] = mapped_column(nullable=False, default=date.today, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    input_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    output_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    tags: Mapped[list["ProblemTag"]] = relationship(cascade="all, delete-orphan", order_by="ProblemTag.tag_id")
    test_cases: Mapped[list["TestCase"]] = relationship(cascade="all, delete-orphan", order_by="TestCase.position")

    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="problem_difficulty"),
        CheckConstraint("time_limit_ms BETWEEN 100 AND 5000", name="problem_time_limit"),
        CheckConstraint("revision >= 1", name="problem_revision"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class ProblemTag(Base):
    __tablename__ = "problem_tags"
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True)
    tag: Mapped[Tag] = relationship()


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (UniqueConstraint("problem_id", "position", name="uq_case_problem_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    output_data: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    problem_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    judging_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        CheckConstraint("language IN ('cpp17')", name="submission_language"),
        CheckConstraint("status IN ('PENDING', 'JUDGING', 'AC', 'WA', 'CE', 'RE', 'TLE', 'OLE', 'SE')", name="submission_status"),
    )

    @validates("language")
    def normalize_legacy_language(self, _key: str, value: str) -> str:
        return "cpp17" if value != "cpp17" else value

    @validates("status")
    def normalize_legacy_status(self, _key: str, value: str) -> str:
        return "PENDING" if value == "queued" else value
