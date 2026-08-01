from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,24}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def normalize_username(value: str) -> str:
    value = value.strip().lower()
    if not USERNAME_RE.fullmatch(value):
        raise ValueError("username must be 3-24 ASCII letters, digits, or underscores")
    return value


def normalize_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.fullmatch(value):
        raise ValueError("email must be valid")
    return value


class RegisterRequest(StrictModel):
    username: str
    email: str
    display_name: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=8, max_length=72)

    _username = field_validator("username")(normalize_username)
    _email = field_validator("email")(normalize_email)


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class ProfileUpdate(StrictModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=32)
    email: str | None = None

    _email = field_validator("email")(lambda value: normalize_email(value) if value is not None else value)

    @model_validator(mode="after")
    def has_change(self):
        if self.display_name is None and self.email is None:
            raise ValueError("at least one profile field is required")
        return self


class PasswordUpdate(StrictModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class SubmissionCreate(StrictModel):
    problem_id: int = Field(gt=0)
    language: Literal["cpp17"]
    source: str = Field(min_length=1)

    @field_validator("source")
    @classmethod
    def source_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 64 * 1024:
            raise ValueError("source must be at most 64 KiB")
        return value


class TagInput(StrictModel):
    name: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("tag name is required")
        return value


class TestCaseInput(StrictModel):
    input: str
    output: str
    is_sample: bool = False

    @model_validator(mode="after")
    def within_byte_limit(self):
        if len(self.input.encode("utf-8")) > 256 * 1024 or len(self.output.encode("utf-8")) > 256 * 1024:
            raise ValueError("test case input and output must be at most 256 KiB")
        return self


class ProblemCreate(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    statement: str
    input: str = ""
    output: str = ""
    difficulty: Literal["easy", "medium", "hard"]
    time_limit_ms: int = Field(ge=100, le=5000)
    published: bool = False
    tags: list[str] = Field(default_factory=list)
    test_cases: list[TestCaseInput] = Field(default_factory=list, max_length=50)


class ProblemUpdate(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    statement: str | None = None
    input: str | None = None
    output: str | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    time_limit_ms: int | None = Field(default=None, ge=100, le=5000)
    published: bool | None = None
    tags: list[str] | None = None
    test_cases: list[TestCaseInput] | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def contains_non_null_changes(self):
        if not self.model_fields_set:
            raise ValueError("at least one problem field is required")
        null_fields = [field for field in self.model_fields_set if getattr(self, field) is None]
        if null_fields:
            raise ValueError(f"provided fields cannot be null: {', '.join(sorted(null_fields))}")
        return self
