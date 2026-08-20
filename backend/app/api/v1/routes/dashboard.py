from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.practice import DashboardResponse
from app.services.profile_service import get_or_create_profile
from app.services.progress_service import get_dashboard

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard_summary(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    profile = get_or_create_profile(db, current_user)
    return get_dashboard(db, profile)
