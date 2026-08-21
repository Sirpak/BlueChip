"""Small L2-regularized linear models (numpy only; no sklearn dependency)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LinearModel:
    feature_names: tuple[str, ...]
    coef: np.ndarray
    center: np.ndarray | None = None
    scale: np.ndarray | None = None

    def predict(self, X: np.ndarray) -> np.ndarray:
        x = np.asarray(X, dtype=float)
        if self.center is not None and self.scale is not None:
            x = np.array(x, dtype=float, copy=True)
            x[:, 1:] = (x[:, 1:] - self.center) / self.scale
        return x @ self.coef


def _penalty_mask(n_features: int, *, penalize_intercept: bool = False) -> np.ndarray:
    mask = np.ones(n_features, dtype=float)
    if not penalize_intercept:
        mask[0] = 0.0
    return mask


def fit_ridge(
    X: np.ndarray,
    y: np.ndarray,
    *,
    lam: float,
    penalize_intercept: bool = False,
) -> np.ndarray:
    """Closed-form ridge: (X'X + λ diag)^-1 X'y."""
    x = np.asarray(X, dtype=float)
    yy = np.asarray(y, dtype=float)
    p = x.shape[1]
    penalty = lam * np.diag(_penalty_mask(p, penalize_intercept=penalize_intercept))
    return np.linalg.solve(x.T @ x + penalty, x.T @ yy)


def fit_logistic(
    X: np.ndarray,
    y: np.ndarray,
    *,
    lam: float,
    max_iter: int = 60,
    tol: float = 1e-7,
    penalize_intercept: bool = False,
) -> np.ndarray:
    """Newton-Raphson logistic regression with L2 penalty."""
    x = np.asarray(X, dtype=float)
    yy = np.asarray(y, dtype=float)
    p = x.shape[1]
    w = np.zeros(p, dtype=float)
    pen = lam * _penalty_mask(p, penalize_intercept=penalize_intercept)
    for _ in range(max_iter):
        z = np.clip(x @ w, -35.0, 35.0)
        prob = 1.0 / (1.0 + np.exp(-z))
        grad = x.T @ (prob - yy) + pen * w
        w_diag = prob * (1.0 - prob)
        # Avoid singular Hessian when predictions saturate.
        w_diag = np.clip(w_diag, 1e-8, None)
        h = x.T @ (x * w_diag[:, None]) + np.diag(pen)
        step = np.linalg.solve(h, grad)
        w_new = w - step
        if float(np.max(np.abs(w_new - w))) < tol:
            w = w_new
            break
        w = w_new
    return w
