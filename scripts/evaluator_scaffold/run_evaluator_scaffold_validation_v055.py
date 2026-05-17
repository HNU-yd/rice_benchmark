#!/usr/bin/env python3
"""Run evaluator scaffold join checks, leakage guards, validation, and report."""

from evaluator_scaffold_v055_utils import parse_args, print_summary, validate_and_report


def main() -> None:
    args = parse_args(__doc__ or "Validate evaluator scaffold.")
    rows = validate_and_report(args)
    n_failed = sum(1 for row in rows if row.get("status") == "fail")
    print_summary("evaluator_scaffold_validation", rows, extra=f"failed_checks={n_failed}")


if __name__ == "__main__":
    main()
