import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.question import Question
from app.models.topic_progress import TopicProgress

RECENT_ATTEMPT_LIMIT = 20


@dataclass(frozen=True)
class MasteryAttempt:
    is_correct: bool
    difficulty: str | None = None


def calculate_mastery(attempts: Sequence[MasteryAttempt]) -> float:
    """Return a 0-100 score with recent outcomes weighted most heavily."""
    recent = list(attempts)[-RECENT_ATTEMPT_LIMIT:]
    if not recent:
        return 0.0

    weighted_signal = 0.0
    total_weight = 0.0
    difficulty_weights = {"easy": 0.9, "medium": 1.0, "hard": 1.1}
    for recency, attempt in enumerate(recent, start=1):
        weight = recency * difficulty_weights.get(attempt.difficulty or "medium", 1.0)
        weighted_signal += weight if attempt.is_correct else -weight
        total_weight += weight

    normalized = ((weighted_signal / total_weight) + 1.0) * 50.0
    return round(max(0.0, min(100.0, normalized)), 1)


def classify_mastery(score: float) -> str:
    if score < 40:
        return "weak"
    if score < 70:
        return "developing"
    if score < 85:
        return "strong"
    return "mastered"


def update_topic_progress(
    db: Session,
    *,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
    practiced_at: datetime,
) -> TopicProgress:
    recent_rows = db.execute(
        select(Attempt.is_correct, Question.difficulty)
        .join(Question, Question.id == Attempt.question_id)
        .where(Attempt.user_id == user_id, Question.topic_id == topic_id)
        .order_by(Attempt.answered_at.desc())
        .limit(RECENT_ATTEMPT_LIMIT)
    ).all()
    recent_attempts = [
        MasteryAttempt(is_correct=is_correct, difficulty=difficulty)
        for is_correct, difficulty in reversed(recent_rows)
    ]
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
    progress.mastery_score = calculate_mastery(recent_attempts)
    progress.last_practiced_at = practiced_at
    db.flush()
    return progress
