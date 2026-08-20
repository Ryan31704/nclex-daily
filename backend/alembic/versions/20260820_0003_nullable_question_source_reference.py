"""allow nullable question source references

Revision ID: 20260820_0003
Revises: 20260820_0002
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0003"
down_revision: str | None = "20260820_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "questions",
        "source_reference",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "questions",
        "source_reference",
        existing_type=sa.String(length=255),
        nullable=False,
    )
