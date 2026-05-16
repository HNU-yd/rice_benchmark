#!/usr/bin/env python3
"""Validate chr1 SNP-only minimal Task 1 instance prototype."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/task1_chr1_snp"
REPORT_DIR = REPO_ROOT / "reports/task1_chr1_snp"

FROZEN_TRAITS = REPO_ROOT / "reports/trait_state_review/frozen_v0_1_traits.tsv"
HIGH_CONF_ACCESSIONS = REPO_ROOT / "data/interim/trait_state/high_confidence_accessions.tsv"
WINDOW_TABLE = REPO_ROOT / "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv"
INSTANCE_TABLE = INTERIM_DIR / "task1_chr1_snp_instances.tsv"
WINDOW_SIGNAL = INTERIM_DIR / "window_weak_signal_chr1_snp.tsv"
VARIANT_LABEL = INTERIM_DIR / "variant_weak_label_chr1_snp.tsv"
VALIDATION = REPORT_DIR / "task1_chr1_snp_validation.tsv"

VALIDATION_FIELDS = ["check_name", "status", "observed", "expected", "notes"]
FORBIDDEN_LABEL_TOKENS = ("negative", "causal", "non_causal", "non-causal", "ground_truth", "ground truth")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VALIDATION_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pass_fail(condition: bool) -> str:
    return "pass" if condition else "fail"


def main() -> int:
    frozen = {row["trait_id"] for row in read_tsv(FROZEN_TRAITS)}
    high_conf = {row["genotype_sample_id"] for row in read_tsv(HIGH_CONF_ACCESSIONS)}
    windows = read_tsv(WINDOW_TABLE)
    window_ids = {row["window_id"] for row in windows}
    rows: list[dict[str, object]] = []

    n_instances = 0
    bad_trait = 0
    bad_accession = 0
    bad_window = 0
    bad_chrom = 0
    forbidden_instance_labels = 0
    unknown_instance_labels = 0
    pair_counts: Counter[tuple[str, str]] = Counter()
    instance_expected_windows_ok = True
    current_pair: tuple[str, str] | None = None
    current_windows: set[str] = set()

    def flush_pair() -> None:
        nonlocal instance_expected_windows_ok, current_windows
        if current_pair is not None and current_windows != window_ids:
            instance_expected_windows_ok = False
        current_windows = set()

    with INSTANCE_TABLE.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            n_instances += 1
            trait_id = row["trait_id"]
            genotype = row["genotype_sample_id"]
            window_id = row["window_id"]
            pair = (trait_id, genotype)
            if current_pair is None:
                current_pair = pair
            elif pair != current_pair:
                flush_pair()
                current_pair = pair
            current_windows.add(window_id)
            pair_counts[pair] += 1
            if trait_id not in frozen:
                bad_trait += 1
            if genotype not in high_conf:
                bad_accession += 1
            if window_id not in window_ids:
                bad_window += 1
            if row["chrom"] != "1":
                bad_chrom += 1
            label = row.get("window_label_state", "")
            if any(token in label for token in FORBIDDEN_LABEL_TOKENS):
                forbidden_instance_labels += 1
            if label == "unknown_unlabeled":
                unknown_instance_labels += 1
    flush_pair()

    expected_instances = len(pair_counts) * len(window_ids)
    duplicate_by_construction = any(count != len(window_ids) for count in pair_counts.values()) or n_instances != expected_instances or not instance_expected_windows_ok
    rows.extend(
        [
            {
                "check_name": "instance_id_unique",
                "status": pass_fail(not duplicate_by_construction),
                "observed": n_instances,
                "expected": expected_instances,
                "notes": "validated by trait/accession pair and complete window set; instance_id = trait_id + genotype_sample_id + window_id",
            },
            {"check_name": "traits_are_frozen", "status": pass_fail(bad_trait == 0), "observed": bad_trait, "expected": 0, "notes": "all instance traits must be frozen v0.1 traits"},
            {"check_name": "accessions_high_confidence", "status": pass_fail(bad_accession == 0), "observed": bad_accession, "expected": 0, "notes": "all instance accessions must come from high-confidence subset"},
            {"check_name": "windows_known_chr1", "status": pass_fail(bad_window == 0 and bad_chrom == 0), "observed": f"bad_window={bad_window};bad_chrom={bad_chrom}", "expected": 0, "notes": "all windows must be chr1 windows"},
            {"check_name": "instance_label_forbidden_tokens_absent", "status": pass_fail(forbidden_instance_labels == 0), "observed": forbidden_instance_labels, "expected": 0, "notes": "label_state must not contain forbidden supervised-label terms"},
            {"check_name": "unknown_unlabeled_retained_in_instances", "status": pass_fail(unknown_instance_labels > 0), "observed": unknown_instance_labels, "expected": ">0", "notes": "absence of evidence remains unknown_unlabeled"},
        ]
    )

    for table_name, path, label_field in [
        ("window_signal", WINDOW_SIGNAL, "window_label_state"),
        ("variant_label", VARIANT_LABEL, "variant_label_state"),
    ]:
        forbidden = 0
        unknown = 0
        n_rows = 0
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                n_rows += 1
                label = row.get(label_field, "")
                if any(token in label for token in FORBIDDEN_LABEL_TOKENS):
                    forbidden += 1
                if label == "unknown_unlabeled":
                    unknown += 1
        rows.append(
            {
                "check_name": f"{table_name}_forbidden_tokens_absent",
                "status": pass_fail(forbidden == 0),
                "observed": forbidden,
                "expected": 0,
                "notes": f"checked {n_rows} rows in {path.name}",
            }
        )
        rows.append(
            {
                "check_name": f"{table_name}_unknown_unlabeled_retained",
                "status": pass_fail(unknown > 0),
                "observed": unknown,
                "expected": ">0",
                "notes": f"checked {n_rows} rows in {path.name}",
            }
        )

    write_tsv(VALIDATION, rows)
    failed = [row for row in rows if row["status"] != "pass"]
    print(f"validation_checks={len(rows)}")
    print(f"validation_failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
