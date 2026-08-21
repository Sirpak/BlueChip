"""BCW-HFA: expanding mean of regular-season home margin.

Default 2.0 until 80 completed REG games (HFA is ~1.5–2.5, not 3; 2020 later).
"""

from ml.features.constants import HFA_PRIOR_DEFAULT, HFA_PRIOR_MIN_N
from ml.features.ratings import walk_ratings

__all__ = ["HFA_PRIOR_DEFAULT", "HFA_PRIOR_MIN_N", "SNAPSHOT_COLS", "train"]

SNAPSHOT_COLS = ("hfa_prior",)


def train(games, team_games):  # noqa: ANN001
    return walk_ratings(games, team_games)[list(SNAPSHOT_COLS) + ["game_id"]]
