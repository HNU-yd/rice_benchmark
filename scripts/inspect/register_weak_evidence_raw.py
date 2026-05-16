#!/usr/bin/env python3
"""Register existing weak evidence raw files in manifests."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DOWNLOAD_MANIFEST = Path("manifest/download_manifest.tsv")
CHECKSUM_TABLE = Path("manifest/checksum_table.tsv")

DOWNLOAD_FIELDS = [
    "download_id",
    "source_id",
    "data_category",
    "file_role",
    "original_filename",
    "local_path",
    "download_url_or_access_method",
    "access_method_type",
    "download_command",
    "download_status",
    "file_size_bytes",
    "checksum_sha256",
    "download_started_at",
    "download_finished_at",
    "source_version",
    "reference_build",
    "notes",
]

CHECKSUM_FIELDS = [
    "file_id",
    "download_id",
    "source_id",
    "local_path",
    "checksum_algorithm",
    "checksum_value",
    "file_size_bytes",
    "computed_at",
    "verification_status",
    "notes",
]

WEAK_EVIDENCE_FILES = [
    {
        "download_id": "DL_WEAK_ORYZABASE_GENE_001",
        "file_id": "FILE_WEAK_ORYZABASE_GENE_001",
        "source_id": "SRC_WEAK_ORYZABASE_GENE_001",
        "data_category": "weak_evidence",
        "file_role": "known_trait_gene_list",
        "local_path": "data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv",
        "source_version": "to_be_confirmed",
        "reference_build": "mixed_or_to_be_confirmed",
        "notes": (
            "Phase 3C registration; Oryzabase known/cloned trait gene candidate; "
            "weak localization evidence only"
        ),
    },
    {
        "download_id": "DL_WEAK_QTARO_QTL_001",
        "file_id": "FILE_WEAK_QTARO_QTL_001",
        "source_id": "SRC_WEAK_QTARO_QTL_001",
        "data_category": "weak_evidence",
        "file_role": "qtl_interval_archive",
        "local_path": "data/raw/evidence/qtl/qtaro/qtaro_sjis.zip",
        "source_version": "to_be_confirmed",
        "reference_build": "to_be_confirmed",
        "notes": (
            "Phase 3C registration; Q-TARO QTL interval archive candidate; "
            "weak localization evidence only"
        ),
    },
]


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
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


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_unique(rows: list[dict[str, str]], field: str, table_name: str) -> None:
    counts = Counter(row.get(field, "") for row in rows)
    duplicates = sorted(value for value, count in counts.items() if value and count > 1)
    if duplicates:
        raise ValueError(f"{table_name} has duplicate {field}: {', '.join(duplicates)}")


def upsert(rows: list[dict[str, str]], key_field: str, new_row: dict[str, object]) -> None:
    key = str(new_row[key_field])
    for index, row in enumerate(rows):
        if row.get(key_field) == key:
            rows[index] = {field: str(new_row.get(field, "")) for field in row.keys() | new_row.keys()}
            return
    rows.append({field: str(value) for field, value in new_row.items()})


def main() -> int:
    download_fields, download_rows = read_tsv(DOWNLOAD_MANIFEST)
    checksum_fields, checksum_rows = read_tsv(CHECKSUM_TABLE)
    download_fields = download_fields or DOWNLOAD_FIELDS
    checksum_fields = checksum_fields or CHECKSUM_FIELDS

    missing_download_fields = [field for field in DOWNLOAD_FIELDS if field not in download_fields]
    missing_checksum_fields = [field for field in CHECKSUM_FIELDS if field not in checksum_fields]
    if missing_download_fields:
        raise ValueError(f"download manifest missing columns: {', '.join(missing_download_fields)}")
    if missing_checksum_fields:
        raise ValueError(f"checksum table missing columns: {', '.join(missing_checksum_fields)}")

    timestamp = datetime.now(timezone.utc).isoformat()
    registered = 0
    for item in WEAK_EVIDENCE_FILES:
        path = Path(item["local_path"])
        if not path.exists():
            raise FileNotFoundError(f"raw weak evidence file not found: {path}")
        checksum = sha256sum(path)
        size = path.stat().st_size
        filename = path.name

        download_row = {
            "download_id": item["download_id"],
            "source_id": item["source_id"],
            "data_category": item["data_category"],
            "file_role": item["file_role"],
            "original_filename": filename,
            "local_path": item["local_path"],
            "download_url_or_access_method": "manual_local_registration_from_existing_raw_file",
            "access_method_type": "manual",
            "download_command": "no new download; Phase 3C registered existing raw file",
            "download_status": "downloaded",
            "file_size_bytes": size,
            "checksum_sha256": checksum,
            "download_started_at": "",
            "download_finished_at": timestamp,
            "source_version": item["source_version"],
            "reference_build": item["reference_build"],
            "notes": item["notes"],
        }
        checksum_row = {
            "file_id": item["file_id"],
            "download_id": item["download_id"],
            "source_id": item["source_id"],
            "local_path": item["local_path"],
            "checksum_algorithm": "sha256",
            "checksum_value": checksum,
            "file_size_bytes": size,
            "computed_at": timestamp,
            "verification_status": "verified",
            "notes": "computed by register_weak_evidence_raw.py",
        }

        upsert(download_rows, "download_id", download_row)
        upsert(checksum_rows, "local_path", checksum_row)
        registered += 1

    ensure_unique(download_rows, "download_id", "download_manifest.tsv")
    ensure_unique(checksum_rows, "local_path", "checksum_table.tsv")

    write_tsv(DOWNLOAD_MANIFEST, download_fields, download_rows)
    write_tsv(CHECKSUM_TABLE, checksum_fields, checksum_rows)
    print(f"registered_weak_evidence_raw_files={registered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
