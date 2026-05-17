#!/usr/bin/env python3
"""Build evaluator object input table for the v0.5.5 chr1 SNP prototype."""

from evaluator_scaffold_v055_utils import build_evaluator_object_input, parse_args, print_summary


def main() -> None:
    args = parse_args(__doc__ or "Build evaluator object input table.")
    rows = build_evaluator_object_input(args)
    print_summary("evaluator_object_input", rows)


if __name__ == "__main__":
    main()
