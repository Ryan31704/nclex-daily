"""Import every SQLAlchemy model so Alembic can discover its metadata."""

from app.models.answer_choice import AnswerChoice
from app.models.attempt import Attempt
from app.models.daily_session import DailySession
from app.models.profile import Profile
from app.models.question import Question
from app.models.session_question import SessionQuestion
from app.models.topic import Topic
from app.models.topic_progress import TopicProgress

__all__ = [
    "AnswerChoice",
    "Attempt",
    "DailySession",
    "Profile",
    "Question",
    "SessionQuestion",
    "Topic",
    "TopicProgress",
]
