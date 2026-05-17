#!/usr/bin/env python3
"""Validate the v0.5.5 matched-ranking evaluator dry-run."""

from evaluator_dry_run_v055_utils import parse_args, print_summary, validate_evaluator_dry_run


def main() -> None:
    args = parse_args(__doc__ or "Validate evaluator dry-run.")
    rows = validate_evaluator_dry_run(args)
    n_failed = sum(1 for row in rows if row.get("status") == "fail")
    print_summary("dry_run_validation", rows, extra=f"failed_checks={n_failed}")


if __name__ == "__main__":
    main()
