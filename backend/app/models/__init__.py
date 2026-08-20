"""Import every SQLAlchemy model so Alembic can discover its metadata."""

from app.models.answer_choice import AnswerChoice
from app.models.profile import Profile
from app.models.question import Question
from app.models.topic import Topic

__all__ = ["AnswerChoice", "Profile", "Question", "Topic"]
