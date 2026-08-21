"""Margin error metrics for pregame Ridge models."""

from __future__ import annotations

import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs(y[mask] - p[mask])))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    if mask.sum() == 0:
        return float("nan")
    return float(np.sqrt(np.mean((y[mask] - p[mask]) ** 2)))
