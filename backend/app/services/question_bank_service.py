import uuid

from sqlalchemy.orm import Session

from app.repositories.question_bank import (
    get_active_question_for_review,
    get_active_topic,
    get_question_counts_by_topic,
    list_active_topics,
)
from app.schemas.question_bank import (
    AnswerChoiceReview,
    ChildTopicSummary,
    QuestionReview,
    TopicDetail,
    TopicReference,
    TopicSummary,
)


def list_topic_hierarchy(db: Session) -> list[TopicSummary]:
    topics = list_active_topics(db)
    counts = get_question_counts_by_topic(db)
    parents = [topic for topic in topics if topic.parent_topic_id is None]
    return [
        TopicSummary(
            id=parent.id,
            name=parent.name,
            slug=parent.slug,
            description=parent.description,
            display_order=parent.display_order,
            question_count=sum(counts.get(child.id, 0) for child in parent.children),
            children=[
                ChildTopicSummary(
                    id=child.id,
                    name=child.name,
                    slug=child.slug,
                    description=child.description,
                    display_order=child.display_order,
                    question_count=counts.get(child.id, 0),
                )
                for child in parent.children
                if child.is_active
            ],
        )
        for parent in parents
    ]


def get_topic_detail(db: Session, topic_id: uuid.UUID) -> TopicDetail | None:
    topic = get_active_topic(db, topic_id)
    if topic is None:
        return None

    counts = get_question_counts_by_topic(db)
    children = [child for child in topic.children if child.is_active]
    direct_count = counts.get(topic.id, 0)
    question_count = direct_count + sum(counts.get(child.id, 0) for child in children)
    return TopicDetail(
        id=topic.id,
        name=topic.name,
        slug=topic.slug,
        description=topic.description,
        display_order=topic.display_order,
        is_active=topic.is_active,
        created_at=topic.created_at,
        question_count=question_count,
        parent=(
            TopicReference.model_validate(topic.parent) if topic.parent is not None else None
        ),
        children=[
            ChildTopicSummary(
                id=child.id,
                name=child.name,
                slug=child.slug,
                description=child.description,
                display_order=child.display_order,
                question_count=counts.get(child.id, 0),
            )
            for child in children
        ],
    )


def get_question_review(db: Session, question_id: uuid.UUID) -> QuestionReview | None:
    question = get_active_question_for_review(db, question_id)
    if question is None:
        return None

    return QuestionReview(
        id=question.id,
        question_text=question.question_text,
        rationale=question.rationale,
        difficulty=question.difficulty,
        question_type=question.question_type,
        source_type=question.source_type,
        source_reference=question.source_reference,
        license_status=question.license_status,
        topic=TopicReference.model_validate(question.topic),
        choices=[
            AnswerChoiceReview(
                id=choice.id,
                choice_text=choice.choice_text,
                display_order=choice.display_order,
            )
            for choice in question.answer_choices
        ],
    )
