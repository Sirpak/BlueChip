"""De-vig two-way (or multi-way) implied probabilities."""

from __future__ import annotations

from collections.abc import Sequence


def _validate(raw: Sequence[float]) -> list[float]:
    probs = [float(p) for p in raw]
    if any(p <= 0 for p in probs):
        raise ValueError("implied probabilities must be positive")
    return probs


def multiplicative(raw: Sequence[float]) -> list[float]:
    """Normalize so probabilities sum to 1 (default for two-way markets)."""
    probs = _validate(raw)
    total = sum(probs)
    return [p / total for p in probs]


def additive(raw: Sequence[float]) -> list[float]:
    """Split overround equally, then clip and renormalize."""
    probs = _validate(raw)
    n = len(probs)
    overround = sum(probs) - 1.0
    adjusted = [p - overround / n for p in probs]
    if any(p <= 0 for p in adjusted):
        adjusted = [max(p, 1e-12) for p in adjusted]
    total = sum(adjusted)
    return [p / total for p in adjusted]


def shin(raw: Sequence[float], *, iterations: int = 64) -> list[float]:
    """Shin (1993): allocate more margin to longshots.

    Binary-search the insider-trading parameter z so Shin probabilities
    sum to 1. For -110/-110 this collapses to 50/50 like multiplicative.
    """
    pi = _validate(raw)
    s = sum(pi)

    def shin_given_z(z: float) -> list[float]:
        if abs(z - 1.0) < 1e-12:
            return multiplicative(pi)
        out = []
        for p in pi:
            inner = z * z + 4.0 * (1.0 - z) * (p * p) / s
            out.append((inner**0.5 - z) / (2.0 * (1.0 - z)))
        return out

    lo, hi = 0.0, 1.0
    best = multiplicative(pi)
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        cand = shin_given_z(mid)
        total = sum(cand)
        best = cand
        if total > 1.0:
            lo = mid
        else:
            hi = mid
    total = sum(best)
    if total <= 0:
        return multiplicative(pi)
    return [p / total for p in best]


def devig(raw: Sequence[float], method: str = "multiplicative") -> list[float]:
    key = method.lower().strip()
    if key in {"multiplicative", "normalize", "multi"}:
        return multiplicative(raw)
    if key in {"additive", "add"}:
        return additive(raw)
    if key == "shin":
        return shin(raw)
    raise ValueError(f"unknown de-vig method: {method}")
