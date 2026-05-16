#!/usr/bin/env python3
"""Shared utilities for Phase 7A external knowledge collection.

This module is used by scripts in scripts/external_knowledge/.
Run the collection through:
  bash scripts/external_knowledge/run_collect_external_knowledge_07a.sh
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import mimetypes
import os
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DOWNLOAD_MANIFEST = REPO_ROOT / "manifest/download_manifest.tsv"
CHECKSUM_TABLE = REPO_ROOT / "manifest/checksum_table.tsv"
MAX_DOWNLOAD_BYTES = 60 * 1024 * 1024
USER_AGENT = "rice_benchmark_external_knowledge_07a/0.1"

DOWNLOAD_COLUMNS = [
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

CHECKSUM_COLUMNS = [
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

DOWNLOAD_LOG_COLUMNS = [
    "source_database",
    "download_id",
    "source_id",
    "data_category",
    "file_role",
    "url",
    "local_path",
    "download_status",
    "file_size_bytes",
    "checksum_sha256",
    "source_version",
    "reference_build",
    "notes",
]


@dataclass(frozen=True)
class DownloadTarget:
    download_id: str
    file_id: str
    source_database: str
    source_id: str
    data_category: str
    file_role: str
    url: str
    local_path: Path
    source_version: str
    reference_build: str
    notes: str
    max_bytes: int = MAX_DOWNLOAD_BYTES


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel_path(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def request(url: str, method: str = "GET") -> urllib.request.Request:
    return urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})


def open_url(url: str, method: str = "GET", timeout: int = 45):
    context = ssl.create_default_context()
    return urllib.request.urlopen(request(url, method=method), timeout=timeout, context=context)


def head_content_length(url: str) -> tuple[int | None, str]:
    try:
        with open_url(url, method="HEAD", timeout=30) as response:
            length = response.headers.get("Content-Length")
            return (int(length) if length else None, "")
    except Exception as exc:
        return None, f"HEAD failed: {exc}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(target: DownloadTarget) -> dict[str, object]:
    started = now_iso()
    target.local_path.parent.mkdir(parents=True, exist_ok=True)
    expected_size, head_error = head_content_length(target.url)
    if expected_size is not None and expected_size > target.max_bytes:
        return {
            "download_id": target.download_id,
            "source_id": target.source_id,
            "data_category": target.data_category,
            "file_role": target.file_role,
            "original_filename": Path(urllib.parse.urlparse(target.url).path).name or target.local_path.name,
            "local_path": rel_path(target.local_path),
            "download_url_or_access_method": target.url,
            "access_method_type": "https",
            "download_command": f"skipped: HEAD content-length {expected_size} exceeds {target.max_bytes}",
            "download_status": "skipped",
            "file_size_bytes": "",
            "checksum_sha256": "",
            "download_started_at": started,
            "download_finished_at": now_iso(),
            "source_version": target.source_version,
            "reference_build": target.reference_build,
            "notes": target.notes,
        }

    try:
        with open_url(target.url, method="GET", timeout=90) as response, target.local_path.open("wb") as output:
            shutil.copyfileobj(response, output)
    except Exception as exc:
        return {
            "download_id": target.download_id,
            "source_id": target.source_id,
            "data_category": target.data_category,
            "file_role": target.file_role,
            "original_filename": Path(urllib.parse.urlparse(target.url).path).name or target.local_path.name,
            "local_path": rel_path(target.local_path),
            "download_url_or_access_method": target.url,
            "access_method_type": "https",
            "download_command": f"urllib.request GET {target.url}",
            "download_status": "failed",
            "file_size_bytes": "",
            "checksum_sha256": "",
            "download_started_at": started,
            "download_finished_at": now_iso(),
            "source_version": target.source_version,
            "reference_build": target.reference_build,
            "notes": f"{target.notes}; {head_error}; GET failed: {exc}",
        }

    file_size = target.local_path.stat().st_size
    checksum = sha256_file(target.local_path)
    return {
        "download_id": target.download_id,
        "source_id": target.source_id,
        "data_category": target.data_category,
        "file_role": target.file_role,
        "original_filename": Path(urllib.parse.urlparse(target.url).path).name or target.local_path.name,
        "local_path": rel_path(target.local_path),
        "download_url_or_access_method": target.url,
        "access_method_type": "https",
        "download_command": f"urllib.request GET {target.url}",
        "download_status": "downloaded",
        "file_size_bytes": file_size,
        "checksum_sha256": checksum,
        "download_started_at": started,
        "download_finished_at": now_iso(),
        "source_version": target.source_version,
        "reference_build": target.reference_build,
        "notes": target.notes,
    }


def read_tsv(path: Path, columns: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [{column: row.get(column, "") for column in columns} for row in reader]


def write_tsv(path: Path, rows: Iterable[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def upsert_tsv(path: Path, new_rows: list[dict[str, object]], columns: list[str], key: str) -> None:
    existing = read_tsv(path, columns)
    new_keys = {str(row[key]) for row in new_rows}
    kept = [row for row in existing if row.get(key, "") not in new_keys]
    write_tsv(path, [*kept, *new_rows], columns)


def checksum_rows(download_rows: list[dict[str, object]], file_ids: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    computed_at = now_iso()
    for row in download_rows:
        if row.get("download_status") != "downloaded":
            continue
        download_id = str(row["download_id"])
        rows.append(
            {
                "file_id": file_ids[download_id],
                "download_id": download_id,
                "source_id": row["source_id"],
                "local_path": row["local_path"],
                "checksum_algorithm": "sha256",
                "checksum_value": row["checksum_sha256"],
                "file_size_bytes": row["file_size_bytes"],
                "computed_at": computed_at,
                "verification_status": "verified",
                "notes": "computed by Phase 7A external knowledge collection script",
            }
        )
    return rows


def collect_targets(targets: list[DownloadTarget], report_dir: Path, log_name: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for target in targets:
        row = download_file(target)
        rows.append(row)
        print(f"{target.source_database}\t{row['download_status']}\t{row['local_path']}")

    upsert_tsv(DOWNLOAD_MANIFEST, rows, DOWNLOAD_COLUMNS, "download_id")
    file_ids = {target.download_id: target.file_id for target in targets}
    checksum = checksum_rows(rows, file_ids)
    if checksum:
        upsert_tsv(CHECKSUM_TABLE, checksum, CHECKSUM_COLUMNS, "file_id")

    log_rows = [
        {
            "source_database": target.source_database,
            "download_id": row["download_id"],
            "source_id": row["source_id"],
            "data_category": row["data_category"],
            "file_role": row["file_role"],
            "url": row["download_url_or_access_method"],
            "local_path": row["local_path"],
            "download_status": row["download_status"],
            "file_size_bytes": row["file_size_bytes"],
            "checksum_sha256": row["checksum_sha256"],
            "source_version": row["source_version"],
            "reference_build": row["reference_build"],
            "notes": row["notes"],
        }
        for target, row in zip(targets, rows)
    ]
    write_tsv(report_dir / log_name, log_rows, DOWNLOAD_LOG_COLUMNS)
    return rows


def guess_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".tsv.gz") or name.endswith(".txt.gz") or name.endswith(".gff.gz") or name.endswith(".gff3.gz") or name.endswith(".gtf.gz"):
        return name.rsplit(".", 2)[-2] + ".gz"
    if name.endswith(".html") or name.endswith(".shtml"):
        return "html"
    if name.endswith(".json"):
        return "json"
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".gz"):
        return "gz"
    suffix = path.suffix.lower().lstrip(".")
    return suffix or (mimetypes.guess_type(str(path))[0] or "unknown")


def text_open(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace", newline="")


def detect_delimiter(sample: str) -> str:
    candidates = ["\t", ",", ";"]
    return max(candidates, key=lambda delimiter: sample.count(delimiter))


def detect_columns(columns: list[str], patterns: list[str]) -> str:
    out = [column for column in columns if any(pattern.lower() in column.lower() for pattern in patterns)]
    return ";".join(out)
