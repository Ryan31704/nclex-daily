import csv
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.topic import Topic
from app.services.question_import_service import import_question_csv, parse_question_csv
from app.services.question_bank_verification import collect_question_bank_metrics
from app.scripts.activate_question_bank import activate_question_hashes

HEADERS = (
    "question",
    "answer",
    "choice_a",
    "choice_b",
    "choice_c",
    "choice_d",
    "chapter",
    "topic",
)


@pytest.fixture
def database() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    with testing_session() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _valid_row(**overrides: str) -> dict[str, str]:
    row = {
        "question": "Which finding should the nurse report first?",
        "answer": "B - Oxygen saturation of 84%",
        "choice_a": "Temperature of 99 F",
        "choice_b": "Oxygen saturation of 84%",
        "choice_c": "Pain score of 3",
        "choice_d": "Heart rate of 88",
        "chapter": "Chapter 1: Fundamentals",
        "topic": "Prioritization",
    }
    row.update(overrides)
    return row


def test_parses_a_through_d_and_assigns_correct_choices(
    tmp_path: Path,
    database: Session,
) -> None:
    rows = [
        _valid_row(
            question=f"Question {letter}",
            answer=f"{letter} - {letter} choice",
            choice_a="A choice",
            choice_b="B choice",
            choice_c="C choice",
            choice_d="D choice",
        )
        for letter in "ABCD"
    ]
    csv_path = _write_csv(tmp_path / "questions.csv", rows)

    result = import_question_csv(database, csv_path)

    assert result.questions_inserted == 4
    questions = list(
        database.scalars(select(Question).order_by(Question.question_text)).all()
    )
    for expected_index, question in enumerate(questions):
        correct = [choice for choice in question.answer_choices if choice.is_correct]
        assert len(question.answer_choices) == 4
        assert len(correct) == 1
        assert correct[0].display_order == expected_index + 1


def test_reports_malformed_and_mismatched_answers(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path / "invalid.csv",
        [
            _valid_row(question="Malformed", answer="choice B"),
            _valid_row(question="Mismatch", answer="A - Not the A choice"),
        ],
    )

    parsed, errors, source_rows = parse_question_csv(csv_path)

    assert source_rows == 2
    assert parsed == []
    assert [error.row_number for error in errors] == [2, 3]
    assert [error.error_type for error in errors] == [
        "malformed_answer",
        "answer_choice_mismatch",
    ]


def test_builds_hierarchy_and_reimport_is_idempotent(
    tmp_path: Path,
    database: Session,
) -> None:
    csv_path = _write_csv(
        tmp_path / "questions.csv",
        [
            _valid_row(question="Question one"),
            _valid_row(question="Question two", topic="Safety"),
            _valid_row(
                question="Question three",
                chapter="Chapter 2: Pharmacology",
                topic="Medication Safety",
            ),
        ],
    )

    first = import_question_csv(database, csv_path)
    second = import_question_csv(database, csv_path)

    assert first.parent_topics_created == 2
    assert first.child_topics_created == 3
    assert first.questions_inserted == 3
    assert second.parent_topics_created == 0
    assert second.child_topics_created == 0
    assert second.questions_inserted == 0
    assert second.questions_skipped == 3
    assert database.scalar(select(func.count()).select_from(Topic)) == 5
    assert database.scalar(select(func.count()).select_from(Question)) == 3
    assert database.scalar(select(func.count()).select_from(AnswerChoice)) == 12
    metrics = collect_question_bank_metrics(database)
    assert metrics.questions_without_four_choices == 0
    assert metrics.questions_without_one_correct_choice == 0
    assert metrics.questions_without_topic == 0
    assert metrics.questions_assigned_to_parent_topic == 0
    assert metrics.orphan_child_topics == 0


def test_can_preview_and_reversibly_activate_a_question_set(
    tmp_path: Path,
    database: Session,
) -> None:
    first_csv = _write_csv(
        tmp_path / "first.csv",
        [_valid_row(question="Question one")],
    )
    second_csv = _write_csv(
        tmp_path / "second.csv",
        [
            _valid_row(
                question="Question two",
                chapter="Chapter 2: Pharmacology",
                topic="Medication Safety",
            )
        ],
    )
    first_parsed, _, _ = parse_question_csv(first_csv)
    second_parsed, _, _ = parse_question_csv(second_csv)
    import_question_csv(database, first_csv)
    import_question_csv(database, second_csv)

    matched, missing, active_before = activate_question_hashes(
        database,
        {second_parsed[0].content_hash},
        apply=False,
    )
    assert (matched, missing, active_before) == (1, 0, 2)

    activate_question_hashes(
        database,
        {second_parsed[0].content_hash},
        apply=True,
    )
    active_questions = set(
        database.scalars(
            select(Question.content_hash).where(Question.is_active.is_(True))
        ).all()
    )
    assert active_questions == {second_parsed[0].content_hash}

    activate_question_hashes(
        database,
        {first_parsed[0].content_hash},
        apply=True,
    )
    restored_questions = set(
        database.scalars(
            select(Question.content_hash).where(Question.is_active.is_(True))
        ).all()
    )
    assert restored_questions == {first_parsed[0].content_hash}
