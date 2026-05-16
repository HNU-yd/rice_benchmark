#!/usr/bin/env python3
"""Build chr1 sliding windows and SNP-to-window mapping for v0.1-mini."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/v0_1_mini"
REPORT_DIR = REPO_ROOT / "reports/v0_1_mini"
REFERENCE_INVENTORY = REPO_ROOT / "reports/raw_data_inventory/reference_inventory.tsv"
REFERENCE_FASTA = REPO_ROOT / "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz"
VARIANT_TABLE = INTERIM_DIR / "variant_table_chr1_snp_v0_1.tsv"

CHROM = "1"
REFSEQ_CHROM = "NC_029256.1"
WINDOW_SIZE = 100000
STRIDE = 50000

WINDOW_FIELDS = ["window_id", "chrom", "refseq_chrom", "start", "end", "window_size", "stride", "n_snp", "notes"]
MAPPING_FIELDS = ["variant_id", "window_id", "chrom", "refseq_chrom", "pos", "relative_position_in_window", "variant_type", "notes"]
SUMMARY_FIELDS = [
    "chrom",
    "refseq_chrom",
    "reference_length",
    "window_size",
    "stride",
    "n_windows",
    "n_variants",
    "n_variant_window_mapping_rows",
    "notes",
]


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})


def reference_length() -> int:
    if REFERENCE_INVENTORY.exists():
        with REFERENCE_INVENTORY.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row.get("seq_name") == REFSEQ_CHROM:
                    return int(row["seq_length"])
    current = ""
    length = 0
    with gzip.open(REFERENCE_FASTA, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith(">"):
                if current == REFSEQ_CHROM:
                    return length
                current = line[1:].split()[0]
                length = 0
            elif current == REFSEQ_CHROM:
                length += len(line.strip())
    if current == REFSEQ_CHROM:
        return length
    raise RuntimeError(f"cannot determine reference length for {REFSEQ_CHROM}")


def read_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with VARIANT_TABLE.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append({**row, "pos_int": int(row["pos"])})
    rows.sort(key=lambda row: int(row["pos_int"]))
    return rows


def build_windows(seq_length: int) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    start = 1
    while start <= seq_length:
        end = min(start + WINDOW_SIZE - 1, seq_length)
        windows.append(
            {
                "window_id": f"chr1_{start}_{end}",
                "chrom": CHROM,
                "refseq_chrom": REFSEQ_CHROM,
                "start": start,
                "end": end,
                "window_size": WINDOW_SIZE,
                "stride": STRIDE,
                "n_snp": 0,
                "notes": "1-based inclusive sliding window for chr1 SNP-only prototype",
            }
        )
        if end == seq_length:
            break
        start += STRIDE
    return windows


def main() -> int:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    seq_length = reference_length()
    variants = read_variants()
    windows = build_windows(seq_length)
    mapping_rows: list[dict[str, object]] = []
    for variant in variants:
        pos = int(variant["pos_int"])
        # At most three windows are relevant with current overlap; check a small local range.
        approx_idx = max(0, (pos - 1) // STRIDE - 2)
        for window in windows[approx_idx : min(len(windows), approx_idx + 6)]:
            start = int(window["start"])
            end = int(window["end"])
            if start <= pos <= end:
                window["n_snp"] = int(window["n_snp"]) + 1
                mapping_rows.append(
                    {
                        "variant_id": variant["variant_id"],
                        "window_id": window["window_id"],
                        "chrom": CHROM,
                        "refseq_chrom": REFSEQ_CHROM,
                        "pos": pos,
                        "relative_position_in_window": pos - start + 1,
                        "variant_type": "SNP",
                        "notes": "SNP may map to multiple overlapping windows; unknown is not negative",
                    }
                )
    summary = [
        {
            "chrom": CHROM,
            "refseq_chrom": REFSEQ_CHROM,
            "reference_length": seq_length,
            "window_size": WINDOW_SIZE,
            "stride": STRIDE,
            "n_windows": len(windows),
            "n_variants": len(variants),
            "n_variant_window_mapping_rows": len(mapping_rows),
            "notes": "windows are 1-based inclusive; no label semantics assigned here",
        }
    ]
    write_tsv(INTERIM_DIR / "window_table_chr1_v0_1.tsv", windows, WINDOW_FIELDS)
    write_tsv(INTERIM_DIR / "variant_window_mapping_chr1_v0_1.tsv", mapping_rows, MAPPING_FIELDS)
    write_tsv(REPORT_DIR / "window_table_chr1_summary.tsv", summary, SUMMARY_FIELDS)
    print(f"chr1_windows={len(windows)}")
    print(f"variant_window_mapping_rows={len(mapping_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
