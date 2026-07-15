from __future__ import annotations

import sys


def run() -> int:
    if sys.argv[1:] == ["--self-test-credentials"]:
        from replykey.credentials import verify_credential_backend

        try:
            verify_credential_backend()
        except Exception:
            return 2
        return 0

    from replykey.app import main

    return main()


if __name__ == "__main__":
    raise SystemExit(run())
