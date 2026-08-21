"""Bounded 2009–2022 development search.

CLI: ``python -m ml.pregame.experiments``

Does not open 2023–2025. Does not freeze a feature_version.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from db.session import get_session_factory
from ml.evaluation.calibration import reliability_buckets
from ml.evaluation.leaderboard import evaluate_margin_frame, evaluate_win_frame
from ml.evaluation.protocol import (
    CANDIDATE_VERSION,
    DEV_SEASON_END,
    DEV_SEASON_START,
    LAMBDA_GRID,
    MODEL_LOGISTIC,
    MODEL_RIDGE_PURE,
    MODEL_RIDGE_RESIDUAL,
)
from ml.pregame.data import load_pregame_frame
from ml.pregame.families import FAMILIES, FAMILY_NOTES, PURE_KIND
from ml.pregame.freeze import write_freeze
from ml.pregame.persist import persist_oos_predictions
from ml.pregame.walk import walk_forward_calibrated_win, walk_forward_predict

logger = logging.getLogger(__name__)

SEARCH_NAME = "BCW-DEV-SEARCH-v0.1.json"
CANDIDATE_NAME = "BCW-RIDGE-CANDIDATE.json"

DEFAULT_LAM = 5.0
DEFAULT_FAMILY = "B"


def _json_ready(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _json_ready(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_ready(v) for v in obj]
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except (ValueError, AttributeError):
            return str(obj)
    return obj


def run_lambda_grid(df, family: str = DEFAULT_FAMILY) -> list[dict[str, Any]]:  # noqa: ANN001
    cols = FAMILIES[family]
    rows: list[dict[str, Any]] = []
    for lam in LAMBDA_GRID:
        pred = walk_forward_predict(df, feature_cols=cols, task="margin", lam=lam)
        frame = df.copy()
        frame["pred_margin"] = pred
        metrics = evaluate_margin_frame(frame, mu_col="pred_margin")
        rows.append(
            {
                "experiment_id": f"BCW-RIDGE-PURE/{family}/lam={lam}",
                "family": family,
                "lam": lam,
                "kind": PURE_KIND[family],
                "metrics": metrics,
            }
        )
        logger.info("Ridge λ=%s family=%s MAE=%s", lam, family, metrics.get("mae"))
    return rows


def run_family_grid(df, *, lam: float = DEFAULT_LAM) -> list[dict[str, Any]]:  # noqa: ANN001
    rows: list[dict[str, Any]] = []
    for letter, cols in FAMILIES.items():
        pred = walk_forward_predict(df, feature_cols=cols, task="margin", lam=lam)
        frame = df.copy()
        frame["pred_margin"] = pred
        metrics = evaluate_margin_frame(frame, mu_col="pred_margin")
        rows.append(
            {
                "experiment_id": f"BCW-RIDGE-PURE/{letter}/lam={lam}",
                "family": letter,
                "note": FAMILY_NOTES[letter],
                "lam": lam,
                "kind": PURE_KIND[letter],
                "metrics": metrics,
            }
        )
        logger.info("Ridge family %s MAE=%s", letter, metrics.get("mae"))
    return rows


def run_logistic_grid(df, *, family: str = DEFAULT_FAMILY) -> list[dict[str, Any]]:  # noqa: ANN001
    cols = FAMILIES[family]
    rows: list[dict[str, Any]] = []
    for lam in LAMBDA_GRID:
        pred = walk_forward_predict(df, feature_cols=cols, task="win", lam=lam)
        frame = df.copy()
        frame["home_win_prob"] = pred
        metrics = evaluate_win_frame(frame, prob_col="home_win_prob")
        buckets = reliability_buckets(
            frame.loc[pred.notna(), "home_win"].to_numpy(),
            pred.dropna().to_numpy(),
        )
        rows.append(
            {
                "experiment_id": f"BCW-LOGISTIC/{family}/lam={lam}",
                "family": family,
                "lam": lam,
                "metrics": metrics,
                "reliability": buckets,
            }
        )
        logger.info("Logistic λ=%s Brier=%s", lam, metrics.get("brier"))
    return rows


def run_logistic_families(df, *, lam: float = DEFAULT_LAM) -> list[dict[str, Any]]:  # noqa: ANN001
    rows: list[dict[str, Any]] = []
    for letter, cols in FAMILIES.items():
        pred = walk_forward_predict(df, feature_cols=cols, task="win", lam=lam)
        frame = df.copy()
        frame["home_win_prob"] = pred
        metrics = evaluate_win_frame(frame, prob_col="home_win_prob")
        rows.append(
            {
                "experiment_id": f"BCW-LOGISTIC/{letter}/lam={lam}",
                "family": letter,
                "lam": lam,
                "metrics": metrics,
            }
        )
    return rows


def run_calibration(df, *, family: str = DEFAULT_FAMILY, lam: float = DEFAULT_LAM) -> list[dict[str, Any]]:  # noqa: ANN001
    cols = FAMILIES[family]
    rows: list[dict[str, Any]] = []
    for method in ("none", "platt", "isotonic"):
        if method == "none":
            pred = walk_forward_predict(df, feature_cols=cols, task="win", lam=lam)
        else:
            pred = walk_forward_calibrated_win(df, feature_cols=cols, lam=lam, method=method)
        frame = df.copy()
        frame["home_win_prob"] = pred
        metrics = evaluate_win_frame(frame, prob_col="home_win_prob")
        rows.append({"experiment_id": f"BCW-LOGISTIC/{family}/{method}", "method": method, "metrics": metrics})
        logger.info("Logistic cal %s ECE=%s Brier=%s", method, metrics.get("ece"), metrics.get("brier"))
    return rows


def run_residual(df, *, family: str = DEFAULT_FAMILY, lam: float = DEFAULT_LAM) -> dict[str, Any]:  # noqa: ANN001
    cols = FAMILIES[family]
    hybrid = walk_forward_predict(df, feature_cols=cols, task="residual", lam=lam)
    pure = walk_forward_predict(df, feature_cols=cols, task="margin", lam=lam)
    hybrid_df = df.copy()
    hybrid_df["pred_margin"] = hybrid
    pure_df = df.copy()
    pure_df["pred_margin"] = pure
    market_df = df.copy()
    market_df["pred_margin"] = market_df["market_spread"]
    return {
        "experiment_id": f"{MODEL_RIDGE_RESIDUAL}/{family}/lam={lam}",
        "note": "Research only. Not a PURE model. μ = MarketMargin + residual_hat.",
        "market0": evaluate_margin_frame(market_df, mu_col="pred_margin"),
        "ridge_pure": evaluate_margin_frame(pure_df, mu_col="pred_margin"),
        "ridge_market_residual": evaluate_margin_frame(hybrid_df, mu_col="pred_margin"),
    }


def _best_mae(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [r for r in rows if isinstance(r.get("metrics", {}).get("mae"), (int, float))]
    if not scored:
        return None
    return min(scored, key=lambda r: r["metrics"]["mae"])


def run_search(session, *, persist: bool) -> dict[str, Any]:  # noqa: ANN001
    df = load_pregame_frame(session, season_start=DEV_SEASON_START, season_end=DEV_SEASON_END)
    logger.info("Dev search on %s REG games %s–%s", len(df), DEV_SEASON_START, DEV_SEASON_END)

    family_rows = run_family_grid(df)
    best_family = _best_mae(family_rows) or {"family": DEFAULT_FAMILY}
    fam = str(best_family.get("family") or DEFAULT_FAMILY)

    lambda_rows = run_lambda_grid(df, family=fam)
    best_lam_row = _best_mae(lambda_rows) or {"lam": DEFAULT_LAM}
    lam = float(best_lam_row.get("lam") or DEFAULT_LAM)

    logistic_lam = run_logistic_grid(df, family=fam)
    logistic_fam = run_logistic_families(df, lam=DEFAULT_LAM)
    logistic_cal = run_calibration(df, family=fam, lam=DEFAULT_LAM)
    residual = run_residual(df, family=fam, lam=lam)

    hfa = evaluate_margin_frame(df, mu_col="hfa_prior")
    srs = evaluate_margin_frame(df, mu_col="srs_pred_margin")

    candidate_pred = walk_forward_predict(df, feature_cols=FAMILIES[fam], task="margin", lam=lam)
    cand_df = df.copy()
    cand_df["pred_margin"] = candidate_pred
    candidate_metrics = evaluate_margin_frame(cand_df, mu_col="pred_margin")

    payload: dict[str, Any] = {
        "experiment_id": "BCW-DEV-SEARCH-v0.1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "window": {"season_start": DEV_SEASON_START, "season_end": DEV_SEASON_END, "season_type": "REG"},
        "holdout_opened": False,
        "n_games": int(len(df)),
        "protocol": {
            "metrics": ["brier", "log_loss", "ece", "mae", "rmse", "ats", "n", "bootstrap"],
            "standardize": True,
            "ewma_alpha_on_snapshots": 0.20,
            "family_F": FAMILY_NOTES["F"],
        },
        "baselines": {"BCW-HFA": hfa, "BCW-SRS": srs},
        "ridge_families": family_rows,
        "ridge_lambda": lambda_rows,
        "logistic_lambda": logistic_lam,
        "logistic_families": logistic_fam,
        "logistic_calibration": logistic_cal,
        "market_residual": residual,
        "candidate": {
            "model_name": MODEL_RIDGE_PURE,
            "model_version": CANDIDATE_VERSION,
            "family": fam,
            "lam": lam,
            "kind": PURE_KIND[fam],
            "metrics": candidate_metrics,
            "public_probability": False,
            "label": "Research Preview",
        },
        "notes": "Not a freeze. Raw vs adj still open. 2023–2025 sealed.",
    }

    if persist:
        n = persist_oos_predictions(
            session,
            cand_df,
            model_name=MODEL_RIDGE_PURE,
            model_version=CANDIDATE_VERSION,
            mu_col="pred_margin",
            extra={"family": fam, "lam": lam, "kind": PURE_KIND[fam]},
        )
        payload["persisted_rows"] = n
        logger.info("Persisted %s OOS candidate rows", n)

    return payload


def save_search(payload: dict[str, Any]) -> tuple[Path, Path]:
    settings = get_settings()
    out_dir = settings.data_dir / "walk_forward"
    out_dir.mkdir(parents=True, exist_ok=True)
    search_path = out_dir / SEARCH_NAME
    cand_path = out_dir / CANDIDATE_NAME
    ready = _json_ready(payload)
    search_path.write_text(json.dumps(ready, indent=2), encoding="utf-8")
    cand_path.write_text(json.dumps(_json_ready(payload["candidate"]), indent=2), encoding="utf-8")
    write_freeze(
        {
            "status": "searching",
            "ridge_family": payload["candidate"]["family"],
            "ridge_lambda": payload["candidate"]["lam"],
            "feature_version": payload["candidate"]["kind"],
            "ewma_alpha": 0.20,
        }
    )
    return search_path, cand_path


def load_candidate() -> dict[str, Any] | None:
    path = get_settings().data_dir / "walk_forward" / CANDIDATE_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_search() -> dict[str, Any] | None:
    path = get_settings().data_dir / "walk_forward" / SEARCH_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.pregame.experiments")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    session = get_session_factory()()
    try:
        payload = run_search(session, persist=not args.no_persist)
    finally:
        session.close()
    search_path, cand_path = save_search(payload)
    summary = {
        "saved": str(search_path),
        "candidate": str(cand_path),
        "ridge_family": payload["candidate"]["family"],
        "ridge_lambda": payload["candidate"]["lam"],
        "ridge_mae": payload["candidate"]["metrics"].get("mae"),
        "holdout_opened": False,
    }
    print(json.dumps(_json_ready(summary), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
