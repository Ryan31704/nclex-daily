"""recalculate mastery from unique question coverage

Revision ID: 20260820_0006
Revises: 20260820_0005
Create Date: 2026-08-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260820_0006"
down_revision: str | None = "20260820_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A question contributes one point only when the user's latest answer to it
    # is correct. Unseen and latest-incorrect questions contribute zero.
    op.execute(
        """
        WITH ranked_attempts AS (
            SELECT
                attempts.user_id,
                attempts.question_id,
                questions.topic_id,
                attempts.is_correct,
                ROW_NUMBER() OVER (
                    PARTITION BY attempts.user_id, attempts.question_id
                    ORDER BY attempts.answered_at DESC, attempts.id DESC
                ) AS attempt_rank
            FROM attempts
            JOIN questions ON questions.id = attempts.question_id
            WHERE questions.is_active = true
        ),
        coverage AS (
            SELECT
                topic_progress.id AS progress_id,
                COALESCE(SUM(
                    CASE WHEN ranked_attempts.is_correct = true THEN 1 ELSE 0 END
                ), 0) AS correct_latest_answers,
                (
                    SELECT COUNT(*)
                    FROM questions
                    WHERE questions.topic_id = topic_progress.topic_id
                        AND questions.is_active = true
                ) AS total_questions
            FROM topic_progress
            LEFT JOIN ranked_attempts
                ON ranked_attempts.user_id = topic_progress.user_id
                AND ranked_attempts.topic_id = topic_progress.topic_id
                AND ranked_attempts.attempt_rank = 1
            GROUP BY topic_progress.id, topic_progress.topic_id
        )
        UPDATE topic_progress
        SET mastery_score = COALESCE(
            (
                SELECT ROUND(
                    CAST(
                        100.0 * coverage.correct_latest_answers
                        / NULLIF(coverage.total_questions, 0)
                        AS numeric
                    ),
                    1
                )
                FROM coverage
                WHERE coverage.progress_id = topic_progress.id
            ),
            0
        )
        """
    )


def downgrade() -> None:
    # The former weighted score cannot be reconstructed from persisted data.
    pass
