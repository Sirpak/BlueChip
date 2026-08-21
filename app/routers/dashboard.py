"""Browser dashboard and JSON feeds."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.deps import UserDep, get_optional_user
from app.auth.jinja import auth_template_context
from db.models import User
from app.config import ROOT_DIR
from app.services import dashboard as dash
from app.services import schedule as sched
from db.session import get_session

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))


def _fmt_epa(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:+.3f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def _fmt_num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:,.{digits}f}"


templates.env.filters["epa"] = _fmt_epa
templates.env.filters["pct"] = _fmt_pct
templates.env.filters["num"] = _fmt_num


@router.get("/legacy", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    session: Session = Depends(get_session),
    user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    payload = dash.dashboard_payload(session)
    weeks = payload.get("weekly_scoring") or []
    max_total = max((w["avg_total"] or 0) for w in weeks) if weeks else 1
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "payload": payload,
            "max_total": max_total or 1,
            **auth_template_context(user),
        },
    )


@router.get("/legacy/games", response_class=HTMLResponse)
def games_page(
    request: Request,
    session: Session = Depends(get_session),
    tab: str = "nfl",
    user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    payload = dash.dashboard_payload(session)
    upcoming = sched.upcoming_window()
    tab = tab.lower() if tab.lower() in {"nfl", "cfb"} else "nfl"
    return templates.TemplateResponse(
        request,
        "games.html",
        {
            "payload": payload,
            "upcoming": upcoming,
            "tab": tab,
            **auth_template_context(user),
        },
    )


@router.get("/api/dashboard")
def dashboard_json(session: Session = Depends(get_session), _user: UserDep = ...) -> dict:
    return dash.dashboard_payload(session)


@router.get("/games/upcoming")
def games_upcoming(_user: UserDep = ...) -> dict:
    return sched.upcoming_window()


@router.get("/teams/{team_id}/ratings")
def team_ratings(team_id: str, session: Session = Depends(get_session), season: int | None = None) -> dict:
    season = season or dash.latest_season(session)
    if season is None:
        raise HTTPException(status_code=404, detail="No seasons ingested")
    rating = dash.team_ratings(session, team_id, season)
    if rating is None:
        raise HTTPException(status_code=404, detail=f"No ratings for {team_id.upper()} in {season}")
    return rating
