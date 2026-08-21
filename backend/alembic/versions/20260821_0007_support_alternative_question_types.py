"""support alternative and NGN question types

Revision ID: 20260821_0007
Revises: 20260820_0006
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0007"
down_revision: str | None = "20260820_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("external_id", sa.String(255), nullable=True))
    op.add_column("questions", sa.Column("interaction_data", sa.JSON(), nullable=True))
    op.add_column("questions", sa.Column("answer_key", sa.JSON(), nullable=True))
    op.add_column("questions", sa.Column("case_study_markdown", sa.Text(), nullable=True))
    op.create_index("ix_questions_external_id", "questions", ["external_id"], unique=True)
    op.drop_constraint(
        "ck_answer_choices_display_order", "answer_choices", type_="check"
    )
    op.create_check_constraint(
        "ck_answer_choices_display_order",
        "answer_choices",
        "display_order >= 1 AND display_order <= 20",
    )
    op.alter_column("attempts", "selected_answer_id", nullable=True)
    op.add_column("attempts", sa.Column("answer_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "answer_data")
    op.alter_column("attempts", "selected_answer_id", nullable=False)
    op.drop_constraint(
        "ck_answer_choices_display_order", "answer_choices", type_="check"
    )
    op.create_check_constraint(
        "ck_answer_choices_display_order",
        "answer_choices",
        "display_order >= 1 AND display_order <= 4",
    )
    op.drop_index("ix_questions_external_id", table_name="questions")
    op.drop_column("questions", "case_study_markdown")
    op.drop_column("questions", "answer_key")
    op.drop_column("questions", "interaction_data")
    op.drop_column("questions", "external_id")
