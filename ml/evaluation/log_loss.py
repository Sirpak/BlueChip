"""Binary log loss."""

from __future__ import annotations

import numpy as np

EPS = 1e-15


def log_loss(y_true: np.ndarray, y_prob: np.ndarray, *, eps: float = EPS) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(y_prob, dtype=float), eps, 1.0 - eps)
    if y.shape != p.shape:
        raise ValueError(f"shape mismatch: y {y.shape} vs p {p.shape}")
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))
