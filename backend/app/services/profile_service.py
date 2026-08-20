from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.auth import AuthenticatedUser


def get_or_create_profile(db: Session, user: AuthenticatedUser) -> Profile:
    existing_profile = db.scalar(
        select(Profile).where(Profile.auth_user_id == user.id)
    )
    if existing_profile is not None:
        return existing_profile

    profile = Profile(
        auth_user_id=user.id,
        display_name=_display_name_for(user),
    )
    db.add(profile)

    try:
        db.commit()
        db.refresh(profile)
        return profile
    except IntegrityError:
        # Another concurrent request may have created this user's profile first.
        db.rollback()
        concurrent_profile = db.scalar(
            select(Profile).where(Profile.auth_user_id == user.id)
        )
        if concurrent_profile is None:
            raise
        return concurrent_profile


def _display_name_for(user: AuthenticatedUser) -> str:
    for key in ("display_name", "full_name", "name"):
        value = user.user_metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:100]

    if user.email:
        return user.email.split("@", maxsplit=1)[0][:100]
    return "Nursing Student"
