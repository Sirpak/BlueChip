"""Expected points — next-score multinomial, then EP as a value.

nflfastR EP asks: given down/distance/field/time/roof, what is the expected
value of the *next scoring event* (not the final score).

Seven classes (offense/defense TD, FG, safety, no score). Approximate EP:

    EP = 7 P(off TD) + 3 P(off FG) + 2 P(off safety)
       - 7 P(def TD) - 3 P(def FG) - 2 P(def safety)

Exact published weights differ slightly (e.g. extra point / 2-pt / safety
handling). This module documents the mapping; training is not v0.1.

EPA = EP_after − EP_before, with possession/score flips.
"""

from __future__ import annotations

from typing import Any

import numpy as np

# Baldwin OSF 2020-09-28 EP XGBoost.
EP_PRESET: dict[str, Any] = {
    "objective": "multi:softprob",
    "num_class": 7,
    "max_depth": 5,
    "learning_rate": 0.025,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_estimators": 525,
    "min_child_weight": 1,
    "gamma": 1,
    "tree_method": "hist",
}

EP_FEATURES: list[str] = [
    "half_seconds_remaining",
    "yardline_100",
    "home",
    "retractable",
    "dome",
    "outdoors",
    "ydstogo",
    "era0",
    "era1",
    "era2",
    "era3",
    "era4",
    "down1",
    "down2",
    "down3",
    "down4",
    "posteam_timeouts_remaining",
    "defteam_timeouts_remaining",
]

# Class order used by nflfastR / open-source-football write-up.
NEXT_SCORE_CLASSES: tuple[str, ...] = (
    "opp_safety",
    "opp_field_goal",
    "opp_touchdown",
    "no_score",
    "safety",
    "field_goal",
    "touchdown",
)

# Approximate points from the possession team's perspective.
EP_POINTS: dict[str, float] = {
    "touchdown": 7.0,
    "field_goal": 3.0,
    "safety": 2.0,
    "no_score": 0.0,
    "opp_safety": -2.0,
    "opp_field_goal": -3.0,
    "opp_touchdown": -7.0,
}


def next_score_class_names() -> tuple[str, ...]:
    return NEXT_SCORE_CLASSES


def ep_from_probs(probs: np.ndarray, *, class_names: tuple[str, ...] | None = None) -> np.ndarray:
    """Convert (n, 7) next-score probabilities into expected points."""
    names = class_names or NEXT_SCORE_CLASSES
    p = np.asarray(probs, dtype=float)
    if p.ndim != 2 or p.shape[1] != len(names):
        raise ValueError(f"expected (n, {len(names)}) probs, got {p.shape}")
    weights = np.array([EP_POINTS[name] for name in names], dtype=float)
    return p @ weights


def train(*_args, **_kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError(
        "EP training is next after WP v0.1 is calibrated against nflverse wp."
    )
