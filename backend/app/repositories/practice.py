import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.answer_choice import AnswerChoice
from app.models.attempt import Attempt
from app.models.daily_session import DailySession
from app.models.question import Question
from app.models.session_question import SessionQuestion
from app.models.topic import Topic
from app.models.topic_progress import TopicProgress


def get_session_for_user(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    lock: bool = False,
) -> DailySession | None:
    statement = (
        select(DailySession)
        .where(DailySession.id == session_id, DailySession.user_id == user_id)
        .options(
            selectinload(DailySession.session_questions)
            .joinedload(SessionQuestion.question)
            .joinedload(Question.topic),
            selectinload(DailySession.session_questions)
            .joinedload(SessionQuestion.question)
            .selectinload(Question.answer_choices),
        )
    )
    if lock:
        statement = statement.with_for_update()
    return db.scalar(statement)


def list_active_questions(
    db: Session,
    *,
    topic_ids: set[uuid.UUID] | None = None,
) -> list[Question]:
    statement = (
        select(Question)
        .join(Topic, Topic.id == Question.topic_id)
        .where(Question.is_active.is_(True), Topic.is_active.is_(True))
        .options(joinedload(Question.topic), selectinload(Question.answer_choices))
    )
    if topic_ids is not None:
        statement = statement.where(Question.topic_id.in_(topic_ids))
    return list(db.scalars(statement).unique().all())


def list_user_attempts(db: Session, user_id: uuid.UUID) -> list[Attempt]:
    statement = (
        select(Attempt)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.answered_at.desc())
    )
    return list(db.scalars(statement).all())


def get_user_progress(db: Session, user_id: uuid.UUID) -> list[TopicProgress]:
    statement = (
        select(TopicProgress)
        .where(TopicProgress.user_id == user_id)
        .options(joinedload(TopicProgress.topic))
    )
    return list(db.scalars(statement).all())


def get_answer_choice(
    db: Session,
    *,
    question_id: uuid.UUID,
    choice_id: uuid.UUID,
) -> AnswerChoice | None:
    return db.scalar(
        select(AnswerChoice).where(
            AnswerChoice.id == choice_id,
            AnswerChoice.question_id == question_id,
        )
    )


def get_correct_answer(db: Session, question_id: uuid.UUID) -> AnswerChoice | None:
    return db.scalar(
        select(AnswerChoice).where(
            AnswerChoice.question_id == question_id,
            AnswerChoice.is_correct.is_(True),
        )
    )


def get_session_attempt(
    db: Session,
    *,
    session_id: uuid.UUID,
    question_id: uuid.UUID,
) -> Attempt | None:
    return db.scalar(
        select(Attempt).where(
            Attempt.session_id == session_id,
            Attempt.question_id == question_id,
        )
    )


def list_most_recent_missed_attempts(
    db: Session,
    *,
    user_id: uuid.UUID,
    topic_id: uuid.UUID | None,
    limit: int,
) -> list[Attempt]:
    statement = (
        select(Attempt)
        .join(Question, Question.id == Attempt.question_id)
        .where(Attempt.user_id == user_id)
        .options(
            joinedload(Attempt.question).joinedload(Question.topic),
            joinedload(Attempt.question).selectinload(Question.answer_choices),
        )
        .order_by(Attempt.answered_at.desc())
    )
    if topic_id is not None:
        statement = statement.where(Question.topic_id == topic_id)
    attempts = list(db.scalars(statement).unique().all())
    latest_by_question: dict[uuid.UUID, Attempt] = {}
    for attempt in attempts:
        latest_by_question.setdefault(attempt.question_id, attempt)
    return [
        attempt
        for attempt in latest_by_question.values()
        if not attempt.is_correct
    ][:limit]
