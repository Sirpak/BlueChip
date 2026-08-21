"""CLI: python -m ml.features.build

Builds leakage-safe BCW-SNAP-v0.1 rows (EPA rolling + HFA/Elo/SRS/opp-adj EPA).
Does not open the 2023–2025 holdout for tuning.
"""

from __future__ import annotations

import argparse
import logging
import sys

from ml.features.constants import FEATURE_VERSION
from ml.features.snapshots import build_and_persist
from db.session import get_session_factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.features.build")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    session = get_session_factory()()
    try:
        stats = build_and_persist(session)
    finally:
        session.close()
    print(f"{FEATURE_VERSION} snapshots={stats['snapshots']} games={stats['games']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
