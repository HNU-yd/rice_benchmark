#!/usr/bin/env python3
"""Summarize current local data assets without modifying raw data."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


RAW_ROOT = Path("data/raw")
REPORT_DIR = Path("reports/current_data_status")
DATAVERSE_DIR = Path("reports/dataverse_sanciangco")
DOWNLOAD_MANIFEST = Path("manifest/download_manifest.tsv")
CHECKSUM_TABLE = Path("manifest/checksum_table.tsv")

RAW_FIELDS = [
    "file_path",
    "file_name",
    "file_size_bytes",
    "file_size_mb",
    "data_category_guess",
    "format_guess",
    "checksum_registered",
    "notes",
]

CATEGORY_FIELDS = [
    "data_category",
    "n_files",
    "total_size_bytes",
    "total_size_gb",
    "key_files",
    "status",
    "notes",
]

CHECKSUM_STATUS_FIELDS = [
    "file_path",
    "file_name",
    "in_download_manifest",
    "in_checksum_table",
    "download_id",
    "source_id",
    "download_status",
    "file_size_bytes",
    "manifest_file_size_bytes",
    "checksum_sha256",
    "checksum_value",
    "status",
    "notes",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
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


def compact(values: list[str], limit: int = 8) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return ",".join(seen)
    return ",".join(seen[:limit]) + f",...(+{len(seen) - limit})"


def format_guess(path: Path) -> str:
    name = path.name.lower()
    for suffix in (".tar.gz", ".vcf.gz", ".bed.gz", ".bim.gz", ".fam.gz", ".txt.gz", ".csv.gz", ".fna.gz", ".gff.gz"):
        if name.endswith(suffix):
            return suffix
    return path.suffix.lower() or "no_extension"


def category_guess(path: Path) -> str:
    text = str(path).lower()
    name = path.name.lower()
    if "/listings/" in text:
        return "listing / metadata"
    if "oryzabase" in text:
        return "Oryzabase"
    if "qtaro" in text:
        return "Q-TARO"
    if "qmatrix" in name:
        return "Qmatrix / population structure"
    if "genesys" in text or "prjeb6180" in text or "3k_list_sra" in name:
        return "accession metadata"
    if "/accessions/" in text:
        return "accession metadata"
    if "/traits/" in text or "phenotype" in name:
        return "phenotype / trait"
    if "/variants/snp/pruned" in text or "pruned" in name:
        return "pruned SNP"
    if "/variants/snp/" in text or "snp" in name:
        return "SNP genotype"
    if "/variants/indel/" in text or "indel" in name:
        return "indel genotype"
    if name.endswith(".gff.gz") or "annotation" in text:
        return "annotation"
    if name.endswith((".fna.gz", ".fa.gz", ".fasta.gz")) or "/reference/" in text:
        return "reference"
    if "/metadata/" in text or "/checksums/" in text:
        return "listing / metadata"
    return "other"


def category_status(category: str, n_files: int) -> tuple[str, str]:
    if n_files == 0:
        return "missing", "当前未发现本地文件。"
    notes = {
        "reference": "IRGSP-1.0 FASTA 已在本地，可用于 reference window 后续构建。",
        "annotation": "GFF3 annotation 已在本地，但 RAP/MSU/Gramene cross-reference 仍需补充。",
        "SNP genotype": "3K Rice SNP genotype backbone 已在本地；大型矩阵仍需按 v0.1 范围受控解析。",
        "indel genotype": "3K Rice indel PLINK 文件已在本地；需要与 SNP sample order 对齐。",
        "pruned SNP": "pruned SNP / LD-pruned PLINK 资产已在本地，可用于后续 GWAS 或降维检查。",
        "phenotype / trait": "3K phenotype XLSX 已在本地；只能用于 trait_state，不能作为 phenotype prediction target。",
        "accession metadata": "SNP-Seek SRA list、Genesys MCPD、NCBI RunInfo 等 accession mapping 资产已在本地。",
        "Qmatrix / population structure": "Qmatrix 已在本地，可作为 accession mapping 与自跑 GWAS covariate 候选。",
        "Oryzabase": "Oryzabase known/cloned trait genes 已在本地，只能作为 weak localization evidence。",
        "Q-TARO": "Q-TARO QTL interval archive 已在本地，只能作为 weak localization evidence。",
        "listing / metadata": "下载页、listing、README 和 checksum metadata 已在本地。",
        "Sanciangco / Dataverse": "当前仅登记 Dataverse metadata/selected file list；大规模 GWAS raw files 未下载。",
    }
    return "present", notes.get(category, "本地已有文件，需后续人工判定用途。")


def summarize_dataverse_assets() -> dict[str, object] | None:
    if not DATAVERSE_DIR.exists():
        return None
    files = sorted(path for path in DATAVERSE_DIR.glob("*") if path.is_file())
    if not files:
        return None
    total_size = sum(path.stat().st_size for path in files)
    return {
        "data_category": "Sanciangco / Dataverse",
        "n_files": len(files),
        "total_size_bytes": total_size,
        "total_size_gb": f"{total_size / (1024 ** 3):.6f}",
        "key_files": compact([str(path) for path in files], 8),
        "status": "metadata_only",
        "notes": "HGRSJG metadata 已登记；GWAS/PLINK 大文件未进入 data/raw，不阻塞当前阶段。",
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(path for path in RAW_ROOT.rglob("*") if path.is_file()) if RAW_ROOT.exists() else []
    download_rows = read_tsv(DOWNLOAD_MANIFEST)
    checksum_rows = read_tsv(CHECKSUM_TABLE)
    download_by_path = {row.get("local_path", ""): row for row in download_rows if row.get("local_path")}
    checksum_by_path = {row.get("local_path", ""): row for row in checksum_rows if row.get("local_path")}

    raw_summary: list[dict[str, object]] = []
    checksum_status: list[dict[str, object]] = []
    for path in raw_files:
        local_path = str(path)
        download_row = download_by_path.get(local_path, {})
        checksum_row = checksum_by_path.get(local_path, {})
        checksum_registered = "yes" if checksum_row else "no"
        size = path.stat().st_size
        manifest_size = download_row.get("file_size_bytes", "")
        status = "registered" if checksum_row else "missing_checksum"
        if checksum_row and str(size) != str(checksum_row.get("file_size_bytes", size)):
            status = "checksum_size_mismatch"
        elif download_row and manifest_size and str(size) != str(manifest_size):
            status = "manifest_size_mismatch"

        raw_summary.append(
            {
                "file_path": local_path,
                "file_name": path.name,
                "file_size_bytes": size,
                "file_size_mb": f"{size / (1024 ** 2):.3f}",
                "data_category_guess": category_guess(path),
                "format_guess": format_guess(path),
                "checksum_registered": checksum_registered,
                "notes": "raw data ignored by git",
            }
        )
        checksum_status.append(
            {
                "file_path": local_path,
                "file_name": path.name,
                "in_download_manifest": "yes" if download_row else "no",
                "in_checksum_table": "yes" if checksum_row else "no",
                "download_id": download_row.get("download_id", ""),
                "source_id": download_row.get("source_id", checksum_row.get("source_id", "")),
                "download_status": download_row.get("download_status", ""),
                "file_size_bytes": size,
                "manifest_file_size_bytes": manifest_size,
                "checksum_sha256": download_row.get("checksum_sha256", ""),
                "checksum_value": checksum_row.get("checksum_value", ""),
                "status": status,
                "notes": "current audit only; does not mutate manifest/checksum table",
            }
        )

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in raw_summary:
        grouped[str(row["data_category_guess"])].append(row)

    category_rows: list[dict[str, object]] = []
    for category in sorted(grouped):
        rows = grouped[category]
        total_size = sum(int(row["file_size_bytes"]) for row in rows)
        status, notes = category_status(category, len(rows))
        category_rows.append(
            {
                "data_category": category,
                "n_files": len(rows),
                "total_size_bytes": total_size,
                "total_size_gb": f"{total_size / (1024 ** 3):.6f}",
                "key_files": compact([str(row["file_path"]) for row in rows], 8),
                "status": status,
                "notes": notes,
            }
        )
    dataverse_row = summarize_dataverse_assets()
    if dataverse_row:
        category_rows.append(dataverse_row)

    write_tsv(REPORT_DIR / "current_raw_file_summary.tsv", raw_summary, RAW_FIELDS)
    write_tsv(REPORT_DIR / "current_data_category_summary.tsv", category_rows, CATEGORY_FIELDS)
    write_tsv(REPORT_DIR / "current_manifest_checksum_status.tsv", checksum_status, CHECKSUM_STATUS_FIELDS)
    print(f"current_raw_files={len(raw_summary)}")
    print(f"current_raw_size_bytes={sum(int(row['file_size_bytes']) for row in raw_summary)}")
    print(f"current_data_categories={len(category_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
