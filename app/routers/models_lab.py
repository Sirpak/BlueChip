"""Model Lab leaderboard and Research Preview slate."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_entitlement
from db.models import FeatureSnapshot, ModelPrediction, User
from db.session import get_session
from ml.evaluation.protocol import CANDIDATE_VERSION, MODEL_RIDGE_PURE
from ml.pregame.experiments import load_candidate, load_search
from ml.pregame.freeze import load_freeze
from ml.pregame.walk_forward import load_artifact

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/leaderboard")
def models_leaderboard(_user: User = Depends(require_entitlement("backtests_standard"))) -> dict:
    """Latest 2009–2022 walk-forward metrics. No ROI/units. Holdout sealed."""
    artifact = load_artifact()
    search = load_search()
    if artifact is None and search is None:
        return {"available": False, "message": "Run python -m ml.pregame.experiments"}
    return {
        "available": True,
        "walk_forward": artifact,
        "dev_search": search,
        "candidate": load_candidate(),
        "freeze": load_freeze(),
        "holdout_opened": False,
        "public_probability": False,
    }


@router.get("/candidate")
def models_candidate(_user: User = Depends(require_entitlement("models_full"))) -> dict:
    cand = load_candidate()
    if cand is None:
        return {
            "available": False,
            "label": "Research Preview",
            "public_probability": False,
            "message": "Run python -m ml.pregame.experiments",
        }
    return {"available": True, "public_probability": False, **cand}


@router.get("/slate")
def models_slate(
    session: Session = Depends(get_session),
    _user: User = Depends(require_entitlement("models_full")),
) -> dict:
    """Candidate μ for games that have persisted OOS/live predictions. Never a public cover %."""
    cand = load_candidate() or {}
    rows = (
        session.query(ModelPrediction, FeatureSnapshot)
        .join(FeatureSnapshot, FeatureSnapshot.game_id == ModelPrediction.game_id)
        .filter(
            ModelPrediction.model_name == MODEL_RIDGE_PURE,
            ModelPrediction.model_version == CANDIDATE_VERSION,
        )
        .order_by(FeatureSnapshot.season.desc(), FeatureSnapshot.week.desc())
        .limit(40)
        .all()
    )
    games = []
    for pred, snap in rows:
        games.append(
            {
                "game_id": pred.game_id,
                "season": snap.season,
                "week": snap.week,
                "home_team": snap.home_team,
                "away_team": snap.away_team,
                "market_spread": snap.market_spread,
                "projected_margin": pred.predicted_spread,
                "public_probability": None,
                "model": f"{pred.model_name}-{pred.model_version}",
            }
        )
    return {
        "label": "Research Preview",
        "model": f"{MODEL_RIDGE_PURE}-{CANDIDATE_VERSION}",
        "public_probability": False,
        "candidate": cand,
        "games": games,
    }


@router.get("/experiments")
def models_experiments(_user: User = Depends(require_entitlement("backtests_advanced"))) -> dict:
    search = load_search()
    if search is None:
        return {"available": False, "message": "Run python -m ml.pregame.experiments"}
    return {"available": True, "holdout_opened": False, **search}
