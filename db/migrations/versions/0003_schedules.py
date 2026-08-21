"""Alembic: nflverse schedule fields, game_external_ids, ingest_conflicts.

Revision ID: 0003_schedules
Revises: 0002_data_contract
Create Date: 2026-08-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_schedules"
down_revision: Union[str, None] = "0002_data_contract"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.add_column(sa.Column("game_type", sa.String(length=8), nullable=True))
        batch.add_column(sa.Column("weekday", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("gametime", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("location", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("stadium_name", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("home_rest", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("away_rest", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("home_moneyline", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("away_moneyline", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("spread_home_odds", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("spread_away_odds", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("over_odds", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("under_odds", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("overtime", sa.Boolean(), nullable=True))
        batch.add_column(sa.Column("div_game", sa.Boolean(), nullable=True))
        batch.add_column(sa.Column("neutral_site", sa.Boolean(), nullable=True))

    op.create_table(
        "game_external_ids",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(length=32), nullable=False),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system", "external_id", name="uq_game_ext"),
        sa.UniqueConstraint("game_id", "system", name="uq_game_ext_system"),
    )

    op.create_table(
        "ingest_conflicts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_id", sa.String(length=32), nullable=False),
        sa.Column("field", sa.String(length=32), nullable=False),
        sa.Column("existing_value", sa.String(length=64), nullable=True),
        sa.Column("incoming_value", sa.String(length=64), nullable=True),
        sa.Column("kept", sa.String(length=16), nullable=False),
        sa.Column("source_existing", sa.String(length=32), nullable=True),
        sa.Column("source_incoming", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingest_conflicts_game", "ingest_conflicts", ["game_id", "field"])


def downgrade() -> None:
    op.drop_index("ix_ingest_conflicts_game", table_name="ingest_conflicts")
    op.drop_table("ingest_conflicts")
    op.drop_table("game_external_ids")
    with op.batch_alter_table("games") as batch:
        for col in (
            "game_type",
            "weekday",
            "gametime",
            "location",
            "stadium_name",
            "home_rest",
            "away_rest",
            "home_moneyline",
            "away_moneyline",
            "spread_home_odds",
            "spread_away_odds",
            "over_odds",
            "under_odds",
            "overtime",
            "div_game",
            "neutral_site",
        ):
            batch.drop_column(col)
