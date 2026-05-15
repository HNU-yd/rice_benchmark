#!/usr/bin/env python3
"""Validate the Phase 1 source inventory TSV format."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


REQUIRED_COLUMNS = [
    "source_id",
    "data_category",
    "dataset_name",
    "species",
    "reference_build",
    "variant_type",
    "expected_format",
    "expected_size",
    "candidate_source_name",
    "download_url_or_access_method",
    "access_method_type",
    "priority",
    "required_for_task",
    "used_for_table",
    "verification_status",
    "download_status",
    "risk_level",
    "risk_notes",
    "exclude_from_v1",
    "notes",
]

REQUIRED_CATEGORIES = {
    "accession_metadata",
    "snp_genotype",
    "indel_genotype",
    "reference_genome",
    "gene_annotation",
    "trait_table",
    "weak_evidence",
}

ALLOWED_PRIORITY = {"P0", "P1", "P2"}
ALLOWED_VERIFICATION_STATUS = {
    "verified",
    "partially_verified",
    "needs_manual_review",
    "unavailable",
    "excluded_for_v1",
}
ALLOWED_RISK_LEVEL = {"low", "medium", "high"}
ALLOWED_EXCLUDE = {"yes", "no"}
P0_REQUIRED = {
    "accession_metadata",
    "snp_genotype",
    "indel_genotype",
    "reference_genome",
    "trait_table",
}


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"[ERROR] {error}", file=sys.stderr)
    return 1


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Inventory file not found: {path}"]

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")
            return errors

        rows = list(reader)

    if not rows:
        errors.append("Inventory has no data rows")
        return errors

    source_ids: set[str] = set()
    categories: set[str] = set()
    p0_categories: set[str] = set()

    for line_number, row in enumerate(rows, start=2):
        source_id = row.get("source_id", "").strip()
        if not source_id:
            errors.append(f"Line {line_number}: source_id is empty")
        elif source_id in source_ids:
            errors.append(f"Line {line_number}: duplicate source_id {source_id}")
        source_ids.add(source_id)

        category = row.get("data_category", "").strip()
        if category:
            categories.add(category)

        priority = row.get("priority", "").strip()
        if priority not in ALLOWED_PRIORITY:
            errors.append(f"Line {line_number}: invalid priority {priority!r}")
        if priority == "P0" and category:
            p0_categories.add(category)

        verification_status = row.get("verification_status", "").strip()
        if verification_status not in ALLOWED_VERIFICATION_STATUS:
            errors.append(
                f"Line {line_number}: invalid verification_status {verification_status!r}"
            )

        download_status = row.get("download_status", "").strip()
        if download_status != "not_downloaded":
            errors.append(f"Line {line_number}: download_status must be not_downloaded")

        risk_level = row.get("risk_level", "").strip()
        if risk_level not in ALLOWED_RISK_LEVEL:
            errors.append(f"Line {line_number}: invalid risk_level {risk_level!r}")

        exclude = row.get("exclude_from_v1", "").strip()
        if exclude not in ALLOWED_EXCLUDE:
            errors.append(f"Line {line_number}: invalid exclude_from_v1 {exclude!r}")

    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        errors.append(f"Missing required data_category values: {', '.join(missing_categories)}")

    missing_p0 = sorted(P0_REQUIRED - p0_categories)
    if missing_p0:
        errors.append(f"Missing P0 rows for required categories: {', '.join(missing_p0)}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: python scripts/utils/validate_source_inventory.py "
            "manifest/source_inventory.tsv",
            file=sys.stderr,
        )
        return 2

    errors = validate(Path(argv[1]))
    if errors:
        return fail(errors)

    print("[OK] source inventory validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
