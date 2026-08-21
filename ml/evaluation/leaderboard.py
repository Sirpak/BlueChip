"""Aggregate walk-forward leaderboard metrics (no ROI/units)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.markets.spread import NFL_SIGMA, p_home_win
from ml.evaluation.backtest import (
    ats_accuracy,
    home_covers_actual,
    market0_picks_home_cover,
    model_picks_home_cover,
    stern_home_cover_prob,
)
from ml.evaluation.bootstrap import bootstrap_ci, interval_payload
from ml.evaluation.brier import brier_score
from ml.evaluation.calibration import calibration_table, expected_calibration_error
from ml.evaluation.log_loss import log_loss
from ml.evaluation.margin_metrics import mae, rmse
from ml.reference.nflfastr.validate import metrics_payload, roc_auc


def _market_home_win_prob(spread_line: np.ndarray) -> np.ndarray:
    s = np.asarray(spread_line, dtype=float)
    out = np.full_like(s, np.nan, dtype=float)
    for i, line in enumerate(s):
        if np.isfinite(line):
            home_spread = -float(line)
            mu = -home_spread
            out[i] = p_home_win(mu, NFL_SIGMA, continuity=True)
    return out


def evaluate_win_frame(
    df: pd.DataFrame,
    *,
    prob_col: str,
    label_col: str = "home_win",
    spread_col: str = "market_spread",
) -> dict[str, Any]:
    block = df[[prob_col, label_col, spread_col]].apply(pd.to_numeric, errors="coerce")
    mask = block[prob_col].notna() & block[label_col].notna()
    y = block.loc[mask, label_col].to_numpy(dtype=float)
    p = block.loc[mask, prob_col].to_numpy(dtype=float)
    if len(y) == 0:
        return {"n": 0}
    cal = calibration_table(y, p)
    out: dict[str, Any] = metrics_payload(y, p)
    out["ece"] = expected_calibration_error(cal)
    out["brier_interval"] = interval_payload(bootstrap_ci(y, p, brier_score))
    out["log_loss_interval"] = interval_payload(bootstrap_ci(y, p, log_loss))
    spread = block.loc[mask, spread_col].to_numpy(dtype=float)
    m_prob = _market_home_win_prob(spread)
    m_mask = np.isfinite(m_prob)
    if m_mask.sum():
        out["market0_brier"] = brier_score(y[m_mask], m_prob[m_mask])
        out["market0_log_loss"] = log_loss(y[m_mask], m_prob[m_mask])
    return out


def evaluate_margin_frame(
    df: pd.DataFrame,
    *,
    mu_col: str,
    margin_col: str = "home_margin",
    spread_col: str = "market_spread",
) -> dict[str, Any]:
    block = df[[mu_col, margin_col, spread_col]].apply(pd.to_numeric, errors="coerce")
    mask = block[mu_col].notna() & block[margin_col].notna()
    y = block.loc[mask, margin_col].to_numpy(dtype=float)
    mu = block.loc[mask, mu_col].to_numpy(dtype=float)
    spread = block.loc[mask, spread_col].to_numpy(dtype=float)
    if len(y) == 0:
        return {"n": 0}
    out: dict[str, Any] = {
        "n": int(len(y)),
        "mae": mae(y, mu),
        "rmse": rmse(y, mu),
        "mae_interval": interval_payload(bootstrap_ci(y, mu, mae)),
        "rmse_interval": interval_payload(bootstrap_ci(y, mu, rmse)),
    }
    out.update(ats_accuracy(mu, y, spread))
    # Market 0 ATS: pick home when line >= 0 (home favored or pick'em).
    m_pick = market0_picks_home_cover(spread)
    actual = home_covers_actual(y, spread)
    m_mask = np.isfinite(spread)
    if m_mask.sum():
        out["market0_ats_pct"] = float(np.mean(m_pick[m_mask] == actual[m_mask]))
    # Win metrics via Stern on μ
    p_win = np.array([p_home_win(float(m), NFL_SIGMA, continuity=True) for m in mu])
    hw = (y > 0).astype(float)
    out["brier"] = brier_score(hw, p_win)
    out["log_loss"] = log_loss(hw, p_win)
    out["auc"] = roc_auc(hw, p_win)
    p_cover = stern_home_cover_prob(mu, spread)
    cover_mask = np.isfinite(p_cover) & np.isfinite(spread)
    if cover_mask.sum():
        actual_cover = home_covers_actual(y, spread).astype(float)
        out["cover_brier"] = brier_score(actual_cover[cover_mask], p_cover[cover_mask])
    return out


def compare_ridge_variants(
    raw_df: pd.DataFrame,
    adj_df: pd.DataFrame,
) -> dict[str, Any]:
    raw_metrics = evaluate_margin_frame(raw_df, mu_col="pred_margin")
    adj_metrics = evaluate_margin_frame(adj_df, mu_col="pred_margin")
    winner = "adj"
    if np.isfinite(raw_metrics.get("mae", np.nan)) and np.isfinite(adj_metrics.get("mae", np.nan)):
        if raw_metrics["mae"] < adj_metrics["mae"]:
            winner = "raw"
    return {
        "raw_epa": raw_metrics,
        "adj_epa": adj_metrics,
        "recommended_variant": winner,
    }
