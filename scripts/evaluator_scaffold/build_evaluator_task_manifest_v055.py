#!/usr/bin/env python3
"""Build evaluator task manifest for the v0.5.5 chr1 SNP prototype."""

from evaluator_scaffold_v055_utils import build_task_manifest, parse_args, print_summary


def main() -> None:
    args = parse_args(__doc__ or "Build evaluator task manifest.")
    rows = build_task_manifest(args)
    print_summary("evaluator_task_manifest", rows)


if __name__ == "__main__":
    main()
