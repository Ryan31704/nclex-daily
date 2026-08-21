import uuid
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.answer_choice import AnswerChoice
from app.models.attempt import Attempt
from app.models.profile import Profile
from app.models.question import Question
from app.models.topic import Topic
from app.models.topic_progress import TopicProgress
from app.schemas.auth import AuthenticatedUser
from app.services.daily_practice_service import (
    DailyPracticeService,
    PracticeConflict,
    _score_answer,
    apply_utc_streak,
)
from app.services.mastery_service import (
    MasteryAttempt,
    calculate_mastery,
    classify_mastery,
)


@pytest.fixture
def database() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with testing_session() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def _profile(database: Session, *, auth_user_id: uuid.UUID | None = None) -> Profile:
    profile = Profile(
        auth_user_id=auth_user_id or uuid.uuid4(),
        display_name="Morgan Student",
    )
    database.add(profile)
    database.flush()
    return profile


def _child_topic(database: Session, name: str = "Safety") -> Topic:
    parent = Topic(name=f"{name} Chapter", slug=f"{name.lower()}-chapter")
    child = Topic(name=name, slug=name.lower().replace(" ", "-"), parent=parent)
    database.add(child)
    database.flush()
    return child


def _question(database: Session, topic: Topic, label: str) -> Question:
    question = Question(
        topic=topic,
        question_text=f"Question {label}",
        question_type="multiple_choice",
        source_type="original_human",
        source_reference=None,
        license_status="approved",
        content_hash=f"{label:0>64}"[-64:],
        answer_choices=[
            AnswerChoice(
                choice_text=f"{label} choice {index}",
                is_correct=index == 1,
                display_order=index,
            )
            for index in range(1, 5)
        ],
    )
    database.add(question)
    database.flush()
    return question


def test_mastery_measures_correct_unique_question_coverage() -> None:
    assert calculate_mastery([], total_question_count=100) == 0.0
    assert calculate_mastery(
        [MasteryAttempt(True)] * 2,
        total_question_count=100,
    ) == 2.0
    assert calculate_mastery(
        [MasteryAttempt(True)] * 5,
        total_question_count=100,
    ) == 5.0
    assert calculate_mastery(
        [MasteryAttempt(True)] * 85 + [MasteryAttempt(False)] * 15,
        total_question_count=100,
    ) == 85.0
    assert calculate_mastery(
        [MasteryAttempt(True)] * 100,
        total_question_count=100,
    ) == 100.0
    assert classify_mastery(39.9) == "weak"
    assert classify_mastery(40) == "developing"
    assert classify_mastery(70) == "strong"
    assert classify_mastery(99.9) == "strong"
    assert classify_mastery(100) == "mastered"


def test_alternative_question_answers_are_scored_by_type() -> None:
    assert _score_answer("multiple_choice", "a", "a") is True
    assert _score_answer("multiple_response", ["a", "b"], ["b", "a"]) is True
    assert _score_answer("multiple_response", ["a"], ["a", "b"]) is False
    assert _score_answer("ordered_response", ["a", "b"], ["a", "b"]) is True
    assert _score_answer("ordered_response", ["b", "a"], ["a", "b"]) is False
    assert _score_answer(
        "numeric_response", "89.1", {"value": 89.1, "unit": "mg"}
    ) is True
    assert _score_answer(
        "matrix",
        {"rows": {"r1": ["c1", "c2"]}},
        {"rows": {"r1": ["c2", "c1"]}},
    ) is True


def test_daily_selection_uses_weak_developing_strong_unseen_mix(
    database: Session,
) -> None:
    profile = _profile(database)
    topics = {
        "weak": _child_topic(database, "Weak"),
        "developing": _child_topic(database, "Developing"),
        "strong": _child_topic(database, "Strong"),
        "unseen": _child_topic(database, "Unseen"),
    }
    for category, topic in topics.items():
        for index in range(6):
            _question(database, topic, f"{category}-{index}")
    database.add_all(
        [
            TopicProgress(
                user_id=profile.id,
                topic_id=topics["weak"].id,
                attempted_questions=5,
                correct_questions=1,
                mastery_score=20,
            ),
            TopicProgress(
                user_id=profile.id,
                topic_id=topics["developing"].id,
                attempted_questions=5,
                correct_questions=3,
                mastery_score=55,
            ),
            TopicProgress(
                user_id=profile.id,
                topic_id=topics["strong"].id,
                attempted_questions=5,
                correct_questions=4,
                mastery_score=80,
            ),
        ]
    )
    database.commit()

    selected = DailyPracticeService(database, profile).select_questions(
        target_question_count=10
    )
    selected_topic_ids = [question.topic_id for question in selected]

    assert len(selected) == 10
    assert len({question.id for question in selected}) == 10
    assert selected_topic_ids.count(topics["weak"].id) == 5
    assert selected_topic_ids.count(topics["developing"].id) == 3
    assert sum(
        selected_topic_ids.count(topics[name].id) for name in ("strong", "unseen")
    ) == 2

    quick_review = DailyPracticeService(database, profile).generate_quick_review_session()
    random_test = DailyPracticeService(database, profile).generate_random_session(20)
    assert quick_review.practice_type == "quick_review"
    assert quick_review.target_question_count == 10
    assert random_test.practice_type == "random"
    assert random_test.target_question_count == 20
    assert len({item.question_id for item in random_test.session_questions}) == 20


def test_answer_scoring_is_server_side_and_cannot_award_duplicate_xp(
    database: Session,
) -> None:
    now = datetime(2026, 8, 20, 14, 0, tzinfo=UTC)
    profile = _profile(database)
    topic = _child_topic(database)
    question = _question(database, topic, "score")
    database.commit()
    correct_choice = next(choice for choice in question.answer_choices if choice.is_correct)
    service = DailyPracticeService(database, profile, clock=lambda: now)
    session = service.generate_topic_session(topic.id, target_question_count=1)

    result = service.submit_answer(
        session_id=session.id,
        question_id=question.id,
        answer_choice_id=correct_choice.id,
        response_time_ms=1200,
    )

    assert result.is_correct is True
    assert result.xp_earned == 10
    assert result.correct_answer.id == correct_choice.id
    assert profile.total_xp == 10
    assert database.scalar(select(Attempt)).is_correct is True

    with pytest.raises(PracticeConflict):
        service.submit_answer(
            session_id=session.id,
            question_id=question.id,
            answer_choice_id=correct_choice.id,
            response_time_ms=1200,
        )
    assert profile.total_xp == 10

    wrong_choice = next(choice for choice in question.answer_choices if not choice.is_correct)
    second_session = service.generate_topic_session(topic.id, target_question_count=1)
    incorrect_result = service.submit_answer(
        session_id=second_session.id,
        question_id=question.id,
        answer_choice_id=wrong_choice.id,
        response_time_ms=800,
    )
    completion = service.complete_session(second_session.id)
    assert incorrect_result.is_correct is False
    assert incorrect_result.xp_earned == 5
    assert completion.completion_bonus_xp == 0
    assert completion.total_xp == 15


def test_completion_bonus_and_utc_streak_are_idempotent(database: Session) -> None:
    now = datetime(2026, 8, 20, 23, 30, tzinfo=UTC)
    profile = _profile(database)
    topic = _child_topic(database)
    question = _question(database, topic, "complete")
    database.commit()
    correct_choice = next(choice for choice in question.answer_choices if choice.is_correct)
    service = DailyPracticeService(database, profile, clock=lambda: now)
    session = service.generate_daily_session(target_question_count=1)
    service.submit_answer(
        session_id=session.id,
        question_id=question.id,
        answer_choice_id=correct_choice.id,
        response_time_ms=None,
    )

    first = service.complete_session(session.id)
    second = service.complete_session(session.id)

    assert first.completion_bonus_xp == 25
    assert first.total_xp == 35
    assert first.current_streak == 1
    assert second.completion_bonus_xp == 0
    assert second.total_xp == 35
    assert profile.last_practice_date == date(2026, 8, 20)

    apply_utc_streak(profile, date(2026, 8, 21))
    assert profile.current_streak == 2
    apply_utc_streak(profile, date(2026, 8, 21))
    assert profile.current_streak == 2
    apply_utc_streak(profile, date(2026, 8, 23))
    assert profile.current_streak == 1
    assert profile.longest_streak == 2


@pytest.fixture
def quiz_api_client() -> Generator[dict[str, object], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    auth_user_id = uuid.uuid4()
    with testing_session() as database:
        profile = _profile(database, auth_user_id=auth_user_id)
        topic = _child_topic(database)
        question = _question(database, topic, "api")
        database.commit()
        profile_id = profile.id
        topic_id = topic.id
        question_id = question.id

    def override_db() -> Generator[Session, None, None]:
        with testing_session() as database:
            yield database

    async def override_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=auth_user_id,
            email="student@example.com",
            user_metadata={},
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    try:
        with TestClient(app) as client:
            yield {
                "client": client,
                "sessions": testing_session,
                "profile_id": profile_id,
                "topic_id": topic_id,
                "question_id": question_id,
                "auth_user_id": auth_user_id,
            }
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_practice_api_hides_correctness_scores_and_checks_ownership(
    quiz_api_client: dict[str, object],
) -> None:
    client = quiz_api_client["client"]
    testing_session = quiz_api_client["sessions"]
    topic_id = quiz_api_client["topic_id"]
    assert isinstance(client, TestClient)
    assert isinstance(testing_session, sessionmaker)

    start_response = client.post(
        f"/api/v1/practice/topic/{topic_id}/start",
        json={"target_question_count": 1},
    )
    assert start_response.status_code == 200
    session_payload = start_response.json()
    question_payload = session_payload["questions"][0]["question"]
    assert all("is_correct" not in choice for choice in question_payload["choices"])

    with testing_session() as database:
        question = database.get(Question, uuid.UUID(question_payload["id"]))
        assert question is not None
        correct_choice = next(
            choice for choice in question.answer_choices if choice.is_correct
        )
        wrong_choice = next(
            choice for choice in question.answer_choices if not choice.is_correct
        )
    answer_response = client.post(
        f"/api/v1/practice/sessions/{session_payload['id']}/answer",
        json={
            "question_id": question_payload["id"],
            "answer_choice_id": str(correct_choice.id),
            "response_time_ms": 900,
        },
    )
    assert answer_response.status_code == 200
    assert answer_response.json()["is_correct"] is True
    assert answer_response.json()["xp_earned"] == 10

    duplicate_response = client.post(
        f"/api/v1/practice/sessions/{session_payload['id']}/answer",
        json={
            "question_id": question_payload["id"],
            "answer_choice_id": str(correct_choice.id),
        },
    )
    assert duplicate_response.status_code == 409

    second_session = client.post(
        f"/api/v1/practice/topic/{topic_id}/start",
        json={"target_question_count": 1},
    ).json()
    incorrect_response = client.post(
        f"/api/v1/practice/sessions/{second_session['id']}/answer",
        json={
            "question_id": question_payload["id"],
            "answer_choice_id": str(wrong_choice.id),
        },
    )
    assert incorrect_response.status_code == 200
    assert incorrect_response.json()["is_correct"] is False
    assert incorrect_response.json()["xp_earned"] == 5

    progress_response = client.get(f"/api/v1/topics/{topic_id}/progress")
    overall_response = client.get("/api/v1/progress")
    dashboard_response = client.get("/api/v1/dashboard")
    review_response = client.get("/api/v1/review/missed")
    assert progress_response.status_code == 200
    assert progress_response.json()["attempted_questions"] == 2
    assert overall_response.json()["questions_answered"] == 2
    assert dashboard_response.json()["total_xp"] == 15
    assert len(review_response.json()) == 1
    assert all(
        "is_correct" not in choice
        for choice in review_response.json()[0]["question"]["choices"]
    )
    review_start_response = client.post(
        f"/api/v1/practice/review/{question_payload['id']}/start",
        json={},
    )
    assert review_start_response.status_code == 200
    assert (
        review_start_response.json()["questions"][0]["question"]["id"]
        == question_payload["id"]
    )

    other_auth_user = AuthenticatedUser(
        id=uuid.uuid4(),
        email="other@example.com",
        user_metadata={},
    )

    async def override_other_user() -> AuthenticatedUser:
        return other_auth_user

    app.dependency_overrides[get_current_user] = override_other_user
    ownership_response = client.get(
        f"/api/v1/practice/sessions/{session_payload['id']}"
    )
    assert ownership_response.status_code == 404


def test_quiz_engine_routes_require_authentication() -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/practice/daily/start", json={}).status_code == 401
        assert client.post("/api/v1/practice/quick-review/start", json={}).status_code == 401
        assert client.post("/api/v1/practice/random/start", json={}).status_code == 401
        assert client.get("/api/v1/progress").status_code == 401
        assert client.get("/api/v1/review/missed").status_code == 401
        assert client.get("/api/v1/dashboard").status_code == 401
