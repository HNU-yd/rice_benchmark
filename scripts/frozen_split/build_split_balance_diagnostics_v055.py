#!/usr/bin/env python3
"""Build split balance diagnostics for v0.5.5 chr1 SNP prototype split.

Usage:
  python scripts/frozen_split/build_split_balance_diagnostics_v055.py
"""

from __future__ import annotations

from frozen_split_v055_utils import build_balance_diagnostics, parse_args, print_summary


def main() -> int:
    args = parse_args("Build v0.5.5 split balance diagnostics")
    rows = build_balance_diagnostics(args)
    print_summary("split_balance_diagnostics", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
