#!/usr/bin/env python3
"""Validate v0.5.5 chr1 SNP prototype split outputs and write report.

Usage:
  python scripts/frozen_split/validate_frozen_split_v055.py
"""

from __future__ import annotations

from frozen_split_v055_utils import parse_args, print_summary, validate_and_report


def main() -> int:
    args = parse_args("Validate v0.5.5 frozen prototype split")
    rows = validate_and_report(args)
    n_failed = sum(1 for row in rows if row.get("status") == "fail")
    print_summary("split_validation", rows, f"validation_failed={n_failed}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
