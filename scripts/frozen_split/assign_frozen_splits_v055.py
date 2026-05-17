#!/usr/bin/env python3
"""Assign v0.5.5 chr1 SNP prototype split labels.

Usage:
  python scripts/frozen_split/assign_frozen_splits_v055.py
"""

from __future__ import annotations

from frozen_split_v055_utils import build_assignment, parse_args, print_summary


def main() -> int:
    args = parse_args("Assign v0.5.5 frozen prototype splits")
    rows = build_assignment(args)
    print_summary("frozen_split_assignment", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
