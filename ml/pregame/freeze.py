"""Write / load the BCW-v0.1 freeze artifact. Holdout stays closed until David signs off."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from ml.evaluation.protocol import DEV_SEASON_END, DEV_SEASON_START, HOLDOUT_SEASON_END, HOLDOUT_SEASON_START, METRICS

FREEZE_NAME = "BCW-v0.1-freeze.json"


def freeze_path() -> Path:
    return get_settings().data_dir / "model_freezes" / FREEZE_NAME


def default_freeze() -> dict[str, Any]:
    return {
        "development_period": f"{DEV_SEASON_START}-{DEV_SEASON_END}",
        "holdout_period": f"{HOLDOUT_SEASON_START}-{HOLDOUT_SEASON_END}",
        "feature_version": None,
        "ridge_family": None,
        "ridge_lambda": None,
        "ewma_alpha": 0.20,
        "logistic_family": None,
        "logistic_lambda": None,
        "probability_conversion": None,
        "calibration_method": None,
        "metrics": list(METRICS),
        "holdout_opened": False,
        "status": "searching",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": "Protocol frozen. Feature λ/α/family not frozen. 2023–2025 sealed.",
    }


def write_freeze(payload: dict[str, Any] | None = None) -> Path:
    dest = freeze_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = default_freeze()
    if payload:
        body.update(payload)
        body["holdout_opened"] = False
    dest.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return dest


def load_freeze() -> dict[str, Any] | None:
    dest = freeze_path()
    if not dest.is_file():
        return None
    return json.loads(dest.read_text(encoding="utf-8"))
