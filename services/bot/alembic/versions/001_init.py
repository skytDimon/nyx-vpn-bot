"""init bot tables

Revision ID: 001_init
Revises:
Create Date: 2026-01-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("tg_id", sa.BigInteger(), nullable=False, unique=True),
            sa.Column("username", sa.Text()),
            sa.Column("referrer_tg_id", sa.BigInteger()),
            sa.Column(
                "referral_balance", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "first_payment_done",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
        )

    if "subscriptions" not in existing_tables:
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("tg_id", sa.BigInteger(), nullable=False, unique=True),
            sa.Column("start_at", sa.DateTime(timezone=True)),
            sa.Column("end_at", sa.DateTime(timezone=True)),
            sa.Column("subscription_link", sa.Text()),
            sa.Column("instructions", sa.Text()),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
        )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("users")
