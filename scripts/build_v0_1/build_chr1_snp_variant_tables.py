#!/usr/bin/env python3
"""Build chr1 SNP variant tables from the 3K Rice core PLINK BIM file."""

from __future__ import annotations

import csv
import gzip
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/v0_1_mini"
REPORT_DIR = REPO_ROOT / "reports/v0_1_mini"
SNP_BIM = REPO_ROOT / "data/raw/variants/snp/core_v0.7.bim.gz"
CHROM_MAP = INTERIM_DIR / "chromosome_map.tsv"

VARIANT_FIELDS = [
    "variant_id",
    "chrom",
    "refseq_chrom",
    "pos",
    "plink_variant_id",
    "allele1",
    "allele2",
    "variant_type",
    "source_file",
    "notes",
]
SUMMARY_FIELDS = ["chrom", "refseq_chrom", "n_variants", "min_pos", "max_pos", "n_missing_pos", "n_duplicate_variant_id", "notes"]


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})


def read_chrom_map() -> dict[str, str]:
    with CHROM_MAP.open("r", encoding="utf-8", newline="") as handle:
        return {row["numeric_chrom"]: row["refseq_chrom"] for row in csv.DictReader(handle, delimiter="\t")}


def main() -> int:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    chrom_map = read_chrom_map()
    refseq = chrom_map["1"]
    rows: list[dict[str, object]] = []
    missing_pos = 0
    variant_ids: Counter[str] = Counter()
    positions: list[int] = []
    with gzip.open(SNP_BIM, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split()
            if len(parts) < 6:
                continue
            chrom, plink_id, _cm, pos_text, allele1, allele2 = parts[:6]
            if chrom != "1":
                continue
            try:
                pos = int(pos_text)
            except ValueError:
                pos = 0
                missing_pos += 1
            variant_id = f"chr1_{pos}_{plink_id}"
            variant_ids[variant_id] += 1
            if pos > 0:
                positions.append(pos)
            rows.append(
                {
                    "variant_id": variant_id,
                    "chrom": chrom,
                    "refseq_chrom": refseq,
                    "pos": pos_text,
                    "plink_variant_id": plink_id,
                    "allele1": allele1,
                    "allele2": allele2,
                    "variant_type": "SNP",
                    "source_file": str(SNP_BIM.relative_to(REPO_ROOT)),
                    "notes": "PLINK BIM allele1/allele2 orientation requires later validation; not ref/alt",
                }
            )
    duplicate_count = sum(1 for count in variant_ids.values() if count > 1)
    summary = [
        {
            "chrom": "1",
            "refseq_chrom": refseq,
            "n_variants": len(rows),
            "min_pos": min(positions) if positions else "",
            "max_pos": max(positions) if positions else "",
            "n_missing_pos": missing_pos,
            "n_duplicate_variant_id": duplicate_count,
            "notes": "chr1 SNP-only prototype; allele orientation requires later validation",
        }
    ]
    write_tsv(INTERIM_DIR / "variant_table_chr1_snp_v0_1.tsv", rows, VARIANT_FIELDS)
    write_tsv(INTERIM_DIR / "snp_table_chr1_v0_1.tsv", rows, VARIANT_FIELDS)
    write_tsv(REPORT_DIR / "variant_table_chr1_summary.tsv", summary, SUMMARY_FIELDS)
    print(f"chr1_snp_variants={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
