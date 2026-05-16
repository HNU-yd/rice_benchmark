#!/usr/bin/env python3
"""Build deterministic baseline score tables for chr1 SNP Task 1 prototype.

Inputs:
  data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
  data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv
  data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
  data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
  data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv
  reports/trait_state_review/frozen_v0_1_traits.tsv

Outputs:
  data/interim/baselines_chr1_snp/window_baseline_scores.tsv
  data/interim/baselines_chr1_snp/variant_baseline_scores.tsv

Usage:
  python scripts/baselines/build_chr1_snp_baselines.py
"""

from __future__ import annotations

import csv
import hashlib
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/baselines_chr1_snp"

FROZEN_TRAITS = REPO_ROOT / "reports/trait_state_review/frozen_v0_1_traits.tsv"
TASK1_CONFIG = REPO_ROOT / "configs/task1_chr1_snp_v0_1.yaml"
FROZEN_TRAIT_CONFIG = REPO_ROOT / "configs/v0_1_frozen_traits.yaml"
INSTANCE_MANIFEST = REPO_ROOT / "data/interim/task1_chr1_snp/task1_chr1_snp_instance_manifest.tsv"
TASK1_TRAIT_SUMMARY = REPO_ROOT / "reports/task1_chr1_snp/task1_chr1_snp_trait_summary.tsv"
TASK1_WINDOW_SUMMARY = REPO_ROOT / "reports/task1_chr1_snp/task1_chr1_snp_window_signal_summary.tsv"
WINDOW_SIGNAL = REPO_ROOT / "data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv"
VARIANT_LABEL = REPO_ROOT / "data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv"
WINDOW_TABLE = REPO_ROOT / "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv"
VARIANT_TABLE = REPO_ROOT / "data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv"
VARIANT_WINDOW_MAPPING = REPO_ROOT / "data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv"

RUN_ID = "v0_1_chr1_snp_20260516"
RANDOM_SEED = 20260516
POSITIVE_LABEL_STATES = {"positive_weak_evidence", "regional_weak_evidence"}

WINDOW_FIELDS = [
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
]

VARIANT_FIELDS = [
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
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require_inputs() -> None:
    missing = [
        path
        for path in [
            TASK1_CONFIG,
            FROZEN_TRAIT_CONFIG,
            INSTANCE_MANIFEST,
            TASK1_TRAIT_SUMMARY,
            TASK1_WINDOW_SUMMARY,
            FROZEN_TRAITS,
            WINDOW_SIGNAL,
            VARIANT_LABEL,
            WINDOW_TABLE,
            VARIANT_TABLE,
            VARIANT_WINDOW_MAPPING,
        ]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("missing required input files: " + ", ".join(str(path) for path in missing))


def fmt_float(value: float, digits: int = 10) -> str:
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def deterministic_uniform(*parts: str) -> float:
    key = "|".join([str(RANDOM_SEED), *parts]).encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    seed = int(digest[:16], 16)
    return random.Random(seed).random()


def rank_and_write(path: Path, rows: list[dict[str, object]], fields: list[str], id_field: str) -> None:
    rows.sort(key=lambda row: (-float(row["score"]), str(row[id_field])))
    n_rows = len(rows)
    denom = max(n_rows - 1, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        for index, row in enumerate(rows, start=1):
            row["score_rank"] = index
            row["score_percentile"] = fmt_float((n_rows - index) / denom)
            row["score"] = fmt_float(float(row["score"]))
            writer.writerow({field: row.get(field, "") for field in fields})


def init_output(path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n").writeheader()


def trait_ids() -> list[str]:
    return [row["trait_id"] for row in read_tsv(FROZEN_TRAITS)]


def chromosome_length(window_rows: list[dict[str, str]], variant_rows: list[dict[str, str]]) -> int:
    max_window_end = max(int(row["end"]) for row in window_rows)
    max_variant_pos = max(int(row["pos"]) for row in variant_rows)
    return max(max_window_end, max_variant_pos)


def shuffled_trait_map(traits: list[str]) -> dict[str, str]:
    shuffled = traits[:]
    random.Random(RANDOM_SEED).shuffle(shuffled)
    if len(traits) <= 1:
        return dict(zip(traits, shuffled))
    for offset in range(len(traits)):
        candidate = shuffled[offset:] + shuffled[:offset]
        if all(target != source for target, source in zip(traits, candidate)):
            return dict(zip(traits, candidate))
    raise ValueError("could not construct trait shuffle without self mappings")


def window_signal_scores() -> dict[tuple[str, str], float]:
    scores: dict[tuple[str, str], float] = {}
    for row in read_tsv(WINDOW_SIGNAL):
        scores[(row["trait_id"], row["window_id"])] = float(row.get("window_weak_signal") or 0)
    return scores


def variant_signal_scores() -> dict[tuple[str, str], float]:
    scores: dict[tuple[str, str], float] = {}
    for row in read_tsv(VARIANT_LABEL):
        scores[(row["trait_id"], row["variant_id"])] = 1.0 if row["variant_label_state"] in POSITIVE_LABEL_STATES else 0.0
    return scores


def variant_density_scores(window_by_id: dict[str, dict[str, str]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for row in read_tsv(VARIANT_WINDOW_MAPPING):
        density = float(window_by_id[row["window_id"]]["n_snp"])
        current = scores.get(row["variant_id"])
        if current is None or density > current:
            scores[row["variant_id"]] = density
    return scores


def window_score_rows(
    baseline_name: str,
    trait_id: str,
    window_rows: list[dict[str, str]],
    chr_length: int,
    shuffled_source: str | None,
    source_window_scores: dict[tuple[str, str], float],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for window in window_rows:
        if baseline_name == "random_uniform":
            score = deterministic_uniform("window", trait_id, window["window_id"])
            notes = "fixed seed random score within trait"
        elif baseline_name == "window_snp_density":
            score = float(window["n_snp"])
            notes = "window score equals n_snp_in_window"
        elif baseline_name == "genomic_position":
            score = float(window["start"]) / chr_length
            notes = "window_start divided by chr1 prototype length"
        elif baseline_name == "shuffled_trait":
            assert shuffled_source is not None
            score = source_window_scores.get((shuffled_source, window["window_id"]), 0.0)
            notes = f"trait-shuffled weak signal from {shuffled_source}; prototype sanity check only"
        else:
            raise ValueError(f"unsupported baseline_name: {baseline_name}")
        rows.append(
            {
                "run_id": RUN_ID,
                "baseline_name": baseline_name,
                "trait_id": trait_id,
                "window_id": window["window_id"],
                "chrom": window["chrom"],
                "refseq_chrom": window["refseq_chrom"],
                "start": window["start"],
                "end": window["end"],
                "score": score,
                "score_rank": "",
                "score_percentile": "",
                "notes": notes,
            }
        )
    return rows


def variant_score_rows(
    baseline_name: str,
    trait_id: str,
    variant_rows: list[dict[str, str]],
    chr_length: int,
    density_by_variant: dict[str, float],
    shuffled_source: str | None,
    source_variant_scores: dict[tuple[str, str], float],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for variant in variant_rows:
        if baseline_name == "random_uniform":
            score = deterministic_uniform("variant", trait_id, variant["variant_id"])
            notes = "fixed seed random score within trait"
        elif baseline_name == "window_snp_density":
            score = density_by_variant.get(variant["variant_id"], 0.0)
            notes = "variant inherits max n_snp among overlapping windows"
        elif baseline_name == "genomic_position":
            score = float(variant["pos"]) / chr_length
            notes = "variant position divided by chr1 prototype length"
        elif baseline_name == "shuffled_trait":
            assert shuffled_source is not None
            score = source_variant_scores.get((shuffled_source, variant["variant_id"]), 0.0)
            notes = f"trait-shuffled weak signal from {shuffled_source}; prototype sanity check only"
        else:
            raise ValueError(f"unsupported baseline_name: {baseline_name}")
        rows.append(
            {
                "run_id": RUN_ID,
                "baseline_name": baseline_name,
                "trait_id": trait_id,
                "variant_id": variant["variant_id"],
                "chrom": variant["chrom"],
                "refseq_chrom": variant["refseq_chrom"],
                "pos": variant["pos"],
                "score": score,
                "score_rank": "",
                "score_percentile": "",
                "notes": notes,
            }
        )
    return rows


def main() -> int:
    require_inputs()
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    traits = trait_ids()
    window_rows = read_tsv(WINDOW_TABLE)
    variant_rows = read_tsv(VARIANT_TABLE)
    window_by_id = {row["window_id"]: row for row in window_rows}
    chr_length = chromosome_length(window_rows, variant_rows)
    density_by_variant = variant_density_scores(window_by_id)
    source_window_scores = window_signal_scores()
    source_variant_scores = variant_signal_scores()
    shuffle_map = shuffled_trait_map(traits)
    baseline_names = ["random_uniform", "window_snp_density", "genomic_position", "shuffled_trait"]

    window_output = INTERIM_DIR / "window_baseline_scores.tsv"
    variant_output = INTERIM_DIR / "variant_baseline_scores.tsv"
    init_output(window_output, WINDOW_FIELDS)
    init_output(variant_output, VARIANT_FIELDS)

    for baseline_name in baseline_names:
        for trait_id in traits:
            source_trait = shuffle_map[trait_id] if baseline_name == "shuffled_trait" else None
            rank_and_write(
                window_output,
                window_score_rows(baseline_name, trait_id, window_rows, chr_length, source_trait, source_window_scores),
                WINDOW_FIELDS,
                "window_id",
            )
            rank_and_write(
                variant_output,
                variant_score_rows(
                    baseline_name,
                    trait_id,
                    variant_rows,
                    chr_length,
                    density_by_variant,
                    source_trait,
                    source_variant_scores,
                ),
                VARIANT_FIELDS,
                "variant_id",
            )

    print(f"baseline_names={','.join(baseline_names)}")
    print(f"n_traits={len(traits)}")
    print(f"n_window_score_rows={len(baseline_names) * len(traits) * len(window_rows)}")
    print(f"n_variant_score_rows={len(baseline_names) * len(traits) * len(variant_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
