"""Weekly featured desk publish API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.auth.deps import UserDep
from app.services import weekly_desk

router = APIRouter(prefix="/api/weekly", tags=["weekly-desk"])


@router.get("/slate")
def weekly_slate(_user: UserDep) -> dict:
    payload = weekly_desk.load_weekly()
    if payload is None:
        return {
            "available": False,
            "message": "Run python -m ml.pregame.weekly_publish",
            "cards": [],
        }
    return {"available": True, **payload}


@router.get("/game")
def weekly_game(_user: UserDep, game_id: str = Query(...)) -> dict:
    card = weekly_desk.card_for_game(game_id)
    if card is None:
        return {"available": False, "game_id": game_id}
    return {"available": True, "card": card}


@router.post("/publish")
def weekly_publish(
    _user: UserDep,
    nfl: int = Query(default=0, ge=0, le=64),
    cfb: int = Query(default=0, ge=0, le=200),
    ai_top: int = Query(default=8, ge=0, le=20),
) -> dict:
    """Regenerate Week 1 desk. nfl/cfb of 0 = all Week 1 games."""
    try:
        payload = weekly_desk.publish_weekly(nfl_n=nfl, cfb_n=cfb, ai_top=ai_top)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "ok": True,
        "published_at": payload["published_at"],
        "counts": payload["counts"],
        "highest_confidence_cfb_week1": payload.get("highest_confidence_cfb_week1"),
    }
