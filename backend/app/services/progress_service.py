import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.daily_session import DailySession
from app.models.profile import Profile
from app.models.topic import Topic
from app.models.topic_progress import TopicProgress
from app.repositories.practice import (
    get_session_for_user,
    list_most_recent_missed_attempts,
)
from app.schemas.practice import (
    DashboardResponse,
    MissedQuestionResponse,
    PracticeQuestion,
    ProgressResponse,
    TopicProgressResponse,
)
from app.schemas.question_bank import AnswerChoiceReview, TopicReference
from app.services.daily_practice_service import serialize_session
from app.services.mastery_service import classify_mastery


def get_topic_progress_response(
    db: Session,
    *,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
) -> TopicProgressResponse | None:
    topic = db.get(Topic, topic_id)
    if topic is None or not topic.is_active:
        return None

    topic_ids = [topic.id]
    if topic.parent_topic_id is None:
        topic_ids = list(
            db.scalars(
                select(Topic.id).where(
                    Topic.parent_topic_id == topic.id,
                    Topic.is_active.is_(True),
                )
            ).all()
        )
    progress_rows = list(
        db.scalars(
            select(TopicProgress).where(
                TopicProgress.user_id == user_id,
                TopicProgress.topic_id.in_(topic_ids),
            )
        ).all()
    )
    return _aggregate_topic_progress(topic, progress_rows)


def get_overall_progress(db: Session, profile: Profile) -> ProgressResponse:
    topics = list(
        db.scalars(
            select(Topic)
            .where(
                Topic.parent_topic_id.is_not(None),
                Topic.is_active.is_(True),
            )
            .order_by(Topic.display_order, Topic.name)
        ).all()
    )
    progress_by_topic = {
        progress.topic_id: progress
        for progress in db.scalars(
            select(TopicProgress).where(TopicProgress.user_id == profile.id)
        ).all()
    }
    topic_responses = [
        _aggregate_topic_progress(
            topic,
            [progress_by_topic[topic.id]] if topic.id in progress_by_topic else [],
        )
        for topic in topics
    ]
    questions_answered, correct_questions = db.execute(
        select(
            func.count(Attempt.id),
            func.sum(Attempt.is_correct.cast(Integer)),
        ).where(Attempt.user_id == profile.id)
    ).one()
    attempted_total = sum(item.attempted_questions for item in topic_responses)
    overall_mastery = (
        round(
            sum(item.mastery_score * item.attempted_questions for item in topic_responses)
            / attempted_total,
            1,
        )
        if attempted_total
        else 0.0
    )
    return ProgressResponse(
        overall_mastery=overall_mastery,
        questions_answered=int(questions_answered or 0),
        correct_questions=int(correct_questions or 0),
        topics=topic_responses,
    )


def get_missed_questions(
    db: Session,
    *,
    profile: Profile,
    topic_id: uuid.UUID | None,
    limit: int,
) -> list[MissedQuestionResponse]:
    attempts = list_most_recent_missed_attempts(
        db,
        user_id=profile.id,
        topic_id=topic_id,
        limit=limit,
    )
    return [
        MissedQuestionResponse(
            attempt_id=attempt.id,
            attempted_at=attempt.answered_at,
            selected_answer_id=attempt.selected_answer_id,
            question=PracticeQuestion(
                id=attempt.question.id,
                question_text=attempt.question.question_text,
                question_type=attempt.question.question_type,
                topic=TopicReference.model_validate(attempt.question.topic),
                choices=[
                    AnswerChoiceReview(
                        id=choice.id,
                        choice_text=choice.choice_text,
                        display_order=choice.display_order,
                    )
                    for choice in attempt.question.answer_choices
                ],
            ),
        )
        for attempt in attempts
    ]


def get_dashboard(db: Session, profile: Profile) -> DashboardResponse:
    progress = get_overall_progress(db, profile)
    day_start = datetime.combine(datetime.now(UTC).date(), datetime.min.time(), tzinfo=UTC)
    latest_daily = db.scalar(
        select(DailySession)
        .where(
            DailySession.user_id == profile.id,
            DailySession.practice_type == "daily",
            DailySession.started_at >= day_start,
            DailySession.started_at < day_start + timedelta(days=1),
        )
        .order_by(DailySession.started_at.desc())
    )
    daily_session = None
    if latest_daily is not None:
        loaded = get_session_for_user(
            db,
            session_id=latest_daily.id,
            user_id=profile.id,
        )
        if loaded is not None:
            daily_session = serialize_session(loaded)

    weakest = sorted(
        (item for item in progress.topics if item.attempted_questions > 0),
        key=lambda item: (item.mastery_score, item.topic.name),
    )[:3]
    return DashboardResponse(
        display_name=profile.display_name,
        current_streak=profile.current_streak,
        longest_streak=profile.longest_streak,
        total_xp=profile.total_xp,
        questions_answered=progress.questions_answered,
        overall_mastery=progress.overall_mastery,
        daily_session=daily_session,
        weakest_topics=weakest,
    )


def _aggregate_topic_progress(
    topic: Topic,
    progress_rows: list[TopicProgress],
) -> TopicProgressResponse:
    attempted = sum(row.attempted_questions for row in progress_rows)
    correct = sum(row.correct_questions for row in progress_rows)
    mastery = (
        round(
            sum(row.mastery_score * row.attempted_questions for row in progress_rows)
            / attempted,
            1,
        )
        if attempted
        else 0.0
    )
    practiced_dates = [
        row.last_practiced_at
        for row in progress_rows
        if row.last_practiced_at is not None
    ]
    return TopicProgressResponse(
        topic=TopicReference.model_validate(topic),
        attempted_questions=attempted,
        correct_questions=correct,
        correct_percentage=round((correct / attempted) * 100, 1) if attempted else 0.0,
        mastery_score=mastery,
        classification=classify_mastery(mastery),
        last_practiced_at=max(practiced_dates) if practiced_dates else None,
    )
