"""ATS vs close and cover helpers (nflverse spread convention)."""

from __future__ import annotations

import numpy as np

from app.markets.spread import NFL_SIGMA, p_home_cover, p_home_win


def home_covers_actual(home_margin: np.ndarray, spread_line: np.ndarray) -> np.ndarray:
    """nflverse: ``spread_line > 0`` ⇒ home favored; home covers if M > spread_line."""
    m = np.asarray(home_margin, dtype=float)
    s = np.asarray(spread_line, dtype=float)
    return m > s


def model_picks_home_cover(pred_margin: np.ndarray, spread_line: np.ndarray) -> np.ndarray:
    """Ridge μ vs line: pick home cover when predicted margin exceeds the close."""
    mu = np.asarray(pred_margin, dtype=float)
    s = np.asarray(spread_line, dtype=float)
    return mu > s


def ats_accuracy(
    pred_margin: np.ndarray,
    home_margin: np.ndarray,
    spread_line: np.ndarray,
) -> dict[str, float | int]:
    """Fraction of games where the model's cover pick matches the outcome."""
    mu = np.asarray(pred_margin, dtype=float)
    m = np.asarray(home_margin, dtype=float)
    s = np.asarray(spread_line, dtype=float)
    mask = np.isfinite(mu) & np.isfinite(m) & np.isfinite(s)
    if mask.sum() == 0:
        return {"n": 0, "ats_pct": float("nan"), "correct": 0}
    pick = model_picks_home_cover(mu[mask], s[mask])
    actual = home_covers_actual(m[mask], s[mask])
    correct = int(np.sum(pick == actual))
    n = int(mask.sum())
    return {"n": n, "ats_pct": float(correct / n), "correct": correct}


def market0_picks_home_cover(spread_line: np.ndarray) -> np.ndarray:
    """Market 0 baseline: side favored by the close (μ_market = spread_line)."""
    s = np.asarray(spread_line, dtype=float)
    return np.isfinite(s) & (s >= 0.0)


def stern_home_win_prob(pred_margin: np.ndarray, *, sigma: float = NFL_SIGMA) -> np.ndarray:
    mu = np.asarray(pred_margin, dtype=float)
    out = np.full_like(mu, np.nan, dtype=float)
    for i, m in enumerate(mu):
        if np.isfinite(m):
            out[i] = p_home_win(float(m), sigma, continuity=True)
    return out


def stern_home_cover_prob(
    pred_margin: np.ndarray,
    spread_line: np.ndarray,
    *,
    sigma: float = NFL_SIGMA,
) -> np.ndarray:
    """Convert nflverse spread + μ to P(home cover) via Stern."""
    mu = np.asarray(pred_margin, dtype=float)
    s = np.asarray(spread_line, dtype=float)
    out = np.full_like(mu, np.nan, dtype=float)
    for i, (m, line) in enumerate(zip(mu, s, strict=True)):
        if np.isfinite(m) and np.isfinite(line):
            # app/markets uses negative for home fav; nflverse uses positive.
            home_spread = -float(line)
            out[i] = p_home_cover(float(m), home_spread, sigma, continuity=True)
    return out
