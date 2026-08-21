"""BCW-NFL-WP-XGB-MARKET-v0.1 — in-game WP with decaying pregame spread.

Adds ``spread_time``. This is a MARKET model. Never a PURE feature.
nflfastR publishes this as ``vegas_wp``; we keep that column name only as
the *reference label* from nflverse, not as a BlueChip feature.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from ml.reference.nflfastr.features import (
    LABEL_COL,
    MARKET_WP_FEATURES,
    load_pbp_seasons,
    wp_training_frame,
)
from ml.reference.nflfastr.validate import leave_one_season_out
from ml.reference.nflfastr.wp_model import fit_wp, predict_wp, score_wp

logger = logging.getLogger(__name__)

FAMILY = "BCW-nflfastR-replication-v1"
MODEL_ID = "BCW-NFL-WP-XGB-MARKET-v0.1"
MARKET_FEATURES = True

# Baldwin OSF 2020-09-28 spread-adjusted WP (approx.; monotone constraints omitted in v0.1).
NFLFASTR_VEGAS_WP_PRESET: dict[str, Any] = {
    "objective": "binary:logistic",
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.9224245,
    "colsample_bytree": 5 / 12,
    "n_estimators": 534,
    "min_child_weight": 7,
    "gamma": 0.79012017,
    "tree_method": "hist",
    "eval_metric": "logloss",
}


def train_holdout(
    *,
    train_seasons: list[int],
    test_season: int,
    preset: str = "bcw_v0.1",
    force_download: bool = False,
    n_estimators: int | None = None,
) -> dict[str, Any]:
    seasons = sorted(set(train_seasons) | {test_season})
    raw = load_pbp_seasons(seasons, force_download=force_download)
    frame = wp_training_frame(raw, market=True)
    train = frame[frame["season"].isin(train_seasons)]
    test = frame[frame["season"] == test_season]
    model = fit_wp(
        train,
        preset=preset,
        features=MARKET_WP_FEATURES,
        n_estimators=n_estimators,
    )
    pred = predict_wp(model, test, features=MARKET_WP_FEATURES)
    y = test[LABEL_COL].to_numpy(dtype=float)
    nfl_wp = test["vegas_wp"].to_numpy(dtype=float) if "vegas_wp" in test.columns else None
    metrics = score_wp(y, pred, nflverse_wp=nfl_wp)
    metrics.update(
        {
            "model_id": MODEL_ID,
            "family": FAMILY,
            "market_features": MARKET_FEATURES,
            "preset": preset,
            "train_seasons": train_seasons,
            "test_season": test_season,
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "features": MARKET_WP_FEATURES,
            "reference_column": "vegas_wp",
        }
    )
    return {"model": model, "metrics": metrics, "pred": pred, "test": test}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ml.reference.nflfastr.vegas_wp_model",
        description="Train MARKET in-game WP (spread_time). Not a PURE model.",
    )
    parser.add_argument("--train-season", type=int, action="append", required=True)
    parser.add_argument("--test-season", type=int, required=True)
    parser.add_argument("--preset", default="bcw_v0.1")
    parser.add_argument("--n-estimators", type=int, default=None)
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--loso", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    train_seasons = sorted(set(args.train_season))
    if args.loso:
        seasons = sorted(set(train_seasons) | {args.test_season})
        raw = load_pbp_seasons(seasons, force_download=args.force_download)
        frame = wp_training_frame(raw, market=True)
        for train_s, holdout in leave_one_season_out(seasons):
            train = frame[frame["season"].isin(train_s)]
            test = frame[frame["season"] == holdout]
            model = fit_wp(
                train,
                preset=args.preset,
                features=MARKET_WP_FEATURES,
                n_estimators=args.n_estimators,
            )
            pred = predict_wp(model, test, features=MARKET_WP_FEATURES)
            y = test[LABEL_COL].to_numpy(dtype=float)
            nfl_wp = test["vegas_wp"].to_numpy(dtype=float) if "vegas_wp" in test.columns else None
            m = score_wp(y, pred, nflverse_wp=nfl_wp)
            m["holdout_season"] = holdout
            print(json.dumps(m, default=str))
        return 0

    result = train_holdout(
        train_seasons=train_seasons,
        test_season=args.test_season,
        preset=args.preset,
        force_download=args.force_download,
        n_estimators=args.n_estimators,
    )
    print(json.dumps(result["metrics"], indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
