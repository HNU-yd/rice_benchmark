#!/usr/bin/env python3
"""Build v0.5.5 Q-TARO/QTL interval reference table.

Usage:
  python scripts/external_knowledge/build_qtl_interval_evidence_table.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    QTL_INTERVAL_EVIDENCE_FIELDS,
    build_qtl_interval_rows,
    ensure_output_dirs,
    parse_args,
    print_summary,
    write_tsv,
)


def main() -> int:
    args = parse_args("Build qtl_interval_evidence_table.tsv")
    ensure_output_dirs(args.interim_root, args.report_root)
    rows = build_qtl_interval_rows(args.repo_root)
    out = args.interim_root / "evidence/qtl_interval_evidence_table.tsv"
    write_tsv(out, rows, QTL_INTERVAL_EVIDENCE_FIELDS)
    write_tsv(args.report_root / "qtl_interval_evidence_table.preview.tsv", rows[:500], QTL_INTERVAL_EVIDENCE_FIELDS)
    print_summary("qtl_interval_evidence_table", rows, f"output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
