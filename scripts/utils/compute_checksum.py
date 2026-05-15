#!/usr/bin/env python3
"""Compute sha256 checksum and file size for a local file."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def compute_sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/utils/compute_checksum.py <file_path>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return 1
    if not path.is_file():
        print(f"[ERROR] Not a regular file: {path}", file=sys.stderr)
        return 1

    checksum, size = compute_sha256(path)
    print(f"{checksum}\t{size}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

