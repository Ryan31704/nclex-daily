import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.question_bank import TopicDetail, TopicSummary
from app.services.question_bank_service import get_topic_detail, list_topic_hierarchy

router = APIRouter(prefix="/topics")


@router.get("", response_model=list[TopicSummary])
def get_topics(
    _current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TopicSummary]:
    return list_topic_hierarchy(db)


@router.get("/{topic_id}", response_model=TopicDetail)
def get_topic(
    topic_id: uuid.UUID,
    _current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TopicDetail:
    topic = get_topic_detail(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")
    return topic
