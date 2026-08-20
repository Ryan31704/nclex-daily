"""create quiz engine tables

Revision ID: 20260820_0004
Revises: 20260820_0003
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0004"
down_revision: str | None = "20260820_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_question_count", sa.Integer(), nullable=False),
        sa.Column("questions_completed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("xp_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column(
            "practice_type",
            sa.String(length=20),
            server_default="daily",
            nullable=False,
        ),
        sa.Column("topic_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "target_question_count > 0 AND questions_completed >= 0 "
            "AND correct_count >= 0 AND xp_earned >= 0",
            name="ck_daily_sessions_nonnegative_counts",
        ),
        sa.CheckConstraint(
            "practice_type IN ('daily', 'topic')",
            name="ck_daily_sessions_practice_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="ck_daily_sessions_status",
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_sessions_user_id", "daily_sessions", ["user_id"])
    op.create_index("ix_daily_sessions_topic_id", "daily_sessions", ["topic_id"])
    op.create_index(
        "ix_daily_sessions_user_started_at",
        "daily_sessions",
        ["user_id", "started_at"],
    )

    op.create_table(
        "session_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["daily_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "display_order",
            name="uq_session_questions_session_order",
        ),
        sa.UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_session_questions_session_question",
        ),
    )
    op.create_index(
        "ix_session_questions_session_id",
        "session_questions",
        ["session_id"],
    )
    op.create_index(
        "ix_session_questions_question_id",
        "session_questions",
        ["question_id"],
    )

    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("selected_answer_id", sa.Uuid(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column(
            "answered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "response_time_ms IS NULL OR response_time_ms >= 0",
            name="ck_attempts_nonnegative_response_time",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["selected_answer_id"],
            ["answer_choices.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["daily_sessions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_attempts_session_question",
        ),
    )
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])
    op.create_index("ix_attempts_question_id", "attempts", ["question_id"])
    op.create_index("ix_attempts_answered_at", "attempts", ["answered_at"])
    op.create_index("ix_attempts_session_id", "attempts", ["session_id"])
    op.create_index(
        "ix_attempts_user_question_answered_at",
        "attempts",
        ["user_id", "question_id", "answered_at"],
    )

    op.create_table(
        "topic_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("attempted_questions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("correct_questions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mastery_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "mastery_score >= 0 AND mastery_score <= 100",
            name="ck_topic_progress_mastery_range",
        ),
        sa.CheckConstraint(
            "attempted_questions >= 0 AND correct_questions >= 0",
            name="ck_topic_progress_nonnegative_counts",
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "topic_id", name="uq_topic_progress_user_topic"),
    )
    op.create_index("ix_topic_progress_user_id", "topic_progress", ["user_id"])
    op.create_index("ix_topic_progress_topic_id", "topic_progress", ["topic_id"])

    op.execute("ALTER TABLE daily_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE session_questions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE attempts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE topic_progress ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_topic_progress_topic_id", table_name="topic_progress")
    op.drop_index("ix_topic_progress_user_id", table_name="topic_progress")
    op.drop_table("topic_progress")
    op.drop_index("ix_attempts_user_question_answered_at", table_name="attempts")
    op.drop_index("ix_attempts_session_id", table_name="attempts")
    op.drop_index("ix_attempts_answered_at", table_name="attempts")
    op.drop_index("ix_attempts_question_id", table_name="attempts")
    op.drop_index("ix_attempts_user_id", table_name="attempts")
    op.drop_table("attempts")
    op.drop_index("ix_session_questions_question_id", table_name="session_questions")
    op.drop_index("ix_session_questions_session_id", table_name="session_questions")
    op.drop_table("session_questions")
    op.drop_index("ix_daily_sessions_user_started_at", table_name="daily_sessions")
    op.drop_index("ix_daily_sessions_topic_id", table_name="daily_sessions")
    op.drop_index("ix_daily_sessions_user_id", table_name="daily_sessions")
    op.drop_table("daily_sessions")
