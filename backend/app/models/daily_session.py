import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailySession(Base):
    __tablename__ = "daily_sessions"
    __table_args__ = (
        Index("ix_daily_sessions_user_started_at", "user_id", "started_at"),
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="ck_daily_sessions_status",
        ),
        CheckConstraint(
            "practice_type IN ('daily', 'topic', 'quick_review', 'random')",
            name="ck_daily_sessions_practice_type",
        ),
        CheckConstraint(
            "target_question_count > 0 AND questions_completed >= 0 "
            "AND correct_count >= 0 AND xp_earned >= 0",
            name="ck_daily_sessions_nonnegative_counts",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    target_question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    questions_completed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    correct_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    xp_earned: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    practice_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="daily",
        server_default="daily",
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    session_questions: Mapped[list["SessionQuestion"]] = relationship(
        "SessionQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionQuestion.display_order",
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        "Attempt",
        back_populates="session",
    )


from app.models.attempt import Attempt  # noqa: E402
from app.models.session_question import SessionQuestion  # noqa: E402
