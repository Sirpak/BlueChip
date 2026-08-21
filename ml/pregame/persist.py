"""Persist walk-forward OOS rows to model_predictions (2009–2022 only)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.markets.spread import NFL_SIGMA, p_home_win
from db.models import ModelPrediction


def persist_oos_predictions(
    session: Session,
    df: pd.DataFrame,
    *,
    model_name: str,
    model_version: str,
    mu_col: str | None = None,
    prob_col: str | None = None,
    extra: dict | None = None,
) -> int:
    """Upsert OOS rows. Never writes 2023–2025 holdout labels as training evidence."""
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    for rec in df.to_dict(orient="records"):
        season = int(rec["season"])
        if season >= 2023:
            continue
        mu = rec.get(mu_col) if mu_col else None
        prob = rec.get(prob_col) if prob_col else None
        if mu is None or (isinstance(mu, float) and pd.isna(mu)):
            if prob is None or (isinstance(prob, float) and pd.isna(prob)):
                continue
        if prob is None or (isinstance(prob, float) and pd.isna(prob)):
            if mu is not None and not pd.isna(mu):
                prob = p_home_win(float(mu), NFL_SIGMA, continuity=True)
        kick = rec.get("kickoff") or rec.get("prediction_at")
        try:
            if kick is not None and pd.isna(kick):
                kick = None
        except (TypeError, ValueError):
            pass
        if hasattr(kick, "to_pydatetime"):
            kick = kick.to_pydatetime()
        if isinstance(kick, datetime) and kick.tzinfo is None:
            kick = kick.replace(tzinfo=timezone.utc)
        if not isinstance(kick, datetime):
            kick = now
        rows.append(
            {
                "game_id": rec["game_id"],
                "model_name": model_name,
                "model_version": model_version,
                "home_win_prob": float(prob),
                "predicted_spread": None if mu is None or pd.isna(mu) else float(mu),
                "predicted_total": None,
                "market_home_win_prob": None,
                "edge": None,
                "features_json": json.dumps(extra or {}, separators=(",", ":")),
                "predicted_at": kick if kick else now,
            }
        )
    if not rows:
        return 0
    n_cols = len(rows[0])
    batch = max(1, 900 // n_cols)
    for i in range(0, len(rows), batch):
        stmt = sqlite_insert(ModelPrediction).values(rows[i : i + batch])
        stmt = stmt.on_conflict_do_update(
            index_elements=["game_id", "model_name", "model_version"],
            set_={
                "home_win_prob": stmt.excluded.home_win_prob,
                "predicted_spread": stmt.excluded.predicted_spread,
                "features_json": stmt.excluded.features_json,
                "predicted_at": stmt.excluded.predicted_at,
            },
        )
        session.execute(stmt)
    session.commit()
    return len(rows)
