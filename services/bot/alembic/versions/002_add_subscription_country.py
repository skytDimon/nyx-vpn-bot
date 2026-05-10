"""add subscription country

Revision ID: 002_add_subscription_country
Revises: 001_init
Create Date: 2026-02-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "002_add_subscription_country"
down_revision = "001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("country", sa.Text(), nullable=False, server_default="fi"),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "country")
