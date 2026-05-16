#!/usr/bin/env python3
"""Validate chr1 SNP baseline and evaluator prototype outputs.

Inputs:
  data/interim/baselines_chr1_snp/window_baseline_scores.tsv
  data/interim/baselines_chr1_snp/variant_baseline_scores.tsv
  data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
  data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv
  reports/baselines_chr1_snp/window_baseline_metrics.tsv
  reports/baselines_chr1_snp/variant_baseline_metrics.tsv

Output:
  reports/baselines_chr1_snp/baseline_validation.tsv

Usage:
  python scripts/eval/validate_baseline_outputs.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/baselines_chr1_snp"
REPORT_DIR = REPO_ROOT / "reports/baselines_chr1_snp"

FROZEN_TRAITS = REPO_ROOT / "reports/trait_state_review/frozen_v0_1_traits.tsv"
WINDOW_TABLE = REPO_ROOT / "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv"
VARIANT_TABLE = REPO_ROOT / "data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv"
WINDOW_SIGNAL = REPO_ROOT / "data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv"
VARIANT_LABEL = REPO_ROOT / "data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv"
WINDOW_SCORES = INTERIM_DIR / "window_baseline_scores.tsv"
VARIANT_SCORES = INTERIM_DIR / "variant_baseline_scores.tsv"
WINDOW_METRICS = REPORT_DIR / "window_baseline_metrics.tsv"
VARIANT_METRICS = REPORT_DIR / "variant_baseline_metrics.tsv"
TOPK_WINDOW = REPORT_DIR / "topk_window_hits.tsv"
TOPK_VARIANT = REPORT_DIR / "topk_variant_hits.tsv"
VALIDATION = REPORT_DIR / "baseline_validation.tsv"

WINDOW_SCORE_FIELDS = {
    "run_id",
    "baseline_name",
    "trait_id",
    "window_id",
    "chrom",
    "refseq_chrom",
    "start",
    "end",
    "score",
    "score_rank",
    "score_percentile",
    "notes",
}
VARIANT_SCORE_FIELDS = {
    "run_id",
    "baseline_name",
    "trait_id",
    "variant_id",
    "chrom",
    "refseq_chrom",
    "pos",
    "score",
    "score_rank",
    "score_percentile",
    "notes",
}
FORMAL_METRIC_TOKENS = {"auroc", "auprc"}
FORBIDDEN_LABEL_TOKENS = ("negative", "causal", "non_causal", "non-causal", "ground_truth", "ground truth")
REQUIRED_BASELINES = {"random_uniform", "window_snp_density", "genomic_position", "shuffled_trait"}
VALIDATION_FIELDS = ["check_name", "status", "observed", "expected", "notes"]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VALIDATION_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pass_fail(condition: bool) -> str:
    return "pass" if condition else "fail"


def trait_ids() -> set[str]:
    return {row["trait_id"] for row in read_tsv(FROZEN_TRAITS)}


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _line in handle) - 1, 0)


def score_counts(path: Path, item_field: str) -> tuple[dict[str, set[str]], dict[tuple[str, str], int], int]:
    baselines_by_trait: dict[str, set[str]] = defaultdict(set)
    count_by_pair: dict[tuple[str, str], int] = defaultdict(int)
    duplicate_ranks = 0
    ranks_seen: dict[tuple[str, str], set[str]] = defaultdict(set)
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            key = (row["baseline_name"], row["trait_id"])
            baselines_by_trait[row["baseline_name"]].add(row["trait_id"])
            count_by_pair[key] += 1
            rank_key = row["score_rank"]
            if rank_key in ranks_seen[key]:
                duplicate_ranks += 1
            ranks_seen[key].add(rank_key)
            if not row.get(item_field):
                duplicate_ranks += 1
    return baselines_by_trait, count_by_pair, duplicate_ranks


def forbidden_label_count(path: Path, label_field: str) -> int:
    count = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            label = row.get(label_field, "").lower()
            if any(token in label for token in FORBIDDEN_LABEL_TOKENS):
                count += 1
    return count


def formal_metric_fields() -> list[str]:
    bad_fields: list[str] = []
    for path in [WINDOW_METRICS, VARIANT_METRICS, TOPK_WINDOW, TOPK_VARIANT]:
        for field in header(path):
            lower = field.lower()
            if any(token in lower for token in FORMAL_METRIC_TOKENS):
                bad_fields.append(f"{path.name}:{field}")
    return bad_fields


def main() -> int:
    expected_traits = trait_ids()
    expected_windows = count_rows(WINDOW_TABLE)
    expected_variants = count_rows(VARIANT_TABLE)
    rows: list[dict[str, object]] = []

    window_fields = set(header(WINDOW_SCORES))
    variant_fields = set(header(VARIANT_SCORES))
    rows.append(
        {
            "check_name": "window_score_fields_complete",
            "status": pass_fail(WINDOW_SCORE_FIELDS.issubset(window_fields)),
            "observed": len(WINDOW_SCORE_FIELDS.intersection(window_fields)),
            "expected": len(WINDOW_SCORE_FIELDS),
            "notes": "window_baseline_scores.tsv required fields",
        }
    )
    rows.append(
        {
            "check_name": "variant_score_fields_complete",
            "status": pass_fail(VARIANT_SCORE_FIELDS.issubset(variant_fields)),
            "observed": len(VARIANT_SCORE_FIELDS.intersection(variant_fields)),
            "expected": len(VARIANT_SCORE_FIELDS),
            "notes": "variant_baseline_scores.tsv required fields",
        }
    )

    window_baselines, window_counts, duplicate_window_ranks = score_counts(WINDOW_SCORES, "window_id")
    variant_baselines, variant_counts, duplicate_variant_ranks = score_counts(VARIANT_SCORES, "variant_id")
    observed_window_baselines = set(window_baselines)
    observed_variant_baselines = set(variant_baselines)
    bad_window_trait_sets = {baseline: sorted(expected_traits - traits) for baseline, traits in window_baselines.items() if traits != expected_traits}
    bad_variant_trait_sets = {baseline: sorted(expected_traits - traits) for baseline, traits in variant_baselines.items() if traits != expected_traits}
    bad_window_counts = sum(1 for count in window_counts.values() if count != expected_windows)
    bad_variant_counts = sum(1 for count in variant_counts.values() if count != expected_variants)
    rows.extend(
        [
            {
                "check_name": "required_baselines_present",
                "status": pass_fail(REQUIRED_BASELINES.issubset(observed_window_baselines) and REQUIRED_BASELINES.issubset(observed_variant_baselines)),
                "observed": f"window={','.join(sorted(observed_window_baselines))};variant={','.join(sorted(observed_variant_baselines))}",
                "expected": ",".join(sorted(REQUIRED_BASELINES)),
                "notes": "required baseline score tables are present at both levels",
            },
            {
                "check_name": "every_trait_has_window_scores",
                "status": pass_fail(not bad_window_trait_sets and bad_window_counts == 0),
                "observed": f"missing_trait_sets={len(bad_window_trait_sets)};bad_counts={bad_window_counts}",
                "expected": f"{len(expected_traits)} traits x {expected_windows} windows per baseline",
                "notes": "score table is complete at trait-window level",
            },
            {
                "check_name": "every_trait_has_variant_scores",
                "status": pass_fail(not bad_variant_trait_sets and bad_variant_counts == 0),
                "observed": f"missing_trait_sets={len(bad_variant_trait_sets)};bad_counts={bad_variant_counts}",
                "expected": f"{len(expected_traits)} traits x {expected_variants} variants per baseline",
                "notes": "score table is complete at trait-variant level",
            },
            {
                "check_name": "window_score_ranks_unique_per_trait_baseline",
                "status": pass_fail(duplicate_window_ranks == 0),
                "observed": duplicate_window_ranks,
                "expected": 0,
                "notes": "rank uniqueness check within each baseline and trait",
            },
            {
                "check_name": "variant_score_ranks_unique_per_trait_baseline",
                "status": pass_fail(duplicate_variant_ranks == 0),
                "observed": duplicate_variant_ranks,
                "expected": 0,
                "notes": "rank uniqueness check within each baseline and trait",
            },
        ]
    )

    forbidden_window = forbidden_label_count(WINDOW_SIGNAL, "window_label_state")
    forbidden_variant = forbidden_label_count(VARIANT_LABEL, "variant_label_state")
    bad_formal_fields = formal_metric_fields()
    rows.extend(
        [
            {
                "check_name": "window_label_forbidden_tokens_absent",
                "status": pass_fail(forbidden_window == 0),
                "observed": forbidden_window,
                "expected": 0,
                "notes": "window label_state must avoid forbidden supervised-label terms",
            },
            {
                "check_name": "variant_label_forbidden_tokens_absent",
                "status": pass_fail(forbidden_variant == 0),
                "observed": forbidden_variant,
                "expected": 0,
                "notes": "variant label_state must avoid forbidden supervised-label terms",
            },
            {
                "check_name": "formal_auroc_auprc_fields_absent",
                "status": pass_fail(not bad_formal_fields),
                "observed": ";".join(bad_formal_fields),
                "expected": "no AUROC/AUPRC fields",
                "notes": "formal binary-classifier metrics require matched decoy",
            },
        ]
    )

    write_tsv(VALIDATION, rows)
    failed = [row for row in rows if row["status"] != "pass"]
    print(f"validation_checks={len(rows)}")
    print(f"validation_failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
