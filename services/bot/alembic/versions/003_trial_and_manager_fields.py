"""add trial_used and manager api fields

Revision ID: 003_trial_and_manager
Revises: 002_add_subscription_country
Create Date: 2026-05-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "003_trial_and_manager"
down_revision = "002_add_subscription_country"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("trial_used", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "subscriptions",
        sa.Column("client_uuid", sa.Text(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("sub_id", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "sub_id")
    op.drop_column("subscriptions", "client_uuid")
    op.drop_column("users", "trial_used")
