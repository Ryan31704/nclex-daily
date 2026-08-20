from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.profile import MeResponse
from app.services.profile_service import get_or_create_profile

router = APIRouter()


@router.get("/me", response_model=MeResponse)
def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    profile = get_or_create_profile(db, current_user)
    return MeResponse.model_validate(
        {
            "id": profile.id,
            "auth_user_id": profile.auth_user_id,
            "email": current_user.email,
            "display_name": profile.display_name,
            "created_at": profile.created_at,
            "current_streak": profile.current_streak,
            "longest_streak": profile.longest_streak,
            "total_xp": profile.total_xp,
            "last_practice_date": profile.last_practice_date,
        }
    )
