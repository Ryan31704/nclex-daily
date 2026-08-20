import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.question_bank import AnswerChoiceReview, TopicReference


class StartPracticeRequest(BaseModel):
    target_question_count: int = Field(default=10, ge=1, le=50)


class PracticeQuestion(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    topic: TopicReference
    choices: list[AnswerChoiceReview]


class SessionQuestionResponse(BaseModel):
    display_order: int
    answered: bool
    question: PracticeQuestion


class PracticeSessionResponse(BaseModel):
    id: uuid.UUID
    practice_type: str
    topic_id: uuid.UUID | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    target_question_count: int
    questions_completed: int
    correct_count: int
    xp_earned: int
    questions: list[SessionQuestionResponse]


class SubmitAnswerRequest(BaseModel):
    question_id: uuid.UUID
    answer_choice_id: uuid.UUID
    response_time_ms: int | None = Field(default=None, ge=0, le=3_600_000)


class CorrectAnswerResponse(BaseModel):
    id: uuid.UUID
    choice_text: str


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: CorrectAnswerResponse
    rationale: str | None
    xp_earned: int
    updated_topic_mastery: float
    mastery_classification: str
    questions_completed: int
    target_question_count: int


class CompleteSessionResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    correct_count: int
    question_count: int
    xp_earned: int
    completion_bonus_xp: int
    total_xp: int
    current_streak: int
    longest_streak: int
    completed_at: datetime


class TopicProgressResponse(BaseModel):
    topic: TopicReference
    attempted_questions: int
    correct_questions: int
    correct_percentage: float
    mastery_score: float
    classification: str
    last_practiced_at: datetime | None


class ProgressResponse(BaseModel):
    overall_mastery: float
    questions_answered: int
    correct_questions: int
    topics: list[TopicProgressResponse]


class MissedQuestionResponse(BaseModel):
    attempt_id: uuid.UUID
    attempted_at: datetime
    selected_answer_id: uuid.UUID
    question: PracticeQuestion


class DashboardResponse(BaseModel):
    display_name: str
    current_streak: int
    longest_streak: int
    total_xp: int
    questions_answered: int
    overall_mastery: float
    daily_session: PracticeSessionResponse | None
    weakest_topics: list[TopicProgressResponse]
