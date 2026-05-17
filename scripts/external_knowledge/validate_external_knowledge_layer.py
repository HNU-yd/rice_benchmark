#!/usr/bin/env python3
"""Validate and report the v0.5.5 external knowledge layer.

Usage:
  python scripts/external_knowledge/validate_external_knowledge_layer.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    MANUAL_REVIEW_FIELDS,
    ensure_output_dirs,
    merge_manual_review_tables,
    parse_args,
    print_summary,
    validate_external_knowledge,
    write_tsv,
)


def main() -> int:
    args = parse_args("Validate external_knowledge_v055 outputs")
    ensure_output_dirs(args.interim_root, args.report_root)
    manual_review_rows = merge_manual_review_tables(args.interim_root)
    manual_review_out = args.interim_root / "qc_diagnostics/external_knowledge_manual_review_table.tsv"
    write_tsv(manual_review_out, manual_review_rows, MANUAL_REVIEW_FIELDS)
    write_tsv(args.report_root / "external_knowledge_manual_review_table.preview.tsv", manual_review_rows[:500], MANUAL_REVIEW_FIELDS)
    validation_rows = validate_external_knowledge(args.repo_root, args.interim_root, args.report_root)
    n_failed = sum(1 for row in validation_rows if row.get("status") == "fail")
    print_summary("external_knowledge_validation", validation_rows, f"manual_review_rows={len(manual_review_rows)}\nvalidation_failed={n_failed}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
