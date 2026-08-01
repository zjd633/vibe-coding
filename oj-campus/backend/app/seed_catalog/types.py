"""Immutable seed-catalog models and validation rules."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping


MAX_CASE_BYTES = 256 * 1024
MAX_CASES = 50
VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
LEGACY_TITLES = frozenset({
    "两数之和", "奇偶判断", "区间求和", "最大公约数", "括号匹配", "矩阵行和",
    "最短路径（无权图）", "最长递增子序列长度", "网格最小路径和",
})


@dataclass(frozen=True)
class SeedCase:
    input_data: str
    output_data: str
    is_sample: bool = False


@dataclass(frozen=True)
class SeedProblem:
    title: str
    difficulty: str
    tags: tuple[str, ...]
    statement: str
    input_text: str
    output_text: str
    cases: tuple[SeedCase, ...]
    time_limit_ms: int = 1000
    legacy: bool = False


def _problem_error(problem: SeedProblem, field: str, message: str) -> ValueError:
    return ValueError(f"problem {problem.title!r}: {field} {message}")


def _validate_required_text(problem: SeedProblem, field: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise _problem_error(problem, field, "must not be blank")


def _case_byte_length(value: str) -> int:
    return len(value.encode("utf-8"))


def _validate_cases(problem: SeedProblem, minimum_cases: int, minimum_hidden: int) -> None:
    if not isinstance(problem.cases, tuple):
        raise _problem_error(problem, "cases", "must be a tuple")
    if len(problem.cases) > MAX_CASES:
        raise _problem_error(problem, "cases", f"allows at most {MAX_CASES} cases")

    samples = 0
    hidden = 0
    for index, case in enumerate(problem.cases, start=1):
        if not isinstance(case, SeedCase):
            raise _problem_error(problem, "cases", f"case {index} must be a SeedCase")
        if not isinstance(case.input_data, str) or not isinstance(case.output_data, str):
            raise _problem_error(problem, "cases", f"case {index} text must be strings")
        try:
            input_bytes = _case_byte_length(case.input_data)
        except UnicodeEncodeError as error:
            raise _problem_error(problem, "cases", f"case {index} input must be valid UTF-8") from error
        if input_bytes > MAX_CASE_BYTES:
            raise _problem_error(problem, "cases", f"case {index} input exceeds {MAX_CASE_BYTES} UTF-8 bytes")
        try:
            output_bytes = _case_byte_length(case.output_data)
        except UnicodeEncodeError as error:
            raise _problem_error(problem, "cases", f"case {index} output must be valid UTF-8") from error
        if output_bytes > MAX_CASE_BYTES:
            raise _problem_error(problem, "cases", f"case {index} output exceeds {MAX_CASE_BYTES} UTF-8 bytes")
        if case.is_sample:
            samples += 1
        else:
            hidden += 1

    if samples < 1:
        raise _problem_error(problem, "sample", "requires at least one sample case")
    if hidden < minimum_hidden:
        raise _problem_error(problem, "hidden", f"requires at least {minimum_hidden} hidden cases")
    if len(problem.cases) < minimum_cases:
        raise _problem_error(problem, "cases", f"requires at least {minimum_cases} cases")


def validate_problem(problem: SeedProblem) -> None:
    """Raise ``ValueError`` when a seed problem cannot safely be imported."""
    _validate_required_text(problem, "title", problem.title)
    if len(problem.title) > 200:
        raise _problem_error(problem, "title", "must be at most 200 characters")
    _validate_required_text(problem, "statement", problem.statement)
    _validate_required_text(problem, "input_text", problem.input_text)
    _validate_required_text(problem, "output_text", problem.output_text)

    if problem.difficulty not in VALID_DIFFICULTIES:
        raise _problem_error(problem, "difficulty", "must be easy, medium, or hard")
    if not isinstance(problem.time_limit_ms, int) or isinstance(problem.time_limit_ms, bool) or not 100 <= problem.time_limit_ms <= 5000:
        raise _problem_error(problem, "time_limit_ms", "must be between 100 and 5000 ms")

    is_legacy_problem = problem.legacy and problem.title in LEGACY_TITLES
    if problem.legacy and not is_legacy_problem:
        raise _problem_error(problem, "legacy", "is only allowed for fixed original titles")
    if not isinstance(problem.tags, tuple) or not problem.tags:
        raise _problem_error(problem, "tags", "must contain at least one tag")

    normalized_tags: set[str] = set()
    for tag in problem.tags:
        if not isinstance(tag, str) or not tag or len(tag) > 64:
            raise _problem_error(problem, "tags", "must be non-empty strings of at most 64 characters")
        if tag != tag.strip():
            raise _problem_error(problem, "tags", "must not have surrounding whitespace")
        normalized = tag.casefold()
        if normalized in normalized_tags:
            raise _problem_error(problem, "tags", "must be unique ignoring case")
        normalized_tags.add(normalized)
        if tag.isascii() and tag != tag.lower() and not (is_legacy_problem and tag == "BFS"):
            raise _problem_error(problem, "tags", "new ASCII tags must be lowercase")

    if is_legacy_problem:
        _validate_cases(problem, minimum_cases=2, minimum_hidden=1)
    else:
        _validate_cases(problem, minimum_cases=4, minimum_hidden=3)


def validate_catalog(
    problems: tuple[SeedProblem, ...],
    expected_counts: Mapping[str, int] | None = None,
) -> None:
    """Validate a catalog and, optionally, enforce its difficulty distribution."""
    seen_titles: set[str] = set()
    difficulties: Counter[str] = Counter()
    for problem in problems:
        validate_problem(problem)
        if problem.title in seen_titles:
            raise ValueError(f"catalog: duplicate title {problem.title!r}")
        seen_titles.add(problem.title)
        difficulties[problem.difficulty] += 1

    if expected_counts is not None and difficulties != Counter(expected_counts):
        raise ValueError(
            f"catalog: difficulty counts {dict(difficulties)} do not match {dict(expected_counts)}"
        )
