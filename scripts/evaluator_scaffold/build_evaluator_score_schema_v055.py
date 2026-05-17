#!/usr/bin/env python3
"""Build evaluator score input and future output schemas for v0.5.5."""

from evaluator_scaffold_v055_utils import (
    build_output_schema,
    build_score_schema,
    parse_args,
    print_summary,
)


def main() -> None:
    args = parse_args(__doc__ or "Build evaluator schemas.")
    score_rows = build_score_schema(args)
    output_rows = build_output_schema(args)
    print_summary("evaluator_score_input_schema", score_rows)
    print_summary("evaluator_output_schema", output_rows)


if __name__ == "__main__":
    main()
