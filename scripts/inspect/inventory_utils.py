#!/usr/bin/env python3
"""Shared helpers for Phase 3 raw data inventory scripts."""

from __future__ import annotations

import csv
import gzip
import re
from pathlib import Path
from typing import Iterable


RAW_ROOT = Path("data/raw")
REPORT_DIR = Path("reports/raw_data_inventory")
INTERIM_DIR = Path("data/interim/inventory")


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)


def write_tsv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def extension_for(path: Path) -> str:
    name = path.name.lower()
    for ext in (".tar.gz", ".vcf.gz", ".bed.gz", ".bim.gz", ".fam.gz", ".fna.gz", ".gff.gz", ".txt.gz"):
        if name.endswith(ext):
            return ext
    return path.suffix.lower()


def infer_category(path_or_name: str) -> str:
    lower = path_or_name.lower()
    if "reference" in lower or lower.endswith((".fna.gz", ".fa.gz", ".fasta.gz")):
        return "reference"
    if "gff" in lower or "annotation" in lower:
        return "annotation"
    if "phenotype" in lower or "trait" in lower:
        return "trait_table"
    if "evidence" in lower or "qtl" in lower or "gwas" in lower or "known_genes" in lower or "oryzabase" in lower:
        return "weak_evidence"
    if "indel" in lower:
        return "indel_genotype"
    if "snp" in lower or "core" in lower or lower.endswith((".vcf.gz", ".bim.gz", ".fam.gz", ".bed.gz", ".ped", ".map")):
        return "snp_genotype"
    if "rice_rp" in lower or "qmatrix" in lower or "manifest" in lower or "download" in lower:
        return "accession_metadata"
    if "readme" in lower or "license" in lower:
        return "metadata"
    if "listing" in lower or "aws_3kricegenome" in lower:
        return "listing_metadata"
    return "metadata"


def normalize_id(value: str) -> str:
    value = str(value or "").strip().strip('"').strip("'")
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[-_.]+v\d+$", "", value, flags=re.I)
    value = re.sub(r"[^A-Za-z0-9]+", "", value)
    return value.upper()


def compact_list(values: Iterable[object], limit: int = 20) -> str:
    items = [str(v) for v in values if str(v) != ""]
    if len(items) <= limit:
        return ",".join(items)
    return ",".join(items[:limit]) + f",...(+{len(items) - limit})"


def unique_preserve(values: Iterable[object], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = str(value)
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
        if limit is not None and len(out) >= limit:
            break
    return out


def read_checksum_paths() -> set[str]:
    rows = read_tsv(Path("manifest/checksum_table.tsv"))
    return {row.get("local_path", "") for row in rows if row.get("local_path")}
