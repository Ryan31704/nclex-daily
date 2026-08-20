import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TopicReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class ChildTopicSummary(TopicReference):
    description: str | None
    display_order: int
    question_count: int


class TopicSummary(TopicReference):
    description: str | None
    display_order: int
    question_count: int
    children: list[ChildTopicSummary]


class TopicDetail(TopicReference):
    description: str | None
    display_order: int
    is_active: bool
    created_at: datetime
    question_count: int
    parent: TopicReference | None
    children: list[ChildTopicSummary]


class AnswerChoiceReview(BaseModel):
    id: uuid.UUID
    choice_text: str
    display_order: int


class QuestionReview(BaseModel):
    id: uuid.UUID
    question_text: str
    rationale: str | None
    difficulty: str | None
    question_type: str
    source_type: str
    source_reference: str | None
    license_status: str
    topic: TopicReference
    choices: list[AnswerChoiceReview]
