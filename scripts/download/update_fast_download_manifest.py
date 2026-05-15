#!/usr/bin/env python3
"""Update manifests from files downloaded under data/raw."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


RAW_ROOT = Path("data/raw")
REPORT_DIR = Path("reports/fast_download")
DOWNLOAD_MANIFEST = Path("manifest/download_manifest.tsv")
CHECKSUM_TABLE = Path("manifest/checksum_table.tsv")
CANDIDATES = REPORT_DIR / "auto_download_candidates.tsv"

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
FORBIDDEN = (".bam", ".cram", ".fastq", ".fq", ".sra")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
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
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_id_for(row: dict[str, str]) -> str:
    notes = row.get("notes", "")
    for token in notes.split(";"):
        token = token.strip()
        if token.startswith("source_id="):
            return token.split("=", 1)[1]
    category = row.get("data_category", "")
    if category == "snp_genotype":
        return "SRC_3K_SNP_GENOTYPE_001"
    if category == "indel_genotype":
        return "SRC_3K_INDEL_GENOTYPE_002"
    if category == "trait_table":
        return "SRC_TRAIT_TABLE_003"
    if category == "reference":
        return "SRC_REF_IRGSP_FASTA_003"
    if category == "annotation":
        return "SRC_REF_IRGSP_FASTA_003"
    if category == "accession_metadata":
        return "SRC_3K_ACCESSION_METADATA_001"
    return "auto_discovered"


def reference_build_for(row: dict[str, str]) -> str:
    category = row.get("data_category", "")
    remote = row.get("remote_path_or_url", "")
    if "IRGSP-1.0" in remote or "GCF_001433935.1" in remote:
        return "IRGSP-1.0"
    if category in {"snp_genotype", "indel_genotype"}:
        return "Nipponbare / IRGSP-1.0"
    return "to_be_confirmed"


def main() -> int:
    candidates = {row["local_path"]: row for row in read_tsv(CANDIDATES)}
    now = datetime.now(timezone.utc).isoformat()
    downloaded_rows: list[dict[str, str]] = []
    checksum_rows: list[dict[str, str]] = []

    if RAW_ROOT.exists():
        files = sorted(path for path in RAW_ROOT.rglob("*") if path.is_file())
    else:
        files = []

    for index, path in enumerate(files, start=1):
        if path.suffix.lower() in FORBIDDEN or any(part.lower() in {"bam", "cram", "fastq"} for part in path.parts):
            continue
        local_path = str(path)
        candidate = candidates.get(local_path, {})
        checksum = sha256(path)
        size = path.stat().st_size
        source_id = source_id_for(candidate)
        candidate_id = candidate.get("candidate_id", f"RAW_{index:04d}")
        download_id = f"FD_{candidate_id}"
        data_category = candidate.get("data_category", "auto_discovered")
        file_role = candidate.get("file_role", "auto_discovered")
        remote = candidate.get("remote_path_or_url", "unknown")
        access_method = candidate.get("access_method_type", "unknown")

        downloaded_rows.append(
            {
                "download_id": download_id,
                "source_id": source_id,
                "data_category": data_category,
                "file_role": file_role,
                "original_filename": path.name,
                "local_path": local_path,
                "download_url_or_access_method": remote,
                "access_method_type": access_method,
                "download_command": "fast_download_selected_data.sh --execute",
                "download_status": "downloaded",
                "file_size_bytes": str(size),
                "checksum_sha256": checksum,
                "download_started_at": "",
                "download_finished_at": now,
                "source_version": "to_be_confirmed",
                "reference_build": reference_build_for(candidate),
                "notes": "fast_download; source_id requires later curation" if source_id == "auto_discovered" else "fast_download",
            }
        )
        checksum_rows.append(
            {
                "file_id": f"FILE_{candidate_id}",
                "download_id": download_id,
                "source_id": source_id,
                "local_path": local_path,
                "checksum_algorithm": "sha256",
                "checksum_value": checksum,
                "file_size_bytes": str(size),
                "computed_at": now,
                "verification_status": "verified",
                "notes": "computed by update_fast_download_manifest.py",
            }
        )

    downloaded_local_paths = {row["local_path"] for row in downloaded_rows}
    existing_downloads = [
        row
        for row in read_tsv(DOWNLOAD_MANIFEST)
        if not (
            row.get("download_status") == "planned"
            and row.get("local_path") in downloaded_local_paths
        )
    ]
    existing_by_id = {row["download_id"]: row for row in existing_downloads if row.get("download_id")}
    for row in downloaded_rows:
        existing_by_id[row["download_id"]] = row
    write_tsv(DOWNLOAD_MANIFEST, list(existing_by_id.values()), DOWNLOAD_FIELDS)

    existing_checksums = read_tsv(CHECKSUM_TABLE)
    existing_checksum_by_file = {row["local_path"]: row for row in existing_checksums if row.get("local_path")}
    for row in checksum_rows:
        existing_checksum_by_file[row["local_path"]] = row
    write_tsv(CHECKSUM_TABLE, list(existing_checksum_by_file.values()), CHECKSUM_FIELDS)

    write_tsv(REPORT_DIR / "downloaded_files.tsv", downloaded_rows, DOWNLOAD_FIELDS)
    write_tsv(REPORT_DIR / "checksum_summary.tsv", checksum_rows, CHECKSUM_FIELDS)
    print(f"downloaded_files={len(downloaded_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
