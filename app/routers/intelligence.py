"""Game Intelligence Package API — read cached briefs (no LLM on page view)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.auth.deps import UserDep
from app.services.intelligence import package as intel

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.get("/index")
def intelligence_index(_user: UserDep) -> dict:
    idx = intel.load_index()
    return {"available": bool(idx.get("packages")), **idx}


@router.get("/game")
def intelligence_game(_user: UserDep, game_id: str = Query(...)) -> dict:
    pkg = intel.load_package(game_id)
    if pkg is None:
        return {
            "available": False,
            "game_id": game_id,
            "message": "Run python -m ml.matchup.build_intelligence",
        }
    return {"available": True, "package": pkg}


@router.post("/build")
def intelligence_build(
    _user: UserDep,
    limit: int | None = Query(default=None),
    force: bool = Query(default=False),
    no_llm: bool = Query(default=False),
) -> dict:
    try:
        return intel.build_from_weekly(use_llm=not no_llm, limit=limit, force=force)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
