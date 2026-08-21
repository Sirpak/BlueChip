"""BCW-NFL-WP-XGB-v0.1 — in-game P(possession team wins).

Question nflfastR asks: given *current* game state, P(posteam eventually wins).
That is not the BlueChip pregame question (distribution of final margin).

PURE features only. ``spread_time`` belongs in ``vegas_wp_model``.

Training uses native ``xgboost.train`` (same family as R ``xgboost()``),
not the sklearn ``XGBClassifier`` wrapper.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb

from app.config import ROOT_DIR
from ml.evaluation.brier import brier_score
from ml.evaluation.calibration import calibration_table, expected_calibration_error
from ml.evaluation.log_loss import log_loss
from ml.reference.nflfastr.features import (
    LABEL_COL,
    PURE_WP_FEATURES,
    load_pbp_seasons,
    wp_training_frame,
)
from ml.reference.nflfastr.validate import leave_one_season_out, metrics_payload, roc_auc

logger = logging.getLogger(__name__)

FAMILY = "BCW-nflfastR-replication-v1"
MODEL_ID = "BCW-NFL-WP-XGB-v0.1"
MARKET_FEATURES = False

# Baldwin OSF 2020-09-28 published WP (non-spread) hyperparameters.
NFLFASTR_WP_PRESET: dict[str, Any] = {
    "objective": "binary:logistic",
    "max_depth": 4,
    "learning_rate": 0.2,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_estimators": 65,
    "min_child_weight": 1,
    "gamma": 0,
    "tree_method": "hist",
    "eval_metric": "logloss",
}

# Our first Python replication run — EP-like schedule, more trees.
BCW_V01_PRESET: dict[str, Any] = {
    "objective": "binary:logistic",
    "max_depth": 5,
    "learning_rate": 0.025,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_estimators": 500,
    "tree_method": "hist",
    "eval_metric": "logloss",
}

PRESETS = {
    "bcw_v0.1": BCW_V01_PRESET,
    "nflfastr_wp": NFLFASTR_WP_PRESET,
}


@dataclass
class WpModel:
    """Native xgboost Booster — same API family as nflfastR's R ``xgboost()``."""

    booster: xgb.Booster
    features: list[str]
    preset: str

    def save_model(self, path: Path | str) -> None:
        self.booster.save_model(str(path))


def booster_params(
    *,
    preset: str = "bcw_v0.1",
    n_estimators: int | None = None,
    seed: int = 42,
    **overrides: Any,
) -> tuple[dict[str, Any], int]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}; expected one of {sorted(PRESETS)}")
    raw = {**PRESETS[preset], **overrides}
    rounds = int(n_estimators if n_estimators is not None else raw.pop("n_estimators"))
    raw.pop("n_estimators", None)
    if "learning_rate" in raw:
        raw["eta"] = raw.pop("learning_rate")
    raw["seed"] = seed
    return raw, rounds


def fit_wp(
    frame: pd.DataFrame,
    *,
    preset: str = "bcw_v0.1",
    features: list[str] | None = None,
    n_estimators: int | None = None,
    **fit_kwargs: Any,
) -> WpModel:
    cols = features or PURE_WP_FEATURES
    params, rounds = booster_params(preset=preset, n_estimators=n_estimators, **fit_kwargs)
    x = frame[cols].to_numpy(dtype=float)
    y = frame[LABEL_COL].to_numpy(dtype=float)
    dtrain = xgb.DMatrix(x, label=y, feature_names=cols)
    booster = xgb.train(params, dtrain, num_boost_round=rounds)
    return WpModel(booster=booster, features=cols, preset=preset)


def predict_wp(
    model: WpModel,
    frame: pd.DataFrame,
    *,
    features: list[str] | None = None,
) -> np.ndarray:
    cols = features or model.features
    x = frame[cols].to_numpy(dtype=float)
    dtest = xgb.DMatrix(x, feature_names=cols)
    return np.asarray(model.booster.predict(dtest), dtype=float)


def score_wp(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    *,
    nflverse_wp: np.ndarray | None = None,
) -> dict[str, Any]:
    payload = metrics_payload(y_true, y_prob)
    if nflverse_wp is not None:
        ref = np.asarray(nflverse_wp, dtype=float)
        mask = np.isfinite(ref)
        payload["nflverse_wp"] = {
            "n": int(mask.sum()),
            "brier": brier_score(y_true[mask], ref[mask]) if mask.any() else None,
            "log_loss": log_loss(y_true[mask], ref[mask]) if mask.any() else None,
            "mae_vs_bcw": (
                float(np.mean(np.abs(y_prob[mask] - ref[mask]))) if mask.any() else None
            ),
        }
    return payload


def train_holdout(
    *,
    train_seasons: list[int],
    test_season: int,
    preset: str = "bcw_v0.1",
    force_download: bool = False,
    n_estimators: int | None = None,
) -> dict[str, Any]:
    seasons = sorted(set(train_seasons) | {test_season})
    logger.info("Loading PBP seasons %s", seasons)
    raw = load_pbp_seasons(seasons, force_download=force_download)
    frame = wp_training_frame(raw, market=False)
    train = frame[frame["season"].isin(train_seasons)]
    test = frame[frame["season"] == test_season]
    logger.info("Train rows=%s test rows=%s preset=%s", len(train), len(test), preset)

    model = fit_wp(train, preset=preset, n_estimators=n_estimators)
    pred = predict_wp(model, test)
    y = test[LABEL_COL].to_numpy(dtype=float)
    nfl_wp = test["wp"].to_numpy(dtype=float) if "wp" in test.columns else None
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
            "features": PURE_WP_FEATURES,
        }
    )
    cal = calibration_table(y, pred)
    metrics["ece"] = expected_calibration_error(cal)
    metrics["auc"] = roc_auc(y, pred)
    return {"model": model, "metrics": metrics, "calibration": cal, "test": test, "pred": pred}


def save_run(result: dict[str, Any], dest_dir: Path | None = None) -> Path:
    dest_dir = dest_dir or (ROOT_DIR / "data" / "models")
    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = MODEL_ID
    model_path = dest_dir / f"{stem}.json"
    result["model"].save_model(model_path)
    meta = {k: v for k, v in result["metrics"].items()}
    (dest_dir / f"{stem}.metrics.json").write_text(
        json.dumps(meta, indent=2, default=str),
        encoding="utf-8",
    )
    result["calibration"].to_csv(dest_dir / f"{stem}.calibration.csv", index=False)
    return model_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ml.reference.nflfastr.wp_model",
        description="Train BCW-NFL-WP-XGB-v0.1 (PURE in-game WP, Python XGBoost).",
    )
    parser.add_argument("--train-season", type=int, action="append", required=True)
    parser.add_argument("--test-season", type=int, required=True)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="bcw_v0.1")
    parser.add_argument("--n-estimators", type=int, default=None)
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--save", action="store_true", help="Write model + metrics under data/models/")
    parser.add_argument("--loso", action="store_true", help="Leave-one-season-out over train+test seasons")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    train_seasons = sorted(set(args.train_season))

    if args.loso:
        seasons = sorted(set(train_seasons) | {args.test_season})
        raw = load_pbp_seasons(seasons, force_download=args.force_download)
        frame = wp_training_frame(raw, market=False)
        for train_s, holdout in leave_one_season_out(seasons):
            train = frame[frame["season"].isin(train_s)]
            test = frame[frame["season"] == holdout]
            model = fit_wp(train, preset=args.preset, n_estimators=args.n_estimators)
            pred = predict_wp(model, test)
            y = test[LABEL_COL].to_numpy(dtype=float)
            nfl_wp = test["wp"].to_numpy(dtype=float) if "wp" in test.columns else None
            m = score_wp(y, pred, nflverse_wp=nfl_wp)
            m["holdout_season"] = holdout
            m["n_test"] = int(len(test))
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
    if args.save:
        path = save_run(result)
        print(f"saved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
