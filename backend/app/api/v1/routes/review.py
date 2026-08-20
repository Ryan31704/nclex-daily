import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.practice import MissedQuestionResponse
from app.services.profile_service import get_or_create_profile
from app.services.progress_service import get_missed_questions

router = APIRouter(prefix="/review")


@router.get("/missed", response_model=list[MissedQuestionResponse])
def review_missed_questions(
    topic_id: uuid.UUID | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MissedQuestionResponse]:
    profile = get_or_create_profile(db, current_user)
    return get_missed_questions(
        db,
        profile=profile,
        topic_id=topic_id,
        limit=limit,
    )
