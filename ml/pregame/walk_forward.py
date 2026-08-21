"""Season walk-forward on 2009–2022 development window.

CLI: ``python -m ml.pregame.walk_forward``
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
from ml.evaluation.leaderboard import compare_ridge_variants, evaluate_margin_frame, evaluate_win_frame
from ml.pregame import logistic, ridge_margin
from ml.pregame.data import load_pregame_frame
from ml.pregame.feature_columns import DEV_SEASON_END, DEV_SEASON_START, MODEL_LOGISTIC, MODEL_RIDGE
from ml.pregame.ridge_margin import train as train_ridge

logger = logging.getLogger(__name__)

ARTIFACT_NAME = "BCW-WF-v0.1.json"


def run_walk_forward(session) -> dict[str, Any]:  # noqa: ANN001
    df = load_pregame_frame(
        session,
        season_start=DEV_SEASON_START,
        season_end=DEV_SEASON_END,
    )
    logger.info("Loaded %s REG games (%s–%s)", len(df), DEV_SEASON_START, DEV_SEASON_END)

    log_oos = logistic.fit_and_predict_oos(df)
    ridge_raw = ridge_margin.fit_and_predict_oos(df, variant="raw")
    ridge_adj = ridge_margin.fit_and_predict_oos(df, variant="adj")

    # Full-window refit for coefficient export (not used as OOS metrics).
    full_adj_model = train_ridge(df, variant="adj")

    logistic_metrics = evaluate_win_frame(log_oos, prob_col="home_win_prob")
    ridge_compare = compare_ridge_variants(ridge_raw, ridge_adj)
    hfa_baseline = evaluate_margin_frame(df, mu_col="hfa_prior")
    srs_baseline = evaluate_margin_frame(df, mu_col="srs_pred_margin")

    payload: dict[str, Any] = {
        "experiment_id": "BCW-WF-v0.1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "window": {"season_start": DEV_SEASON_START, "season_end": DEV_SEASON_END, "season_type": "REG"},
        "n_games": int(len(df)),
        "models": {
            MODEL_LOGISTIC: logistic_metrics,
            MODEL_RIDGE: ridge_compare,
            "BCW-HFA": hfa_baseline,
            "BCW-SRS": srs_baseline,
        },
        "ridge_full_fit_adj_coef": ridge_margin.summary_payload(full_adj_model, variant="adj"),
        "notes": "OOS season walk-forward inside 2009–2022. Holdout 2023–2025 not opened.",
    }
    return payload


def save_artifact(payload: dict[str, Any], path: Path | None = None) -> Path:
    settings = get_settings()
    out_dir = settings.data_dir / "walk_forward"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = path or (out_dir / ARTIFACT_NAME)
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def load_artifact(path: Path | None = None) -> dict[str, Any] | None:
    settings = get_settings()
    dest = path or (settings.data_dir / "walk_forward" / ARTIFACT_NAME)
    if not dest.is_file():
        return None
    return json.loads(dest.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.pregame.walk_forward")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--out", type=Path, default=None, help="Optional output JSON path")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    session = get_session_factory()()
    try:
        payload = run_walk_forward(session)
    finally:
        session.close()
    dest = save_artifact(payload, args.out)
    print(json.dumps({"saved": str(dest), "n_games": payload["n_games"], "models": payload["models"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
