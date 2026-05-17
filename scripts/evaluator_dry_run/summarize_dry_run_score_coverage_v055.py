#!/usr/bin/env python3
"""Summarize score coverage and missing-score diagnostics for 09B."""

from evaluator_dry_run_v055_utils import parse_args, summarize_dry_run_score_coverage


def main() -> None:
    args = parse_args(__doc__ or "Summarize dry-run score coverage.")
    coverage_rows, missing_rows = summarize_dry_run_score_coverage(args)
    print(f"dry_run_score_coverage_rows={len(coverage_rows)}")
    print(f"dry_run_missing_score_diagnostics_rows={len(missing_rows)}")


if __name__ == "__main__":
    main()
