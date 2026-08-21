"""Administrator API (ADMIN role required)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import func, inspect
from sqlalchemy.orm import Session

from app import __version__
from app.auth.deps import AdminDep, SessionDep
from app.config import get_settings
from app.ingest.contract_checks import assert_core_contract
from db.models import FeatureSnapshot, Game, ModelPrediction, Play, User
from ml.pregame.experiments import load_candidate, load_search
from ml.pregame.freeze import load_freeze
from ml.pregame.walk_forward import ARTIFACT_NAME, load_artifact

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/health")
def admin_health(session: SessionDep, _admin: AdminDep) -> dict:
    """Full system health — not exposed to normal users."""
    insp = inspect(session.get_bind())
    tables = set(insp.get_table_names())
    contract = assert_core_contract(session) if "games" in tables else {}
    snap_n = session.query(func.count(FeatureSnapshot.id)).scalar() if "feature_snapshots" in tables else 0
    return {
        "status": "ok",
        "app_version": __version__,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "database": {
            "connected": True,
            "games": session.query(func.count(Game.game_id)).scalar() if "games" in tables else 0,
            "plays": session.query(func.count(Play.id)).scalar() if "plays" in tables else 0,
            "feature_snapshots": int(snap_n or 0),
        },
        "contract": contract,
        "ingestion": {
            "nflverse_pbp": "done" if contract.get("games", 0) > 1000 else "partial",
            "schedules": "done" if contract.get("games_with_kickoff", 0) > 1000 else "partial",
            "snapshots": "done" if snap_n else "pending",
        },
    }


@router.get("/dashboard")
def admin_dashboard(session: SessionDep, _admin: AdminDep) -> dict:
    user_count = session.query(func.count(User.id)).scalar() or 0
    admin_count = session.query(func.count(User.id)).filter(User.role == "ADMIN").scalar() or 0
    return {
        "users": int(user_count),
        "admins": int(admin_count),
        "deployed_version": __version__,
        "notes": "Pipeline, model jobs, and cost dashboards ship in Sprint E.",
    }


@router.get("/models")
def admin_models(_admin: AdminDep) -> dict:
    """Latest walk-forward artifact (2009–2022 dev window)."""
    artifact = load_artifact()
    settings = get_settings()
    path = settings.data_dir / "walk_forward" / ARTIFACT_NAME
    return {
        "artifact_path": str(path),
        "artifact_exists": artifact is not None,
        "walk_forward": artifact,
        "cli": "python -m ml.pregame.walk_forward",
        "experiments": load_search(),
        "candidate": load_candidate(),
        "freeze": load_freeze(),
    }


@router.get("/pipeline")
def admin_pipeline(session: SessionDep, _admin: AdminDep) -> dict:
    health = admin_health(session, _admin)
    freeze = load_freeze() or {}
    return {
        "ingestion": health["ingestion"],
        "database": health["database"],
        "commands": [
            "python -m app.ingest --from-season 1999 --to-season 2025",
            "python -m app.ingest --schedules --from-season 1999 --to-season 2025",
            "python -m ml.features.build",
            "python -m ml.pregame.experiments",
        ],
        "holdout_opened": bool(freeze.get("holdout_opened")),
        "cfbd": "ping only — no ingest until NFL gates pass",
    }


@router.get("/logs")
def admin_logs(session: SessionDep, _admin: AdminDep) -> dict:
    last_snap = (
        session.query(FeatureSnapshot.retrieved_at)
        .order_by(FeatureSnapshot.retrieved_at.desc())
        .limit(1)
        .scalar()
    )
    last_pred = (
        session.query(ModelPrediction.predicted_at)
        .order_by(ModelPrediction.predicted_at.desc())
        .limit(1)
        .scalar()
    )
    return {
        "entries": [
            {
                "level": "info",
                "message": "Feature snapshots last retrieved",
                "at": last_snap.isoformat() if last_snap else None,
            },
            {
                "level": "info",
                "message": "Latest model_predictions write",
                "at": last_pred.isoformat() if last_pred else None,
            },
            {
                "level": "info",
                "message": "Sacred holdout 2023–2025 remains sealed",
                "at": datetime.now(timezone.utc).isoformat(),
            },
        ]
    }


@router.get("/predictions")
def admin_predictions(session: SessionDep, _admin: AdminDep) -> dict:
    n = session.query(func.count(ModelPrediction.id)).scalar() or 0
    return {"model_predictions": int(n), "candidate": load_candidate()}


@router.get("/experiments")
def admin_experiments(_admin: AdminDep) -> dict:
    return {"search": load_search(), "freeze": load_freeze(), "holdout_opened": False}


@router.get("/users")
def admin_users(session: SessionDep, _admin: AdminDep) -> list[dict]:
    rows = session.query(User).order_by(User.username).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "plan": getattr(u, "plan", None),
            "display_name": getattr(u, "display_name", None),
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in rows
    ]
