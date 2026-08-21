"""Leakage guards for pregame snapshots."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from ml.features.constants import FEATURE_VERSION
from db.models import FeatureSnapshot


def assert_snapshot_leakage(session: Session) -> dict[str, int]:
    insp = inspect(session.get_bind())
    tables = set(insp.get_table_names())
    if "feature_snapshots" not in tables:
        return {"snapshots": 0, "known_at_ok": 0}
    cols = {c["name"] for c in insp.get_columns("feature_snapshots")}
    if "vegas_wp" in cols:
        raise AssertionError("feature_snapshots must not store vegas_wp")
    n = session.query(FeatureSnapshot).filter(FeatureSnapshot.feature_version == FEATURE_VERSION).count()
    if n == 0:
        return {"snapshots": 0, "known_at_ok": 0}

    bad = session.execute(
        text(
            """
            SELECT COUNT(*) FROM feature_snapshots
            WHERE feature_version = :ver
              AND prediction_at IS NOT NULL
              AND known_at_max IS NOT NULL
              AND known_at_max >= prediction_at
            """
        ),
        {"ver": FEATURE_VERSION},
    ).scalar_one()
    if bad:
        raise AssertionError(f"{bad} snapshots with known_at_max >= prediction_at")

    return {"snapshots": n, "known_at_ok": n}
