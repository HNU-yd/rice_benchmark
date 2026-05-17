#!/usr/bin/env python3
"""Build baseline score dry-run input for the v0.5.5 evaluator scaffold."""

from evaluator_scaffold_v055_utils import build_baseline_score_dry_run, parse_args, print_summary


def main() -> None:
    args = parse_args(__doc__ or "Build baseline score dry-run input.")
    rows = build_baseline_score_dry_run(args)
    print_summary("baseline_score_dry_run_join_summary", rows)


if __name__ == "__main__":
    main()
