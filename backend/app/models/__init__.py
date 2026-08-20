"""Import every SQLAlchemy model so Alembic can discover its metadata."""

from app.models.profile import Profile

__all__ = ["Profile"]
