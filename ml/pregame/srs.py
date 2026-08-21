"""PFR-style Simple Rating System (iterative SOS). Pregame only.

``srs_pred_margin = srs_home - srs_away + hfa_prior``. Mean-centered.
Refit when game_date changes so Thursday can inform Sunday.
"""

from ml.features.ratings import fit_srs, walk_ratings

__all__ = ["SNAPSHOT_COLS", "train", "fit_srs"]

SNAPSHOT_COLS = ("srs_home", "srs_away", "srs_diff", "srs_pred_margin")


def train(games, team_games):  # noqa: ANN001
    return walk_ratings(games, team_games)[list(SNAPSHOT_COLS) + ["game_id"]]
