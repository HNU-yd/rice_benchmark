#!/usr/bin/env python3
"""Inspect PLINK-style raw files and collect sample IDs."""

from __future__ import annotations

import gzip
from collections import defaultdict
from pathlib import Path

from inventory_utils import INTERIM_DIR, RAW_ROOT, REPORT_DIR, compact_list, ensure_dirs, unique_preserve, write_tsv


PLINK_FIELDS = [
    "file_group",
    "data_category_guess",
    "fam_path",
    "bim_path",
    "bed_path",
    "sample_count",
    "variant_count",
    "chrom_values",
    "first_samples",
    "first_variants",
    "notes",
]
SAMPLE_FIELDS = ["source_file", "sample_id", "sample_order"]


def group_key(path: Path) -> str:
    name = path.name
    for suffix in (".fam.gz", ".bim.gz", ".bed.gz"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def read_fam(path: Path) -> list[str]:
    samples: list[str] = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) >= 2:
                samples.append(parts[1])
            elif parts:
                samples.append(parts[0])
    return samples


def read_bim(path: Path) -> tuple[int, list[str], list[str]]:
    variant_count = 0
    chroms: list[str] = []
    seen_chroms: set[str] = set()
    first_variants: list[str] = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            variant_count += 1
            if parts[0] not in seen_chroms and len(chroms) < 100:
                chroms.append(parts[0])
                seen_chroms.add(parts[0])
            if len(first_variants) < 10:
                first_variants.append(parts[1])
    return variant_count, chroms, first_variants


def main() -> int:
    ensure_dirs()
    groups: dict[str, dict[str, Path]] = defaultdict(dict)
    for path in sorted((RAW_ROOT / "variants").rglob("*.gz")):
        if path.name.endswith(".fam.gz"):
            groups[group_key(path)]["fam"] = path
        elif path.name.endswith(".bim.gz"):
            groups[group_key(path)]["bim"] = path
        elif path.name.endswith(".bed.gz"):
            groups[group_key(path)]["bed"] = path

    rows: list[dict[str, object]] = []
    plink_samples: list[dict[str, object]] = []
    indel_samples: list[dict[str, object]] = []
    snp_samples: list[dict[str, object]] = []
    for key, files in sorted(groups.items()):
        fam_path = files.get("fam")
        bim_path = files.get("bim")
        bed_path = files.get("bed")
        category = "indel_genotype" if "indel" in key.lower() else "snp_genotype"
        samples: list[str] = read_fam(fam_path) if fam_path else []
        variant_count = 0
        chroms: list[str] = []
        first_variants: list[str] = []
        if bim_path:
            variant_count, chroms, first_variants = read_bim(bim_path)
        source_for_samples = str(fam_path or bim_path or bed_path or key)
        sample_rows = [
            {"source_file": source_for_samples, "sample_id": sample, "sample_order": index}
            for index, sample in enumerate(samples, start=1)
        ]
        plink_samples.extend(sample_rows)
        if category == "indel_genotype":
            indel_samples.extend(sample_rows)
        else:
            snp_samples.extend(sample_rows)
        rows.append(
            {
                "file_group": key,
                "data_category_guess": category,
                "fam_path": str(fam_path or ""),
                "bim_path": str(bim_path or ""),
                "bed_path": str(bed_path or ""),
                "sample_count": len(samples),
                "variant_count": variant_count,
                "chrom_values": compact_list(chroms, 50),
                "first_samples": compact_list(samples, 10),
                "first_variants": compact_list(first_variants, 10),
                "notes": "bed_not_parsed_binary_only_presence_recorded" if bed_path else "",
            }
        )

    existing_snp_samples = []
    snp_samples_path = INTERIM_DIR / "snp_samples.tsv"
    if snp_samples_path.exists():
        import csv

        with snp_samples_path.open("r", encoding="utf-8", newline="") as handle:
            existing_snp_samples = list(csv.DictReader(handle, delimiter="\t"))
    write_tsv(REPORT_DIR / "plink_file_inventory.tsv", rows, PLINK_FIELDS)
    write_tsv(
        REPORT_DIR / "indel_file_inventory.tsv",
        [row for row in rows if row["data_category_guess"] == "indel_genotype"],
        PLINK_FIELDS,
    )
    write_tsv(INTERIM_DIR / "plink_samples.tsv", plink_samples, SAMPLE_FIELDS)
    write_tsv(INTERIM_DIR / "indel_samples.tsv", indel_samples, SAMPLE_FIELDS)
    write_tsv(INTERIM_DIR / "snp_samples.tsv", existing_snp_samples + snp_samples, SAMPLE_FIELDS)
    print(f"plink_groups={len(rows)}")
    print(f"plink_samples={len(plink_samples)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
