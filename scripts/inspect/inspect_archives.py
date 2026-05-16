#!/usr/bin/env python3
"""List archive contents without full extraction."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from inventory_utils import RAW_ROOT, REPORT_DIR, ensure_dirs, extension_for, infer_category, write_tsv


FIELDS = [
    "archive_path",
    "member_name",
    "member_size_bytes",
    "member_extension",
    "inferred_member_category",
    "extract_recommended",
    "notes",
]

EXTRACT_EXTS = {".txt", ".csv", ".tsv", ".xls", ".xlsx", ".fam", ".bim", ".map", ".html", ".htm"}
MAX_EXTRACT_RECOMMEND_BYTES = 20 * 1024 * 1024


def member_extension(name: str) -> str:
    lower = name.lower()
    for ext in (".tar.gz", ".vcf.gz", ".bed.gz", ".bim.gz", ".fam.gz", ".txt.gz"):
        if lower.endswith(ext):
            return ext
    return Path(name).suffix.lower()


def extract_recommended(name: str, size: int) -> tuple[str, str]:
    ext = member_extension(name)
    if size <= 0:
        return "no", "directory_or_empty_member"
    if ext in EXTRACT_EXTS and size <= MAX_EXTRACT_RECOMMEND_BYTES:
        return "yes", "small_metadata_or_plink_map_member"
    if ext in {".bed", ".ped", ".vcf", ".vcf.gz", ".bed.gz"}:
        return "no", "large_genotype_member_not_extracted"
    if size > MAX_EXTRACT_RECOMMEND_BYTES:
        return "no", "member_larger_than_metadata_threshold"
    return "no", "not_needed_for_phase3_inventory"


def inspect_tar(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with tarfile.open(path, "r:gz") as tar:
        for member in tar.getmembers():
            rec, note = extract_recommended(member.name, member.size)
            rows.append(
                {
                    "archive_path": str(path),
                    "member_name": member.name,
                    "member_size_bytes": member.size,
                    "member_extension": member_extension(member.name),
                    "inferred_member_category": infer_category(f"{path}/{member.name}"),
                    "extract_recommended": rec,
                    "notes": note,
                }
            )
    return rows


def inspect_zip(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            rec, note = extract_recommended(member.filename, member.file_size)
            rows.append(
                {
                    "archive_path": str(path),
                    "member_name": member.filename,
                    "member_size_bytes": member.file_size,
                    "member_extension": member_extension(member.filename),
                    "inferred_member_category": infer_category(f"{path}/{member.filename}"),
                    "extract_recommended": rec,
                    "notes": note,
                }
            )
    return rows


def main() -> int:
    ensure_dirs()
    rows: list[dict[str, object]] = []
    for path in sorted(RAW_ROOT.rglob("*")):
        if not path.is_file():
            continue
        ext = extension_for(path)
        if ext == ".tar.gz":
            rows.extend(inspect_tar(path))
        elif ext == ".zip":
            rows.extend(inspect_zip(path))
    write_tsv(REPORT_DIR / "archive_contents.tsv", rows, FIELDS)
    print(f"archive_members={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
