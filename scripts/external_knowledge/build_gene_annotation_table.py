#!/usr/bin/env python3
"""Build the v0.5.5 unified rice gene annotation table.

Usage:
  python scripts/external_knowledge/build_gene_annotation_table.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    GENE_ANNOTATION_FIELDS,
    build_gene_annotation_rows,
    ensure_output_dirs,
    parse_args,
    print_summary,
    write_tsv,
)


def main() -> int:
    args = parse_args("Build gene_annotation_table.tsv")
    ensure_output_dirs(args.interim_root, args.report_root)
    rows = build_gene_annotation_rows(args.repo_root)
    out = args.interim_root / "annotation/gene_annotation_table.tsv"
    write_tsv(out, rows, GENE_ANNOTATION_FIELDS)
    write_tsv(args.report_root / "gene_annotation_table.preview.tsv", rows[:500], GENE_ANNOTATION_FIELDS)
    print_summary("gene_annotation_table", rows, f"output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
