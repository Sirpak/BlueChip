"""BCW Elo (pregame). Hand-coded recursive rating.

Ratings are written onto ``feature_snapshots`` by ``python -m ml.features.build``.
K=20, HFA=55 Elo points, mean 1500, 25% regression toward the mean between seasons.
"""

from ml.features.ratings import walk_ratings

SNAPSHOT_COLS = ("elo_home", "elo_away", "elo_diff", "elo_win_home")


def train(games, team_games):  # noqa: ANN001
    """Walk-forward pregame Elo. Current-game result is applied after the snapshot."""
    return walk_ratings(games, team_games)[list(SNAPSHOT_COLS) + ["game_id"]]
