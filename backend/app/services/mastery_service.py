import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.question import Question
from app.models.topic_progress import TopicProgress

@dataclass(frozen=True)
class MasteryAttempt:
    is_correct: bool


def calculate_mastery(
    latest_question_attempts: Sequence[MasteryAttempt],
    *,
    total_question_count: int,
) -> float:
    """Return the percentage of the active question pool answered correctly.

    Callers provide only the latest attempt for each unique question. Unseen
    questions contribute zero, and repeating one question cannot inflate the
    score.
    """
    if total_question_count <= 0:
        return 0.0
    correct_question_count = sum(
        1 for attempt in latest_question_attempts if attempt.is_correct
    )
    return round(
        max(0.0, min(100.0, (correct_question_count / total_question_count) * 100)),
        1,
    )


def classify_mastery(score: float) -> str:
    if score < 40:
        return "weak"
    if score < 70:
        return "developing"
    if score < 100:
        return "strong"
    return "mastered"


def update_topic_progress(
    db: Session,
    *,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
    practiced_at: datetime,
) -> TopicProgress:
    attempt_rows = db.execute(
        select(Attempt.question_id, Attempt.is_correct)
        .join(Question, Question.id == Attempt.question_id)
        .where(
            Attempt.user_id == user_id,
            Question.topic_id == topic_id,
            Question.is_active.is_(True),
        )
        .order_by(Attempt.answered_at.desc(), Attempt.id.desc())
    ).all()
    latest_by_question: dict[uuid.UUID, MasteryAttempt] = {}
    for question_id, is_correct in attempt_rows:
        latest_by_question.setdefault(
            question_id,
            MasteryAttempt(is_correct=is_correct),
        )
    total_question_count = db.scalar(
        select(func.count(Question.id)).where(
            Question.topic_id == topic_id,
            Question.is_active.is_(True),
        )
    )
    attempted_count, correct_count = db.execute(
        select(
            func.count(Attempt.id),
            func.sum(Attempt.is_correct.cast(Integer)),
        )
        .join(Question, Question.id == Attempt.question_id)
        .where(Attempt.user_id == user_id, Question.topic_id == topic_id)
    ).one()

    progress = db.scalar(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic_id,
        )
    )
    if progress is None:
        progress = TopicProgress(user_id=user_id, topic_id=topic_id)
        db.add(progress)

    progress.attempted_questions = int(attempted_count or 0)
    progress.correct_questions = int(correct_count or 0)
    progress.mastery_score = calculate_mastery(
        list(latest_by_question.values()),
        total_question_count=int(total_question_count or 0),
    )
    progress.last_practiced_at = practiced_at
    db.flush()
    return progress
