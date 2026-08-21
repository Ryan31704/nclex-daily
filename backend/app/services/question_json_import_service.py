import copy
import hashlib
import json
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.topic import Topic
from app.services.question_import_service import slugify

SUPPORTED_TYPES = {
    "multiple_choice",
    "multiple_response",
    "numeric_response",
    "ordered_response",
    "highlight",
    "cloze",
    "matching",
    "matrix",
    "bow_tie",
}

LEADING_LABEL_PATTERN = re.compile(
    r"^(?:Clinical summary|Handoff note|Preceptor case):\s*",
    re.IGNORECASE,
)
GENERIC_INTRO_PATTERNS = (
    re.compile(r"^The nurse reviews a care decision in .+?\.\s+", re.IGNORECASE),
    re.compile(
        r"^During clinical planning in .+?, the nurse compares several options\.\s+",
        re.IGNORECASE,
    ),
    re.compile(
        r"^A preceptor presents a nursing question from .+?\.\s+",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:Using the generated case (?:data|record)|After reviewing the alternate case(?: record)?|Based on the new client scenario),\s+",
        re.IGNORECASE,
    ),
)
ADDITIONAL_DETAIL_PATTERN = re.compile(
    r"^consider this additional detail:\s*", re.IGNORECASE
)


def normalize_question_stem(stem: str) -> str:
    """Remove generator framing without removing clinical facts."""
    cleaned = LEADING_LABEL_PATTERN.sub("", stem.strip())
    for pattern in GENERIC_INTRO_PATTERNS:
        updated = pattern.sub("", cleaned)
        if updated != cleaned:
            cleaned = updated
            break
    cleaned = ADDITIONAL_DETAIL_PATTERN.sub("", cleaned).strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


@dataclass(frozen=True)
class ParsedJsonQuestion:
    external_id: str
    question_text: str
    rationale: str
    difficulty: str
    question_type: str
    parent_name: str
    topic_name: str
    topic_slug: str
    options: list[dict[str, str]]
    answer: dict[str, Any]
    interaction: dict[str, Any] | None
    case_study_markdown: str | None
    content_hash: str


@dataclass
class JsonImportResult:
    source_questions: int = 0
    questions_inserted: int = 0
    questions_skipped: int = 0
    answer_choices_inserted: int = 0
    parent_topics_created: int = 0
    child_topics_created: int = 0
    type_counts: dict[str, int] = field(default_factory=dict)
    content_hashes: set[str] = field(default_factory=set)


def _canonical_hash(question: dict[str, Any]) -> str:
    content = {
        "external_id": question["id"],
        "question_type": question["question_type"],
        "stem_markdown": question["stem_markdown"],
        "options": question.get("options") or [],
        "answer": question["answer"],
        "interaction": question.get("interaction"),
        "topic_path": question["topic_path"],
    }
    encoded = json.dumps(
        content, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _public_interaction(value: Any) -> Any:
    """Remove every answer-bearing field before interaction data reaches a client."""
    if isinstance(value, list):
        return [_public_interaction(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _public_interaction(item)
            for key, item in value.items()
            if not key.startswith("correct") and key != "is_correct"
        }
    return value


def parse_question_json(path: Path) -> list[ParsedJsonQuestion]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        raise ValueError("JSON root must contain a questions array.")

    case_studies = {
        item.get("id"): item
        for item in data.get("case_studies", [])
        if isinstance(item, dict) and item.get("id")
    }
    parsed: list[ParsedJsonQuestion] = []
    seen_ids: set[str] = set()
    for index, question in enumerate(data["questions"], start=1):
        if not isinstance(question, dict):
            raise ValueError(f"Question {index} is not an object.")
        missing = [
            key
            for key in (
                "id",
                "question_type",
                "stem_markdown",
                "answer",
                "topic_name",
                "topic_path",
                "topic_slug",
                "rationale_markdown",
                "difficulty",
            )
            if question.get(key) in (None, "", [])
        ]
        if missing:
            raise ValueError(f"Question {index} is missing: {', '.join(missing)}")
        external_id = str(question["id"])
        if external_id in seen_ids:
            raise ValueError(f"Duplicate question id: {external_id}")
        seen_ids.add(external_id)
        question_type = str(question["question_type"])
        if question_type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported question type: {question_type}")

        options = question.get("options") or []
        if not isinstance(options, list) or len(options) > 20:
            raise ValueError(f"{external_id} has an invalid options array.")
        option_ids = {str(option.get("id")) for option in options}
        if len(option_ids) != len(options) or any(
            not option.get("id") or not option.get("text_markdown") for option in options
        ):
            raise ValueError(f"{external_id} has invalid or duplicate options.")
        answer = question["answer"]
        if question_type in {"multiple_choice", "multiple_response"}:
            correct_ids = {str(item) for item in answer.get("correct_option_ids", [])}
            if not correct_ids or not correct_ids.issubset(option_ids):
                raise ValueError(f"{external_id} has an invalid option answer key.")
        if question_type == "ordered_response":
            order = [str(item) for item in answer.get("correct_order", [])]
            if set(order) != option_ids or len(order) != len(options):
                raise ValueError(f"{external_id} has an invalid ordered answer key.")
        if question_type == "numeric_response" and answer.get("numeric_value") is None:
            raise ValueError(f"{external_id} has no numeric answer.")
        if question_type not in {
            "multiple_choice",
            "multiple_response",
            "ordered_response",
            "numeric_response",
        } and not answer.get("structured_key"):
            raise ValueError(f"{external_id} has no structured answer key.")

        topic_path = question["topic_path"]
        if not isinstance(topic_path, list) or not all(topic_path):
            raise ValueError(f"{external_id} has an invalid topic path.")
        case = case_studies.get(question.get("case_study_id"))
        parsed.append(
            ParsedJsonQuestion(
                external_id=external_id,
                question_text=normalize_question_stem(str(question["stem_markdown"])),
                rationale=str(question["rationale_markdown"]).strip(),
                difficulty=str(question["difficulty"]).strip(),
                question_type=question_type,
                parent_name=str(topic_path[0]).strip(),
                topic_name=str(question["topic_name"]).strip(),
                topic_slug=str(question["topic_slug"]).strip(),
                options=copy.deepcopy(options),
                answer=copy.deepcopy(answer),
                interaction=_public_interaction(question.get("interaction")),
                case_study_markdown=(
                    str(case.get("intro_markdown")).strip()
                    if case and case.get("intro_markdown")
                    else None
                ),
                content_hash=_canonical_hash(question),
            )
        )
    return parsed


def _normalized_answer_key(
    item: ParsedJsonQuestion, option_id_map: dict[str, str]
) -> Any:
    answer = item.answer
    if item.question_type == "multiple_choice":
        return option_id_map[str(answer["correct_option_ids"][0])]
    if item.question_type == "multiple_response":
        return [option_id_map[str(value)] for value in answer["correct_option_ids"]]
    if item.question_type == "ordered_response":
        return [option_id_map[str(value)] for value in answer["correct_order"]]
    if item.question_type == "numeric_response":
        return {
            "value": answer["numeric_value"],
            "unit": answer.get("numeric_unit"),
        }
    return answer["structured_key"]


def import_question_json(db: Session, path: Path) -> JsonImportResult:
    parsed = parse_question_json(path)
    result = JsonImportResult(
        source_questions=len(parsed),
        type_counts=dict(Counter(item.question_type for item in parsed)),
        content_hashes={item.content_hash for item in parsed},
    )
    topics = list(db.scalars(select(Topic)).all())
    parents = {topic.slug: topic for topic in topics if topic.parent_topic_id is None}
    children = {
        (topic.parent_topic_id, topic.slug): topic
        for topic in topics
        if topic.parent_topic_id is not None
    }
    existing_hashes = set(db.scalars(select(Question.content_hash)).all())
    existing_external_ids = set(
        value
        for value in db.scalars(select(Question.external_id)).all()
        if value is not None
    )
    parent_order = max((topic.display_order for topic in parents.values()), default=0)
    child_orders = {
        parent.id: max((child.display_order for child in parent.children), default=0)
        for parent in parents.values()
    }

    try:
        for item in parsed:
            parent_slug = slugify(item.parent_name)
            parent = parents.get(parent_slug)
            if parent is None:
                parent_order += 1
                parent = Topic(
                    name=item.parent_name,
                    slug=parent_slug,
                    display_order=parent_order,
                )
                db.add(parent)
                db.flush()
                parents[parent_slug] = parent
                child_orders[parent.id] = 0
                result.parent_topics_created += 1

            child_slug = slugify(item.topic_slug)
            child = children.get((parent.id, child_slug))
            if child is None:
                child_orders[parent.id] = child_orders.get(parent.id, 0) + 1
                child = Topic(
                    name=item.topic_name,
                    slug=child_slug,
                    parent_topic_id=parent.id,
                    display_order=child_orders[parent.id],
                )
                db.add(child)
                db.flush()
                children[(parent.id, child_slug)] = child
                result.child_topics_created += 1

            if item.content_hash in existing_hashes:
                result.questions_skipped += 1
                continue
            if item.external_id in existing_external_ids:
                raise ValueError(
                    f"Question id {item.external_id} already exists with different content."
                )

            option_ids = {str(option["id"]): uuid.uuid4() for option in item.options}
            correct_source_ids = {
                str(value) for value in item.answer.get("correct_option_ids", [])
            }
            question = Question(
                topic_id=child.id,
                question_text=item.question_text,
                rationale=item.rationale,
                difficulty=item.difficulty,
                question_type=item.question_type,
                source_type="generated_private",
                source_reference=path.name,
                license_status="review_required",
                content_hash=item.content_hash,
                external_id=item.external_id,
                interaction_data=item.interaction,
                case_study_markdown=item.case_study_markdown,
                answer_choices=[
                    AnswerChoice(
                        id=option_ids[str(option["id"])],
                        choice_text=str(option["text_markdown"]).strip(),
                        is_correct=str(option["id"]) in correct_source_ids,
                        display_order=index,
                    )
                    for index, option in enumerate(item.options, start=1)
                ],
            )
            question.answer_key = _normalized_answer_key(
                item, {key: str(value) for key, value in option_ids.items()}
            )
            db.add(question)
            existing_hashes.add(item.content_hash)
            existing_external_ids.add(item.external_id)
            result.questions_inserted += 1
            result.answer_choices_inserted += len(item.options)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return result
