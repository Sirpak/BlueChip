"""Pregame feature_snapshots (BCW-SNAP-v0.1).

Revision ID: 0004_feature_snapshots
Revises: 0003_schedules
Create Date: 2026-08-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_feature_snapshots"
down_revision: Union[str, None] = "0003_schedules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(length=32), nullable=False),
        sa.Column("feature_version", sa.String(length=32), nullable=False),
        sa.Column("prediction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("known_at_max", sa.DateTime(timezone=True), nullable=True),
        sa.Column("era", sa.String(length=16), nullable=True),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("home_team", sa.String(length=8), nullable=False),
        sa.Column("away_team", sa.String(length=8), nullable=False),
        sa.Column("home_rest", sa.Integer(), nullable=True),
        sa.Column("away_rest", sa.Integer(), nullable=True),
        sa.Column("rest_diff", sa.Float(), nullable=True),
        sa.Column("elo_home", sa.Float(), nullable=True),
        sa.Column("elo_away", sa.Float(), nullable=True),
        sa.Column("elo_diff", sa.Float(), nullable=True),
        sa.Column("elo_win_home", sa.Float(), nullable=True),
        sa.Column("srs_home", sa.Float(), nullable=True),
        sa.Column("srs_away", sa.Float(), nullable=True),
        sa.Column("srs_diff", sa.Float(), nullable=True),
        sa.Column("srs_pred_margin", sa.Float(), nullable=True),
        sa.Column("hfa_prior", sa.Float(), nullable=True),
        sa.Column("adj_off_home", sa.Float(), nullable=True),
        sa.Column("adj_def_home", sa.Float(), nullable=True),
        sa.Column("adj_off_away", sa.Float(), nullable=True),
        sa.Column("adj_def_away", sa.Float(), nullable=True),
        sa.Column("adj_pred_margin", sa.Float(), nullable=True),
        sa.Column("home_off_epa", sa.Float(), nullable=True),
        sa.Column("away_off_epa", sa.Float(), nullable=True),
        sa.Column("home_def_epa", sa.Float(), nullable=True),
        sa.Column("away_def_epa", sa.Float(), nullable=True),
        sa.Column("home_pass_epa", sa.Float(), nullable=True),
        sa.Column("away_pass_epa", sa.Float(), nullable=True),
        sa.Column("home_rush_epa", sa.Float(), nullable=True),
        sa.Column("away_rush_epa", sa.Float(), nullable=True),
        sa.Column("home_pass_epa_allowed", sa.Float(), nullable=True),
        sa.Column("away_pass_epa_allowed", sa.Float(), nullable=True),
        sa.Column("home_rush_epa_allowed", sa.Float(), nullable=True),
        sa.Column("away_rush_epa_allowed", sa.Float(), nullable=True),
        sa.Column("success_rate_diff", sa.Float(), nullable=True),
        sa.Column("explosive_play_diff", sa.Float(), nullable=True),
        sa.Column("home_margin", sa.Float(), nullable=True),
        sa.Column("home_win", sa.Float(), nullable=True),
        sa.Column("market_spread", sa.Float(), nullable=True),
        sa.Column("extras_json", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "feature_version", name="uq_feature_snapshots_game_ver"),
    )
    op.create_index("ix_feature_snapshots_season", "feature_snapshots", ["season", "week"])


def downgrade() -> None:
    op.drop_index("ix_feature_snapshots_season", table_name="feature_snapshots")
    op.drop_table("feature_snapshots")
