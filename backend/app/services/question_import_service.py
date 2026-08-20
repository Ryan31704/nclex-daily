import csv
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.topic import Topic

REQUIRED_COLUMNS = (
    "question",
    "answer",
    "choice_a",
    "choice_b",
    "choice_c",
    "choice_d",
    "chapter",
    "topic",
)
ANSWER_PATTERN = re.compile(r"^\s*([A-D])\s*-\s*(.*?)\s*$")
CHOICE_COLUMNS = ("choice_a", "choice_b", "choice_c", "choice_d")


@dataclass(frozen=True)
class ParsedQuestion:
    row_number: int
    question_text: str
    chapter: str
    topic: str
    choices: tuple[str, str, str, str]
    correct_index: int
    content_hash: str


@dataclass(frozen=True)
class ImportValidationError:
    row_number: int
    error_type: str
    question_text: str
    reason: str


@dataclass
class ImportResult:
    source_rows: int = 0
    parent_topics_created: int = 0
    child_topics_created: int = 0
    questions_inserted: int = 0
    questions_skipped: int = 0
    answer_choices_inserted: int = 0
    errors: list[ImportValidationError] = field(default_factory=list)

    @property
    def invalid_rows(self) -> int:
        return len({error.row_number for error in self.errors if error.row_number > 1})


def parse_question_csv(
    csv_path: Path,
) -> tuple[list[ParsedQuestion], list[ImportValidationError], int]:
    parsed: list[ParsedQuestion] = []
    errors: list[ImportValidationError] = []
    source_rows = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing_headers = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing_headers:
            errors.append(
                ImportValidationError(
                    row_number=1,
                    error_type="missing_columns",
                    question_text="",
                    reason=f"Missing required columns: {', '.join(missing_headers)}",
                )
            )
            return parsed, errors, source_rows

        for row_number, row in enumerate(reader, start=2):
            source_rows += 1
            row_errors = _validate_row(row_number, row)
            if row_errors:
                errors.extend(row_errors)
                continue

            question_text = row["question"]
            chapter = row["chapter"]
            topic = row["topic"]
            choices = tuple(row[column] for column in CHOICE_COLUMNS)
            answer_match = ANSWER_PATTERN.fullmatch(row["answer"])
            assert answer_match is not None
            correct_index = ord(answer_match.group(1)) - ord("A")
            parsed.append(
                ParsedQuestion(
                    row_number=row_number,
                    question_text=question_text,
                    chapter=chapter,
                    topic=topic,
                    choices=choices,  # type: ignore[arg-type]
                    correct_index=correct_index,
                    content_hash=build_content_hash(
                        chapter,
                        topic,
                        question_text,
                        choices,
                        correct_index,
                    ),
                )
            )

    return parsed, errors, source_rows


def _validate_row(
    row_number: int,
    row: dict[str, str | None],
) -> list[ImportValidationError]:
    question_text = row.get("question") or ""
    errors: list[ImportValidationError] = []
    missing_values = [
        column for column in REQUIRED_COLUMNS if not (row.get(column) or "").strip()
    ]
    if missing_values:
        errors.append(
            ImportValidationError(
                row_number=row_number,
                error_type="missing_values",
                question_text=question_text,
                reason=f"Required values are empty: {', '.join(missing_values)}",
            )
        )
        return errors

    answer = row["answer"]
    assert answer is not None
    answer_match = ANSWER_PATTERN.fullmatch(answer)
    if answer_match is None:
        errors.append(
            ImportValidationError(
                row_number=row_number,
                error_type="malformed_answer",
                question_text=question_text,
                reason="Answer must use the format 'A - answer text' through 'D - answer text'.",
            )
        )
        return errors

    answer_index = ord(answer_match.group(1)) - ord("A")
    choice_value = row[CHOICE_COLUMNS[answer_index]]
    assert choice_value is not None
    if answer_match.group(2).strip() != choice_value.strip():
        errors.append(
            ImportValidationError(
                row_number=row_number,
                error_type="answer_choice_mismatch",
                question_text=question_text,
                reason=(
                    f"Answer text does not exactly match choice "
                    f"{answer_match.group(1)} after trimming whitespace."
                ),
            )
        )
    return errors


def build_content_hash(
    chapter: str,
    topic: str,
    question_text: str,
    choices: tuple[str, ...],
    correct_index: int,
) -> str:
    canonical_content = json.dumps(
        {
            "chapter": chapter.strip(),
            "topic": topic.strip(),
            "question": question_text.strip(),
            "choices": [choice.strip() for choice in choices],
            "correct_index": correct_index,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if slug:
        return slug
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def import_question_csv(db: Session, csv_path: Path) -> ImportResult:
    parsed, errors, source_rows = parse_question_csv(csv_path)
    result = ImportResult(source_rows=source_rows, errors=errors)
    if errors:
        return result

    existing_topics = list(db.scalars(select(Topic)).all())
    parent_topics = {
        topic.slug: topic for topic in existing_topics if topic.parent_topic_id is None
    }
    child_topics = {
        (topic.parent_topic_id, topic.slug): topic
        for topic in existing_topics
        if topic.parent_topic_id is not None
    }
    existing_hashes = set(db.scalars(select(Question.content_hash)).all())
    next_parent_order = max(
        (topic.display_order for topic in parent_topics.values()),
        default=0,
    )
    next_child_orders = {
        parent.id: max((child.display_order for child in parent.children), default=0)
        for parent in parent_topics.values()
    }

    try:
        for item in parsed:
            parent_slug = slugify(item.chapter)
            parent = parent_topics.get(parent_slug)
            if parent is None:
                next_parent_order += 1
                parent = Topic(
                    name=item.chapter,
                    slug=parent_slug,
                    display_order=next_parent_order,
                )
                db.add(parent)
                db.flush()
                parent_topics[parent_slug] = parent
                next_child_orders[parent.id] = 0
                result.parent_topics_created += 1

            child_slug = slugify(item.topic)
            child_key = (parent.id, child_slug)
            child = child_topics.get(child_key)
            if child is None:
                next_child_orders[parent.id] = next_child_orders.get(parent.id, 0) + 1
                child = Topic(
                    name=item.topic,
                    slug=child_slug,
                    parent_topic_id=parent.id,
                    display_order=next_child_orders[parent.id],
                )
                db.add(child)
                db.flush()
                child_topics[child_key] = child
                result.child_topics_created += 1

            if item.content_hash in existing_hashes:
                result.questions_skipped += 1
                continue

            question = Question(
                topic_id=child.id,
                question_text=item.question_text,
                rationale=None,
                difficulty=None,
                question_type="multiple_choice",
                source_type="imported_private",
                source_reference=csv_path.name,
                license_status="review_required",
                content_hash=item.content_hash,
            )
            question.answer_choices = [
                AnswerChoice(
                    choice_text=choice_text,
                    is_correct=index == item.correct_index,
                    display_order=index + 1,
                )
                for index, choice_text in enumerate(item.choices)
            ]
            db.add(question)
            existing_hashes.add(item.content_hash)
            result.questions_inserted += 1
            result.answer_choices_inserted += 4

        db.commit()
    except Exception:
        db.rollback()
        raise

    return result


def write_error_report(
    errors: list[ImportValidationError],
    report_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("csv_row", "error_type", "question_text", "reason"),
        )
        writer.writeheader()
        for error in errors:
            writer.writerow(
                {
                    "csv_row": error.row_number,
                    "error_type": error.error_type,
                    "question_text": error.question_text,
                    "reason": error.reason,
                }
            )
