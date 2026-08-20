import uuid
import random
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.daily_session import DailySession
from app.models.profile import Profile
from app.models.question import Question
from app.models.session_question import SessionQuestion
from app.models.topic import Topic
from app.models.topic_progress import TopicProgress
from app.repositories.practice import (
    get_answer_choice,
    get_correct_answer,
    get_session_attempt,
    get_session_for_user,
    get_user_progress,
    list_active_questions,
    list_user_attempts,
)
from app.schemas.practice import (
    CompleteSessionResponse,
    CorrectAnswerResponse,
    PracticeQuestion,
    PracticeSessionResponse,
    SessionQuestionResponse,
    SubmitAnswerResponse,
)
from app.schemas.question_bank import AnswerChoiceReview, TopicReference
from app.services.mastery_service import classify_mastery, update_topic_progress

CORRECT_ANSWER_XP = 10
INCORRECT_ANSWER_XP = 5
DAILY_COMPLETION_BONUS_XP = 25


class PracticeError(Exception):
    pass


class PracticeNotFound(PracticeError):
    pass


class PracticeConflict(PracticeError):
    pass


class PracticeInvalidRequest(PracticeError):
    pass


class EmptyQuestionBank(PracticeError):
    pass


class DailyPracticeService:
    def __init__(
        self,
        db: Session,
        profile: Profile,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self.profile = profile
        self.clock = clock or (lambda: datetime.now(UTC))

    def generate_daily_session(self, target_question_count: int = 10) -> DailySession:
        now = self.clock()
        day_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        existing = self.db.scalar(
            select(DailySession)
            .where(
                DailySession.user_id == self.profile.id,
                DailySession.practice_type == "daily",
                DailySession.started_at >= day_start,
                DailySession.started_at < day_end,
            )
            .order_by(DailySession.started_at.desc())
        )
        if existing is not None:
            return existing

        selected = self.select_questions(target_question_count=target_question_count)
        return self._create_session(selected, practice_type="daily")

    def generate_topic_session(
        self,
        topic_id: uuid.UUID,
        target_question_count: int = 10,
    ) -> DailySession:
        topic = self.db.get(Topic, topic_id)
        if topic is None or not topic.is_active:
            raise PracticeNotFound("Topic not found.")

        topic_ids = {topic.id}
        if topic.parent_topic_id is None:
            topic_ids.update(
                self.db.scalars(
                    select(Topic.id).where(
                        Topic.parent_topic_id == topic.id,
                        Topic.is_active.is_(True),
                    )
                ).all()
            )
        selected = self.select_questions(
            target_question_count=target_question_count,
            topic_ids=topic_ids,
        )
        return self._create_session(
            selected,
            practice_type="topic",
            topic_id=topic.id,
        )

    def generate_review_session(self, question_id: uuid.UUID) -> DailySession:
        question = self.db.get(Question, question_id)
        if question is None or not question.is_active:
            raise PracticeNotFound("Question not found.")
        latest_attempt = self.db.scalar(
            select(Attempt)
            .where(
                Attempt.user_id == self.profile.id,
                Attempt.question_id == question_id,
            )
            .order_by(Attempt.answered_at.desc())
        )
        if latest_attempt is None or latest_attempt.is_correct:
            raise PracticeConflict("This question is not in your missed review list.")
        return self._create_session(
            [question],
            practice_type="topic",
            topic_id=question.topic_id,
        )

    def generate_quick_review_session(self) -> DailySession:
        selected = self.select_questions(target_question_count=10)
        return self._create_session(selected, practice_type="quick_review")

    def generate_random_session(self, target_question_count: int) -> DailySession:
        candidates = list_active_questions(self.db)
        if not candidates:
            raise EmptyQuestionBank("No active questions are available for this practice session.")
        count = min(target_question_count, len(candidates))
        selected = random.SystemRandom().sample(candidates, count)
        return self._create_session(selected, practice_type="random")

    def select_questions(
        self,
        *,
        target_question_count: int,
        topic_ids: set[uuid.UUID] | None = None,
    ) -> list[Question]:
        candidates = list_active_questions(self.db, topic_ids=topic_ids)
        if not candidates:
            raise EmptyQuestionBank("No active questions are available for this practice session.")

        attempts = list_user_attempts(self.db, self.profile.id)
        latest_attempts: dict[uuid.UUID, Attempt] = {}
        for attempt in attempts:
            latest_attempts.setdefault(attempt.question_id, attempt)
        progress_by_topic = {
            progress.topic_id: progress
            for progress in get_user_progress(self.db, self.profile.id)
        }

        buckets: dict[str, list[Question]] = {
            "weak": [],
            "developing": [],
            "strong_or_unseen": [],
        }
        for question in candidates:
            progress = progress_by_topic.get(question.topic_id)
            if progress is None or progress.attempted_questions == 0:
                bucket = "strong_or_unseen"
            elif progress.mastery_score < 40:
                bucket = "weak"
            elif progress.mastery_score < 70:
                bucket = "developing"
            else:
                bucket = "strong_or_unseen"
            buckets[bucket].append(question)

        def priority(question: Question) -> tuple[int, float, str]:
            attempt = latest_attempts.get(question.id)
            if attempt is None:
                return (0, 0.0, str(question.id))
            seen_priority = 1 if not attempt.is_correct else 2
            timestamp = _as_utc(attempt.answered_at).timestamp()
            return (seen_priority, timestamp, str(question.id))

        for bucket_questions in buckets.values():
            bucket_questions.sort(key=priority)

        weak_target = int(target_question_count * 0.5)
        developing_target = int(target_question_count * 0.3)
        strong_target = target_question_count - weak_target - developing_target
        selected: list[Question] = []
        selected.extend(buckets["weak"][:weak_target])
        selected.extend(buckets["developing"][:developing_target])
        selected.extend(buckets["strong_or_unseen"][:strong_target])

        selected_ids = {question.id for question in selected}
        remaining = sorted(
            (question for question in candidates if question.id not in selected_ids),
            key=priority,
        )
        selected.extend(remaining[: max(0, target_question_count - len(selected))])
        return selected[:target_question_count]

    def submit_answer(
        self,
        *,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        answer_choice_id: uuid.UUID,
        response_time_ms: int | None,
    ) -> SubmitAnswerResponse:
        session = get_session_for_user(
            self.db,
            session_id=session_id,
            user_id=self.profile.id,
            lock=True,
        )
        if session is None:
            raise PracticeNotFound("Practice session not found.")
        if session.status != "active":
            raise PracticeConflict("This practice session is no longer active.")
        self._lock_profile()

        session_question = next(
            (
                item
                for item in session.session_questions
                if item.question_id == question_id
            ),
            None,
        )
        if session_question is None:
            raise PracticeInvalidRequest("Question does not belong to this session.")
        if get_session_attempt(
            self.db,
            session_id=session.id,
            question_id=question_id,
        ) is not None:
            raise PracticeConflict("This question has already been answered in the session.")

        selected_answer = get_answer_choice(
            self.db,
            question_id=question_id,
            choice_id=answer_choice_id,
        )
        if selected_answer is None:
            raise PracticeInvalidRequest("Answer choice does not belong to the question.")
        correct_answer = get_correct_answer(self.db, question_id)
        if correct_answer is None:
            raise PracticeInvalidRequest("Question does not have a valid correct answer.")

        now = self.clock()
        is_correct = selected_answer.id == correct_answer.id
        answer_xp = CORRECT_ANSWER_XP if is_correct else INCORRECT_ANSWER_XP
        attempt = Attempt(
            user_id=self.profile.id,
            question_id=question_id,
            selected_answer_id=selected_answer.id,
            is_correct=is_correct,
            answered_at=now,
            response_time_ms=response_time_ms,
            session_id=session.id,
        )
        self.db.add(attempt)
        session_question.answered_at = now
        session.questions_completed += 1
        session.correct_count += int(is_correct)
        session.xp_earned += answer_xp
        self.profile.total_xp += answer_xp

        try:
            self.db.flush()
            progress = update_topic_progress(
                self.db,
                user_id=self.profile.id,
                topic_id=session_question.question.topic_id,
                practiced_at=now,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise PracticeConflict(
                "This question has already been answered in the session."
            ) from exc

        return SubmitAnswerResponse(
            is_correct=is_correct,
            correct_answer=CorrectAnswerResponse(
                id=correct_answer.id,
                choice_text=correct_answer.choice_text,
            ),
            rationale=session_question.question.rationale,
            xp_earned=answer_xp,
            updated_topic_mastery=progress.mastery_score,
            mastery_classification=classify_mastery(progress.mastery_score),
            questions_completed=session.questions_completed,
            target_question_count=session.target_question_count,
        )

    def complete_session(self, session_id: uuid.UUID) -> CompleteSessionResponse:
        session = get_session_for_user(
            self.db,
            session_id=session_id,
            user_id=self.profile.id,
            lock=True,
        )
        if session is None:
            raise PracticeNotFound("Practice session not found.")
        self._lock_profile()

        if session.status == "completed":
            assert session.completed_at is not None
            return self._completion_response(session, completion_bonus=0)
        if session.status != "active":
            raise PracticeConflict("This practice session cannot be completed.")
        if session.questions_completed < session.target_question_count:
            raise PracticeConflict("Answer every session question before completing it.")

        now = self.clock()
        completion_bonus = (
            DAILY_COMPLETION_BONUS_XP if session.practice_type == "daily" else 0
        )
        session.status = "completed"
        session.completed_at = now
        session.xp_earned += completion_bonus
        self.profile.total_xp += completion_bonus
        if session.practice_type == "daily":
            apply_utc_streak(self.profile, now.date())
        self.db.commit()
        return self._completion_response(
            session,
            completion_bonus=completion_bonus,
        )

    def _create_session(
        self,
        questions: list[Question],
        *,
        practice_type: str,
        topic_id: uuid.UUID | None = None,
    ) -> DailySession:
        session = DailySession(
            user_id=self.profile.id,
            started_at=self.clock(),
            target_question_count=len(questions),
            practice_type=practice_type,
            topic_id=topic_id,
            session_questions=[
                SessionQuestion(question_id=question.id, display_order=index)
                for index, question in enumerate(questions, start=1)
            ],
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _lock_profile(self) -> None:
        locked_profile = self.db.scalar(
            select(Profile)
            .where(Profile.id == self.profile.id)
            .with_for_update()
        )
        if locked_profile is None:
            raise PracticeNotFound("User profile not found.")
        self.profile = locked_profile

    def _completion_response(
        self,
        session: DailySession,
        *,
        completion_bonus: int,
    ) -> CompleteSessionResponse:
        assert session.completed_at is not None
        return CompleteSessionResponse(
            session_id=session.id,
            status=session.status,
            correct_count=session.correct_count,
            question_count=session.target_question_count,
            xp_earned=session.xp_earned,
            completion_bonus_xp=completion_bonus,
            total_xp=self.profile.total_xp,
            current_streak=self.profile.current_streak,
            longest_streak=self.profile.longest_streak,
            completed_at=session.completed_at,
        )


def serialize_session(session: DailySession) -> PracticeSessionResponse:
    return PracticeSessionResponse(
        id=session.id,
        practice_type=session.practice_type,
        topic_id=session.topic_id,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        target_question_count=session.target_question_count,
        questions_completed=session.questions_completed,
        correct_count=session.correct_count,
        xp_earned=session.xp_earned,
        questions=[
            SessionQuestionResponse(
                display_order=item.display_order,
                answered=item.answered_at is not None,
                question=PracticeQuestion(
                    id=item.question.id,
                    question_text=item.question.question_text,
                    question_type=item.question.question_type,
                    topic=TopicReference.model_validate(item.question.topic),
                    choices=[
                        AnswerChoiceReview(
                            id=choice.id,
                            choice_text=choice.choice_text,
                            display_order=choice.display_order,
                        )
                        for choice in item.question.answer_choices
                    ],
                ),
            )
            for item in session.session_questions
        ],
    )


def apply_utc_streak(profile: Profile, practice_date: date) -> None:
    if profile.last_practice_date == practice_date:
        return
    if profile.last_practice_date == practice_date - timedelta(days=1):
        profile.current_streak += 1
    else:
        profile.current_streak = 1
    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
    profile.last_practice_date = practice_date


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
