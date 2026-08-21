"""Unit tests for pregame logistic / Ridge (synthetic, no DB)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.evaluation.backtest import ats_accuracy, home_covers_actual
from ml.evaluation.leaderboard import evaluate_margin_frame, evaluate_win_frame
from ml.pregame import logistic, ridge_margin
from ml.pregame.feature_columns import ADJ_EPA_FEATURES, add_derived_columns


def _synthetic_frame(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    seasons = np.repeat(np.arange(2010, 2016), n // 6)
    elo_diff = rng.normal(0, 50, size=len(seasons))
    srs_diff = elo_diff / 100.0 + rng.normal(0, 0.5, size=len(seasons))
    rest_diff = rng.integers(-2, 3, size=len(seasons))
    success_rate_diff = rng.normal(0, 0.05, size=len(seasons))
    explosive_play_diff = rng.normal(0, 0.03, size=len(seasons))
    adj_off_diff = rng.normal(0, 0.08, size=len(seasons))
    adj_def_diff = rng.normal(0, 0.08, size=len(seasons))
    home_margin = (
        0.04 * elo_diff
        + 3.0 * srs_diff
        + 0.5 * rest_diff
        + 20.0 * success_rate_diff
        + rng.normal(0, 8, size=len(seasons))
    )
    spread = np.round(home_margin + rng.normal(0, 3, size=len(seasons)), 1)
    df = pd.DataFrame(
        {
            "season": seasons,
            "week": 1,
            "home_win": (home_margin > 0).astype(float),
            "home_margin": home_margin,
            "market_spread": spread,
            "elo_diff": elo_diff,
            "srs_diff": srs_diff,
            "rest_diff": rest_diff,
            "success_rate_diff": success_rate_diff,
            "explosive_play_diff": explosive_play_diff,
            "adj_off_home": adj_off_diff / 2,
            "adj_off_away": -adj_off_diff / 2,
            "adj_def_home": -adj_def_diff / 2,
            "adj_def_away": adj_def_diff / 2,
            "home_off_epa": adj_off_diff / 2,
            "away_off_epa": -adj_off_diff / 2,
            "home_def_epa": adj_def_diff / 2,
            "away_def_epa": -adj_def_diff / 2,
            "hfa_prior": 2.0,
            "srs_pred_margin": srs_diff * 3,
        }
    )
    return add_derived_columns(df)


def test_logistic_walk_forward_produces_probs() -> None:
    df = _synthetic_frame()
    oos = logistic.fit_and_predict_oos(df, feature_cols=ADJ_EPA_FEATURES)
    probs = oos["home_win_prob"].dropna()
    assert len(probs) > 50
    assert probs.between(0, 1).all()
    metrics = evaluate_win_frame(oos, prob_col="home_win_prob")
    assert metrics["n"] > 50
    assert metrics["brier"] < 0.35


def test_ridge_walk_forward_beats_noise() -> None:
    df = _synthetic_frame()
    oos = ridge_margin.fit_and_predict_oos(df, variant="adj")
    mu = oos["pred_margin"].dropna()
    assert len(mu) > 50
    metrics = evaluate_margin_frame(oos, mu_col="pred_margin")
    assert metrics["mae"] < 12.0


def test_nflverse_cover_rule() -> None:
    assert bool(home_covers_actual(np.array([7.0]), np.array([3.5]))[0])
    assert not bool(home_covers_actual(np.array([3.0]), np.array([3.5]))[0])
    res = ats_accuracy(np.array([10.0, 1.0]), np.array([14.0, 0.0]), np.array([3.5, -3.0]))
    assert res["n"] == 2
    assert res["correct"] == 2
