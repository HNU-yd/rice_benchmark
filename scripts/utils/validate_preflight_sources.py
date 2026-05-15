#!/usr/bin/env python3
"""Validate Phase 2A preflight_verified_sources.tsv."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = [
    "source_id",
    "data_category",
    "priority",
    "candidate_source_name",
    "download_url_or_access_method",
    "access_method_type",
    "verification_status",
    "risk_level",
    "phase2b_ready",
    "manual_confirmation_required",
    "preflight_check_method",
    "preflight_check_result",
    "recommended_action",
    "notes",
]

ALLOWED_READY = {"yes", "no", "needs_manual_confirmation", "defer", "exclude_from_v1"}
ALLOWED_ACTION = {
    "download_in_phase2b",
    "manual_verify_before_download",
    "listing_only",
    "defer",
    "exclude_from_v1",
}
REQUIRED_P0_CATEGORIES = {
    "accession_metadata",
    "snp_genotype",
    "indel_genotype",
    "reference_genome",
    "trait_table",
    "weak_evidence",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Preflight sources file not found: {path}"]

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            return [f"Missing required columns: {', '.join(missing)}"]
        rows = list(reader)

    p0_categories: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        ready = row.get("phase2b_ready", "").strip()
        action = row.get("recommended_action", "").strip()
        if ready not in ALLOWED_READY:
            errors.append(f"Line {line_number}: invalid phase2b_ready {ready!r}")
        if action not in ALLOWED_ACTION:
            errors.append(f"Line {line_number}: invalid recommended_action {action!r}")

        source_id = row.get("source_id", "").strip()
        category = row.get("data_category", "").strip()
        if row.get("priority", "").strip() == "P0" and category:
            p0_categories.add(category)

        source_text = " ".join(
            [
                row.get("candidate_source_name", ""),
                row.get("download_url_or_access_method", ""),
                row.get("notes", ""),
            ]
        ).lower()
        if "snp-seek" in source_text and ready == "yes":
            errors.append(f"Line {line_number}: SNP-Seek source cannot be phase2b_ready=yes")

        if row.get("verification_status", "").strip() == "excluded_for_v1":
            if ready != "exclude_from_v1":
                errors.append(f"Line {line_number}: excluded_for_v1 source must set phase2b_ready=exclude_from_v1")
            if action != "exclude_from_v1":
                errors.append(f"Line {line_number}: excluded_for_v1 source must set recommended_action=exclude_from_v1")
        if source_id.startswith("SRC_EXCLUDED") and ready != "exclude_from_v1":
            errors.append(f"Line {line_number}: excluded source_id must set phase2b_ready=exclude_from_v1")

    missing_p0 = sorted(REQUIRED_P0_CATEGORIES - p0_categories)
    if missing_p0:
        errors.append(f"Missing P0 source categories: {', '.join(missing_p0)}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: python scripts/utils/validate_preflight_sources.py "
            "manifest/preflight_verified_sources.tsv",
            file=sys.stderr,
        )
        return 2

    errors = validate(Path(argv[1]))
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print("[OK] preflight sources validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
