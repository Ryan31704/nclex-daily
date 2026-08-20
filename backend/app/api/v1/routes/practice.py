import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.repositories.practice import get_session_for_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.practice import (
    CompleteSessionResponse,
    PracticeSessionResponse,
    StartPracticeRequest,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.daily_practice_service import (
    DailyPracticeService,
    EmptyQuestionBank,
    PracticeConflict,
    PracticeInvalidRequest,
    PracticeNotFound,
    serialize_session,
)
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/practice")


@router.post("/daily/start", response_model=PracticeSessionResponse)
def start_daily_practice(
    request: StartPracticeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    profile = get_or_create_profile(db, current_user)
    service = DailyPracticeService(db, profile)
    try:
        session = service.generate_daily_session(request.target_question_count)
    except EmptyQuestionBank as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    loaded = get_session_for_user(db, session_id=session.id, user_id=profile.id)
    assert loaded is not None
    return serialize_session(loaded)


@router.post("/topic/{topic_id}/start", response_model=PracticeSessionResponse)
def start_topic_practice(
    topic_id: uuid.UUID,
    request: StartPracticeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    profile = get_or_create_profile(db, current_user)
    service = DailyPracticeService(db, profile)
    try:
        session = service.generate_topic_session(
            topic_id,
            request.target_question_count,
        )
    except PracticeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmptyQuestionBank as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    loaded = get_session_for_user(db, session_id=session.id, user_id=profile.id)
    assert loaded is not None
    return serialize_session(loaded)


@router.get("/sessions/{session_id}", response_model=PracticeSessionResponse)
def get_practice_session(
    session_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    profile = get_or_create_profile(db, current_user)
    session = get_session_for_user(db, session_id=session_id, user_id=profile.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice session not found.",
        )
    return serialize_session(session)


@router.post(
    "/sessions/{session_id}/answer",
    response_model=SubmitAnswerResponse,
)
def submit_practice_answer(
    session_id: uuid.UUID,
    request: SubmitAnswerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmitAnswerResponse:
    profile = get_or_create_profile(db, current_user)
    service = DailyPracticeService(db, profile)
    try:
        return service.submit_answer(
            session_id=session_id,
            question_id=request.question_id,
            answer_choice_id=request.answer_choice_id,
            response_time_ms=request.response_time_ms,
        )
    except PracticeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PracticeConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PracticeInvalidRequest as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/sessions/{session_id}/complete",
    response_model=CompleteSessionResponse,
)
def complete_practice_session(
    session_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompleteSessionResponse:
    profile = get_or_create_profile(db, current_user)
    service = DailyPracticeService(db, profile)
    try:
        return service.complete_session(session_id)
    except PracticeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PracticeConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
