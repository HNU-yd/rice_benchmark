#!/usr/bin/env python3
"""Build evaluator decoy input table for the v0.5.5 chr1 SNP prototype."""

from evaluator_scaffold_v055_utils import build_evaluator_decoy_input, parse_args, print_summary


def main() -> None:
    args = parse_args(__doc__ or "Build evaluator decoy input table.")
    rows = build_evaluator_decoy_input(args)
    print_summary("evaluator_decoy_input", rows)


if __name__ == "__main__":
    main()
