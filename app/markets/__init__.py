"""Market conversion engine: American odds, de-vig, Stern spread math."""

from app.markets.american_odds import american_from_prob, break_even_prob, implied_prob_american
from app.markets.devig import additive, devig, multiplicative, shin
from app.markets.expected_value import price_market
from app.markets.spread import (
    CFB_SIGMA,
    NFL_SIGMA,
    NFL_SIGMA_PFR,
    NFL_SIGMA_STERN,
    favorite_win_prob,
    market_expected_margin,
    p_home_cover,
    p_home_win,
    phi,
)

__all__ = [
    "CFB_SIGMA",
    "NFL_SIGMA",
    "NFL_SIGMA_PFR",
    "NFL_SIGMA_STERN",
    "additive",
    "american_from_prob",
    "break_even_prob",
    "devig",
    "favorite_win_prob",
    "implied_prob_american",
    "market_expected_margin",
    "multiplicative",
    "p_home_cover",
    "p_home_win",
    "phi",
    "price_market",
    "shin",
]
