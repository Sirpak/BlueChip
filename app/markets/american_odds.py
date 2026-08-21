"""American-odds prices and implied (vigged) probabilities."""

from __future__ import annotations


def implied_prob_american(odds: int | float) -> float:
    """Raw implied probability from American odds (includes vig).

    Negative: |o| / (|o| + 100). Positive: 100 / (o + 100).
    """
    o = float(odds)
    if o == 0:
        raise ValueError("American odds cannot be 0")
    if o < 0:
        return abs(o) / (abs(o) + 100.0)
    return 100.0 / (o + 100.0)


def american_from_prob(p: float) -> float:
    """Fair American odds from a probability in (0, 1)."""
    if not 0 < p < 1:
        raise ValueError("probability must be in (0, 1)")
    if p >= 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


def break_even_prob(odds: int | float) -> float:
    """Minimum win rate to profit at this price (same as raw implied)."""
    return implied_prob_american(odds)
