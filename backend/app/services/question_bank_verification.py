from dataclasses import asdict, dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, aliased

from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.topic import Topic


@dataclass(frozen=True)
class QuestionBankMetrics:
    questions: int
    answer_choices: int
    parent_topics: int
    child_topics: int
    questions_without_four_choices: int
    questions_without_one_correct_choice: int
    questions_without_topic: int
    questions_assigned_to_parent_topic: int
    orphan_child_topics: int
    invalid_source_metadata: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def collect_question_bank_metrics(db: Session) -> QuestionBankMetrics:
    choice_counts = (
        select(
            AnswerChoice.question_id.label("question_id"),
            func.count(AnswerChoice.id).label("choice_count"),
            func.sum(case((AnswerChoice.is_correct.is_(True), 1), else_=0)).label(
                "correct_count"
            ),
        )
        .group_by(AnswerChoice.question_id)
        .subquery()
    )
    questions_without_four = db.scalar(
        select(func.count())
        .select_from(Question)
        .outerjoin(choice_counts, choice_counts.c.question_id == Question.id)
        .where(func.coalesce(choice_counts.c.choice_count, 0) != 4)
    ) or 0
    questions_without_one_correct = db.scalar(
        select(func.count())
        .select_from(Question)
        .outerjoin(choice_counts, choice_counts.c.question_id == Question.id)
        .where(func.coalesce(choice_counts.c.correct_count, 0) != 1)
    ) or 0
    questions_without_topic = db.scalar(
        select(func.count())
        .select_from(Question)
        .outerjoin(Topic, Topic.id == Question.topic_id)
        .where(Topic.id.is_(None))
    ) or 0
    questions_assigned_to_parent = db.scalar(
        select(func.count())
        .select_from(Question)
        .join(Topic, Topic.id == Question.topic_id)
        .where(Topic.parent_topic_id.is_(None))
    ) or 0
    child_topic = aliased(Topic)
    parent_topic = aliased(Topic)
    orphan_children = db.scalar(
        select(func.count())
        .select_from(child_topic)
        .outerjoin(parent_topic, parent_topic.id == child_topic.parent_topic_id)
        .where(child_topic.parent_topic_id.is_not(None), parent_topic.id.is_(None))
    ) or 0
    invalid_source_metadata = db.scalar(
        select(func.count())
        .select_from(Question)
        .where(
            (Question.question_type != "multiple_choice")
            | (Question.source_type != "imported_private")
            | Question.source_reference.is_(None)
            | (Question.source_reference == "")
            | (Question.license_status != "review_required")
            | Question.rationale.is_not(None)
            | Question.difficulty.is_not(None)
        )
    ) or 0

    return QuestionBankMetrics(
        questions=db.scalar(select(func.count()).select_from(Question)) or 0,
        answer_choices=db.scalar(select(func.count()).select_from(AnswerChoice)) or 0,
        parent_topics=db.scalar(
            select(func.count()).select_from(Topic).where(Topic.parent_topic_id.is_(None))
        )
        or 0,
        child_topics=db.scalar(
            select(func.count()).select_from(Topic).where(Topic.parent_topic_id.is_not(None))
        )
        or 0,
        questions_without_four_choices=questions_without_four,
        questions_without_one_correct_choice=questions_without_one_correct,
        questions_without_topic=questions_without_topic,
        questions_assigned_to_parent_topic=questions_assigned_to_parent,
        orphan_child_topics=orphan_children,
        invalid_source_metadata=invalid_source_metadata,
    )
