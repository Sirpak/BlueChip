"""Bootstrap intervals for walk-forward metrics. No ROI."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from ml.evaluation.protocol import BOOTSTRAP_DRAWS, BOOTSTRAP_HI, BOOTSTRAP_LO, BOOTSTRAP_SEED


def bootstrap_ci(
    y: np.ndarray,
    pred: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    n_boot: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
    lo: float = BOOTSTRAP_LO,
    hi: float = BOOTSTRAP_HI,
) -> dict[str, float]:
    y = np.asarray(y, dtype=float)
    p = np.asarray(pred, dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    y = y[mask]
    p = p[mask]
    n = int(len(y))
    point = float(metric(y, p)) if n else float("nan")
    if n < 20:
        return {"point": point, "lo": float("nan"), "hi": float("nan"), "n": float(n), "draws": 0}
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        stats[i] = metric(y[idx], p[idx])
    return {
        "point": point,
        "lo": float(np.nanpercentile(stats, lo)),
        "hi": float(np.nanpercentile(stats, hi)),
        "n": float(n),
        "draws": float(n_boot),
    }


def interval_payload(ci: dict[str, float]) -> dict[str, Any]:
    return {
        "point": ci["point"],
        "lo": ci["lo"],
        "hi": ci["hi"],
        "n": int(ci["n"]),
        "draws": int(ci["draws"]),
    }
