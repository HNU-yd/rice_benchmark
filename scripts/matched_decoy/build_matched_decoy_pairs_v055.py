#!/usr/bin/env python3
"""Select matched decoy v0.5.5 background pairs.

Usage:
  python scripts/matched_decoy/build_matched_decoy_pairs_v055.py
"""

from __future__ import annotations

from matched_decoy_v055_utils import build_pairs, parse_args, print_summary


def main() -> int:
    args = parse_args("Build matched decoy v0.5.5 pair table")
    rows = build_pairs(args)
    n_failed = sum(1 for row in rows if row.get("matching_status") == "failed_no_candidate")
    print_summary("matched_decoy_pair_table", rows, f"failed_decoy_pairs={n_failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
