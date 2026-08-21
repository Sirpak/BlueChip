"""python -m app.seed_users — idempotent local demo accounts."""

from __future__ import annotations

import sys

from app.auth.seed import seed_dev_users
from db.session import get_session_factory


def main() -> int:
    session = get_session_factory()()
    try:
        seed_dev_users(session)
    finally:
        session.close()
    print("Seeded demo_free, demo_pro, demo_research, admin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
