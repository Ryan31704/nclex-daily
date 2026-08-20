import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnswerChoice(Base):
    __tablename__ = "answer_choices"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "display_order",
            name="uq_answer_choices_question_display_order",
        ),
        CheckConstraint(
            "display_order >= 1 AND display_order <= 4",
            name="ck_answer_choices_display_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    choice_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="answer_choices",
    )


from app.models.question import Question  # noqa: E402
