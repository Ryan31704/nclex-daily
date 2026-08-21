import argparse
from pathlib import Path

from sqlalchemy import func, select, update

from app.db.session import SessionLocal
from app.models.question import Question
from app.models.topic import Topic
from app.models.daily_session import DailySession
from app.services.question_json_import_service import (
    import_question_json,
    parse_question_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or import the generated JSON question-bank format."
    )
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--apply", action="store_true", help="Import validated questions")
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Make this the only active bank after importing (requires --apply)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    path = args.json_path.resolve()
    if not path.is_file():
        print(f"Source JSON not found: {path}")
        return 2
    parsed = parse_question_json(path)
    type_counts: dict[str, int] = {}
    for question in parsed:
        type_counts[question.question_type] = type_counts.get(question.question_type, 0) + 1
    print(f"Validated questions: {len(parsed)}")
    for question_type, count in sorted(type_counts.items()):
        print(f"  {question_type}: {count}")
    if not args.apply:
        print("Validation only; no database rows changed. Add --apply to import.")
        return 0

    with SessionLocal() as database:
        result = import_question_json(database, path)
        print(f"Questions inserted: {result.questions_inserted}")
        print(f"Questions already present: {result.questions_skipped}")
        print(f"Answer choices inserted: {result.answer_choices_inserted}")
        print(f"Parent topics created: {result.parent_topics_created}")
        print(f"Child topics created: {result.child_topics_created}")
        if args.activate:
            hashes = result.content_hashes
            matched = int(
                database.scalar(
                    select(func.count()).select_from(Question).where(
                        Question.content_hash.in_(hashes)
                    )
                )
                or 0
            )
            if matched != len(hashes):
                raise RuntimeError(
                    f"Activation refused: matched {matched} of {len(hashes)} questions."
                )
            selected_topic_ids = set(
                database.scalars(
                    select(Question.topic_id).where(Question.content_hash.in_(hashes))
                ).all()
            )
            parent_ids = set(
                parent_id
                for parent_id in database.scalars(
                    select(Topic.parent_topic_id).where(Topic.id.in_(selected_topic_ids))
                ).all()
                if parent_id is not None
            )
            database.execute(update(Question).values(is_active=False))
            database.execute(
                update(Question)
                .where(Question.content_hash.in_(hashes))
                .values(is_active=True)
            )
            database.execute(update(Topic).values(is_active=False))
            database.execute(
                update(Topic)
                .where(Topic.id.in_(selected_topic_ids | parent_ids))
                .values(is_active=True)
            )
            database.execute(
                update(DailySession)
                .where(DailySession.status == "active")
                .values(status="abandoned")
            )
            database.commit()
            print(f"Activation applied. Active questions: {matched}")
            print("Previous questions and attempt history remain safely stored as inactive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
