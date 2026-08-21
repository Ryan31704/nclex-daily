import argparse

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.question import Question
from app.services.question_json_import_service import normalize_question_stem


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview or remove repeated generator framing from active stems."
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with SessionLocal() as database:
        questions = list(
            database.scalars(
                select(Question).where(Question.is_active.is_(True))
            ).all()
        )
        changed = [
            (question, normalize_question_stem(question.question_text))
            for question in questions
            if normalize_question_stem(question.question_text) != question.question_text
        ]
        print(
            "Active questions inspected: "
            f"{database.scalar(select(func.count()).select_from(Question).where(Question.is_active.is_(True))) or 0}"
        )
        print(f"Question stems to normalize: {len(changed)}")
        for question, normalized in changed[:5]:
            print(f"- {question.question_text[:100]}")
            print(f"  -> {normalized[:100]}")
        if not args.apply:
            print("Preview only; add --apply to update the displayed stems.")
            return 0
        for question, normalized in changed:
            question.question_text = normalized
        database.commit()
        print(f"Normalized question stems: {len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
