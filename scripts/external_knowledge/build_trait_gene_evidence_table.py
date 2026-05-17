#!/usr/bin/env python3
"""Build v0.5.5 trait-gene reference table.

Usage:
  python scripts/external_knowledge/build_trait_gene_evidence_table.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    MANUAL_REVIEW_FIELDS,
    TRAIT_GENE_EVIDENCE_FIELDS,
    build_trait_gene_evidence_rows,
    ensure_output_dirs,
    parse_args,
    print_summary,
    write_tsv,
)


def main() -> int:
    args = parse_args("Build trait_gene_evidence_table.tsv")
    ensure_output_dirs(args.interim_root, args.report_root)
    rows, manual_review = build_trait_gene_evidence_rows(args.repo_root, args.interim_root)
    out = args.interim_root / "evidence/trait_gene_evidence_table.tsv"
    review_out = args.interim_root / "evidence/trait_gene_manual_review_table.tsv"
    write_tsv(out, rows, TRAIT_GENE_EVIDENCE_FIELDS)
    write_tsv(review_out, manual_review, MANUAL_REVIEW_FIELDS)
    write_tsv(args.report_root / "trait_gene_evidence_table.preview.tsv", rows[:500], TRAIT_GENE_EVIDENCE_FIELDS)
    print_summary("trait_gene_evidence_table", rows, f"manual_review_rows={len(manual_review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
