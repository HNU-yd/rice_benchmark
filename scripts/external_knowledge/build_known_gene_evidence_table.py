#!/usr/bin/env python3
"""Build v0.5.5 known/functional gene reference table.

Usage:
  python scripts/external_knowledge/build_known_gene_evidence_table.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    KNOWN_GENE_EVIDENCE_FIELDS,
    build_known_gene_evidence_rows,
    ensure_output_dirs,
    parse_args,
    print_summary,
    write_tsv,
)


def main() -> int:
    args = parse_args("Build known_gene_evidence_table.tsv")
    ensure_output_dirs(args.interim_root, args.report_root)
    rows = build_known_gene_evidence_rows(args.repo_root, args.interim_root)
    out = args.interim_root / "evidence/known_gene_evidence_table.tsv"
    write_tsv(out, rows, KNOWN_GENE_EVIDENCE_FIELDS)
    write_tsv(args.report_root / "known_gene_evidence_table.preview.tsv", rows[:500], KNOWN_GENE_EVIDENCE_FIELDS)
    print_summary("known_gene_evidence_table", rows, f"output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
