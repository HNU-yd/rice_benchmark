#!/usr/bin/env python3
"""Build v0.5.5 evidence coordinate mapping and source manifest tables.

Usage:
  python scripts/external_knowledge/build_evidence_coordinate_mapping_table.py
"""

from __future__ import annotations

from external_knowledge_v055_utils import (
    EVIDENCE_COORDINATE_MAPPING_FIELDS,
    EVIDENCE_SOURCE_MANIFEST_FIELDS,
    build_coordinate_mapping_rows,
    build_source_manifest_rows,
    ensure_output_dirs,
    parse_args,
    print_summary,
    write_tsv,
)


def main() -> int:
    args = parse_args("Build evidence_coordinate_mapping_table.tsv and evidence_source_manifest.tsv")
    ensure_output_dirs(args.interim_root, args.report_root)
    coordinate_rows = build_coordinate_mapping_rows(args.interim_root)
    source_rows = build_source_manifest_rows(args.repo_root)
    coordinate_out = args.interim_root / "evidence/evidence_coordinate_mapping_table.tsv"
    source_out = args.interim_root / "evidence/evidence_source_manifest.tsv"
    write_tsv(coordinate_out, coordinate_rows, EVIDENCE_COORDINATE_MAPPING_FIELDS)
    write_tsv(source_out, source_rows, EVIDENCE_SOURCE_MANIFEST_FIELDS)
    write_tsv(args.report_root / "evidence_coordinate_mapping_table.preview.tsv", coordinate_rows[:500], EVIDENCE_COORDINATE_MAPPING_FIELDS)
    write_tsv(args.report_root / "evidence_source_manifest.tsv", source_rows, EVIDENCE_SOURCE_MANIFEST_FIELDS)
    print_summary("evidence_coordinate_mapping_table", coordinate_rows, f"evidence_source_manifest_rows={len(source_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
