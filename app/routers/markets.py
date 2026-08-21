"""Stern conversion engine — JSON + calculator page."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.jinja import auth_template_context
from app.auth.permissions import require_entitlement
from db.models import User

from app.config import ROOT_DIR
from app.markets.expected_value import price_market
from app.markets.spread import CFB_SIGMA, NFL_SIGMA, NFL_SIGMA_PFR, NFL_SIGMA_STERN

router = APIRouter(tags=["markets"])
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))


def _optional_float(value: str | float | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


@router.get("/api/markets/price")
def market_price(
    _user: User = Depends(require_entitlement("markets")),
    home_spread: float | None = Query(default=-7, description="Home closing spread, e.g. -7"),
    home_american: int | None = Query(default=-110),
    away_american: int | None = Query(default=-110),
    projected_home_margin: float | None = Query(
        default=None,
        description="BlueChip E[home margin]. Omit to use the market spread as prior.",
    ),
    league: str = Query(default="NFL"),
    continuity: bool = Query(default=True),
    devig_method: str = Query(default="multiplicative"),
    sigma: float | None = Query(default=None),
) -> dict:
    return price_market(
        home_spread=home_spread,
        home_american=home_american,
        away_american=away_american,
        projected_home_margin=projected_home_margin,
        league=league,
        sigma=sigma,
        continuity=continuity,
        devig_method=devig_method,
    )


@router.get("/legacy/markets", response_class=HTMLResponse)
def markets_page(
    request: Request,
    user: User = Depends(require_entitlement("markets")),
    home_spread: float = -7,
    home_american: int = -110,
    away_american: int = -110,
    projected_home_margin: str | None = "9.1",
    league: str = "NFL",
    continuity: bool = True,
    devig_method: str = "multiplicative",
) -> HTMLResponse:
    mu = _optional_float(projected_home_margin)
    priced = price_market(
        home_spread=home_spread,
        home_american=home_american,
        away_american=away_american,
        projected_home_margin=mu,
        league=league,
        continuity=continuity,
        devig_method=devig_method,
    )
    return templates.TemplateResponse(
        request,
        "markets.html",
        {
            "priced": priced,
            "home_spread": home_spread,
            "home_american": home_american,
            "away_american": away_american,
            "projected_home_margin": mu,
            "league": league,
            "continuity": continuity,
            "devig_method": devig_method,
            **auth_template_context(user),
            "sigmas": {
                "NFL default": NFL_SIGMA,
                "Stern 1991": NFL_SIGMA_STERN,
                "PFR": NFL_SIGMA_PFR,
                "CFB": CFB_SIGMA,
            },
        },
    )
