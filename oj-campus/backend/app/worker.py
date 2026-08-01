"""Command-line entry point for the trusted-local judge worker."""
from __future__ import annotations

import os

from .database import default_database_url
from .judge import run_worker


def main() -> None:
    run_worker(os.environ.get("OJ_DATABASE_URL") or default_database_url())


if __name__ == "__main__":
    main()
