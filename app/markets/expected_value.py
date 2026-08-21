"""Price a two-way market vs a projected home margin."""

from __future__ import annotations

from typing import Any

from app.markets.american_odds import american_from_prob, implied_prob_american
from app.markets.devig import devig
from app.markets.spread import (
    favorite_win_prob,
    market_expected_margin,
    p_home_cover,
    p_home_win,
    p_push,
    sigma_for_league,
)


def price_market(
    *,
    home_spread: float | None = None,
    home_american: int | float | None = None,
    away_american: int | float | None = None,
    projected_home_margin: float | None = None,
    league: str = "NFL",
    sigma: float | None = None,
    continuity: bool = True,
    devig_method: str = "multiplicative",
) -> dict[str, Any]:
    """Return break-even, no-vig, model cover/win, and both edges.

    If `projected_home_margin` is omitted, the market spread is the prior
    (Stern: E[M] = -home_spread) — Model 0, not a BlueChip fundamental.
    """
    sigma = sigma if sigma is not None else sigma_for_league(league)

    home_raw = implied_prob_american(home_american) if home_american is not None else None
    away_raw = implied_prob_american(away_american) if away_american is not None else None
    fair: list[float] | None = None
    if home_raw is not None and away_raw is not None:
        fair = devig([home_raw, away_raw], method=devig_method)

    mu_market = market_expected_margin(home_spread) if home_spread is not None else None
    mu_model = projected_home_margin
    mu = mu_model if mu_model is not None else mu_market

    win = cover = push = None
    if mu is not None:
        win = p_home_win(mu, sigma, continuity=continuity)
        if home_spread is not None:
            cover = p_home_cover(mu, home_spread, sigma, continuity=continuity)
            push = p_push(mu, home_spread, sigma)

    stern_from_line = None
    if home_spread is not None:
        favored_by = abs(home_spread)
        stern_from_line = favorite_win_prob(favored_by, sigma)

    edge_vs_breakeven = None
    edge_vs_market = None
    if cover is not None and home_raw is not None:
        edge_vs_breakeven = cover - home_raw
    if cover is not None and fair is not None:
        edge_vs_market = cover - fair[0]

    fair_ml = american_from_prob(win) if win is not None else None

    return {
        "league": league.upper(),
        "sigma": sigma,
        "continuity_correction": continuity,
        "devig_method": devig_method,
        "home_spread": home_spread,
        "market_expected_margin": mu_market,
        "projected_home_margin": mu_model,
        "mu_used": mu,
        "home_american": home_american,
        "away_american": away_american,
        "break_even_home": home_raw,
        "break_even_away": away_raw,
        "fair_home": fair[0] if fair else None,
        "fair_away": fair[1] if fair else None,
        "overround": (home_raw + away_raw) if home_raw is not None and away_raw is not None else None,
        "model_home_win": win,
        "model_home_cover": cover,
        "model_push": push,
        "stern_favorite_win_from_line": stern_from_line,
        "fair_home_moneyline": fair_ml,
        "edge_vs_breakeven": edge_vs_breakeven,
        "edge_vs_market": edge_vs_market,
        "note": (
            "mu from model"
            if mu_model is not None
            else "mu from market spread (Model 0 / nflverse close prior)"
            if mu_market is not None
            else "insufficient inputs"
        ),
    }
