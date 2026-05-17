#!/usr/bin/env python3
"""Compute dry-run rank-position diagnostics for matched sets."""

from evaluator_dry_run_v055_utils import compute_dry_run_rank_positions, parse_args, print_summary


def main() -> None:
    args = parse_args(__doc__ or "Compute dry-run rank positions.")
    rows = compute_dry_run_rank_positions(args)
    print_summary("dry_run_rank_position", rows)


if __name__ == "__main__":
    main()
