"""Opponent-adjusted EPA: EPA_ij ≈ Off_i + Def_j + HFA·home.

Ridge λ=5. Pregame strengths only — prior games, not the game being predicted.
``adj_pred_margin = (off_home - def_away) - (off_away - def_home) + hfa_prior``.
"""

from ml.features.constants import ADJ_RIDGE_LAM
from ml.features.ratings import fit_adj_epa, walk_ratings

__all__ = ["ADJ_RIDGE_LAM", "SNAPSHOT_COLS", "fit_adj_epa", "train"]

SNAPSHOT_COLS = (
    "adj_off_home",
    "adj_def_home",
    "adj_off_away",
    "adj_def_away",
    "adj_pred_margin",
)


def train(games, team_games):  # noqa: ANN001
    return walk_ratings(games, team_games)[list(SNAPSHOT_COLS) + ["game_id"]]
