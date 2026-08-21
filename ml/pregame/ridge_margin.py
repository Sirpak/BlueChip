"""BCW-RIDGE-v0.1 — L2 ridge expected home margin (published μ before Stern)."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from ml.features.constants import ADJ_RIDGE_LAM
from ml.pregame._l2 import LinearModel, fit_ridge
from ml.pregame.feature_columns import ADJ_EPA_FEATURES, RAW_EPA_FEATURES, feature_matrix

MODEL_VERSION = "v0.1"
DEFAULT_LAM = ADJ_RIDGE_LAM

EpaVariant = Literal["raw", "adj"]


def feature_cols_for_variant(variant: EpaVariant) -> tuple[str, ...]:
    return RAW_EPA_FEATURES if variant == "raw" else ADJ_EPA_FEATURES


def train(
    df: pd.DataFrame,
    *,
    feature_cols: tuple[str, ...] | None = None,
    variant: EpaVariant = "adj",
    lam: float = DEFAULT_LAM,
) -> LinearModel:
    """Fit ridge home-margin model on a training frame."""
    cols = feature_cols or feature_cols_for_variant(variant)
    y = pd.to_numeric(df["home_margin"], errors="coerce")
    x_df, mask = feature_matrix(df, cols)
    yy = y.loc[mask].to_numpy(dtype=float)
    coef = fit_ridge(x_df.to_numpy(dtype=float), yy, lam=lam)
    return LinearModel(feature_names=tuple(x_df.columns), coef=coef)


def predict(model: LinearModel, df: pd.DataFrame) -> pd.Series:
    """Predicted home margin μ aligned to ``df.index``."""
    cols = [c for c in model.feature_names if c != "intercept"]
    x_df, mask = feature_matrix(df, tuple(cols))
    mu = x_df.to_numpy(dtype=float) @ model.coef
    out = pd.Series(np.nan, index=df.index, dtype=float)
    out.loc[mask] = mu
    return out


def fit_and_predict_oos(
    df: pd.DataFrame,
    *,
    variant: EpaVariant = "adj",
    lam: float = DEFAULT_LAM,
) -> pd.DataFrame:
    """Season walk-forward OOS μ (train strictly before each test season)."""
    cols = feature_cols_for_variant(variant)
    seasons = sorted(df["season"].dropna().unique().astype(int))
    preds = pd.Series(np.nan, index=df.index, dtype=float)
    for i in range(1, len(seasons)):
        train_seasons = seasons[:i]
        test_season = seasons[i]
        train_df = df[df["season"].isin(train_seasons)]
        test_df = df[df["season"] == test_season]
        if train_df.empty or test_df.empty:
            continue
        model = train(train_df, feature_cols=cols, lam=lam)
        preds.loc[test_df.index] = predict(model, test_df).loc[test_df.index]
    out = df.copy()
    out["pred_margin"] = preds
    return out


def contribution_table(model: LinearModel, row: pd.Series) -> dict[str, float]:
    """β_j x_j decomposition for one game (interpretability)."""
    cols = [c for c in model.feature_names if c != "intercept"]
    contribs: dict[str, float] = {}
    for i, name in enumerate(model.feature_names):
        val = 1.0 if name == "intercept" else float(row.get(name, np.nan))
        if np.isfinite(val):
            contribs[name] = float(model.coef[i] * val)
    return contribs


def summary_payload(model: LinearModel, *, variant: EpaVariant) -> dict[str, Any]:
    return {
        "variant": variant,
        "feature_names": list(model.feature_names),
        "coef": {n: float(c) for n, c in zip(model.feature_names, model.coef, strict=True)},
    }
