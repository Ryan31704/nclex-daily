"""expand practice modes and confidence-adjust existing mastery

Revision ID: 20260820_0005
Revises: 20260820_0004
Create Date: 2026-08-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260820_0005"
down_revision: str | None = "20260820_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_daily_sessions_practice_type",
        "daily_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_daily_sessions_practice_type",
        "daily_sessions",
        "practice_type IN ('daily', 'topic', 'quick_review', 'random')",
    )
    # Existing scores were pure performance values. Apply the same ten-attempt
    # confidence ramp used by the updated mastery service.
    op.execute(
        """
        UPDATE topic_progress
        SET mastery_score = ROUND(
            CAST(mastery_score * LEAST(attempted_questions / 10.0, 1.0) AS numeric),
            1
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "UPDATE daily_sessions SET practice_type = 'topic' "
        "WHERE practice_type IN ('quick_review', 'random')"
    )
    op.drop_constraint(
        "ck_daily_sessions_practice_type",
        "daily_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_daily_sessions_practice_type",
        "daily_sessions",
        "practice_type IN ('daily', 'topic')",
    )
