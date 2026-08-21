"""Validation splits and metric packing.

nflfastR replication: leave-one-season-out (season stays intact — no play leakage).
BlueChip pregame betting models: chronological walk-forward (real-time simulation).
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from ml.evaluation.brier import brier_score
from ml.evaluation.log_loss import log_loss


def leave_one_season_out(seasons: list[int]) -> Iterator[tuple[list[int], int]]:
    ordered = sorted(seasons)
    for holdout in ordered:
        train = [s for s in ordered if s != holdout]
        if not train:
            continue
        yield train, holdout


def chronological_walk_forward(seasons: list[int]) -> Iterator[tuple[list[int], int]]:
    """Expanding window: train on all earlier seasons, test the next."""
    ordered = sorted(seasons)
    for i in range(1, len(ordered)):
        yield ordered[:i], ordered[i]


def roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Mann–Whitney AUC; midranks for ties."""
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(y_score, dtype=float)
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    y_sorted = y[order]
    ranks = np.empty(len(y), dtype=float)
    i = 0
    while i < len(y):
        j = i
        while j + 1 < len(y) and s[order[j + 1]] == s[order[i]]:
            j += 1
        mid = 0.5 * (i + j) + 1.0
        ranks[i : j + 1] = mid
        i = j + 1
    sum_pos_ranks = float(ranks[y_sorted == 1].sum())
    return float((sum_pos_ranks - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def metrics_payload(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float | int]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_prob, dtype=float)
    return {
        "n": int(len(y)),
        "brier": brier_score(y, p),
        "log_loss": log_loss(y, p),
        "auc": roc_auc(y, p),
        "mean_pred": float(np.mean(p)),
        "base_rate": float(np.mean(y)),
    }
