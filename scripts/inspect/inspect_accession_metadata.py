#!/usr/bin/env python3
"""Inspect downloaded accession metadata candidates."""

from __future__ import annotations

import csv
import tarfile
from pathlib import Path

from inventory_utils import INTERIM_DIR, RAW_ROOT, REPORT_DIR, compact_list, ensure_dirs, unique_preserve, write_tsv


INVENTORY_FIELDS = [
    "source_file",
    "extracted_file",
    "n_rows",
    "n_cols",
    "columns",
    "candidate_accession_columns",
    "candidate_subpopulation_columns",
    "candidate_country_columns",
    "n_candidate_accessions",
    "notes",
]
ACCESSION_FIELDS = ["source_file", "accession_candidate", "accession_column", "row_id"]

MAX_EXTRACT_BYTES = 5 * 1024 * 1024
EXTRACTED_DIR = INTERIM_DIR / "extracted_metadata"


def extract_small_metadata_from_tar(path: Path) -> list[Path]:
    extracted: list[Path] = []
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.isdir() or member.size <= 0 or member.size > MAX_EXTRACT_BYTES:
                continue
            lower = member.name.lower()
            if not lower.endswith((".txt", ".csv", ".tsv", ".xls", ".xlsx", ".fam")):
                continue
            target = EXTRACTED_DIR / member.name.replace("/", "__")
            source = tar.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as handle:
                handle.write(source.read())
            extracted.append(target)
    return extracted


def inspect_fam(source_file: Path, extracted_file: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    with extracted_file.open("r", encoding="utf-8", errors="replace") as handle:
        for row_id, line in enumerate(handle, start=1):
            parts = line.strip().split()
            if len(parts) >= 2:
                rows.append(
                    {
                        "source_file": str(source_file),
                        "accession_candidate": parts[1],
                        "accession_column": "IID",
                        "row_id": row_id,
                    }
                )
    unique_ids = unique_preserve(row["accession_candidate"] for row in rows)
    inv = {
        "source_file": str(source_file),
        "extracted_file": str(extracted_file),
        "n_rows": len(rows),
        "n_cols": 6,
        "columns": "FID,IID,paternal_id,maternal_id,sex,phenotype",
        "candidate_accession_columns": "IID",
        "candidate_subpopulation_columns": "",
        "candidate_country_columns": "",
        "n_candidate_accessions": len(unique_ids),
        "notes": "FAM extracted from archive; IDs require mapping to phenotype/accession metadata",
    }
    return inv, rows


def inspect_qmatrix(path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    id_col = "id" if "id" in fieldnames else (fieldnames[0] if fieldnames else "")
    accession_rows = [
        {
            "source_file": str(path),
            "accession_candidate": row.get(id_col, ""),
            "accession_column": id_col,
            "row_id": index,
        }
        for index, row in enumerate(rows, start=2)
        if row.get(id_col, "")
    ]
    inv = {
        "source_file": str(path),
        "extracted_file": "",
        "n_rows": len(rows) + 1,
        "n_cols": len(fieldnames),
        "columns": compact_list(fieldnames, 80),
        "candidate_accession_columns": id_col,
        "candidate_subpopulation_columns": compact_list([name for name in fieldnames if name != id_col], 30),
        "candidate_country_columns": "",
        "n_candidate_accessions": len(unique_preserve(row["accession_candidate"] for row in accession_rows)),
        "notes": "Qmatrix population structure metadata; not a complete passport table",
    }
    return inv, accession_rows


def inspect_readme_like(path: Path) -> dict[str, object]:
    try:
        n_rows = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
    except UnicodeDecodeError:
        n_rows = 0
    return {
        "source_file": str(path),
        "extracted_file": "",
        "n_rows": n_rows,
        "n_cols": "",
        "columns": "",
        "candidate_accession_columns": "",
        "candidate_subpopulation_columns": "",
        "candidate_country_columns": "",
        "n_candidate_accessions": 0,
        "notes": "description_or_manifest_file; inspect manually if needed",
    }


def main() -> int:
    ensure_dirs()
    inventory_rows: list[dict[str, object]] = []
    accession_rows: list[dict[str, object]] = []

    rice_rp = RAW_ROOT / "accessions" / "RICE_RP.tar.gz"
    if rice_rp.exists():
        for extracted in extract_small_metadata_from_tar(rice_rp):
            if extracted.name.lower().endswith(".fam"):
                inv, rows = inspect_fam(rice_rp, extracted)
                inventory_rows.append(inv)
                accession_rows.extend(rows)
            else:
                inventory_rows.append(inspect_readme_like(extracted))

    qmatrix = RAW_ROOT / "metadata" / "Qmatrix-k9-3kRG.csv"
    if qmatrix.exists():
        inv, rows = inspect_qmatrix(qmatrix)
        inventory_rows.append(inv)
        accession_rows.extend(rows)

    for path in sorted((RAW_ROOT / "metadata").glob("README*")) + sorted((RAW_ROOT / "metadata").glob("*download*.htm*")):
        inventory_rows.append(inspect_readme_like(path))

    write_tsv(REPORT_DIR / "accession_metadata_inventory.tsv", inventory_rows, INVENTORY_FIELDS)
    write_tsv(INTERIM_DIR / "metadata_accessions.tsv", accession_rows, ACCESSION_FIELDS)
    print(f"accession_metadata_sources={len(inventory_rows)}")
    print(f"metadata_accession_candidates={len(unique_preserve(row['accession_candidate'] for row in accession_rows))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
