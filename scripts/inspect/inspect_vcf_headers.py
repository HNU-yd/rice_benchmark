#!/usr/bin/env python3
"""Inspect VCF headers and sample IDs without full VCF parsing."""

from __future__ import annotations

from pathlib import Path

from inventory_utils import INTERIM_DIR, RAW_ROOT, REPORT_DIR, compact_list, ensure_dirs, open_text, unique_preserve, write_tsv


VCF_FIELDS = [
    "file_path",
    "variant_type_guess",
    "sample_count",
    "first_samples",
    "has_tbi",
    "contig_header_count",
    "first_observed_chroms",
    "reference_build_guess",
    "notes",
]
SAMPLE_FIELDS = ["source_file", "sample_id", "sample_order"]


def inspect_vcf(path: Path) -> tuple[dict[str, object], list[dict[str, object]], list[str]]:
    samples: list[str] = []
    contigs: list[str] = []
    observed_chroms: list[str] = []
    n_data_seen = 0
    header_found = False
    with open_text(path) as handle:
        for line in handle:
            if line.startswith("##contig="):
                contigs.append(line.strip())
                continue
            if line.startswith("#CHROM"):
                header_found = True
                parts = line.rstrip("\n").split("\t")
                samples = parts[9:] if len(parts) > 9 else []
                continue
            if line.startswith("#"):
                continue
            if n_data_seen < 200:
                parts = line.rstrip("\n").split("\t")
                if parts:
                    observed_chroms.append(parts[0])
                n_data_seen += 1
            else:
                break

    sample_rows = [
        {"source_file": str(path), "sample_id": sample, "sample_order": index}
        for index, sample in enumerate(samples, start=1)
    ]
    chrom_values = unique_preserve(observed_chroms, 20)
    row = {
        "file_path": str(path),
        "variant_type_guess": "snp_or_pseudo_snp_vcf",
        "sample_count": len(samples),
        "first_samples": compact_list(samples, 10),
        "has_tbi": "yes" if Path(str(path) + ".tbi").exists() else "no",
        "contig_header_count": len(contigs),
        "first_observed_chroms": compact_list(chrom_values, 20),
        "reference_build_guess": "Nipponbare / IRGSP-1.0; naming appears numeric" if chrom_values else "unknown",
        "notes": "header_found=yes" if header_found else "header_found=no",
    }
    return row, sample_rows, chrom_values


def main() -> int:
    ensure_dirs()
    vcf_rows: list[dict[str, object]] = []
    sample_rows: list[dict[str, object]] = []
    for path in sorted((RAW_ROOT / "variants").rglob("*.vcf.gz")):
        row, samples, _chroms = inspect_vcf(path)
        vcf_rows.append(row)
        sample_rows.extend(samples)
    write_tsv(REPORT_DIR / "snp_file_inventory.tsv", vcf_rows, VCF_FIELDS)
    write_tsv(INTERIM_DIR / "snp_samples.tsv", sample_rows, SAMPLE_FIELDS)
    print(f"vcf_files={len(vcf_rows)}")
    print(f"vcf_samples={len(sample_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
