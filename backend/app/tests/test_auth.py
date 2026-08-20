import asyncio
import uuid
from collections.abc import Generator

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.security import SupabaseTokenValidator, get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.profile import Profile
from app.schemas.auth import AuthenticatedUser


def test_me_rejects_unauthenticated_requests() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired authentication token."


def test_supabase_validator_accepts_a_valid_auth_response() -> None:
    user_id = uuid.uuid4()

    def auth_handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://example.supabase.co/auth/v1/user"
        assert request.headers["apikey"] == "sb_publishable_test"
        assert request.headers["authorization"] == "Bearer valid-token"
        return httpx.Response(
            200,
            json={
                "id": str(user_id),
                "email": "student@example.com",
                "user_metadata": {"display_name": "Morgan"},
            },
        )

    validator = SupabaseTokenValidator(
        Settings(
            supabase_url="https://example.supabase.co/",
            supabase_publishable_key="sb_publishable_test",
        ),
        transport=httpx.MockTransport(auth_handler),
    )

    user = asyncio.run(validator.validate("valid-token"))

    assert user.id == user_id
    assert user.email == "student@example.com"
    assert user.user_metadata == {"display_name": "Morgan"}


def test_supabase_validator_rejects_an_invalid_token() -> None:
    def auth_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "invalid JWT"})

    validator = SupabaseTokenValidator(
        Settings(
            supabase_url="https://example.supabase.co",
            supabase_publishable_key="sb_publishable_test",
        ),
        transport=httpx.MockTransport(auth_handler),
    )

    with pytest.raises(HTTPException) as caught_error:
        asyncio.run(validator.validate("invalid-token"))

    assert caught_error.value.status_code == 401


@pytest.fixture
def authenticated_client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    auth_user = AuthenticatedUser(
        id=uuid.uuid4(),
        email="student@example.com",
        user_metadata={"display_name": "Morgan Student"},
    )

    def override_db() -> Generator[Session, None, None]:
        database = testing_session()
        try:
            yield database
        finally:
            database.close()

    async def override_user() -> AuthenticatedUser:
        return auth_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user

    try:
        with TestClient(app) as client:
            yield client, testing_session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_me_creates_one_profile_idempotently(
    authenticated_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = authenticated_client

    first_response = client.get("/api/v1/me")
    second_response = client.get("/api/v1/me")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert first_response.json()["display_name"] == "Morgan Student"
    assert first_response.json()["email"] == "student@example.com"

    with testing_session() as database:
        profile_count = database.scalar(select(func.count()).select_from(Profile))
    assert profile_count == 1
