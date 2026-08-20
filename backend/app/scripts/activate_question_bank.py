import argparse
from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.question import Question
from app.models.topic import Topic
from app.services.question_import_service import parse_question_csv, write_error_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or activate exactly the questions listed in an imported CSV "
            "without deleting historical data."
        ),
    )
    parser.add_argument("csv_path", type=Path, help="CSV defining the active question set")
    parser.add_argument(
        "--error-report",
        type=Path,
        help="CSV validation report path (defaults beside the source file)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the activation plan; without this flag the command is read-only",
    )
    return parser


def activate_question_hashes(
    db: Session,
    content_hashes: set[str],
    *,
    apply: bool,
) -> tuple[int, int, int]:
    if not content_hashes:
        raise ValueError("The CSV does not contain any valid questions.")

    matched_hashes = set(
        db.scalars(
            select(Question.content_hash).where(Question.content_hash.in_(content_hashes))
        ).all()
    )
    missing_count = len(content_hashes - matched_hashes)
    active_before = int(
        db.scalar(
            select(func.count()).select_from(Question).where(Question.is_active.is_(True))
        )
        or 0
    )
    if missing_count or not apply:
        return len(matched_hashes), missing_count, active_before

    selected_topic_ids = set(
        db.scalars(
            select(Question.topic_id).where(Question.content_hash.in_(content_hashes))
        ).all()
    )
    parent_topic_ids = set(
        parent_id
        for parent_id in db.scalars(
            select(Topic.parent_topic_id).where(Topic.id.in_(selected_topic_ids))
        ).all()
        if parent_id is not None
    )
    active_topic_ids = selected_topic_ids | parent_topic_ids

    db.execute(update(Question).values(is_active=False))
    db.execute(
        update(Question)
        .where(Question.content_hash.in_(content_hashes))
        .values(is_active=True)
    )
    db.execute(update(Topic).values(is_active=False))
    db.execute(
        update(Topic).where(Topic.id.in_(active_topic_ids)).values(is_active=True)
    )
    db.commit()
    return len(matched_hashes), 0, active_before


def main() -> int:
    args = build_parser().parse_args()
    csv_path = args.csv_path.resolve()
    if not csv_path.is_file():
        print(f"Source CSV not found: {csv_path}")
        return 2

    parsed, errors, source_rows = parse_question_csv(csv_path)
    if errors:
        report_path = args.error_report or csv_path.with_suffix(".errors.csv")
        write_error_report(errors, report_path)
        print(f"Activation rejected; error report written to: {report_path.resolve()}")
        return 1

    content_hashes = {question.content_hash for question in parsed}
    with SessionLocal() as database:
        matched, missing, active_before = activate_question_hashes(
            database,
            content_hashes,
            apply=args.apply,
        )

    print(f"Source rows: {source_rows}")
    print(f"Unique questions in requested set: {len(content_hashes)}")
    print(f"Questions matched in database: {matched}")
    print(f"Questions currently active: {active_before}")
    if missing:
        print(f"Activation refused: {missing} questions have not been imported yet.")
        print(f"Run: python -m app.scripts.import_questions {csv_path}")
        return 1
    if not args.apply:
        print("Preview only; no database rows changed. Add --apply to activate this set.")
        return 0

    print(f"Activation applied. Active questions: {matched}")
    print("Older questions and attempt history were preserved as inactive records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
