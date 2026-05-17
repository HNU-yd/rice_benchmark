#!/usr/bin/env python3
"""Utilities for the v0.5.5 matched-ranking evaluator dry-run.

This layer is an evaluator adapter smoke test. It builds score joins, matched-set
diagnostics, rank-position diagnostics, coverage tables, and guards. It does not
produce formal benchmark metrics.
"""

from __future__ import annotations

import argparse
import csv
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DRY_RUN_VERSION = "evaluator_dry_run_v055_chr1_snp_prototype_v1"

DEFAULT_SCAFFOLD_ROOT = REPO_ROOT / "data/interim/evaluator_scaffold_v055"
DEFAULT_BASELINE_ROOT = REPO_ROOT / "data/interim/baselines_chr1_snp"
DEFAULT_MATCHED_DECOY_ROOT = REPO_ROOT / "data/interim/matched_decoy_v055"
DEFAULT_FROZEN_SPLIT_ROOT = REPO_ROOT / "data/interim/frozen_split_v055"
DEFAULT_V01_ROOT = REPO_ROOT / "data/interim/v0_1_mini"
DEFAULT_INTERIM_ROOT = REPO_ROOT / "data/interim/evaluator_dry_run_v055"
DEFAULT_REPORT_ROOT = REPO_ROOT / "reports/evaluator_dry_run_v055"

ALLOWED_SPLITS = {"dev", "prototype_locked", "source_disjoint_or_temporal"}
OBJECT_TYPES = ["variant", "window", "gene", "qtl_interval"]


ADAPTER_FIELDS = [
    "adapter_id",
    "object_type",
    "preferred_score_level",
    "fallback_score_level",
    "aggregation_method",
    "score_source",
    "allowed_for_dry_run",
    "allowed_for_formal_eval",
    "requires_exact_variant_match",
    "requires_exact_window_match",
    "requires_interval_overlap",
    "dry_run_only",
    "notes",
]

MATCHED_SET_FIELDS = [
    "matched_set_id",
    "object_id",
    "decoy_object_id",
    "trait_id",
    "object_type",
    "assigned_split",
    "prototype_locked_not_final",
    "score_source",
    "score_version",
    "score_level_used",
    "adapter_id",
    "evidence_score",
    "decoy_score",
    "score_available_evidence",
    "score_available_decoy",
    "n_decoys_expected",
    "n_decoys_with_score",
    "decoy_semantics",
    "uses_true_negative",
    "uses_unknown_as_negative",
    "dry_run_only",
    "notes",
]

RANK_FIELDS = [
    "rank_record_id",
    "object_id",
    "trait_id",
    "object_type",
    "assigned_split",
    "prototype_locked_not_final",
    "score_source",
    "score_version",
    "score_level_used",
    "adapter_id",
    "n_decoys_expected",
    "n_decoys_with_score",
    "n_decoys_rankable",
    "evidence_score",
    "dry_run_rank",
    "dry_run_rank_percentile",
    "dry_run_top1_indicator",
    "dry_run_top5_indicator",
    "evidence_vs_decoy_mean_delta",
    "evidence_vs_decoy_median_delta",
    "can_rank",
    "rank_failure_reason",
    "dry_run_only",
    "notes",
]

COVERAGE_FIELDS = [
    "coverage_id",
    "assigned_split",
    "trait_id",
    "object_type",
    "score_source",
    "score_level_used",
    "n_objects",
    "n_objects_with_evidence_score",
    "n_objects_with_any_decoy_score",
    "n_objects_with_all_decoy_scores",
    "mean_decoys_with_score",
    "median_decoys_with_score",
    "coverage_rate_evidence",
    "coverage_rate_decoy_any",
    "coverage_rate_decoy_all",
    "dry_run_only",
    "notes",
]

MISSING_FIELDS = [
    "diagnostic_id",
    "object_id",
    "trait_id",
    "object_type",
    "assigned_split",
    "score_source",
    "score_level_expected",
    "missing_evidence_score",
    "n_decoys_expected",
    "n_decoys_with_score",
    "can_rank",
    "failure_reason",
    "dry_run_only",
    "notes",
]

CONTRACT_FIELDS = [
    "contract_item",
    "requirement",
    "current_status",
    "blocking_for_formal_eval",
    "dry_run_only",
    "notes",
]

GUARD_FIELDS = [
    "guard_id",
    "guard_name",
    "status",
    "n_checked",
    "n_failed",
    "details",
    "blocking_issue",
    "dry_run_only",
    "notes",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "n_records",
    "n_failed",
    "details",
    "blocking_issue",
    "dry_run_only",
    "notes",
]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--scaffold-root", type=Path, default=DEFAULT_SCAFFOLD_ROOT)
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE_ROOT)
    parser.add_argument("--matched-decoy-root", type=Path, default=DEFAULT_MATCHED_DECOY_ROOT)
    parser.add_argument("--frozen-split-root", type=Path, default=DEFAULT_FROZEN_SPLIT_ROOT)
    parser.add_argument("--v01-root", type=Path, default=DEFAULT_V01_ROOT)
    parser.add_argument("--interim-root", type=Path, default=DEFAULT_INTERIM_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    return parser.parse_args()


def ensure_output_dirs(interim_root: Path, report_root: Path) -> None:
    for subdir in ["adapter", "matched_sets", "ranks", "coverage", "diagnostics"]:
        (interim_root / subdir).mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
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
            writer.writerow({field: normalize(row.get(field)) for field in fields})


def append_tsv_rows(path: Path, rows: Iterable[dict[str, object]], fields: list[str], write_header: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: normalize(row.get(field)) for field in fields})


def normalize(value: object) -> object:
    if value is None or value == "":
        return "NA"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        if math.isnan(value):
            return "NA"
        return f"{value:.10g}"
    return value


def clean(value: object) -> str:
    return str(value or "").strip()


def is_missing(value: object) -> bool:
    text = clean(value)
    return text == "" or text.lower() in {"na", "n/a", "nan", "none", "null"}


def to_int(value: object, default: int = 0) -> int:
    try:
        return int(float(clean(value)))
    except Exception:
        return default


def to_float(value: object) -> float | None:
    try:
        if is_missing(value):
            return None
        return float(clean(value))
    except Exception:
        return None


def fmt(value: float | None) -> str:
    return "NA" if value is None or math.isnan(value) else f"{value:.10g}"


def rate(numerator: int, denominator: int) -> str:
    return "0" if denominator == 0 else f"{numerator / denominator:.6f}".rstrip("0").rstrip(".")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def current_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        return "unknown"


def write_preview(report_root: Path, name: str, rows: list[dict[str, object]], fields: list[str], n: int = 500) -> None:
    write_tsv(report_root / f"{name}.preview.tsv", rows[:n], fields)


def build_object_score_adapter(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    rows = [
        {
            "adapter_id": "ADAPT_VARIANT_EXACT_V1",
            "object_type": "variant",
            "preferred_score_level": "variant",
            "fallback_score_level": "window",
            "aggregation_method": "exact_variant_score",
            "score_source": "baseline",
            "allowed_for_dry_run": "true",
            "allowed_for_formal_eval": "false",
            "requires_exact_variant_match": "true",
            "requires_exact_window_match": "false",
            "requires_interval_overlap": "false",
            "dry_run_only": "true",
            "notes": "variant objects use exact variant-level baseline score in this dry-run; formal evaluator still undefined",
        },
        {
            "adapter_id": "ADAPT_WINDOW_EXACT_V1",
            "object_type": "window",
            "preferred_score_level": "window",
            "fallback_score_level": "variant",
            "aggregation_method": "exact_window_score",
            "score_source": "baseline",
            "allowed_for_dry_run": "true",
            "allowed_for_formal_eval": "false",
            "requires_exact_variant_match": "false",
            "requires_exact_window_match": "true",
            "requires_interval_overlap": "false",
            "dry_run_only": "true",
            "notes": "window objects use exact window-level baseline score in this dry-run; formal evaluator still undefined",
        },
        {
            "adapter_id": "ADAPT_GENE_WINDOW_MEAN_V1",
            "object_type": "gene",
            "preferred_score_level": "window",
            "fallback_score_level": "nearest_window",
            "aggregation_method": "mean_overlapping_window_score",
            "score_source": "baseline",
            "allowed_for_dry_run": "true",
            "allowed_for_formal_eval": "false",
            "requires_exact_variant_match": "false",
            "requires_exact_window_match": "false",
            "requires_interval_overlap": "true",
            "dry_run_only": "true",
            "notes": "gene objects are scored by overlapping-window aggregation for adapter diagnostics only; not a formal metric",
        },
        {
            "adapter_id": "ADAPT_QTL_INTERVAL_WINDOW_MEAN_V1",
            "object_type": "qtl_interval",
            "preferred_score_level": "window",
            "fallback_score_level": "nearest_window",
            "aggregation_method": "mean_overlapping_window_score",
            "score_source": "baseline",
            "allowed_for_dry_run": "true",
            "allowed_for_formal_eval": "false",
            "requires_exact_variant_match": "false",
            "requires_exact_window_match": "false",
            "requires_interval_overlap": "true",
            "dry_run_only": "true",
            "notes": "QTL interval objects are scored by overlapping-window aggregation for adapter diagnostics only; not a formal metric",
        },
    ]
    write_tsv(args.interim_root / "adapter/object_score_adapter_table.tsv", rows, ADAPTER_FIELDS)
    write_tsv(args.report_root / "object_score_adapter_table.tsv", rows, ADAPTER_FIELDS)
    return rows


def load_adapter(args: argparse.Namespace) -> dict[str, dict[str, str]]:
    rows = read_tsv(args.interim_root / "adapter/object_score_adapter_table.tsv")
    if not rows:
        rows = build_object_score_adapter(args)
    return {row["object_type"]: row for row in rows}


def source_key(baseline_name: str) -> str:
    return f"baseline:{baseline_name}"


def load_score_tables(args: argparse.Namespace) -> tuple[dict[tuple[str, str, str, str], float], dict[tuple[str, str, str, str], float], list[tuple[str, str]]]:
    window_scores: dict[tuple[str, str, str, str], float] = {}
    variant_scores: dict[tuple[str, str, str, str], float] = {}
    sources: set[tuple[str, str]] = set()
    for path, container, key_field in [
        (args.baseline_root / "window_baseline_scores.tsv", window_scores, "window_id"),
        (args.baseline_root / "variant_baseline_scores.tsv", variant_scores, "variant_id"),
    ]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                src = source_key(row.get("baseline_name", "baseline"))
                version = row.get("run_id", "NA")
                score = to_float(row.get("score"))
                if score is None:
                    continue
                container[(src, version, row["trait_id"], row[key_field])] = score
                sources.add((src, version))
    return window_scores, variant_scores, sorted(sources)


def load_windows(args: argparse.Namespace) -> list[dict[str, object]]:
    windows = []
    for row in read_tsv(args.v01_root / "window_table_chr1_v0_1.tsv"):
        windows.append(
            {
                "window_id": row["window_id"],
                "chrom": clean(row.get("chrom")),
                "start": to_int(row.get("start")),
                "end": to_int(row.get("end")),
            }
        )
    return windows


def parse_bg_id(decoy_object_id: str) -> tuple[str, str, int | None, int | None]:
    if decoy_object_id.startswith("VARIANT_BG_"):
        variant_id = decoy_object_id.replace("VARIANT_BG_", "", 1)
        parts = variant_id.split("_")
        if len(parts) >= 3:
            return "variant", variant_id, to_int(parts[-2], -1), to_int(parts[-1], -1)
        return "variant", variant_id, None, None
    if decoy_object_id.startswith("WINDOW_BG_"):
        window_id = decoy_object_id.replace("WINDOW_BG_", "", 1)
        parts = window_id.split("_")
        if len(parts) >= 3:
            return "window", window_id, to_int(parts[-2], -1), to_int(parts[-1], -1)
        return "window", window_id, None, None
    if decoy_object_id.startswith("INTERVAL_BG_"):
        interval_id = decoy_object_id.replace("INTERVAL_BG_", "", 1)
        parts = interval_id.split("_")
        if len(parts) >= 3:
            return "qtl_interval", interval_id, to_int(parts[-2], -1), to_int(parts[-1], -1)
        return "qtl_interval", interval_id, None, None
    if decoy_object_id.startswith("GENE_BG_"):
        return "gene", decoy_object_id.replace("GENE_BG_", "", 1), None, None
    return "unknown", decoy_object_id, None, None


def load_candidate_coords(args: argparse.Namespace) -> dict[str, dict[str, object]]:
    coords: dict[str, dict[str, object]] = {}
    path = args.matched_decoy_root / "candidate_pool/matched_decoy_candidate_pool.tsv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            cid = row.get("candidate_object_id", "")
            if cid and cid not in coords:
                coords[cid] = {
                    "chrom": clean(row.get("candidate_chrom")),
                    "start": to_int(row.get("candidate_start")),
                    "end": to_int(row.get("candidate_end")),
                }
    return coords


def overlapping_window_ids(windows: list[dict[str, object]], chrom: str, start: int, end: int) -> list[str]:
    if start <= 0 or end <= 0:
        return []
    hits = [
        str(row["window_id"])
        for row in windows
        if row["chrom"] == chrom and int(row["start"]) <= end and int(row["end"]) >= start
    ]
    if hits:
        return hits
    midpoint = (start + end) / 2
    same_chrom = [row for row in windows if row["chrom"] == chrom]
    if not same_chrom:
        return []
    nearest = min(same_chrom, key=lambda row: min(abs(midpoint - int(row["start"])), abs(midpoint - int(row["end"]))))
    return [str(nearest["window_id"])]


def score_interval(
    window_scores: dict[tuple[str, str, str, str], float],
    windows: list[dict[str, object]],
    source: str,
    version: str,
    trait_id: str,
    chrom: str,
    start: int,
    end: int,
) -> tuple[float | None, str]:
    window_ids = overlapping_window_ids(windows, chrom, start, end)
    values = [window_scores[(source, version, trait_id, wid)] for wid in window_ids if (source, version, trait_id, wid) in window_scores]
    if not values:
        return None, "window"
    return mean(values), "window"


def evidence_score(
    obj: dict[str, str],
    source: str,
    version: str,
    window_scores: dict[tuple[str, str, str, str], float],
    variant_scores: dict[tuple[str, str, str, str], float],
    windows: list[dict[str, object]],
) -> tuple[float | None, str]:
    trait_id = obj["trait_id"]
    object_type = obj["object_type"]
    if object_type == "variant":
        return variant_scores.get((source, version, trait_id, obj.get("variant_id", ""))), "variant"
    if object_type == "window":
        return window_scores.get((source, version, trait_id, obj.get("window_id", ""))), "window"
    return score_interval(
        window_scores,
        windows,
        source,
        version,
        trait_id,
        clean(obj.get("chrom")),
        to_int(obj.get("start")),
        to_int(obj.get("end")),
    )


def decoy_score(
    decoy: dict[str, str],
    source: str,
    version: str,
    window_scores: dict[tuple[str, str, str, str], float],
    variant_scores: dict[tuple[str, str, str, str], float],
    windows: list[dict[str, object]],
    candidate_coords: dict[str, dict[str, object]],
) -> tuple[float | None, str]:
    trait_id = decoy["trait_id"]
    decoy_object_id = decoy["decoy_object_id"]
    bg_type, bg_id, parsed_start, parsed_end = parse_bg_id(decoy_object_id)
    if bg_type == "variant":
        return variant_scores.get((source, version, trait_id, bg_id)), "variant"
    if bg_type == "window":
        return window_scores.get((source, version, trait_id, bg_id)), "window"
    coords = candidate_coords.get(decoy_object_id)
    if coords:
        chrom = clean(coords.get("chrom"))
        start = to_int(coords.get("start"))
        end = to_int(coords.get("end"))
    else:
        chrom = "1"
        start = parsed_start or 0
        end = parsed_end or 0
    return score_interval(window_scores, windows, source, version, trait_id, chrom, start, end)


def build_dry_run_matched_set_scores(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    adapter = load_adapter(args)
    objects = read_tsv(args.scaffold_root / "inputs/evaluator_object_input_table.tsv")
    decoys = read_tsv(args.scaffold_root / "inputs/evaluator_decoy_input_table.tsv")
    decoys_by_object: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decoys:
        decoys_by_object[row["object_id"]].append(row)
    window_scores, variant_scores, sources = load_score_tables(args)
    windows = load_windows(args)
    candidate_coords = load_candidate_coords(args)

    output_path = args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv"
    if output_path.exists():
        output_path.unlink()
    preview: list[dict[str, object]] = []
    write_header = True
    batch: list[dict[str, object]] = []
    matched_sets_written = 0

    for obj in objects:
        if obj.get("assigned_split") not in ALLOWED_SPLITS:
            continue
        object_decoys = decoys_by_object.get(obj["object_id"], [])
        expected = to_int(obj.get("n_matched_decoys"), len(object_decoys)) or len(object_decoys)
        obj_adapter = adapter[obj["object_type"]]
        adapter_id = obj_adapter["adapter_id"]
        notes = "dry-run exact score join; not a formal metric"
        if obj["object_type"] in {"gene", "qtl_interval"}:
            notes = "dry-run adapter aggregation diagnostic only; not a formal metric"
        for source, version in sources:
            ev_score, ev_level = evidence_score(obj, source, version, window_scores, variant_scores, windows)
            scored_decoys: list[tuple[dict[str, str], float | None, str]] = [
                (decoy, *decoy_score(decoy, source, version, window_scores, variant_scores, windows, candidate_coords))
                for decoy in object_decoys
            ]
            n_decoys_with_score = sum(score is not None for _, score, _ in scored_decoys)
            matched_set_id = f"MSET_{obj['object_id']}_{source.replace(':', '_')}_{version}"
            for decoy, score, level in scored_decoys:
                row = {
                    "matched_set_id": matched_set_id,
                    "object_id": obj["object_id"],
                    "decoy_object_id": decoy["decoy_object_id"],
                    "trait_id": obj["trait_id"],
                    "object_type": obj["object_type"],
                    "assigned_split": obj["assigned_split"],
                    "prototype_locked_not_final": obj["prototype_locked_not_final"],
                    "score_source": source,
                    "score_version": version,
                    "score_level_used": ev_level if ev_score is not None else level,
                    "adapter_id": adapter_id,
                    "evidence_score": fmt(ev_score),
                    "decoy_score": fmt(score),
                    "score_available_evidence": ev_score is not None,
                    "score_available_decoy": score is not None,
                    "n_decoys_expected": expected,
                    "n_decoys_with_score": n_decoys_with_score,
                    "decoy_semantics": "matched_background",
                    "uses_true_negative": "false",
                    "uses_unknown_as_negative": "false",
                    "dry_run_only": "true",
                    "notes": notes,
                }
                if len(preview) < 500:
                    preview.append(dict(row))
                batch.append(row)
                matched_sets_written += 1
                if len(batch) >= 50_000:
                    append_tsv_rows(output_path, batch, MATCHED_SET_FIELDS, write_header=write_header)
                    write_header = False
                    batch = []
    if batch:
        append_tsv_rows(output_path, batch, MATCHED_SET_FIELDS, write_header=write_header)
    write_preview(args.report_root, "dry_run_matched_set_score_table", preview, MATCHED_SET_FIELDS)
    return [{"rows": matched_sets_written}]


def compute_dry_run_rank_positions(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    matched_path = args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv"
    groups: dict[tuple[str, str, str], dict[str, object]] = {}
    with matched_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            key = (row["matched_set_id"], row["object_id"], row["score_source"])
            group = groups.setdefault(
                key,
                {
                    "object_id": row["object_id"],
                    "trait_id": row["trait_id"],
                    "object_type": row["object_type"],
                    "assigned_split": row["assigned_split"],
                    "prototype_locked_not_final": row["prototype_locked_not_final"],
                    "score_source": row["score_source"],
                    "score_version": row["score_version"],
                    "score_level_used": row["score_level_used"],
                    "adapter_id": row["adapter_id"],
                    "n_decoys_expected": to_int(row["n_decoys_expected"]),
                    "evidence_score": to_float(row["evidence_score"]),
                    "decoy_scores": [],
                },
            )
            decoy_value = to_float(row["decoy_score"])
            if decoy_value is not None:
                group["decoy_scores"].append(decoy_value)
    rows: list[dict[str, object]] = []
    for group in groups.values():
        evidence_value = group["evidence_score"]
        decoy_scores = list(group["decoy_scores"])
        n_decoys = len(decoy_scores)
        can_rank = evidence_value is not None and n_decoys > 0
        failure = "NA"
        dry_rank: int | str = "NA"
        percentile: str | float = "NA"
        top1 = "false"
        top5 = "false"
        mean_delta: str | float = "NA"
        median_delta: str | float = "NA"
        if can_rank:
            dry_rank = 1 + sum(score > evidence_value for score in decoy_scores)
            n_rankable = n_decoys + 1
            percentile = (n_rankable - int(dry_rank) + 1) / n_rankable
            top1 = str(int(dry_rank) == 1).lower()
            top5 = str(int(dry_rank) <= 5).lower()
            mean_delta = evidence_value - mean(decoy_scores)
            median_delta = evidence_value - median(decoy_scores)
        else:
            reasons = []
            if evidence_value is None:
                reasons.append("missing_evidence_score")
            if n_decoys == 0:
                reasons.append("no_decoy_score")
            failure = ";".join(reasons) if reasons else "rank_unavailable"
        rows.append(
            {
                "rank_record_id": f"DRRANK_{len(rows) + 1:09d}",
                "object_id": group["object_id"],
                "trait_id": group["trait_id"],
                "object_type": group["object_type"],
                "assigned_split": group["assigned_split"],
                "prototype_locked_not_final": group["prototype_locked_not_final"],
                "score_source": group["score_source"],
                "score_version": group["score_version"],
                "score_level_used": group["score_level_used"],
                "adapter_id": group["adapter_id"],
                "n_decoys_expected": group["n_decoys_expected"],
                "n_decoys_with_score": n_decoys,
                "n_decoys_rankable": n_decoys if evidence_value is not None else 0,
                "evidence_score": fmt(evidence_value),
                "dry_run_rank": dry_rank,
                "dry_run_rank_percentile": percentile,
                "dry_run_top1_indicator": top1,
                "dry_run_top5_indicator": top5,
                "evidence_vs_decoy_mean_delta": mean_delta,
                "evidence_vs_decoy_median_delta": median_delta,
                "can_rank": str(can_rank).lower(),
                "rank_failure_reason": failure,
                "dry_run_only": "true",
                "notes": "rank position is dry-run diagnostic only; not a formal top-k or benchmark metric",
            }
        )
    write_tsv(args.interim_root / "ranks/dry_run_rank_position_table.tsv", rows, RANK_FIELDS)
    write_preview(args.report_root, "dry_run_rank_position_table", rows, RANK_FIELDS)
    return rows


def summarize_dry_run_score_coverage(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    rank_rows = read_tsv(args.interim_root / "ranks/dry_run_rank_position_table.tsv")
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rank_rows:
        groups[(row["assigned_split"], row["trait_id"], row["object_type"], row["score_source"], row["score_level_used"])].append(row)
    coverage_rows: list[dict[str, object]] = []
    for key, rows in sorted(groups.items()):
        assigned_split, trait_id, object_type, score_source, score_level = key
        n_objects = len(rows)
        decoy_counts = [to_int(row.get("n_decoys_with_score")) for row in rows]
        expected = [to_int(row.get("n_decoys_expected")) for row in rows]
        n_evidence = sum(not is_missing(row.get("evidence_score")) for row in rows)
        n_any = sum(to_int(row.get("n_decoys_with_score")) > 0 for row in rows)
        n_all = sum(to_int(row.get("n_decoys_with_score")) >= to_int(row.get("n_decoys_expected")) for row in rows)
        notes = "exact score coverage"
        if object_type in {"gene", "qtl_interval"}:
            notes = "coverage depends on overlapping-window dry-run adapter aggregation; diagnostic only"
        coverage_rows.append(
            {
                "coverage_id": f"DRCOV_{len(coverage_rows) + 1:08d}",
                "assigned_split": assigned_split,
                "trait_id": trait_id,
                "object_type": object_type,
                "score_source": score_source,
                "score_level_used": score_level,
                "n_objects": n_objects,
                "n_objects_with_evidence_score": n_evidence,
                "n_objects_with_any_decoy_score": n_any,
                "n_objects_with_all_decoy_scores": n_all,
                "mean_decoys_with_score": mean(decoy_counts) if decoy_counts else 0,
                "median_decoys_with_score": median(decoy_counts) if decoy_counts else 0,
                "coverage_rate_evidence": rate(n_evidence, n_objects),
                "coverage_rate_decoy_any": rate(n_any, n_objects),
                "coverage_rate_decoy_all": rate(n_all, n_objects),
                "dry_run_only": "true",
                "notes": notes,
            }
        )

    missing_rows: list[dict[str, object]] = []
    for row in rank_rows:
        missing_evidence = is_missing(row.get("evidence_score"))
        n_with = to_int(row.get("n_decoys_with_score"))
        n_expected = to_int(row.get("n_decoys_expected"))
        can_rank = row.get("can_rank") == "true"
        if missing_evidence or not can_rank or n_with < n_expected:
            reason = row.get("rank_failure_reason", "NA")
            if can_rank and n_with < n_expected:
                reason = "partial_decoy_score_coverage"
            missing_rows.append(
                {
                    "diagnostic_id": f"DRMISS_{len(missing_rows) + 1:09d}",
                    "object_id": row["object_id"],
                    "trait_id": row["trait_id"],
                    "object_type": row["object_type"],
                    "assigned_split": row["assigned_split"],
                    "score_source": row["score_source"],
                    "score_level_expected": row["score_level_used"],
                    "missing_evidence_score": str(missing_evidence).lower(),
                    "n_decoys_expected": n_expected,
                    "n_decoys_with_score": n_with,
                    "can_rank": row["can_rank"],
                    "failure_reason": reason,
                    "dry_run_only": "true",
                    "notes": "score/rank diagnostic only; no object is silently filtered",
                }
            )
    if not missing_rows:
        missing_rows.append(
            {
                "diagnostic_id": "DRMISS_000000001",
                "object_id": "NA",
                "trait_id": "NA",
                "object_type": "NA",
                "assigned_split": "NA",
                "score_source": "NA",
                "score_level_expected": "NA",
                "missing_evidence_score": "false",
                "n_decoys_expected": 0,
                "n_decoys_with_score": 0,
                "can_rank": "true",
                "failure_reason": "no_missing_or_unrankable_objects_detected",
                "dry_run_only": "true",
                "notes": "summary row retained so diagnostics table is explicit and nonempty",
            }
        )
    write_tsv(args.interim_root / "coverage/dry_run_score_coverage_table.tsv", coverage_rows, COVERAGE_FIELDS)
    write_tsv(args.report_root / "dry_run_score_coverage_table.tsv", coverage_rows, COVERAGE_FIELDS)
    write_tsv(args.interim_root / "diagnostics/dry_run_missing_score_diagnostics.tsv", missing_rows, MISSING_FIELDS)
    write_preview(args.report_root, "dry_run_missing_score_diagnostics", missing_rows, MISSING_FIELDS)
    return coverage_rows, missing_rows


def build_evaluator_adapter_contract(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    rows = [
        ("score_table_must_provide_trait_level_score", "Formal evaluator score input must be trait-conditioned.", "dry-run baseline scores provide trait_id.", "false", "Current dry-run uses existing trait-level baseline maps."),
        ("accession_level_score_must_be_aggregated", "Accession-level scores must be aggregated before formal evidence evaluation.", "accession_id is not accepted in 09B dry-run outputs.", "true", "Formal model adapters need a declared aggregation recipe."),
        ("decoy_must_be_matched_background", "Decoy records must be treated as matched_background only.", "dry_run_matched_set_score_table sets decoy_semantics=matched_background.", "false", "Decoys are not true negatives."),
        ("unknown_unlabeled_cannot_be_negative", "Unknown or unlabeled variants/windows cannot be negatives.", "uses_unknown_as_negative=false in matched-set rows.", "false", "Genome-wide unknowns are outside this dry-run matched set."),
        ("object_type_specific_adapters_declared", "Each object_type must have an explicit score adapter.", "adapter table covers variant, window, gene, and qtl_interval.", "false", "Gene and QTL adapters are diagnostic only."),
        ("prototype_locked_is_not_final_locked", "Prototype locked split is non-final.", "prototype_locked_not_final is retained and true.", "false", "No final full benchmark split is created."),
        ("gene_qtl_interval_need_formal_aggregation_rule", "Gene/QTL interval scoring needs formal aggregation before formal metrics.", "current aggregation is overlapping-window mean for dry-run diagnostic.", "true", "Do not interpret gene/QTL rank rows as formal metrics."),
    ]
    output = [
        {
            "contract_item": item,
            "requirement": requirement,
            "current_status": status,
            "blocking_for_formal_eval": blocking,
            "dry_run_only": "true",
            "notes": notes,
        }
        for item, requirement, status, blocking, notes in rows
    ]
    write_tsv(args.interim_root / "diagnostics/dry_run_evaluator_adapter_contract.tsv", output, CONTRACT_FIELDS)
    write_tsv(args.report_root / "dry_run_evaluator_adapter_contract.tsv", output, CONTRACT_FIELDS)
    return output


def build_dry_run_leakage_guard(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    objects = read_tsv(args.scaffold_root / "inputs/evaluator_object_input_table.tsv")
    matched = read_tsv(args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv")
    adapter = read_tsv(args.interim_root / "adapter/object_score_adapter_table.tsv")
    matched_objects = read_tsv(args.matched_decoy_root / "objects/matched_decoy_object_table.tsv")
    matched_object_by_id = {row["object_id"]: row for row in matched_objects}
    scaffold_guard = read_tsv(args.scaffold_root / "diagnostics/evaluator_leakage_guard.tsv")
    rows: list[dict[str, object]] = []

    def add(name: str, ok: bool, n_checked: int, n_failed: int, details: str, blocking: bool = True, notes: str = "NA") -> None:
        rows.append(
            {
                "guard_id": f"DRGUARD_{len(rows) + 1:08d}",
                "guard_name": name,
                "status": "pass" if ok else ("warn" if not blocking else "fail"),
                "n_checked": n_checked,
                "n_failed": n_failed,
                "details": details,
                "blocking_issue": str(blocking and not ok).lower(),
                "dry_run_only": "true",
                "notes": notes,
            }
        )

    training = [row for row in objects if matched_object_by_id.get(row["object_id"], {}).get("allowed_usage") == "training_label"]
    add("evidence_allowed_usage_not_training_label", not training, len(objects), len(training), "evaluator objects do not use training_label")
    true_neg = [row for row in matched if row.get("uses_true_negative") != "false" or row.get("decoy_semantics") != "matched_background"]
    add("decoy_uses_true_negative_false", not true_neg, len(matched), len(true_neg), "decoy rows are matched_background and uses_true_negative=false")
    unknown = [row for row in matched if row.get("uses_unknown_as_negative") != "false"]
    add("unknown_as_negative_false", not unknown, len(matched), len(unknown), "uses_unknown_as_negative=false")
    manual = [row for row in objects if row.get("manual_review_required") == "true"]
    add("manual_review_not_in_matched_ranking", not manual, len(objects), len(manual), "manual review excluded upstream")
    broader = [row for row in objects if row.get("broader_evidence") == "true"]
    add("broader_evidence_not_in_matched_ranking", not broader, len(objects), len(broader), "broader evidence excluded upstream")
    proto_bad = [row for row in matched if row.get("prototype_locked_not_final") != "true"]
    add("prototype_locked_not_final_true", not proto_bad, len(matched), len(proto_bad), "prototype_locked_not_final=true in matched rows")
    headers = set()
    for path in [
        args.interim_root / "adapter/object_score_adapter_table.tsv",
        args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv",
        args.interim_root / "ranks/dry_run_rank_position_table.tsv",
        args.interim_root / "coverage/dry_run_score_coverage_table.tsv",
        args.interim_root / "diagnostics/dry_run_evaluator_adapter_contract.tsv",
    ]:
        if path.exists():
            with path.open("r", encoding="utf-8", newline="") as handle:
                headers.update(next(csv.reader(handle, delimiter="\t")))
    add("final_locked_field_absent", "final_locked" not in headers, len(headers), 1 if "final_locked" in headers else 0, "no final_locked field name in 09B outputs")
    add("accession_id_not_score_input_field", "accession_id" not in headers, len(headers), 1 if "accession_id" in headers else 0, "accession_id is not a 09B output score field")
    accession_level = [row for row in adapter if "accession" in row.get("preferred_score_level", "") or "accession" in row.get("fallback_score_level", "")]
    add("accession_level_score_not_direct_formal_evaluation", not accession_level, len(adapter), len(accession_level), "adapter table does not define accession-level direct evaluation")
    scaffold_fail = [row for row in scaffold_guard if row.get("blocking_issue") == "true" or row.get("status") == "fail"]
    add("split_leakage_guard_source_passed", not scaffold_fail, len(scaffold_guard), len(scaffold_fail), "inherits 09A evaluator leakage guard")
    write_tsv(args.interim_root / "diagnostics/dry_run_leakage_guard.tsv", rows, GUARD_FIELDS)
    write_tsv(args.report_root / "dry_run_leakage_guard.tsv", rows, GUARD_FIELDS)
    return rows


def validate_evaluator_dry_run(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    build_evaluator_adapter_contract(args)
    guards = build_dry_run_leakage_guard(args)
    adapter = read_tsv(args.interim_root / "adapter/object_score_adapter_table.tsv")
    matched = read_tsv(args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv")
    ranks = read_tsv(args.interim_root / "ranks/dry_run_rank_position_table.tsv")
    coverage = read_tsv(args.interim_root / "coverage/dry_run_score_coverage_table.tsv")
    missing = read_tsv(args.interim_root / "diagnostics/dry_run_missing_score_diagnostics.tsv")
    rows: list[dict[str, object]] = []

    def add(check: str, ok: bool, n_records: int, n_failed: int, details: str, blocking: bool = True, notes: str = "NA") -> None:
        rows.append(
            {
                "check_name": check,
                "status": "pass" if ok else ("warn" if not blocking else "fail"),
                "n_records": n_records,
                "n_failed": n_failed,
                "details": details,
                "blocking_issue": str(blocking and not ok).lower(),
                "dry_run_only": "true",
                "notes": notes,
            }
        )

    expected = [
        args.interim_root / "adapter/object_score_adapter_table.tsv",
        args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv",
        args.interim_root / "ranks/dry_run_rank_position_table.tsv",
        args.interim_root / "coverage/dry_run_score_coverage_table.tsv",
        args.interim_root / "diagnostics/dry_run_missing_score_diagnostics.tsv",
        args.interim_root / "diagnostics/dry_run_evaluator_adapter_contract.tsv",
        args.interim_root / "diagnostics/dry_run_leakage_guard.tsv",
    ]
    missing_files = [rel(path) for path in expected if count_rows(path) == 0]
    add("outputs_exist_and_nonempty", not missing_files, len(expected), len(missing_files), ";".join(missing_files) if missing_files else "all outputs nonempty")
    dry_bad = [row for row in matched + ranks if row.get("dry_run_only") != "true"]
    add("dry_run_only_true", not dry_bad, len(matched) + len(ranks), len(dry_bad), "matched-set and rank rows are dry_run_only=true")
    formal_fields = [field for field in set().union(*(row.keys() for row in matched + ranks + coverage)) if "formal" in field.lower() or field.lower() == "metric"]
    add("no_formal_metric_output", not formal_fields, len(formal_fields), len(formal_fields), "no formal metric field in 09B core outputs")
    headers = set().union(*(row.keys() for row in matched + ranks + coverage + missing))
    auroc_fields = [field for field in headers if "auroc" in field.lower() or "auprc" in field.lower()]
    add("no_auroc_auprc_fields", not auroc_fields, len(headers), len(auroc_fields), "no AUROC/AUPRC output fields")
    add("rank_table_not_formal_result", all(field.startswith("dry_run_") or not field.endswith("_indicator") for field in RANK_FIELDS), len(RANK_FIELDS), 0, "rank diagnostic fields use dry_run prefix")
    true_neg = [row for row in matched if row.get("uses_true_negative") != "false" or row.get("decoy_semantics") != "matched_background"]
    add("decoy_not_true_negative", not true_neg, len(matched), len(true_neg), "decoy rows are matched background only")
    unknown = [row for row in matched if row.get("uses_unknown_as_negative") != "false"]
    add("unknown_unlabeled_not_negative", not unknown, len(matched), len(unknown), "unknown/unlabeled not used as negative")
    add("missing_score_has_diagnostics", bool(missing), len(missing), 0 if missing else 1, "missing/partial score diagnostics table is explicit")
    adapter_types = {row.get("object_type") for row in adapter}
    absent = sorted(set(OBJECT_TYPES) - adapter_types)
    add("object_score_adapter_covers_all_object_types", not absent, len(adapter), len(absent), ";".join(absent) if absent else "all object types covered")
    diagnostic_bad = [
        row
        for row in adapter
        if row.get("object_type") in {"gene", "qtl_interval"}
        and (row.get("allowed_for_formal_eval") != "false" or "diagnostic" not in row.get("notes", "").lower())
    ]
    add("gene_qtl_interval_adapter_diagnostic_only", not diagnostic_bad, len(adapter), len(diagnostic_bad), "gene/qtl interval adapters are diagnostic and not formal")
    blocking_guards = [row for row in guards if row.get("blocking_issue") == "true"]
    add("validation_no_blocking_issue", not blocking_guards, len(guards), len(blocking_guards), "dry-run leakage guards have no blocking issue")
    write_tsv(args.interim_root / "diagnostics/dry_run_validation.tsv", rows, VALIDATION_FIELDS)
    write_tsv(args.report_root / "dry_run_validation.tsv", rows, VALIDATION_FIELDS)
    write_report(args, adapter, matched, ranks, coverage, missing, guards, rows)
    return rows


def write_report(
    args: argparse.Namespace,
    adapter: list[dict[str, str]],
    matched: list[dict[str, str]],
    ranks: list[dict[str, str]],
    coverage: list[dict[str, str]],
    missing: list[dict[str, str]],
    guards: list[dict[str, str]],
    validation: list[dict[str, object]],
) -> None:
    files = [
        args.interim_root / "adapter/object_score_adapter_table.tsv",
        args.interim_root / "matched_sets/dry_run_matched_set_score_table.tsv",
        args.interim_root / "ranks/dry_run_rank_position_table.tsv",
        args.interim_root / "coverage/dry_run_score_coverage_table.tsv",
        args.interim_root / "diagnostics/dry_run_missing_score_diagnostics.tsv",
        args.interim_root / "diagnostics/dry_run_evaluator_adapter_contract.tsv",
        args.interim_root / "diagnostics/dry_run_leakage_guard.tsv",
        args.interim_root / "diagnostics/dry_run_validation.tsv",
    ]
    object_counter = Counter(row.get("object_type") for row in ranks)
    split_counter = Counter(row.get("assigned_split") for row in ranks)
    source_counter = Counter(row.get("score_source") for row in ranks)
    rankable = sum(row.get("can_rank") == "true" for row in ranks)
    unrankable = len(ranks) - rankable
    split_coverage_lines = []
    for split in ["dev", "prototype_locked", "source_disjoint_or_temporal"]:
        split_rows = [row for row in ranks if row.get("assigned_split") == split]
        split_rankable = sum(row.get("can_rank") == "true" for row in split_rows)
        split_all_decoys = sum(to_int(row.get("n_decoys_with_score")) >= to_int(row.get("n_decoys_expected")) for row in split_rows)
        split_coverage_lines.append(
            f"- {split}: rankable {split_rankable}/{len(split_rows)} ({rate(split_rankable, len(split_rows))}); all-decoy score coverage {split_all_decoys}/{len(split_rows)} ({rate(split_all_decoys, len(split_rows))})."
        )
    true_neg = sum(row.get("uses_true_negative") != "false" for row in matched)
    unknown_neg = sum(row.get("uses_unknown_as_negative") != "false" for row in matched)
    manual_or_broader = sum(
        row.get("guard_name") in {"manual_review_not_in_matched_ranking", "broader_evidence_not_in_matched_ranking"}
        and to_int(row.get("n_failed")) != 0
        for row in guards
    )
    failed = [row for row in validation if row.get("status") == "fail"]
    coverage_summary = summarize_counter(Counter((row.get("object_type"), row.get("score_source")) for row in coverage), limit=8)
    adapter_lines = [
        f"- {row['object_type']}: {row['adapter_id']} ({row['aggregation_method']}); allowed_for_formal_eval={row['allowed_for_formal_eval']}."
        for row in adapter
    ]
    lines = [
        "# Matched-Ranking Dry-Run v0.5.5 Report",
        "",
        "## Scope",
        "",
        "This run is a matched-ranking dry-run and evaluator adapter smoke test for the chr1 SNP-only prototype. It is not a formal evaluator and does not create final locked evaluation outputs.",
        "",
        "No model was trained. No formal AUROC/AUPRC was reported. Evidence is not a training label, matched decoys are matched background only, and unknown/unlabeled rows are not negatives.",
        "",
        "## Generated Tables",
        "",
        "| table | rows |",
        "|---|---:|",
    ]
    for path in files:
        lines.append(f"| `{rel(path)}` | {count_rows(path)} |")
    lines.extend(
        [
            "",
            "## Inputs",
            "",
            f"- Input commit hash: `{current_commit(args.repo_root)}`.",
            "- Baseline score sources used: `random_uniform`, `window_snp_density`, `genomic_position`, and `shuffled_trait` from the chr1 SNP prototype baseline score tables.",
            "- Score sources are represented as `baseline:<baseline_name>` in dry-run outputs.",
            "",
            "## Adapter Summary",
            "",
            *adapter_lines,
            "",
            "## Coverage And Rank Diagnostics",
            "",
            f"- Rank diagnostic rows: {len(ranks)}.",
            f"- Rankable object/source rows: {rankable}.",
            f"- Unrankable object/source rows: {unrankable}.",
            f"- Object types in rank diagnostics: {summarize_counter(object_counter)}.",
            f"- Split distribution in rank diagnostics: {summarize_counter(split_counter)}.",
            f"- Score sources in rank diagnostics: {summarize_counter(source_counter)}.",
            f"- Coverage groups by object_type/source: {coverage_summary}.",
            "",
            "Split-level score coverage:",
            "",
            *split_coverage_lines,
            "",
            "- Dry-run rank, percentile, top1, and top5 fields are process diagnostics only and are not formal top-k hit rates.",
            "- Gene and qtl_interval rank rows use overlapping-window adapter aggregation and are diagnostic only.",
            "",
            "## Guard Summary",
            "",
            f"- Manual review / broader evidence guard failures: {manual_or_broader}.",
            f"- Decoy rows written as true negative: {true_neg}.",
            f"- Unknown/unlabeled rows written as negative: {unknown_neg}.",
            "- Accession_id is not required as a score input field in this dry-run.",
            f"- Validation failed checks: {len(failed)}.",
            f"- Missing-score diagnostic rows: {len(missing)}.",
            "",
            "## Current Limitations",
            "",
            "- This remains a chr1 SNP-only dry-run.",
            "- Variant and window object ranks use baseline scores only.",
            "- Gene and QTL interval scoring relies on overlapping-window mean aggregation and has not been formalized.",
            "- The dry-run does not define formal metric aggregation across traits, splits, or object types.",
            "- No accession-level score adapter is accepted for direct evidence evaluation.",
            "",
            "## Next Step",
            "",
            "The dry-run is ready to feed 09C evaluator scaffold hardening or a candidate gene explanation adapter, while still keeping formal metric reporting out of scope.",
        ]
    )
    (args.report_root / "matched_ranking_dry_run_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_counter(counter: Counter, limit: int = 12) -> str:
    return ";".join(f"{key}:{value}" for key, value in counter.most_common(limit)) if counter else "NA"


def print_summary(name: str, rows: list[dict[str, object]] | list[dict[str, str]], extra: str = "") -> None:
    print(f"{name}_rows={len(rows)}")
    if extra:
        print(extra)
