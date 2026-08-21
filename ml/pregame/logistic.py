"""BCW-LOGISTIC-v0.1 — L2 logistic home-win on pregame rolling features."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml.features.constants import ADJ_RIDGE_LAM
from ml.pregame._l2 import LinearModel, fit_logistic
from ml.pregame.feature_columns import ADJ_EPA_FEATURES, feature_matrix

MODEL_VERSION = "v0.1"
DEFAULT_FEATURES = ADJ_EPA_FEATURES
DEFAULT_LAM = ADJ_RIDGE_LAM


def train(
    df: pd.DataFrame,
    *,
    feature_cols: tuple[str, ...] = DEFAULT_FEATURES,
    lam: float = DEFAULT_LAM,
) -> LinearModel:
    """Fit logistic on a training frame (typically expanding pre-2022 history)."""
    y = pd.to_numeric(df["home_win"], errors="coerce")
    x_df, mask = feature_matrix(df, feature_cols)
    yy = y.loc[mask].to_numpy(dtype=float)
    coef = fit_logistic(x_df.to_numpy(dtype=float), yy, lam=lam)
    return LinearModel(feature_names=tuple(x_df.columns), coef=coef)


def predict(model: LinearModel, df: pd.DataFrame) -> pd.Series:
    """Return home-win probability aligned to ``df.index`` (NaN when features missing)."""
    cols = [c for c in model.feature_names if c != "intercept"]
    x_df, mask = feature_matrix(df, tuple(cols))
    z = x_df.to_numpy(dtype=float) @ model.coef
    prob = 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))
    out = pd.Series(np.nan, index=df.index, dtype=float)
    out.loc[mask] = prob
    return out


def fit_and_predict_oos(
    df: pd.DataFrame,
    *,
    feature_cols: tuple[str, ...] = DEFAULT_FEATURES,
    lam: float = DEFAULT_LAM,
) -> pd.DataFrame:
    """Season walk-forward OOS probabilities (train strictly before each test season)."""
    seasons = sorted(df["season"].dropna().unique().astype(int))
    preds = pd.Series(np.nan, index=df.index, dtype=float)
    for train_seasons, test_season in _expanding_folds(seasons):
        train_df = df[df["season"].isin(train_seasons)]
        test_df = df[df["season"] == test_season]
        if train_df.empty or test_df.empty:
            continue
        model = train(train_df, feature_cols=feature_cols, lam=lam)
        preds.loc[test_df.index] = predict(model, test_df).loc[test_df.index]
    out = df.copy()
    out["home_win_prob"] = preds
    return out


def _expanding_folds(seasons: list[int]) -> list[tuple[list[int], int]]:
    ordered = sorted(seasons)
    folds: list[tuple[list[int], int]] = []
    for i in range(1, len(ordered)):
        folds.append((ordered[:i], ordered[i]))
    return folds


def summary_payload(model: LinearModel) -> dict[str, Any]:
    return {
        "feature_names": list(model.feature_names),
        "coef": {n: float(c) for n, c in zip(model.feature_names, model.coef, strict=True)},
    }
