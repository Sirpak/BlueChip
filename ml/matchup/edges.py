"""W2A — Matchup statistics / EDGE signals from team features.

Separate from BCW-RIDGE-v0.1 freeze. Labels are MATCHUP SIGNAL, not published win %.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Strength = Literal["MAJOR", "STRONG", "MILD", "EVEN", "NEGATIVE"]
Side = Literal["HOME", "AWAY", "EVEN"]


@dataclass
class MatchupEdge:
    key: str
    title: str
    side: Side
    side_team: str
    strength: Strength
    home_stat: float | None
    away_stat: float | None
    mismatch_z: float
    fan_line: str
    label: str = "MATCHUP SIGNAL"
    why: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _strength_from_abs_z(az: float) -> Strength:
    if az >= 1.8:
        return "MAJOR"
    if az >= 1.0:
        return "STRONG"
    if az >= 0.45:
        return "MILD"
    return "EVEN"


def _marks(strength: Strength) -> str:
    return {"MAJOR": "+++", "STRONG": "++", "MILD": "+", "EVEN": "·", "NEGATIVE": "-"}.get(strength, "·")


def _edge(
    *,
    key: str,
    title: str,
    home_team: str,
    away_team: str,
    home_value: float,
    away_value: float,
    scale: float,
    why: str,
    higher_is_home_edge: bool = True,
) -> MatchupEdge:
    """home_value − away_value > 0 ⇒ home edge when higher_is_home_edge."""
    raw = (home_value - away_value) if higher_is_home_edge else (away_value - home_value)
    z = raw / scale if scale > 0 else 0.0
    strength = _strength_from_abs_z(abs(z))
    if abs(z) < 0.25:
        side: Side = "EVEN"
        team = home_team
        fan = f"{title}: roughly even"
        strength = "EVEN"
    elif z > 0:
        side = "HOME"
        team = home_team
        fan = f"{_marks(strength)} {team} — {title}"
    else:
        side = "AWAY"
        team = away_team
        fan = f"{_marks(strength)} {team} — {title}"
    return MatchupEdge(
        key=key,
        title=title,
        side=side,
        side_team=team,
        strength=strength,
        home_stat=round(home_value, 4),
        away_stat=round(away_value, 4),
        mismatch_z=round(z, 3),
        fan_line=fan,
        why=why,
    )


def edges_from_profiles(
    *,
    home_team: str,
    away_team: str,
    home: dict[str, float | None],
    away: dict[str, float | None],
) -> list[MatchupEdge]:
    """Interaction edges: each side's offense vs the other's defense quality.

    For EPA allowed, higher = softer defense. Home attack net =
    home_off_epa − (−away_allowed) is wrong; use home_off − away_def_quality
    where def_quality = −allowed.
    """
    out: list[MatchupEdge] = []

    def attack_nets(off_key: str, allowed_key: str) -> tuple[float, float] | None:
        h_off = home.get(off_key)
        a_off = away.get(off_key)
        h_all = home.get(allowed_key)
        a_all = away.get(allowed_key)
        if None in (h_off, a_off, h_all, a_all):
            return None
        # Soft defense (high EPA allowed) helps the attacker.
        home_attack = float(h_off) + float(a_all)
        away_attack = float(a_off) + float(h_all)
        return home_attack, away_attack

    pass_nets = attack_nets("pass_epa", "pass_epa_allowed")
    if pass_nets:
        h, a = pass_nets
        out.append(
            _edge(
                key="PASSING",
                title="Passing offense vs pass defense",
                home_team=home_team,
                away_team=away_team,
                home_value=h,
                away_value=a,
                scale=0.18,
                why="EPA/play on passes plus how much EPA the opposing defense allows. "
                "EPA weights plays by situation (3rd-and-3 ≠ 3rd-and-20).",
            )
        )

    rush_nets = attack_nets("rush_epa", "rush_epa_allowed")
    if rush_nets:
        h, a = rush_nets
        out.append(
            _edge(
                key="RUN_GAME",
                title="Rushing offense vs run defense",
                home_team=home_team,
                away_team=away_team,
                home_value=h,
                away_value=a,
                scale=0.14,
                why="Rush EPA/play vs EPA allowed on rushes — better than raw yards/carry.",
            )
        )

    h_press = home.get("pass_epa_allowed")
    a_press = away.get("pass_epa_allowed")
    if h_press is not None and a_press is not None:
        # Lower pass EPA allowed ⇒ stronger pass defense / rush proxy
        home_pr = -float(h_press)
        away_pr = -float(a_press)
        out.append(
            _edge(
                key="PASS_RUSH",
                title="Pass rush / protection (proxy)",
                home_team=home_team,
                away_team=away_team,
                home_value=home_pr,
                away_value=away_pr,
                scale=0.10,
                why="Proxy until true pressure/PBWR data: lower pass EPA allowed ⇒ stronger pass defense / rush. "
                "MATCHUP SIGNAL only — not a published win probability.",
            )
        )

    h_off = home.get("off_epa")
    a_off = away.get("off_epa")
    h_def = home.get("def_epa")
    a_def = away.get("def_epa")
    if None not in (h_off, a_off, h_def, a_def):
        # Overall: (off - def) nets; def_epa in nflverse is often defensive EPA (lower better for D)
        home_net = float(h_off) - float(h_def)  # type: ignore[arg-type]
        away_net = float(a_off) - float(a_def)  # type: ignore[arg-type]
        out.append(
            _edge(
                key="OVERALL",
                title="Overall efficiency",
                home_team=home_team,
                away_team=away_team,
                home_value=home_net,
                away_value=away_net,
                scale=0.20,
                why="Net EPA/play (offense minus defense). Broad team-strength interaction.",
            )
        )

    h_sr = home.get("success_off")
    a_sr = away.get("success_off")
    if h_sr is not None and a_sr is not None:
        out.append(
            _edge(
                key="SUCCESS",
                title="Success rate",
                home_team=home_team,
                away_team=away_team,
                home_value=float(h_sr),
                away_value=float(a_sr),
                scale=0.06,
                why="Share of plays that improve down/distance — steadier than explosive outliers.",
            )
        )

    # Sort major first
    order = {"MAJOR": 0, "STRONG": 1, "MILD": 2, "EVEN": 3, "NEGATIVE": 4}
    out.sort(key=lambda e: (order.get(e.strength, 9), -abs(e.mismatch_z)))
    return out


def edges_from_ranks(
    *,
    home_team: str,
    away_team: str,
    home_rank: int | None,
    away_rank: int | None,
) -> list[MatchupEdge]:
    """CFB fallback when EPA profiles are missing — AP rank gap only."""
    if home_rank is None and away_rank is None:
        return []
    hr = float(home_rank or 30)
    ar = float(away_rank or 30)
    # Lower rank better → home edge when home_rank < away_rank → positive when ar - hr > 0
    return [
        _edge(
            key="AP_RANK",
            title="AP ranking gap",
            home_team=home_team,
            away_team=away_team,
            home_value=ar,
            away_value=hr,
            scale=8.0,
            why="College prior until CFB EPA ingest. Lower AP rank is stronger.",
        )
    ]


def paths_to_win(edges: list[MatchupEdge], home: str, away: str) -> dict[str, str]:
    home_edges = [e for e in edges if e.side_team == home and e.strength != "EVEN"]
    away_edges = [e for e in edges if e.side_team == away and e.strength != "EVEN"]
    if home_edges:
        top = home_edges[0]
        home_path = (
            f"Lean on {top.title.lower()}. Convert that mismatch before the game becomes a coin-flip script."
        )
    else:
        home_path = "Stay efficient on early downs and avoid giving the visitor explosive answers."
    if away_edges:
        top = away_edges[0]
        away_path = (
            f"Attack via {top.title.lower()} and keep the favorite from playing its preferred script."
        )
    else:
        away_path = "Shorten the game, win the line of scrimmage, and force the favorite into obvious passing downs."
    return {"home": home_path, "away": away_path}


def what_could_go_wrong(edges: list[MatchupEdge], lean_team: str, other: str) -> list[str]:
    risks = [
        f"Turnovers: the projection assumes roughly normal luck; a +2 swing can flip a {lean_team} lean.",
    ]
    counter = [e for e in edges if e.side_team == other and e.strength in {"MAJOR", "STRONG", "MILD"}]
    if counter:
        risks.append(
            f"{other} path: if {counter[0].title.lower()} plays up, {lean_team}'s edge shrinks."
        )
    risks.append("Injury / inactive surprise on either OL or QB would rewrite the pass-rush signal.")
    return risks


def total_adjustment(edges: list[MatchupEdge]) -> dict[str, Any]:
    """Heuristic points for display only — not a model μ."""
    pts = 0.0
    for e in edges:
        if e.side == "EVEN":
            continue
        mag = {"MAJOR": 1.6, "STRONG": 1.0, "MILD": 0.45}.get(e.strength, 0.0)
        pts += mag if e.side == "HOME" else -mag
    return {
        "points_home": round(pts, 2),
        "label": "MATCHUP SIGNAL (unvalidated additive)",
        "note": "Not fed into BCW-RIDGE-v0.1. Research Preview display only.",
    }
