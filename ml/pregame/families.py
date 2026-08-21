"""PURE feature-ablation families (2009–2022 only).

F (sacks / negative-play rates) is skipped until those columns exist on snapshots.
G replaces raw EPA with opponent-adjusted EPA; it is not stacked on E.
"""

from __future__ import annotations

FAMILIES: dict[str, tuple[str, ...]] = {
    "A": ("elo_diff", "srs_diff", "hfa_prior", "rest_diff"),
    "B": ("elo_diff", "srs_diff", "hfa_prior", "rest_diff", "off_epa_diff", "def_epa_diff"),
    "C": (
        "elo_diff",
        "srs_diff",
        "hfa_prior",
        "rest_diff",
        "off_epa_diff",
        "def_epa_diff",
        "pass_epa_diff",
        "rush_epa_diff",
    ),
    "D": (
        "elo_diff",
        "srs_diff",
        "hfa_prior",
        "rest_diff",
        "off_epa_diff",
        "def_epa_diff",
        "pass_epa_diff",
        "rush_epa_diff",
        "success_rate_diff",
    ),
    "E": (
        "elo_diff",
        "srs_diff",
        "hfa_prior",
        "rest_diff",
        "off_epa_diff",
        "def_epa_diff",
        "pass_epa_diff",
        "rush_epa_diff",
        "success_rate_diff",
        "explosive_play_diff",
    ),
    "G": ("elo_diff", "srs_diff", "hfa_prior", "rest_diff", "adj_off_diff", "adj_def_diff"),
}

FAMILY_NOTES = {
    "A": "Elo / SRS / HFA / rest only",
    "B": "A + raw offensive/defensive EPA",
    "C": "B + pass/rush EPA splits",
    "D": "C + success rate",
    "E": "D + explosiveness",
    "F": "Skipped — sacks / negative-play rates not on BCW-SNAP-v0.1 yet",
    "G": "A + opponent-adjusted EPA instead of raw EPA",
}

PURE_KIND = {
    "A": "PURE-RAW-v0.x",
    "B": "PURE-RAW-v0.x",
    "C": "PURE-RAW-v0.x",
    "D": "PURE-RAW-v0.x",
    "E": "PURE-RAW-v0.x",
    "G": "PURE-ADJ-v0.x",
}


def family_cols(letter: str) -> tuple[str, ...]:
    if letter == "F":
        raise KeyError("Family F is not implemented (sacks not curated)")
    return FAMILIES[letter]
