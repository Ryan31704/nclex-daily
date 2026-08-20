import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: uuid.UUID
    email: str | None
    user_metadata: dict[str, Any] = field(default_factory=dict)
