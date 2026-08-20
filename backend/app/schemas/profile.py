import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    auth_user_id: uuid.UUID
    email: str | None
    display_name: str
    created_at: datetime
    current_streak: int
    longest_streak: int
    total_xp: int
    last_practice_date: date | None
