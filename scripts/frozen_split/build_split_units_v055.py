#!/usr/bin/env python3
"""Build split units for the v0.5.5 chr1 SNP prototype split.

Usage:
  python scripts/frozen_split/build_split_units_v055.py
"""

from __future__ import annotations

from frozen_split_v055_utils import build_split_units, parse_args, print_summary


def main() -> int:
    args = parse_args("Build v0.5.5 split units")
    rows = build_split_units(args)
    print_summary("split_unit_table", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
