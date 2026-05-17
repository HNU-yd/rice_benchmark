#!/usr/bin/env python3
"""Build matched decoy v0.5.5 candidate pool.

Usage:
  python scripts/matched_decoy/build_matched_decoy_candidate_pool_v055.py
"""

from __future__ import annotations

from matched_decoy_v055_utils import build_candidate_pool, parse_args, print_summary


def main() -> int:
    args = parse_args("Build matched decoy v0.5.5 candidate pool")
    rows = build_candidate_pool(args)
    n_failed = sum(1 for row in rows if row.get("candidate_pool_status") == "failed_no_candidate")
    print_summary("matched_decoy_candidate_pool", rows, f"failed_candidate_pool_rows={n_failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
