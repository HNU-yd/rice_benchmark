#!/usr/bin/env python3
"""Validate matched decoy v0.5.5 outputs and write the report.

Usage:
  python scripts/matched_decoy/validate_matched_decoy_v055.py
"""

from __future__ import annotations

from matched_decoy_v055_utils import parse_args, print_summary, validate_and_report


def main() -> int:
    args = parse_args("Validate matched decoy v0.5.5 outputs")
    rows = validate_and_report(args)
    n_failed = sum(1 for row in rows if row.get("status") == "fail")
    print_summary("decoy_validation", rows, f"validation_failed={n_failed}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
