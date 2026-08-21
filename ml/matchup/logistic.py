"""W3 — BCW-MATCHUP-LOGISTIC (Research Preview).

Uses interaction z-scores as features. Not the published Ridge μ.
Trains only when a labeled frame is provided; otherwise scores a heuristic logistic.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ml.matchup.edges import MatchupEdge

MODEL_ID = "BCW-MATCHUP-LOGISTIC-v0.x"


def _sigmoid(z: float) -> float:
    z = max(-30.0, min(30.0, z))
    return float(1.0 / (1.0 + np.exp(-z)))


def score_edges(edges: list[MatchupEdge], *, hfa: float = 0.15) -> dict[str, Any]:
    """Heuristic logistic on mismatch z's until walk-forward training lands."""
    weights = {
        "PASS_RUSH": 0.35,
        "PASSING": 0.40,
        "RUN_GAME": 0.25,
        "OVERALL": 0.45,
        "SUCCESS": 0.20,
        "AP_RANK": 0.30,
    }
    z = hfa
    contrib: list[dict[str, Any]] = []
    for e in edges:
        w = weights.get(e.key, 0.15)
        term = w * e.mismatch_z
        z += term
        contrib.append({"key": e.key, "weight": w, "z": e.mismatch_z, "term": round(term, 4)})
    p = _sigmoid(z)
    return {
        "model_id": MODEL_ID,
        "label": "Research Preview",
        "public_probability_published": False,
        "logit": round(z, 4),
        "p_home_win": round(p, 4),
        "lean": "HOME" if p >= 0.5 else "AWAY",
        "contributions": contrib,
        "note": "Heuristic matchup logistic on EDGE z-scores. Not BCW-RIDGE. Not a ship gate.",
    }
