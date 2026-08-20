import argparse

from app.db.session import SessionLocal
from app.services.question_bank_verification import collect_question_bank_metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify normalized question-bank invariants.")
    parser.add_argument("--expect-questions", type=int, default=1700)
    parser.add_argument("--expect-choices", type=int, default=6800)
    parser.add_argument("--expect-parent-topics", type=int, default=17)
    parser.add_argument(
        "--expect-child-topics",
        type=int,
        default=None,
        help="Optional source-specific expected number of chapter/topic pairs.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with SessionLocal() as database:
        metrics = collect_question_bank_metrics(database)

    for label, value in metrics.to_dict().items():
        print(f"{label.replace('_', ' ').title()}: {value}")

    expected = {
        "questions": args.expect_questions,
        "answer_choices": args.expect_choices,
        "parent_topics": args.expect_parent_topics,
    }
    if args.expect_child_topics is not None:
        expected["child_topics"] = args.expect_child_topics

    failures = [
        f"{name}: expected {expected_value}, found {getattr(metrics, name)}"
        for name, expected_value in expected.items()
        if getattr(metrics, name) != expected_value
    ]
    invariant_fields = (
        "questions_without_four_choices",
        "questions_without_one_correct_choice",
        "questions_without_topic",
        "questions_assigned_to_parent_topic",
        "orphan_child_topics",
        "invalid_source_metadata",
    )
    failures.extend(
        f"{name}: expected 0, found {getattr(metrics, name)}"
        for name in invariant_fields
        if getattr(metrics, name) != 0
    )

    if failures:
        print("Verification: FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Verification: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
