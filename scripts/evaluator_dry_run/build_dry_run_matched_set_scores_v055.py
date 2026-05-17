#!/usr/bin/env python3
"""Build matched-set score table for the v0.5.5 evaluator dry-run."""

from evaluator_dry_run_v055_utils import build_dry_run_matched_set_scores, parse_args


def main() -> None:
    args = parse_args(__doc__ or "Build dry-run matched-set scores.")
    rows = build_dry_run_matched_set_scores(args)
    print(f"dry_run_matched_set_score_rows={rows[0]['rows'] if rows else 0}")


if __name__ == "__main__":
    main()
