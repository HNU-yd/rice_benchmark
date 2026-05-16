#!/usr/bin/env python3
"""Build fixed chromosome mapping for the v0.1-mini IRGSP-1.0 reference."""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/v0_1_mini"
REPORT_DIR = REPO_ROOT / "reports/v0_1_mini"
REFERENCE_BUILD = "IRGSP-1.0 / GCF_001433935.1"

CHROM_MAP = [
    ("1", "NC_029256.1"),
    ("2", "NC_029257.1"),
    ("3", "NC_029258.1"),
    ("4", "NC_029259.1"),
    ("5", "NC_029260.1"),
    ("6", "NC_029261.1"),
    ("7", "NC_029262.1"),
    ("8", "NC_029263.1"),
    ("9", "NC_029264.1"),
    ("10", "NC_029265.1"),
    ("11", "NC_029266.1"),
    ("12", "NC_029267.1"),
]

FIELDS = ["numeric_chrom", "refseq_chrom", "reference_build", "mapping_confidence", "notes"]


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "numeric_chrom": numeric,
            "refseq_chrom": refseq,
            "reference_build": REFERENCE_BUILD,
            "mapping_confidence": "fixed_from_IRGSP_1_0_RefSeq_primary_chromosomes",
            "notes": "manual fixed mapping for v0.1-mini; chromosome naming must remain explicit",
        }
        for numeric, refseq in CHROM_MAP
    ]
    write_tsv(INTERIM_DIR / "chromosome_map.tsv", rows, FIELDS)
    write_tsv(REPORT_DIR / "chromosome_map_report.tsv", rows, FIELDS)
    print(f"chromosome_map_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
