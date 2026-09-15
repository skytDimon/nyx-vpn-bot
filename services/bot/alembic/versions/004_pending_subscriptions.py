"""pending subscriptions by username (panel → cabinet on first /start)

Revision ID: 004_pending_subscriptions
Revises: 003_trial_and_manager
Create Date: 2026-09-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "004_pending_subscriptions"
down_revision = "003_trial_and_manager"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_subscriptions",
        # username хранится в нижнем регистре без '@' — это PK матчинга при /start
        sa.Column("username", sa.Text(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True)),
        sa.Column("end_at", sa.DateTime(timezone=True)),
        sa.Column("subscription_link", sa.Text()),
        sa.Column("instructions", sa.Text()),
        sa.Column("country", sa.Text(), nullable=False, server_default="nl"),
        sa.Column("client_uuid", sa.Text()),
        sa.Column("sub_id", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("pending_subscriptions")
