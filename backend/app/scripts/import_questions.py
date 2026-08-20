import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.services.question_import_service import import_question_csv, write_error_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and idempotently import the private NCLEX question CSV.",
    )
    parser.add_argument("csv_path", type=Path, help="Path to the source CSV file")
    parser.add_argument(
        "--error-report",
        type=Path,
        help="CSV error report path (defaults beside the source file)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    csv_path = args.csv_path.resolve()
    if not csv_path.is_file():
        print(f"Source CSV not found: {csv_path}")
        return 2

    report_path = args.error_report or csv_path.with_suffix(".errors.csv")
    with SessionLocal() as database:
        result = import_question_csv(database, csv_path)

    print(f"Source rows: {result.source_rows}")
    print(f"Parent topics created: {result.parent_topics_created}")
    print(f"Child topics created: {result.child_topics_created}")
    print(f"Questions inserted: {result.questions_inserted}")
    print(f"Questions skipped (already present): {result.questions_skipped}")
    print(f"Answer choices inserted: {result.answer_choices_inserted}")
    print(f"Invalid rows: {result.invalid_rows}")

    if result.errors:
        write_error_report(result.errors, report_path)
        print(f"Import rejected; error report written to: {report_path.resolve()}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
