#!/usr/bin/env python3
"""Build detectability and research-bias proxy tables for matched decoy v0.5.5.

Usage:
  python scripts/matched_decoy/build_detectability_research_bias_v055.py
"""

from __future__ import annotations

from matched_decoy_v055_utils import build_detectability_research_bias, parse_args, print_summary


def main() -> int:
    args = parse_args("Build matched decoy v0.5.5 detectability and research-bias proxies")
    detectability, research = build_detectability_research_bias(args)
    print_summary("detectability_bias_table_v055", detectability)
    print_summary("research_bias_table_v055", research)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
