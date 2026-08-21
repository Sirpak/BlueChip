"""Stern-style margin → win/cover probability.

NFL final margin M = home_score - away_score is modeled as approximately
Normal(μ, σ) with σ ≈ 13.5 (Stern 1991 used 13.86; PFR uses 13.45).

Home spread convention (nflverse/PFR closing line):
  home_spread = -7  → home favored by 7, E[M] ≈ +7.
  Cover home: M > -home_spread. Push: M == -home_spread (integer lines).
"""

from __future__ import annotations

import math
from typing import Literal

League = Literal["NFL", "CFB"]

# Defaults from BlueChip research note 008.
NFL_SIGMA = 13.5
NFL_SIGMA_STERN = 13.86
NFL_SIGMA_PFR = 13.45
CFB_SIGMA = 15.0  # spread-centered college; raw score SD is wider

KEY_NUMBERS_NFL = (3, 7, 6, 10, 14)


def phi(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sigma_for_league(league: str = "NFL") -> float:
    if league.upper() == "CFB":
        return CFB_SIGMA
    return NFL_SIGMA


def market_expected_margin(home_spread: float) -> float:
    """Market prior for E[home margin]: home -7 ⇒ +7."""
    return -float(home_spread)


def cover_threshold(home_spread: float) -> float:
    """Home covers if M > this value (e.g. -7 → 7)."""
    return -float(home_spread)


def p_greater_than(threshold: float, mu: float, sigma: float, *, continuity: bool = True) -> float:
    """P(M > threshold) under N(μ, σ). Continuity correction uses threshold+0.5."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    t = threshold + 0.5 if continuity else threshold
    return 1.0 - phi((t - mu) / sigma)


def p_home_win(mu: float, sigma: float, *, continuity: bool = True) -> float:
    """P(home wins) = P(M > 0)."""
    return p_greater_than(0.0, mu, sigma, continuity=continuity)


def p_home_cover(
    mu: float,
    home_spread: float,
    sigma: float,
    *,
    continuity: bool = True,
) -> float:
    """P(home covers the spread) = P(M > -home_spread)."""
    return p_greater_than(cover_threshold(home_spread), mu, sigma, continuity=continuity)


def p_push(mu: float, home_spread: float, sigma: float) -> float | None:
    """P(M = exactly the integer line), via P(k-0.5 < M < k+0.5)."""
    k = cover_threshold(home_spread)
    if abs(k - round(k)) > 1e-9:
        return None
    k = float(round(k))
    lo = phi((k - 0.5 - mu) / sigma)
    hi = phi((k + 0.5 - mu) / sigma)
    return hi - lo


def favorite_win_prob(points: float, sigma: float = NFL_SIGMA) -> float:
    """Stern: P(favorite of `points` wins) = Φ(p / σ). No continuity."""
    return phi(float(points) / sigma)
