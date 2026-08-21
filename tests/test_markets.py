"""Canonical conversions from Stern (1991) and -110 break-even.

See docs/research/008-margin-probability-foundations.md
"""

from app.markets import (
    NFL_SIGMA,
    NFL_SIGMA_STERN,
    american_from_prob,
    break_even_prob,
    favorite_win_prob,
    implied_prob_american,
    p_home_cover,
    p_home_win,
    price_market,
)
from app.markets.devig import additive, multiplicative, shin


def test_minus_110_break_even() -> None:
    p = break_even_prob(-110)
    assert abs(p - 110 / 210) < 1e-12
    assert round(p, 4) == 0.5238


def test_plus_american() -> None:
    assert abs(implied_prob_american(100) - 0.5) < 1e-12
    assert abs(implied_prob_american(231) - 100 / 331) < 1e-12


def test_minus_110_devig_is_coin_flip() -> None:
    raw = [implied_prob_american(-110), implied_prob_american(-110)]
    assert abs(sum(raw) - 1.0476) < 1e-4
    for method in (multiplicative, additive, shin):
        fair = method(raw)
        assert abs(fair[0] - 0.5) < 1e-6
        assert abs(fair[1] - 0.5) < 1e-6
        assert abs(sum(fair) - 1.0) < 1e-9


def test_seven_point_favorite_win_prob() -> None:
    # TL;DR: Φ(7/13.5) ≈ 69.8%; fair ML ≈ -231
    p = favorite_win_prob(7, NFL_SIGMA)
    assert abs(p - 0.698) < 0.004
    ml = american_from_prob(p)
    assert abs(ml - (-231)) < 4

    # Stern's original σ
    p_stern = favorite_win_prob(7, NFL_SIGMA_STERN)
    assert 0.69 < p_stern < 0.71


def test_cover_at_the_line_is_half_without_continuity() -> None:
    p = p_home_cover(mu=7.0, home_spread=-7.0, sigma=NFL_SIGMA, continuity=False)
    assert abs(p - 0.5) < 1e-9


def test_rams_example_model_edge() -> None:
    # Model P(cover -7) = 54% vs -110 / no-vig 50%
    priced = price_market(
        home_spread=-7,
        home_american=-110,
        away_american=-110,
        projected_home_margin=9.1,
        continuity=False,
    )
    # With μ=9.1, P(M>7) = 1-Φ((7-9.1)/13.5) ≈ 1-Φ(-0.1556) ≈ 0.562
    assert priced["fair_home"] == 0.5
    assert abs(priced["break_even_home"] - 0.5238) < 1e-4
    assert priced["model_home_cover"] > 0.54
    assert priced["edge_vs_market"] > 0.04
    assert priced["edge_vs_breakeven"] > 0.02


def test_home_win_from_spread_prior() -> None:
    priced = price_market(home_spread=-7, continuity=False, sigma=NFL_SIGMA)
    # Market prior μ=7 → P(win)=Φ(7/13.5) with no continuity on P(M>0)=1-Φ(-7/13.5)=Φ(7/13.5)
    assert abs(priced["model_home_win"] - favorite_win_prob(7)) < 1e-9
    assert priced["note"].startswith("mu from market")


def test_p_home_win_continuity() -> None:
    p = p_home_win(7.0, NFL_SIGMA, continuity=True)
    # P(M > 0.5) is slightly *below* P(M > 0) = Φ(7/σ)
    assert p < favorite_win_prob(7, NFL_SIGMA)
    assert p > 0.68
