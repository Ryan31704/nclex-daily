import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        Index(
            "ix_attempts_user_question_answered_at",
            "user_id",
            "question_id",
            "answered_at",
        ),
        UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_attempts_session_question",
        ),
        CheckConstraint(
            "response_time_ms IS NULL OR response_time_ms >= 0",
            name="ck_attempts_nonnegative_response_time",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selected_answer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("answer_choices.id", ondelete="RESTRICT"),
        nullable=True,
    )
    answer_data: Mapped[dict | list | str | int | float | None] = mapped_column(
        JSON, nullable=True
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("daily_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    session: Mapped["DailySession | None"] = relationship(
        "DailySession",
        back_populates="attempts",
    )
    question: Mapped["Question"] = relationship("Question")
    selected_answer: Mapped["AnswerChoice"] = relationship("AnswerChoice")


from app.models.answer_choice import AnswerChoice  # noqa: E402
from app.models.daily_session import DailySession  # noqa: E402
from app.models.question import Question  # noqa: E402
