import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.practice import ProgressResponse, TopicProgressResponse
from app.services.profile_service import get_or_create_profile
from app.services.progress_service import get_overall_progress, get_topic_progress_response

router = APIRouter()


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressResponse:
    profile = get_or_create_profile(db, current_user)
    return get_overall_progress(db, profile)


@router.get("/topics/{topic_id}/progress", response_model=TopicProgressResponse)
def get_topic_progress(
    topic_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TopicProgressResponse:
    profile = get_or_create_profile(db, current_user)
    progress = get_topic_progress_response(
        db,
        user_id=profile.id,
        topic_id=topic_id,
    )
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")
    return progress
