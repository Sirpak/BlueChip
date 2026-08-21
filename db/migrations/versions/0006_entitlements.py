"""Plans, display names, and monthly usage meters.

Revision ID: 0006_entitlements
Revises: 0005_users
Create Date: 2026-08-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_entitlements"
down_revision: Union[str, None] = "0005_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("display_name", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("plan", sa.String(length=16), nullable=False, server_default="FREE"))
        batch.add_column(sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch.add_column(sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "plan_usage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("ai_queries_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_credits_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exports_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deep_research_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "billing_period_start", name="uq_plan_usage_period"),
    )


def downgrade() -> None:
    op.drop_table("plan_usage")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("last_login_at")
        batch.drop_column("email_verified")
        batch.drop_column("plan")
        batch.drop_column("display_name")
