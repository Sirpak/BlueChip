"""Data Contract v0.1: league, identity tables, provenance, Market 0 tags.

Revision ID: 0002_data_contract
Revises: 0001_initial
Create Date: 2026-08-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_data_contract"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leagues",
        sa.Column("league_id", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("league_id"),
    )
    op.create_table(
        "teams",
        sa.Column("team_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("league", sa.String(length=8), nullable=False),
        sa.Column("abbreviation", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("conference", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["league"], ["leagues.league_id"]),
        sa.PrimaryKeyConstraint("team_id"),
        sa.UniqueConstraint("league", "abbreviation", name="uq_teams_league_abbr"),
    )
    op.create_table(
        "team_external_ids",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system", "external_id", name="uq_team_ext"),
    )
    op.create_table(
        "players",
        sa.Column("player_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("league", sa.String(length=8), nullable=False),
        sa.Column("canonical_name", sa.String(length=128), nullable=False),
        sa.Column("position", sa.String(length=16), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["league"], ["leagues.league_id"]),
        sa.PrimaryKeyConstraint("player_id"),
    )
    op.create_index("ix_players_league_name", "players", ["league", "canonical_name"])
    op.create_table(
        "player_external_ids",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system", "external_id", name="uq_player_ext"),
    )

    with op.batch_alter_table("games") as batch:
        batch.add_column(sa.Column("league", sa.String(length=8), nullable=False, server_default="NFL"))
        batch.add_column(sa.Column("source", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("source_id", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_games_league_season", ["league", "season"])

    with op.batch_alter_table("plays") as batch:
        batch.add_column(sa.Column("league", sa.String(length=8), nullable=False, server_default="NFL"))
        batch.add_column(sa.Column("source", sa.String(length=32), nullable=True))
        batch.create_index("ix_plays_league_season", ["league", "season"])

    with op.batch_alter_table("team_ratings") as batch:
        batch.add_column(sa.Column("league", sa.String(length=8), nullable=False, server_default="NFL"))

    with op.batch_alter_table("odds_snapshots") as batch:
        batch.add_column(sa.Column("league", sa.String(length=8), nullable=False, server_default="NFL"))
        batch.add_column(sa.Column("market_source", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("market_type", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("known_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("source", sa.String(length=32), nullable=True))
        batch.create_unique_constraint(
            "uq_odds_market_snapshot",
            ["game_id", "market_source", "market_type", "market", "side"],
        )


def downgrade() -> None:
    with op.batch_alter_table("odds_snapshots") as batch:
        batch.drop_constraint("uq_odds_market_snapshot", type_="unique")
        batch.drop_column("source")
        batch.drop_column("retrieved_at")
        batch.drop_column("known_at")
        batch.drop_column("market_type")
        batch.drop_column("market_source")
        batch.drop_column("league")

    with op.batch_alter_table("team_ratings") as batch:
        batch.drop_column("league")

    with op.batch_alter_table("plays") as batch:
        batch.drop_index("ix_plays_league_season")
        batch.drop_column("source")
        batch.drop_column("league")

    with op.batch_alter_table("games") as batch:
        batch.drop_index("ix_games_league_season")
        batch.drop_column("occurred_at")
        batch.drop_column("retrieved_at")
        batch.drop_column("source_id")
        batch.drop_column("source")
        batch.drop_column("league")

    op.drop_table("player_external_ids")
    op.drop_index("ix_players_league_name", table_name="players")
    op.drop_table("players")
    op.drop_table("team_external_ids")
    op.drop_table("teams")
    op.drop_table("leagues")
