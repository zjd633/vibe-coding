"""Seed problem catalog assembled in a stable compatibility order."""
from __future__ import annotations

from .easy import EASY_PROBLEMS
from .hard import HARD_PROBLEMS
from .medium import MEDIUM_PROBLEMS
from .types import SeedCase, SeedProblem, validate_catalog


_PROBLEMS_BY_DIFFICULTY = EASY_PROBLEMS + MEDIUM_PROBLEMS + HARD_PROBLEMS
PROBLEMS: tuple[SeedProblem, ...] = (
    tuple(problem for problem in _PROBLEMS_BY_DIFFICULTY if problem.legacy)
    + tuple(problem for problem in _PROBLEMS_BY_DIFFICULTY if not problem.legacy)
)

validate_catalog(
    PROBLEMS,
    expected_counts={"easy": 40, "medium": 35, "hard": 25},
)


__all__ = ["EASY_PROBLEMS", "HARD_PROBLEMS", "MEDIUM_PROBLEMS", "PROBLEMS", "SeedCase", "SeedProblem"]
