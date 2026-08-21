"""Leakage-safe Elo, SRS, opponent-adjusted EPA, expanding HFA."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime

import numpy as np
import pandas as pd

from ml.features.constants import (
    ADJ_RIDGE_LAM,
    ELO_HFA,
    ELO_K,
    ELO_MEAN,
    ELO_SEASON_REGRESS,
    HFA_PRIOR_DEFAULT,
    HFA_PRIOR_MIN_N,
)

logger = logging.getLogger(__name__)


def _as_date(val: object) -> date | None:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    ts = pd.Timestamp(val)
    if pd.isna(ts):
        return None
    return ts.date()


def elo_expect(r_home: float, r_away: float, hfa: float = ELO_HFA) -> float:
    return 1.0 / (1.0 + 10.0 ** ((r_away - (r_home + hfa)) / 400.0))


def fit_srs(rows: list[tuple[str, str, float]]) -> dict[str, float]:
    """Mean-centered SRS: R_i - R_j ≈ home margin. Equilibrium of iterative SOS."""
    if not rows:
        return {}
    teams = sorted({h for h, _, _ in rows} | {a for _, a, _ in rows})
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    if n == 1:
        return {teams[0]: 0.0}
    a = np.zeros((n, n), dtype=float)
    b = np.zeros(n, dtype=float)
    for home, away, margin in rows:
        i, j = idx[home], idx[away]
        a[i, i] += 1.0
        a[i, j] -= 1.0
        b[i] += margin
        a[j, j] += 1.0
        a[j, i] -= 1.0
        b[j] -= margin
    a[-1, :] = 1.0
    b[-1] = 0.0
    try:
        r = np.linalg.solve(a, b)
    except np.linalg.LinAlgError:
        r = np.linalg.lstsq(a, b, rcond=None)[0]
        r = r - float(r.mean())
    return {t: float(r[idx[t]]) for t in teams}


def fit_adj_epa(tg: pd.DataFrame, lam: float = ADJ_RIDGE_LAM) -> tuple[dict[str, float], dict[str, float]]:
    """Ridge: off_epa ≈ Off_i + Def_j + HFA * is_home. Returns off, def dicts."""
    if tg.empty or tg["off_epa"].notna().sum() < 20:
        return {}, {}
    work = tg.dropna(subset=["off_epa", "team", "opponent"]).copy()
    if len(work) < 20:
        return {}, {}
    teams = sorted(set(work["team"]) | set(work["opponent"]))
    idx = {t: i for i, t in enumerate(teams)}
    n_t = len(teams)
    p = 2 * n_t + 1
    n = len(work)
    team_i = work["team"].map(idx).to_numpy(dtype=int)
    opp_i = work["opponent"].map(idx).to_numpy(dtype=int)
    is_home = work["is_home"].fillna(False).astype(bool).to_numpy()
    y = work["off_epa"].to_numpy(dtype=float)
    X = np.zeros((n, p), dtype=float)
    rows = np.arange(n)
    X[rows, team_i] = 1.0
    X[rows, n_t + opp_i] = 1.0
    X[:, -1] = is_home.astype(float)
    a = X.T @ X + lam * np.eye(p)
    b = X.T @ y
    try:
        beta = np.linalg.solve(a, b)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(a, b, rcond=None)[0]
    off = {t: float(beta[idx[t]]) for t in teams}
    deff = {t: float(beta[n_t + idx[t]]) for t in teams}
    return off, deff


def walk_ratings(games: pd.DataFrame, team_games: pd.DataFrame) -> pd.DataFrame:
    """For each game, ratings using only completed prior games. Then update Elo.

    SRS and opponent-adjusted EPA refit when ``game_date`` changes so Thursday
    can inform Sunday. Same-day games share those ratings; Elo still updates
    after every completed game.
    """
    games = games.sort_values("sort_ts", kind="mergesort").reset_index(drop=True)
    elo: dict[str, float] = defaultdict(lambda: ELO_MEAN)
    last_season: int | None = None
    srs: dict[str, float] = {}
    adj_off: dict[str, float] = {}
    adj_def: dict[str, float] = {}
    completed_margins: list[tuple[str, str, float]] = []
    margin_sum = 0.0
    margin_n = 0
    last_refit_date: date | None = None
    pending_tg: list[pd.DataFrame] = []
    completed_tg: pd.DataFrame | None = None

    tg_by_game: dict[str, pd.DataFrame] = {}
    if not team_games.empty:
        tg_by_game = {gid: g for gid, g in team_games.groupby("game_id", sort=False)}

    out: list[dict] = []
    n_games = len(games)
    for i, rec in enumerate(games.itertuples(index=False), start=1):
        season = int(rec.season)
        if last_season is not None and season != last_season:
            for team in list(elo.keys()):
                elo[team] = (1.0 - ELO_SEASON_REGRESS) * elo[team] + ELO_SEASON_REGRESS * ELO_MEAN
        last_season = season

        game_date = _as_date(getattr(rec, "game_date", None))
        if game_date != last_refit_date:
            if pending_tg:
                add = pd.concat(pending_tg, ignore_index=True)
                completed_tg = add if completed_tg is None else pd.concat([completed_tg, add], ignore_index=True)
                pending_tg = []
            srs = fit_srs(completed_margins)
            if completed_tg is not None and not completed_tg.empty:
                adj_off, adj_def = fit_adj_epa(completed_tg)
            last_refit_date = game_date

        home, away = rec.home_team, rec.away_team
        eh, ea = float(elo[home]), float(elo[away])
        hfa_mu = (margin_sum / margin_n) if margin_n >= HFA_PRIOR_MIN_N else HFA_PRIOR_DEFAULT
        sh, sa = srs.get(home, 0.0), srs.get(away, 0.0)
        oh, oa = adj_off.get(home, 0.0), adj_off.get(away, 0.0)
        dh, da = adj_def.get(home, 0.0), adj_def.get(away, 0.0)

        out.append(
            {
                "game_id": rec.game_id,
                "elo_home": eh,
                "elo_away": ea,
                "elo_diff": eh - ea,
                "elo_win_home": elo_expect(eh, ea),
                "srs_home": sh,
                "srs_away": sa,
                "srs_diff": sh - sa,
                "srs_pred_margin": sh - sa + hfa_mu,
                "hfa_prior": hfa_mu,
                "adj_off_home": oh,
                "adj_def_home": dh,
                "adj_off_away": oa,
                "adj_def_away": da,
                "adj_pred_margin": (oh - da) - (oa - dh) + hfa_mu,
            }
        )

        margin = rec.home_margin
        if margin is not None and pd.notna(margin):
            margin = float(margin)
            expected = elo_expect(eh, ea)
            actual = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
            elo[home] = eh + ELO_K * (actual - expected)
            elo[away] = ea + ELO_K * ((1.0 - actual) - (1.0 - expected))
            completed_margins.append((home, away, margin))
            if getattr(rec, "season_type", "REG") == "REG":
                margin_sum += margin
                margin_n += 1
            chunk = tg_by_game.get(rec.game_id)
            if chunk is not None:
                pending_tg.append(chunk)

        if i == 1 or i % 500 == 0 or i == n_games:
            logger.info("ratings walk %s/%s", i, n_games)

    return pd.DataFrame(out)
