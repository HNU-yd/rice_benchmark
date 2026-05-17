#!/usr/bin/env python3
"""Build v0.5.5 RAP/MSU/Oryzabase/funRiceGenes/Q-TARO gene ID mappings.

Usage:
  python scripts/external_knowledge/build_gene_id_mapping_table.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    GENE_ID_MAPPING_FIELDS,
    MANUAL_REVIEW_FIELDS,
    build_gene_id_mapping_rows,
    ensure_output_dirs,
    parse_args,
    print_summary,
    write_tsv,
)


def main() -> int:
    args = parse_args("Build gene_id_mapping_table.tsv")
    ensure_output_dirs(args.interim_root, args.report_root)
    rows, manual_review = build_gene_id_mapping_rows(args.repo_root)
    mapping_out = args.interim_root / "mapping/gene_id_mapping_table.tsv"
    review_out = args.interim_root / "mapping/external_knowledge_manual_review_table.tsv"
    write_tsv(mapping_out, rows, GENE_ID_MAPPING_FIELDS)
    write_tsv(review_out, manual_review, MANUAL_REVIEW_FIELDS)
    write_tsv(args.report_root / "gene_id_mapping_table.preview.tsv", rows[:500], GENE_ID_MAPPING_FIELDS)
    write_tsv(args.report_root / "external_knowledge_manual_review_table.preview.tsv", manual_review[:500], MANUAL_REVIEW_FIELDS)
    print_summary("gene_id_mapping_table", rows, f"manual_review_rows={len(manual_review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
