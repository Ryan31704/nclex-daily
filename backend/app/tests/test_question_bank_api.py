import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.topic import Topic
from app.schemas.auth import AuthenticatedUser


@pytest.fixture
def question_bank_client() -> Generator[tuple[TestClient, Question, Topic], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as database:
        parent = Topic(name="Chapter 1", slug="chapter-1", display_order=1)
        child = Topic(
            name="Safety",
            slug="safety",
            display_order=1,
            parent=parent,
        )
        question = Question(
            topic=child,
            question_text="What should the nurse do first?",
            question_type="multiple_choice",
            source_type="imported_private",
            source_reference="original_nclex_study_question_bank_1700.csv",
            license_status="review_required",
            content_hash="a" * 64,
            answer_choices=[
                AnswerChoice(
                    choice_text=f"Choice {index}",
                    is_correct=index == 2,
                    display_order=index,
                )
                for index in range(1, 5)
            ],
        )
        database.add(question)
        database.commit()
        database.refresh(question)
        parent_id = parent.id
        child_id = child.id
        question_id = question.id

    def override_db() -> Generator[Session, None, None]:
        with testing_session() as database:
            yield database

    async def override_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=uuid.uuid4(),
            email="student@example.com",
            user_metadata={},
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    try:
        with testing_session() as database:
            persisted_question = database.get(Question, question_id)
            persisted_child = database.get(Topic, child_id)
            assert persisted_question is not None
            assert persisted_child is not None
            with TestClient(app) as client:
                yield client, persisted_question, persisted_child
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_question_review_never_exposes_correctness(
    question_bank_client: tuple[TestClient, Question, Topic],
) -> None:
    client, question, _child = question_bank_client

    response = client.get(f"/api/v1/questions/{question.id}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["choices"]) == 4
    assert all("is_correct" not in choice for choice in payload["choices"])
    assert "correct_answer" not in payload


def test_topics_return_parent_child_hierarchy_and_counts(
    question_bank_client: tuple[TestClient, Question, Topic],
) -> None:
    client, _question, child = question_bank_client

    list_response = client.get("/api/v1/topics")
    detail_response = client.get(f"/api/v1/topics/{child.id}")

    assert list_response.status_code == 200
    hierarchy = list_response.json()
    assert len(hierarchy) == 1
    assert hierarchy[0]["question_count"] == 1
    assert hierarchy[0]["children"][0]["name"] == "Safety"
    assert hierarchy[0]["children"][0]["question_count"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["parent"]["name"] == "Chapter 1"


def test_question_bank_endpoints_reject_unauthenticated_requests() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/topics").status_code == 401
        assert client.get(f"/api/v1/questions/{uuid.uuid4()}").status_code == 401
