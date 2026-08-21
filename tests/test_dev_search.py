"""Synthetic development-search helpers (no DB)."""

import numpy as np
import pandas as pd

from ml.evaluation.bootstrap import bootstrap_ci
from ml.evaluation.brier import brier_score
from ml.evaluation.calibration import apply_platt, fit_platt, reliability_buckets
from ml.pregame.families import FAMILIES
from ml.pregame.walk import walk_forward_predict


def test_ridge_family_walk_forward() -> None:
    rng = np.random.default_rng(1)
    n = 240
    seasons = np.repeat(np.arange(2010, 2016), n // 6)
    elo = rng.normal(0, 40, len(seasons))
    df = pd.DataFrame(
        {
            "season": seasons,
            "elo_diff": elo,
            "srs_diff": elo / 80,
            "hfa_prior": 2.0,
            "rest_diff": 0.0,
            "off_epa_diff": elo / 400,
            "def_epa_diff": -elo / 500,
            "home_margin": 0.05 * elo + rng.normal(0, 9, len(seasons)),
            "home_win": (0.05 * elo + rng.normal(0, 9, len(seasons)) > 0).astype(float),
            "market_spread": 0.04 * elo,
        }
    )
    pred = walk_forward_predict(df, feature_cols=FAMILIES["A"], task="margin", lam=5.0)
    assert pred.notna().sum() > 100


def test_platt_and_bootstrap() -> None:
    p = np.linspace(0.2, 0.8, 80)
    y = (p + 0.05 > 0.5).astype(float)
    a, b = fit_platt(p, y)
    cal = apply_platt(p, a, b)
    assert cal.min() >= 0 and cal.max() <= 1
    buckets = reliability_buckets(y, cal)
    assert len(buckets) >= 5
    ci = bootstrap_ci(y, cal, brier_score, n_boot=50)
    assert ci["n"] == 80
