"""create profiles table

Revision ID: 20260820_0001
Revises:
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("auth_user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_xp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_practice_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profiles_auth_user_id",
        "profiles",
        ["auth_user_id"],
        unique=True,
    )
    # Profiles are accessed only through authenticated FastAPI routes.
    # No Data API policies are created, so anon/authenticated PostgREST roles are denied.
    op.execute("ALTER TABLE profiles ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_profiles_auth_user_id", table_name="profiles")
    op.drop_table("profiles")
