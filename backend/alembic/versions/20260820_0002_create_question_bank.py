"""create normalized question bank tables

Revision ID: 20260820_0002
Revises: 20260820_0001
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0002"
down_revision: str | None = "20260820_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_topic_id", sa.Uuid(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["parent_topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topics_parent_topic_id", "topics", ["parent_topic_id"])
    op.create_index(
        "uq_topics_parent_slug",
        "topics",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("parent_topic_id IS NULL"),
    )
    op.create_index(
        "uq_topics_child_parent_slug",
        "topics",
        ["parent_topic_id", "slug"],
        unique=True,
        postgresql_where=sa.text("parent_topic_id IS NOT NULL"),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=False),
        sa.Column("license_status", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_topic_id", "questions", ["topic_id"])
    op.create_index(
        "ix_questions_content_hash",
        "questions",
        ["content_hash"],
        unique=True,
    )

    op.create_table(
        "answer_choices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("choice_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "display_order >= 1 AND display_order <= 4",
            name="ck_answer_choices_display_order",
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "question_id",
            "display_order",
            name="uq_answer_choices_question_display_order",
        ),
    )
    op.create_index(
        "ix_answer_choices_question_id",
        "answer_choices",
        ["question_id"],
    )

    # These tables are served only through authenticated FastAPI routes. No
    # PostgREST policies are added, so browser clients cannot query them directly.
    op.execute("ALTER TABLE topics ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE questions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE answer_choices ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_answer_choices_question_id", table_name="answer_choices")
    op.drop_table("answer_choices")
    op.drop_index("ix_questions_content_hash", table_name="questions")
    op.drop_index("ix_questions_topic_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("uq_topics_child_parent_slug", table_name="topics")
    op.drop_index("uq_topics_parent_slug", table_name="topics")
    op.drop_index("ix_topics_parent_topic_id", table_name="topics")
    op.drop_table("topics")
