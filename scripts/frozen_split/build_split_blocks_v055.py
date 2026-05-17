#!/usr/bin/env python3
"""Build leakage-aware split blocks for the v0.5.5 chr1 SNP prototype split.

Usage:
  python scripts/frozen_split/build_split_blocks_v055.py
"""

from __future__ import annotations

from frozen_split_v055_utils import build_split_blocks, parse_args, print_summary


def main() -> int:
    args = parse_args("Build v0.5.5 split blocks")
    rows = build_split_blocks(args)
    print_summary("split_block_table", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
