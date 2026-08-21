"""Brier score: mean squared error of a probability."""

from __future__ import annotations

import numpy as np


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)
    if y.shape != p.shape:
        raise ValueError(f"shape mismatch: y {y.shape} vs p {p.shape}")
    return float(np.mean((p - y) ** 2))
