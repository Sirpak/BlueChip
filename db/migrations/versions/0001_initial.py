"""Initial schema: games, plays, team_ratings, odds_snapshots, model_predictions, stadiums.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stadiums",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("team_abbr", sa.String(length=8), nullable=True),
        sa.Column("city", sa.String(length=64), nullable=True),
        sa.Column("roof", sa.String(length=32), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "games",
        sa.Column("game_id", sa.String(length=32), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("season_type", sa.String(length=8), nullable=False),
        sa.Column("game_date", sa.Date(), nullable=True),
        sa.Column("kickoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column("home_team", sa.String(length=8), nullable=False),
        sa.Column("away_team", sa.String(length=8), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("roof", sa.String(length=32), nullable=True),
        sa.Column("surface", sa.String(length=32), nullable=True),
        sa.Column("temp", sa.Float(), nullable=True),
        sa.Column("wind", sa.Float(), nullable=True),
        sa.Column("stadium_id", sa.Integer(), nullable=True),
        sa.Column("result", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("spread_line", sa.Float(), nullable=True),
        sa.Column("total_line", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["stadium_id"], ["stadiums.id"]),
        sa.PrimaryKeyConstraint("game_id"),
    )
    op.create_index("ix_games_season_week", "games", ["season", "week"])
    op.create_index("ix_games_kickoff", "games", ["kickoff"])

    op.create_table(
        "plays",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(length=32), nullable=False),
        sa.Column("play_id", sa.String(length=32), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("season_type", sa.String(length=8), nullable=False),
        sa.Column("game_date", sa.Date(), nullable=True),
        sa.Column("home_team", sa.String(length=8), nullable=False),
        sa.Column("away_team", sa.String(length=8), nullable=False),
        sa.Column("posteam", sa.String(length=8), nullable=True),
        sa.Column("defteam", sa.String(length=8), nullable=True),
        sa.Column("posteam_type", sa.String(length=8), nullable=True),
        sa.Column("play_type", sa.String(length=32), nullable=True),
        sa.Column("down", sa.Integer(), nullable=True),
        sa.Column("ydstogo", sa.Integer(), nullable=True),
        sa.Column("yardline_100", sa.Float(), nullable=True),
        sa.Column("qtr", sa.Integer(), nullable=True),
        sa.Column("quarter_seconds_remaining", sa.Float(), nullable=True),
        sa.Column("half_seconds_remaining", sa.Float(), nullable=True),
        sa.Column("game_seconds_remaining", sa.Float(), nullable=True),
        sa.Column("yards_gained", sa.Float(), nullable=True),
        sa.Column("air_yards", sa.Float(), nullable=True),
        sa.Column("yards_after_catch", sa.Float(), nullable=True),
        sa.Column("epa", sa.Float(), nullable=True),
        sa.Column("ep", sa.Float(), nullable=True),
        sa.Column("wp", sa.Float(), nullable=True),
        sa.Column("wpa", sa.Float(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("pass_attempt", sa.Boolean(), nullable=True),
        sa.Column("rush_attempt", sa.Boolean(), nullable=True),
        sa.Column("complete_pass", sa.Boolean(), nullable=True),
        sa.Column("incomplete_pass", sa.Boolean(), nullable=True),
        sa.Column("interception", sa.Boolean(), nullable=True),
        sa.Column("touchdown", sa.Boolean(), nullable=True),
        sa.Column("first_down", sa.Boolean(), nullable=True),
        sa.Column("shotgun", sa.Boolean(), nullable=True),
        sa.Column("no_huddle", sa.Boolean(), nullable=True),
        sa.Column("special_teams_play", sa.Boolean(), nullable=True),
        sa.Column("score_differential", sa.Integer(), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("passer_player_id", sa.String(length=32), nullable=True),
        sa.Column("passer_player_name", sa.String(length=64), nullable=True),
        sa.Column("rusher_player_id", sa.String(length=32), nullable=True),
        sa.Column("rusher_player_name", sa.String(length=64), nullable=True),
        sa.Column("desc", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "play_id", name="uq_plays_game_play"),
    )
    op.create_index("ix_plays_season_week", "plays", ["season", "week"])
    op.create_index("ix_plays_posteam", "plays", ["posteam", "season", "week"])
    op.create_index("ix_plays_defteam", "plays", ["defteam", "season", "week"])

    op.create_table(
        "team_ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team", sa.String(length=8), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("rating_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("prior_weight", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team", "season", "week", "rating_type", name="uq_team_ratings"),
    )
    op.create_index("ix_team_ratings_lookup", "team_ratings", ["season", "week", "team"])

    op.create_table(
        "odds_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(length=32), nullable=True),
        sa.Column("external_event_id", sa.String(length=64), nullable=True),
        sa.Column("bookmaker", sa.String(length=64), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=32), nullable=False),
        sa.Column("price_american", sa.Integer(), nullable=True),
        sa.Column("price_decimal", sa.Float(), nullable=True),
        sa.Column("point", sa.Float(), nullable=True),
        sa.Column("implied_prob_raw", sa.Float(), nullable=True),
        sa.Column("implied_prob_devig", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_closing", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_odds_game_book", "odds_snapshots", ["game_id", "bookmaker", "market"])
    op.create_index("ix_odds_captured", "odds_snapshots", ["captured_at"])

    op.create_table(
        "model_predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("home_win_prob", sa.Float(), nullable=False),
        sa.Column("predicted_spread", sa.Float(), nullable=True),
        sa.Column("predicted_total", sa.Float(), nullable=True),
        sa.Column("market_home_win_prob", sa.Float(), nullable=True),
        sa.Column("edge", sa.Float(), nullable=True),
        sa.Column("features_json", sa.Text(), nullable=True),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "game_id",
            "model_name",
            "model_version",
            name="uq_model_predictions",
        ),
    )


def downgrade() -> None:
    op.drop_table("model_predictions")
    op.drop_index("ix_odds_captured", table_name="odds_snapshots")
    op.drop_index("ix_odds_game_book", table_name="odds_snapshots")
    op.drop_table("odds_snapshots")
    op.drop_index("ix_team_ratings_lookup", table_name="team_ratings")
    op.drop_table("team_ratings")
    op.drop_index("ix_plays_defteam", table_name="plays")
    op.drop_index("ix_plays_posteam", table_name="plays")
    op.drop_index("ix_plays_season_week", table_name="plays")
    op.drop_table("plays")
    op.drop_index("ix_games_kickoff", table_name="games")
    op.drop_index("ix_games_season_week", table_name="games")
    op.drop_table("games")
    op.drop_table("stadiums")
