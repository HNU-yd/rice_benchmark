#!/usr/bin/env python3
"""Run split leakage checks for v0.5.5 chr1 SNP prototype split.

Usage:
  python scripts/frozen_split/check_split_leakage_v055.py
"""

from __future__ import annotations

from frozen_split_v055_utils import build_leakage_checks, parse_args, print_summary


def main() -> int:
    args = parse_args("Check v0.5.5 split leakage")
    rows = build_leakage_checks(args)
    n_failed = sum(1 for row in rows if row.get("status") == "fail")
    print_summary("split_leakage_check", rows, f"leakage_failed={n_failed}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
