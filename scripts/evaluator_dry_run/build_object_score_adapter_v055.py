#!/usr/bin/env python3
"""Build object score adapter table for the v0.5.5 matched-ranking dry-run."""

from evaluator_dry_run_v055_utils import build_object_score_adapter, parse_args, print_summary


def main() -> None:
    args = parse_args(__doc__ or "Build object score adapter.")
    rows = build_object_score_adapter(args)
    print_summary("object_score_adapter", rows)


if __name__ == "__main__":
    main()
