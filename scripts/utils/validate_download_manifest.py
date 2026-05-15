#!/usr/bin/env python3
"""Validate Phase 2 download_manifest.tsv without touching raw data."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = [
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

ALLOWED_STATUS = {"planned", "downloading", "downloaded", "failed", "skipped"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Download manifest not found: {path}"]

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            return [f"Missing required columns: {', '.join(missing)}"]
        rows = list(reader)

    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        download_id = row.get("download_id", "").strip()
        if not download_id:
            errors.append(f"Line {line_number}: download_id is empty")
        elif download_id in seen:
            errors.append(f"Line {line_number}: duplicate download_id {download_id}")
        seen.add(download_id)

        if not row.get("source_id", "").strip():
            errors.append(f"Line {line_number}: source_id is empty")

        if not row.get("local_path", "").strip():
            errors.append(f"Line {line_number}: local_path is empty")

        status = row.get("download_status", "").strip()
        if status not in ALLOWED_STATUS:
            errors.append(f"Line {line_number}: invalid download_status {status!r}")

        checksum = row.get("checksum_sha256", "").strip()
        file_size = row.get("file_size_bytes", "").strip()
        if status == "planned" and checksum:
            errors.append(f"Line {line_number}: planned record must not have checksum_sha256")

        if status == "downloaded":
            if not file_size:
                errors.append(f"Line {line_number}: downloaded record missing file_size_bytes")
            if not checksum:
                errors.append(f"Line {line_number}: downloaded record missing checksum_sha256")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: python scripts/utils/validate_download_manifest.py "
            "manifest/download_manifest.tsv",
            file=sys.stderr,
        )
        return 2

    errors = validate(Path(argv[1]))
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print("[OK] download manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

