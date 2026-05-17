#!/usr/bin/env python3
"""Build matched decoy v0.5.5 evidence object table.

Usage:
  python scripts/matched_decoy/build_matched_decoy_objects_v055.py
"""

from __future__ import annotations

from matched_decoy_v055_utils import build_matched_decoy_objects, parse_args, print_summary


def main() -> int:
    args = parse_args("Build matched decoy v0.5.5 object table")
    rows = build_matched_decoy_objects(args)
    n_main = sum(1 for row in rows if row.get("in_main_evaluation_candidate_pool") == "true")
    print_summary("matched_decoy_object_table", rows, f"main_evaluation_candidate_objects={n_main}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
