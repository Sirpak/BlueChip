"""Rewrite historical NFL abbrs onto current franchises across the warehouse.

STL→LAR, OAK→LV, SD→LAC, JAC→JAX, WSH→WAS, LA→LAR, LVR→LV.

One franchise = continuous history: when the city code stops, the new abbr continues
the same team. Run after ingest or whenever ghost codes appear on the desk.

CLI: ``python -m app.ingest.canonicalize_franchises``
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.ingest.identity import NFL_FRANCHISE_CANON
from db.session import get_session_factory

logger = logging.getLogger(__name__)

# (table, columns)
_TARGETS: list[tuple[str, tuple[str, ...]]] = [
    ("games", ("home_team", "away_team")),
    ("plays", ("home_team", "away_team", "posteam", "defteam")),
    ("feature_snapshots", ("home_team", "away_team")),
    ("standings", ("team",)),
]


def _table_exists(session, name: str) -> bool:  # noqa: ANN001
    row = session.execute(
        text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).first()
    return row is not None


def _column_exists(session, table: str, column: str) -> bool:  # noqa: ANN001
    rows = session.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def rewrite_franchises(session) -> dict[str, int]:  # noqa: ANN001
    """UPDATE alias codes in place. Idempotent."""
    counts: dict[str, int] = {}
    for table, columns in _TARGETS:
        if not _table_exists(session, table):
            continue
        for col in columns:
            if not _column_exists(session, table, col):
                continue
            touched = 0
            for old, new in NFL_FRANCHISE_CANON.items():
                result = session.execute(
                    text(f"UPDATE {table} SET {col} = :new WHERE {col} = :old"),
                    {"old": old, "new": new},
                )
                touched += int(result.rowcount or 0)
            key = f"{table}.{col}"
            counts[key] = touched
            if touched:
                logger.info("Canonicalized %s rows in %s", touched, key)
    session.commit()
    return counts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = get_session_factory()()
    try:
        counts = rewrite_franchises(session)
    finally:
        session.close()
    total = sum(counts.values())
    print({"updated_cells": total, "by_column": counts})


if __name__ == "__main__":
    main()
