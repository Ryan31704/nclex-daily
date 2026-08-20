import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.question import Question
from app.models.topic import Topic


def list_active_topics(db: Session) -> list[Topic]:
    statement = (
        select(Topic)
        .where(Topic.is_active.is_(True))
        .options(selectinload(Topic.children))
        .order_by(Topic.display_order, Topic.name)
    )
    return list(db.scalars(statement).unique().all())


def get_active_topic(db: Session, topic_id: uuid.UUID) -> Topic | None:
    statement = (
        select(Topic)
        .where(Topic.id == topic_id, Topic.is_active.is_(True))
        .options(joinedload(Topic.parent), selectinload(Topic.children))
    )
    return db.scalar(statement)


def get_question_counts_by_topic(db: Session) -> dict[uuid.UUID, int]:
    statement = (
        select(Question.topic_id, func.count(Question.id))
        .where(Question.is_active.is_(True))
        .group_by(Question.topic_id)
    )
    return {topic_id: count for topic_id, count in db.execute(statement).all()}


def get_active_question_for_review(
    db: Session,
    question_id: uuid.UUID,
) -> Question | None:
    statement = (
        select(Question)
        .where(Question.id == question_id, Question.is_active.is_(True))
        .options(
            joinedload(Question.topic).joinedload(Topic.parent),
            selectinload(Question.answer_choices),
        )
    )
    return db.scalar(statement)
