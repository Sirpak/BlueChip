"""Equal-width calibration bins for a binary probability."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calibration_table(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    *,
    n_bins: int = 10,
) -> pd.DataFrame:
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    # right-closed last bin so 1.0 is included
    idx = np.digitize(p, edges[1:-1], right=True)
    rows: list[dict[str, float | int]] = []
    for b in range(n_bins):
        mask = idx == b
        n = int(mask.sum())
        if n == 0:
            mean_p = float("nan")
            mean_y = float("nan")
        else:
            mean_p = float(p[mask].mean())
            mean_y = float(y[mask].mean())
        rows.append(
            {
                "bin": b,
                "lo": float(edges[b]),
                "hi": float(edges[b + 1]),
                "n": n,
                "mean_predicted": mean_p,
                "mean_actual": mean_y,
                "gap": mean_p - mean_y if n else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def expected_calibration_error(table: pd.DataFrame) -> float:
    """ECE = weighted mean |predicted − actual| over non-empty bins."""
    n = table["n"].to_numpy(dtype=float)
    total = n.sum()
    if total <= 0:
        return float("nan")
    gap = np.abs(table["mean_predicted"] - table["mean_actual"]).to_numpy(dtype=float)
    valid = n > 0
    return float(np.sum(n[valid] * gap[valid]) / total)


def logit(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    x = np.clip(np.asarray(p, dtype=float), eps, 1.0 - eps)
    return np.log(x / (1.0 - x))


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(np.asarray(z, dtype=float), -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-z))


def fit_platt(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Logistic y ~ a + b * logit(p). Returns (a, b)."""
    from ml.pregame._l2 import fit_logistic

    z = logit(p)
    X = np.column_stack([np.ones(len(z)), z])
    w = fit_logistic(X, np.asarray(y, dtype=float), lam=0.0)
    return float(w[0]), float(w[1])


def apply_platt(p: np.ndarray, a: float, b: float) -> np.ndarray:
    return sigmoid(a + b * logit(p))


def fit_isotonic(p: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """PAVA isotonic regression. Returns (sorted unique p knots, fitted y)."""
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    order = np.argsort(p, kind="mergesort")
    x = p[order]
    v = y[order]
    w = np.ones_like(v)
    # Merge identical p
    xs: list[float] = []
    vs: list[float] = []
    ws: list[float] = []
    for xi, yi in zip(x, v, strict=True):
        if xs and abs(xi - xs[-1]) < 1e-15:
            total = ws[-1] + 1.0
            vs[-1] = (vs[-1] * ws[-1] + yi) / total
            ws[-1] = total
        else:
            xs.append(float(xi))
            vs.append(float(yi))
            ws.append(1.0)
    # Pool adjacent violators
    blocks_x = [[xs[0]]]
    blocks_y = [vs[0]]
    blocks_w = [ws[0]]
    for i in range(1, len(xs)):
        blocks_x.append([xs[i]])
        blocks_y.append(vs[i])
        blocks_w.append(ws[i])
        while len(blocks_y) >= 2 and blocks_y[-2] > blocks_y[-1]:
            w2 = blocks_w[-2] + blocks_w[-1]
            y2 = (blocks_y[-2] * blocks_w[-2] + blocks_y[-1] * blocks_w[-1]) / w2
            x2 = blocks_x[-2] + blocks_x[-1]
            blocks_x[-2:] = [x2]
            blocks_y[-2:] = [y2]
            blocks_w[-2:] = [w2]
    knot_x = np.array([min(b) for b in blocks_x], dtype=float)
    knot_y = np.clip(np.array(blocks_y, dtype=float), 0.0, 1.0)
    return knot_x, knot_y


def apply_isotonic(p: np.ndarray, knot_x: np.ndarray, knot_y: np.ndarray) -> np.ndarray:
    return np.clip(np.interp(np.asarray(p, dtype=float), knot_x, knot_y), 0.0, 1.0)


def reliability_buckets(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    edges: tuple[float, ...] = (0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75),
) -> list[dict[str, float | int]]:
    """Requested 5-point buckets around 45–75% plus tails."""
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)
    cuts = (0.0,) + edges + (1.0,)
    rows: list[dict[str, float | int]] = []
    for lo, hi in zip(cuts[:-1], cuts[1:], strict=True):
        if hi >= 1.0:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        n = int(mask.sum())
        rows.append(
            {
                "lo": float(lo),
                "hi": float(hi),
                "n": n,
                "mean_predicted": float(p[mask].mean()) if n else float("nan"),
                "mean_actual": float(y[mask].mean()) if n else float("nan"),
            }
        )
    return rows
