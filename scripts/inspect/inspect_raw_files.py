#!/usr/bin/env python3
"""Scan downloaded raw files and verify checksum registration."""

from __future__ import annotations

from pathlib import Path

from inventory_utils import RAW_ROOT, REPORT_DIR, ensure_dirs, extension_for, infer_category, read_checksum_paths, size_mb, write_tsv


FIELDS = [
    "file_id",
    "local_path",
    "relative_path",
    "filename",
    "file_size_bytes",
    "file_size_mb",
    "extension",
    "inferred_category",
    "is_compressed",
    "is_archive",
    "checksum_status",
    "notes",
]


def main() -> int:
    ensure_dirs()
    checksum_paths = read_checksum_paths()
    rows: list[dict[str, object]] = []
    files = sorted(path for path in RAW_ROOT.rglob("*") if path.is_file())
    for index, path in enumerate(files, start=1):
        ext = extension_for(path)
        local_path = str(path)
        rows.append(
            {
                "file_id": f"RAW_{index:04d}",
                "local_path": local_path,
                "relative_path": str(path.relative_to(RAW_ROOT)),
                "filename": path.name,
                "file_size_bytes": path.stat().st_size,
                "file_size_mb": f"{size_mb(path):.3f}",
                "extension": ext,
                "inferred_category": infer_category(local_path),
                "is_compressed": "yes" if ext.endswith(".gz") or ext == ".zip" else "no",
                "is_archive": "yes" if ext in {".tar.gz", ".zip"} else "no",
                "checksum_status": "registered" if local_path in checksum_paths else "missing",
                "notes": "raw data ignored by git",
            }
        )
    write_tsv(REPORT_DIR / "raw_file_inventory.tsv", rows, FIELDS)
    print(f"raw_files={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
