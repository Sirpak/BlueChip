"""Train-fold standardization for L2 models (never fit on the test season)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.pregame._l2 import LinearModel
from ml.pregame.feature_columns import feature_matrix


def fit_scaler(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mean/std of non-intercept columns. Zero-variance columns stay at scale=1."""
    cols = X[:, 1:]
    center = cols.mean(axis=0)
    scale = cols.std(axis=0)
    scale = np.where(scale < 1e-8, 1.0, scale)
    return center, scale


def apply_scaler(X: np.ndarray, center: np.ndarray, scale: np.ndarray) -> np.ndarray:
    out = np.array(X, dtype=float, copy=True)
    out[:, 1:] = (out[:, 1:] - center) / scale
    return out


def design_matrix(
    df: pd.DataFrame,
    columns: tuple[str, ...],
    *,
    center: np.ndarray | None = None,
    scale: np.ndarray | None = None,
) -> tuple[np.ndarray, pd.Index, pd.Series]:
    x_df, mask = feature_matrix(df, columns)
    X = x_df.to_numpy(dtype=float)
    if center is not None and scale is not None:
        X = apply_scaler(X, center, scale)
    return X, x_df.index, mask


def attach_scaler(model: LinearModel, center: np.ndarray, scale: np.ndarray) -> LinearModel:
    return LinearModel(
        feature_names=model.feature_names,
        coef=model.coef,
        center=center,
        scale=scale,
    )
