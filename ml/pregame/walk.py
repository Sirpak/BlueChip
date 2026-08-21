"""Season walk-forward helpers with train-only standardization."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from ml.pregame._l2 import LinearModel, fit_logistic, fit_ridge
from ml.pregame.standardize import apply_scaler, design_matrix, fit_scaler

Task = Literal["margin", "win", "residual"]


def expanding_folds(seasons: list[int]) -> list[tuple[list[int], int]]:
    ordered = sorted(seasons)
    return [(ordered[:i], ordered[i]) for i in range(1, len(ordered))]


def _target(df: pd.DataFrame, task: Task) -> pd.Series:
    if task == "win":
        return pd.to_numeric(df["home_win"], errors="coerce")
    if task == "residual":
        m = pd.to_numeric(df["home_margin"], errors="coerce")
        s = pd.to_numeric(df["market_spread"], errors="coerce")
        return m - s
    return pd.to_numeric(df["home_margin"], errors="coerce")


def fit_fold(
    train_df: pd.DataFrame,
    *,
    feature_cols: tuple[str, ...],
    task: Task,
    lam: float,
    standardize: bool = True,
) -> LinearModel | None:
    y = _target(train_df, task)
    X, idx, _mask = design_matrix(train_df, feature_cols)
    yy = y.loc[idx].to_numpy(dtype=float)
    finite = np.isfinite(yy)
    if int(finite.sum()) < max(20, X.shape[1] + 2):
        return None
    X = X[finite]
    yy = yy[finite]
    center = scale = None
    if standardize:
        center, scale = fit_scaler(X)
        X = apply_scaler(X, center, scale)
    coef = fit_logistic(X, yy, lam=lam) if task == "win" else fit_ridge(X, yy, lam=lam)
    return LinearModel(tuple(["intercept", *feature_cols]), coef, center, scale)


def predict_linear(model: LinearModel, df: pd.DataFrame, *, logistic: bool = False) -> pd.Series:
    """Apply a fold model. Scaler is applied here; do not call LinearModel.predict (would double-scale)."""
    cols = [c for c in model.feature_names if c != "intercept"]
    X, _idx, mask = design_matrix(df, tuple(cols), center=model.center, scale=model.scale)
    z = X @ model.coef
    if logistic:
        z = 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))
    out = pd.Series(np.nan, index=df.index, dtype=float)
    out.loc[mask] = z
    return out


def walk_forward_predict(
    df: pd.DataFrame,
    *,
    feature_cols: tuple[str, ...],
    task: Task,
    lam: float,
    standardize: bool = True,
) -> pd.Series:
    seasons = sorted(df["season"].dropna().unique().astype(int))
    preds = pd.Series(np.nan, index=df.index, dtype=float)
    for train_seasons, test_season in expanding_folds(seasons):
        train_df = df[df["season"].isin(train_seasons)]
        test_df = df[df["season"] == test_season]
        model = fit_fold(
            train_df,
            feature_cols=feature_cols,
            task=task,
            lam=lam,
            standardize=standardize,
        )
        if model is None or test_df.empty:
            continue
        hat = predict_linear(model, test_df, logistic=(task == "win"))
        preds.loc[test_df.index] = hat.loc[test_df.index]
    if task == "residual":
        market = pd.to_numeric(df["market_spread"], errors="coerce")
        return market + preds
    return preds


def walk_forward_calibrated_win(
    df: pd.DataFrame,
    *,
    feature_cols: tuple[str, ...],
    lam: float,
    method: str,
    standardize: bool = True,
) -> pd.Series:
    """Calibrator is fit on prior OOS seasons only (never the test season)."""
    from ml.evaluation.calibration import apply_isotonic, apply_platt, fit_isotonic, fit_platt

    seasons = sorted(df["season"].dropna().unique().astype(int))
    raw = pd.Series(np.nan, index=df.index, dtype=float)
    cal = pd.Series(np.nan, index=df.index, dtype=float)
    y = pd.to_numeric(df["home_win"], errors="coerce")
    for train_seasons, test_season in expanding_folds(seasons):
        train_df = df[df["season"].isin(train_seasons)]
        test_df = df[df["season"] == test_season]
        model = fit_fold(
            train_df,
            feature_cols=feature_cols,
            task="win",
            lam=lam,
            standardize=standardize,
        )
        if model is None or test_df.empty:
            continue
        hat = predict_linear(model, test_df, logistic=True)
        raw.loc[test_df.index] = hat.loc[test_df.index]
        prior = raw.loc[df["season"].isin(train_seasons)].dropna()
        prior_y = y.loc[prior.index]
        both = prior.notna() & prior_y.notna()
        if int(both.sum()) < 80:
            cal.loc[test_df.index] = hat.loc[test_df.index]
            continue
        p_tr = prior[both].to_numpy(dtype=float)
        y_tr = prior_y[both].to_numpy(dtype=float)
        te = hat.dropna()
        if method == "platt":
            a, b = fit_platt(p_tr, y_tr)
            cal.loc[te.index] = apply_platt(te.to_numpy(dtype=float), a, b)
        elif method == "isotonic":
            kx, ky = fit_isotonic(p_tr, y_tr)
            cal.loc[te.index] = apply_isotonic(te.to_numpy(dtype=float), kx, ky)
        else:
            cal.loc[test_df.index] = hat.loc[test_df.index]
    return cal
