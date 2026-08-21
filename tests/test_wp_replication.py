"""nflfastR-shaped WP features and a tiny Python XGBoost fit (no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.evaluation.brier import brier_score
from ml.evaluation.log_loss import log_loss
from ml.reference.nflfastr.ep_model import NEXT_SCORE_CLASSES, ep_from_probs
from ml.reference.nflfastr.features import (
    MARKET_WP_FEATURES,
    PURE_WP_FEATURES,
    add_wp_features,
    diff_time_ratio,
    elapsed_share,
    spread_time,
    wp_training_frame,
)
from ml.reference.nflfastr.validate import chronological_walk_forward, leave_one_season_out, roc_auc
from ml.reference.nflfastr.wp_model import MARKET_FEATURES, MODEL_ID, fit_wp, predict_wp, score_wp


def _plays(**overrides) -> pd.DataFrame:
    base = {
        "game_id": ["2024_01_NE_SEA"] * 6,
        "play_id": [1, 2, 3, 4, 5, 6],
        "season": [2024] * 6,
        "qtr": [1, 2, 3, 4, 5, 4],
        "home_team": ["SEA"] * 6,
        "away_team": ["NE"] * 6,
        "posteam": ["SEA", "NE", "SEA", "SEA", "SEA", "SEA"],
        "play_type": ["kickoff", "pass", "run", "pass", "pass", "pass"],
        "down": [np.nan, 1, 2, 1, 1, 1],
        "ydstogo": [np.nan, 10, 7, 10, 10, 10],
        "yardline_100": [np.nan, 75, 40, 20, 20, 20],
        "half_seconds_remaining": [1800, 800, 1800, 120, 120, 120],
        "game_seconds_remaining": [3600, 2600, 1800, 120, 120, 120],
        "score_differential": [0, -3, 4, 7, 7, 7],
        "result": [3, 3, 3, 3, 3, 0],
        "posteam_timeouts_remaining": [3, 3, 3, 2, 2, 2],
        "defteam_timeouts_remaining": [3, 3, 3, 1, 1, 1],
        "spread_line": [3.5, 3.5, 3.5, 3.5, 3.5, 3.5],
        "wp": [0.55, 0.42, 0.70, 0.88, 0.88, 0.88],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_diff_time_ratio_matches_blog_and_r_forms() -> None:
    gsr = np.array([3600.0, 1800.0, 0.0])
    sd = np.array([7.0, 7.0, 7.0])
    share = elapsed_share(gsr)
    blog = sd * np.exp(4.0 * share)
    r_form = sd / np.exp(-4.0 * share)
    got = diff_time_ratio(sd, gsr)
    np.testing.assert_allclose(got, blog)
    np.testing.assert_allclose(got, r_form)
    np.testing.assert_allclose(got[0], 7.0)


def test_spread_time_decays_toward_zero() -> None:
    spread = np.array([7.0, 7.0, 7.0])
    gsr = np.array([3600.0, 1800.0, 0.0])
    st = spread_time(spread, gsr)
    assert st[0] == 7.0
    assert st[1] < st[0]
    assert st[2] < st[1]
    np.testing.assert_allclose(st[2], 7.0 * np.exp(-4.0))


def test_add_wp_features_posteam_spread_and_label() -> None:
    featured = add_wp_features(_plays())
    sea_open = featured.iloc[0]
    assert sea_open["home"] == 1
    assert sea_open["posteam_spread"] == 3.5
    # home won by 3; SEA on offense → label 1; NE on offense → 0
    assert featured.iloc[0]["label"] == 1
    assert featured.iloc[1]["label"] == 0


def test_receive_2h_ko_engineered_when_missing() -> None:
    featured = add_wp_features(_plays())
    # Opening kickoff receiver is SEA (posteam on first kickoff).
    # First-half non-receiver NE should get the 2nd-half kickoff.
    assert featured.iloc[0]["receive_2h_ko"] == 0  # SEA, Q1
    assert featured.iloc[1]["receive_2h_ko"] == 1  # NE, Q2
    assert featured.iloc[2]["receive_2h_ko"] == 0  # second half


def test_training_filter_drops_ot_ties_and_missing_down() -> None:
    frame = wp_training_frame(_plays(), market=False)
    # rows: kickoff (no down), OT, tie — gone. Keep Q2 NE, Q3 SEA, Q4 SEA (result 3).
    assert set(frame["qtr"]) <= {1, 2, 3, 4}
    assert frame["down"].notna().all()
    assert "spread_time" not in frame.columns
    assert set(PURE_WP_FEATURES).issubset(frame.columns)


def test_pure_features_exclude_spread() -> None:
    assert "spread_time" not in PURE_WP_FEATURES
    assert "spread_time" in MARKET_WP_FEATURES
    assert MARKET_FEATURES is False
    assert MODEL_ID == "BCW-NFL-WP-XGB-v0.1"


def test_loso_and_walk_forward() -> None:
    loso = list(leave_one_season_out([2023, 2024, 2025]))
    assert loso[0] == ([2024, 2025], 2023)
    assert loso[-1] == ([2023, 2024], 2025)
    wf = list(chronological_walk_forward([2023, 2024, 2025]))
    assert wf[0] == ([2023], 2024)
    assert wf[1] == ([2023, 2024], 2025)


def test_tiny_xgb_fit_and_metrics() -> None:
    rng = np.random.default_rng(0)
    n = 80
    score_diff = rng.integers(-14, 15, size=n)
    home = rng.integers(0, 2, size=n)
    result = np.where(score_diff + 2 * home > 0, 1, -1)
    result[0] = 3
    df = pd.DataFrame(
        {
            "game_id": [f"g{i // 10}" for i in range(n)],
            "play_id": np.arange(n),
            "season": [2024] * n,
            "qtr": rng.integers(1, 5, size=n),
            "home_team": "SEA",
            "away_team": "NE",
            "posteam": np.where(home == 1, "SEA", "NE"),
            "play_type": "pass",
            "down": rng.integers(1, 5, size=n),
            "ydstogo": rng.integers(1, 15, size=n),
            "yardline_100": rng.integers(1, 99, size=n),
            "half_seconds_remaining": rng.integers(1, 1800, size=n),
            "game_seconds_remaining": rng.integers(1, 3600, size=n),
            "score_differential": score_diff,
            "result": np.where(home == 1, result, -result),
            "posteam_timeouts_remaining": 3,
            "defteam_timeouts_remaining": 3,
            "spread_line": 3.0,
            "wp": 0.5,
            "receive_2h_ko": 0,
        }
    )
    # result: positive = home won. Construct consistently.
    home_win = (score_diff >= 0).astype(int)
    df["result"] = np.where(home_win == 1, 3, -3)
    frame = wp_training_frame(df, market=False)
    assert len(frame) == n
    model = fit_wp(frame, preset="nflfastr_wp", n_estimators=8)
    pred = predict_wp(model, frame)
    assert pred.shape == (n,)
    assert 0.0 <= pred.min() <= pred.max() <= 1.0
    metrics = score_wp(frame["label"].to_numpy(), pred, nflverse_wp=frame["wp"].to_numpy())
    assert metrics["brier"] < 0.3
    assert "nflverse_wp" in metrics


def test_ep_from_probs_td_is_seven() -> None:
    p = np.zeros((1, 7))
    p[0, NEXT_SCORE_CLASSES.index("touchdown")] = 1.0
    np.testing.assert_allclose(ep_from_probs(p), [7.0])


def test_brier_log_loss_auc_sanity() -> None:
    y = np.array([0.0, 0.0, 1.0, 1.0])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert brier_score(y, p) < 0.05
    assert log_loss(y, p) < 0.3
    assert roc_auc(y, p) == 1.0
