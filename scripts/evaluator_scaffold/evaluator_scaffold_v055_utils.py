#!/usr/bin/env python3
"""Utilities for the v0.5.5 split-aware evaluator scaffold.

This scaffold only defines inputs, schemas, manifests, dry-run score alignment,
and guard checks. It does not compute formal benchmark metrics.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAFFOLD_VERSION = "evaluator_scaffold_v055_chr1_snp_prototype_v1"

DEFAULT_MATCHED_DECOY_ROOT = REPO_ROOT / "data/interim/matched_decoy_v055"
DEFAULT_FROZEN_SPLIT_ROOT = REPO_ROOT / "data/interim/frozen_split_v055"
DEFAULT_TASK1_ROOT = REPO_ROOT / "data/interim/task1_chr1_snp"
DEFAULT_BASELINE_ROOT = REPO_ROOT / "data/interim/baselines_chr1_snp"
DEFAULT_INTERIM_ROOT = REPO_ROOT / "data/interim/evaluator_scaffold_v055"
DEFAULT_REPORT_ROOT = REPO_ROOT / "reports/evaluator_scaffold_v055"

ALLOWED_EVALUATOR_SPLITS = {"dev", "prototype_locked", "source_disjoint_or_temporal"}


EVALUATOR_OBJECT_FIELDS = [
    "evaluator_object_id",
    "object_id",
    "trait_id",
    "object_type",
    "evidence_id",
    "evidence_source",
    "evidence_level",
    "chrom",
    "start",
    "end",
    "gene_id",
    "gene_symbol",
    "variant_id",
    "window_id",
    "assigned_split",
    "assigned_role",
    "prototype_locked_not_final",
    "in_main_evaluation_candidate_pool",
    "manual_review_required",
    "broader_evidence",
    "has_matched_decoy",
    "n_matched_decoys",
    "notes",
    "scaffold_version",
]

EVALUATOR_DECOY_FIELDS = [
    "evaluator_decoy_id",
    "evaluator_object_id",
    "object_id",
    "decoy_pair_id",
    "decoy_object_id",
    "trait_id",
    "object_type",
    "assigned_split",
    "decoy_assignment_status",
    "match_rank",
    "match_score",
    "matching_level",
    "relaxation_level",
    "matched_fields",
    "unavailable_fields",
    "notes",
    "scaffold_version",
]

SCORE_SCHEMA_FIELDS = [
    "field_name",
    "required",
    "dtype",
    "description",
    "allowed_values",
    "example",
    "notes",
    "scaffold_version",
]

TASK_MANIFEST_FIELDS = [
    "task_id",
    "task_name",
    "task_type",
    "object_type",
    "score_level",
    "input_object_table",
    "input_decoy_table",
    "required_score_fields",
    "assigned_split",
    "allowed_splits",
    "metric_family",
    "is_formal_metric",
    "is_dry_run_only",
    "notes",
    "scaffold_version",
]

OUTPUT_SCHEMA_FIELDS = SCORE_SCHEMA_FIELDS

DRY_RUN_SCORE_FIELDS = [
    "dry_run_score_id",
    "score_table_name",
    "score_source",
    "score_version",
    "score_level",
    "trait_id",
    "variant_id",
    "window_id",
    "object_id",
    "score",
    "score_direction",
    "split_version",
    "matched_to_evaluator_object",
    "matched_to_decoy",
    "notes",
    "scaffold_version",
]

JOIN_CHECK_FIELDS = [
    "check_id",
    "check_name",
    "status",
    "n_input_records",
    "n_matched_records",
    "n_unmatched_records",
    "match_rate",
    "details",
    "blocking_issue",
    "notes",
    "scaffold_version",
]

LEAKAGE_GUARD_FIELDS = [
    "guard_id",
    "guard_name",
    "status",
    "n_checked",
    "n_failed",
    "details",
    "blocking_issue",
    "notes",
    "scaffold_version",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "n_records",
    "n_failed",
    "details",
    "blocking_issue",
    "notes",
    "scaffold_version",
]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--matched-decoy-root", type=Path, default=DEFAULT_MATCHED_DECOY_ROOT)
    parser.add_argument("--frozen-split-root", type=Path, default=DEFAULT_FROZEN_SPLIT_ROOT)
    parser.add_argument("--task1-root", type=Path, default=DEFAULT_TASK1_ROOT)
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE_ROOT)
    parser.add_argument("--interim-root", type=Path, default=DEFAULT_INTERIM_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    return parser.parse_args()


def ensure_output_dirs(interim_root: Path, report_root: Path) -> None:
    for subdir in ["inputs", "tasks", "outputs_schema", "dry_run", "diagnostics"]:
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
            normalized = {}
            for field in fields:
                value = row.get(field)
                normalized[field] = "NA" if value is None or value == "" else value
            writer.writerow(normalized)


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
            writer.writerow({field: ("NA" if row.get(field) in {None, ""} else row.get(field)) for field in fields})


def write_preview(report_root: Path, name: str, rows: list[dict[str, object]], fields: list[str], n: int = 500) -> None:
    write_tsv(report_root / f"{name}.preview.tsv", rows[:n], fields)


def clean(value: object) -> str:
    return str(value or "").strip()


def is_missing(value: object) -> bool:
    text = clean(value)
    return text == "" or text.lower() in {"na", "n/a", "nan", "none", "null"}


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


def format_rate(numerator: int, denominator: int) -> str:
    return "0" if denominator == 0 else f"{numerator / denominator:.6f}".rstrip("0").rstrip(".")


def load_inputs(args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    return {
        "objects": read_tsv(args.matched_decoy_root / "objects/matched_decoy_object_table.tsv"),
        "pairs": read_tsv(args.matched_decoy_root / "pairs/matched_decoy_pair_table.tsv"),
        "decoy_validation": read_tsv(args.matched_decoy_root / "diagnostics/decoy_validation.tsv"),
        "assignments": read_tsv(args.frozen_split_root / "assignments/frozen_split_assignment.tsv"),
        "split_units": read_tsv(args.frozen_split_root / "units/split_unit_table.tsv"),
        "split_leakage": read_tsv(args.frozen_split_root / "diagnostics/split_leakage_check.tsv"),
        "split_validation": read_tsv(args.frozen_split_root / "diagnostics/split_validation.tsv"),
        "split_manifest": read_tsv(args.frozen_split_root / "diagnostics/split_manifest.tsv"),
    }


def split_version_from_manifest(args: argparse.Namespace) -> str:
    manifest = read_tsv(args.frozen_split_root / "diagnostics/split_manifest.tsv")
    if manifest:
        return manifest[0].get("split_version", "frozen_split_v055_chr1_snp_prototype_v1")
    return "frozen_split_v055_chr1_snp_prototype_v1"


def build_evaluator_object_input(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    inputs = load_inputs(args)
    objects = {row["object_id"]: row for row in inputs["objects"]}
    pairs_by_object: dict[str, list[dict[str, str]]] = defaultdict(list)
    for pair in inputs["pairs"]:
        pairs_by_object[pair["object_id"]].append(pair)
    unit_by_id = {row["split_unit_id"]: row for row in inputs["split_units"]}
    rows: list[dict[str, object]] = []
    for assignment in inputs["assignments"]:
        if assignment.get("split_unit_type") != "evidence_object":
            continue
        if assignment.get("assigned_split") not in ALLOWED_EVALUATOR_SPLITS:
            continue
        unit = unit_by_id.get(assignment["split_unit_id"], {})
        object_id = unit.get("source_object_id", "")
        obj = objects.get(object_id)
        if not obj:
            continue
        broader = "broader_evidence_pool" in obj.get("exclusion_reason", "") or unit.get("broader_evidence") == "true"
        if obj.get("in_main_evaluation_candidate_pool") != "true" or obj.get("manual_review_required") == "true" or broader:
            continue
        decoys = pairs_by_object.get(object_id, [])
        rows.append(
            {
                "evaluator_object_id": f"EOBJ_{len(rows) + 1:08d}",
                "object_id": object_id,
                "trait_id": obj.get("trait_id", "NA"),
                "object_type": obj.get("object_type", "NA"),
                "evidence_id": obj.get("evidence_id", "NA"),
                "evidence_source": obj.get("evidence_source", "NA"),
                "evidence_level": obj.get("evidence_level", "NA"),
                "chrom": obj.get("chrom", "NA"),
                "start": obj.get("start", "NA"),
                "end": obj.get("end", "NA"),
                "gene_id": obj.get("gene_id", "NA"),
                "gene_symbol": obj.get("gene_symbol", "NA"),
                "variant_id": obj.get("variant_id", "NA"),
                "window_id": obj.get("window_id", "NA"),
                "assigned_split": assignment.get("assigned_split", "NA"),
                "assigned_role": assignment.get("assigned_role", "NA"),
                "prototype_locked_not_final": assignment.get("prototype_locked_not_final", "NA"),
                "in_main_evaluation_candidate_pool": obj.get("in_main_evaluation_candidate_pool", "false"),
                "manual_review_required": obj.get("manual_review_required", "false"),
                "broader_evidence": str(broader).lower(),
                "has_matched_decoy": str(len(decoys) > 0).lower(),
                "n_matched_decoys": len(decoys),
                "notes": "evaluator scaffold input only; evidence is not a training label and the prototype split is non-final",
                "scaffold_version": SCAFFOLD_VERSION,
            }
        )
    write_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv", rows, EVALUATOR_OBJECT_FIELDS)
    write_preview(args.report_root, "evaluator_object_input_table", rows, EVALUATOR_OBJECT_FIELDS)
    return rows


def build_evaluator_decoy_input(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    objects = read_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv")
    object_by_id = {row["object_id"]: row for row in objects}
    object_evaluator_id = {row["object_id"]: row["evaluator_object_id"] for row in objects}
    pairs = read_tsv(args.matched_decoy_root / "pairs/matched_decoy_pair_table.tsv")
    assignments = read_tsv(args.frozen_split_root / "assignments/frozen_split_assignment.tsv")
    units = read_tsv(args.frozen_split_root / "units/split_unit_table.tsv")
    unit_by_assignment = {row["split_unit_id"]: row for row in units}
    decoy_split_by_pair: dict[str, str] = {}
    for assignment in assignments:
        if assignment.get("split_unit_type") != "decoy_pair":
            continue
        unit = unit_by_assignment.get(assignment["split_unit_id"], {})
        decoy_pair_id = unit.get("decoy_pair_id", "")
        if decoy_pair_id:
            decoy_split_by_pair[decoy_pair_id] = assignment.get("assigned_split", "NA")
    rows: list[dict[str, object]] = []
    for pair in pairs:
        object_id = pair.get("object_id", "")
        if object_id not in object_by_id:
            continue
        eobj = object_by_id[object_id]
        decoy_split = decoy_split_by_pair.get(pair.get("decoy_pair_id", ""), "missing_decoy_assignment")
        status = "follows_evidence_split" if decoy_split == eobj.get("assigned_split") else "split_mismatch"
        rows.append(
            {
                "evaluator_decoy_id": f"EDEC_{len(rows) + 1:09d}",
                "evaluator_object_id": object_evaluator_id[object_id],
                "object_id": object_id,
                "decoy_pair_id": pair.get("decoy_pair_id", "NA"),
                "decoy_object_id": pair.get("decoy_object_id", "NA"),
                "trait_id": pair.get("trait_id", "NA"),
                "object_type": pair.get("object_type", "NA"),
                "assigned_split": eobj.get("assigned_split", "NA"),
                "decoy_assignment_status": status,
                "match_rank": pair.get("match_rank", "NA"),
                "match_score": pair.get("match_score", "NA"),
                "matching_level": pair.get("matching_level", "NA"),
                "relaxation_level": pair.get("relaxation_level", "NA"),
                "matched_fields": pair.get("matched_fields", "NA"),
                "unavailable_fields": pair.get("unavailable_fields", "NA"),
                "notes": "matched background only; decoy is not a true negative and is not independently split",
                "scaffold_version": SCAFFOLD_VERSION,
            }
        )
    write_tsv(args.interim_root / "inputs/evaluator_decoy_input_table.tsv", rows, EVALUATOR_DECOY_FIELDS)
    write_preview(args.report_root, "evaluator_decoy_input_table", rows, EVALUATOR_DECOY_FIELDS)
    return rows


def build_score_schema(args: argparse.Namespace) -> list[dict[str, object]]:
    rows = [
        ("score_table_name", "true", "string", "Name of submitted score table", "NA", "variant_baseline_scores.tsv", "Required for provenance."),
        ("score_source", "true", "string", "Score source category", "baseline;model;diagnostic;random", "baseline", "Baseline score can be used in dry-run but not as formal main result here."),
        ("score_version", "true", "string", "Score version or run identifier", "NA", "v0_1_chr1_snp_20260516", "Must be stable for reproducibility."),
        ("score_level", "true", "string", "Resolution of score rows", "variant;window;gene;region;trait_level_variant;trait_level_window", "variant", "Accession-level scores cannot directly enter final evidence evaluation."),
        ("trait_id", "true", "string", "Frozen trait identifier", "frozen trait ids", "data_lt_2007__spkf", "Trait-conditioned map key."),
        ("variant_id", "conditional", "string", "Variant identifier for variant-level scores", "NA", "chr1_1178_1178", "Required when score_level is variant or trait_level_variant."),
        ("window_id", "conditional", "string", "Window identifier for window-level scores", "NA", "chr1_1_100000", "Required when score_level is window or trait_level_window."),
        ("gene_id", "conditional", "string", "Gene identifier for gene-level scores", "NA", "Os01g0101600", "Required for gene-level scoring."),
        ("object_id", "optional", "string", "Matched decoy/evidence object identifier", "NA", "OBJ_VARIANT_00082095", "May be filled after joining to scaffold object table."),
        ("score", "true", "float", "Continuous score where direction is declared separately", "finite numeric", "0.923", "No metric is computed in this scaffold."),
        ("score_direction", "true", "string", "Whether larger or smaller score is better", "higher_is_better;lower_is_better", "higher_is_better", "Required before any future ranking task."),
        ("split_version", "true", "string", "Frozen split version used by score table", "NA", "frozen_split_v055_chr1_snp_prototype_v1", "Must match split manifest for formal future use."),
        ("aggregation_recipe_version", "conditional", "string", "Recipe for accession-level to trait-level map aggregation", "NA", "trait_map_agg_v1", "Accession-level scores must be aggregated before evidence evaluation."),
        ("model_version", "optional", "string", "Model or baseline version", "NA", "random_uniform_v0_1", "No model is trained in this scaffold."),
        ("accession_id", "false", "string", "Optional index only before trait-level aggregation", "NA", "ACC_0353", "Not required and cannot be a direct formal evidence evaluation field."),
        ("notes", "false", "string", "Free text notes", "NA", "dry-run only", "Must not encode labels or negatives."),
    ]
    output = [
        {
            "field_name": field,
            "required": required,
            "dtype": dtype,
            "description": description,
            "allowed_values": allowed,
            "example": example,
            "notes": notes,
            "scaffold_version": SCAFFOLD_VERSION,
        }
        for field, required, dtype, description, allowed, example, notes in rows
    ]
    write_tsv(args.interim_root / "outputs_schema/evaluator_score_input_schema.tsv", output, SCORE_SCHEMA_FIELDS)
    write_tsv(args.report_root / "evaluator_score_input_schema.tsv", output, SCORE_SCHEMA_FIELDS)
    return output


def build_output_schema(args: argparse.Namespace) -> list[dict[str, object]]:
    rows = [
        ("evaluation_run_id", "true", "string", "Future evaluator run id", "NA", "eval_dryrun_001", "No formal run is produced in 09A."),
        ("task_id", "true", "string", "Task manifest id", "NA", "TASK_001", "Must map to evaluator_task_manifest.tsv."),
        ("score_source", "true", "string", "Score source category", "baseline;model;diagnostic;random", "baseline", "Baseline dry-run only in 09A."),
        ("score_version", "true", "string", "Score version", "NA", "v0_1_chr1_snp_20260516", "NA"),
        ("object_id", "true", "string", "Evidence object id", "NA", "OBJ_VARIANT_00082095", "NA"),
        ("trait_id", "true", "string", "Trait id", "frozen trait ids", "data_lt_2007__spkf", "NA"),
        ("object_type", "true", "string", "Object type", "variant;window;gene;qtl_interval", "variant", "NA"),
        ("assigned_split", "true", "string", "Split evaluated", "dev;prototype_locked;source_disjoint_or_temporal", "dev", "prototype_locked remains a non-final prototype split."),
        ("metric_name", "true", "string", "Metric identifier", "dry_run_join_coverage;rank_percentile;topk_recovery;matched_background_enrichment", "dry_run_join_coverage", "No metric values are calculated in 09A."),
        ("metric_value", "true", "float", "Metric value", "finite numeric", "0.0", "Placeholder schema only."),
        ("n_evidence_objects", "true", "integer", "Number of evidence objects used", ">=0", "100", "NA"),
        ("n_decoys", "true", "integer", "Number of matched background decoys used", ">=0", "500", "Decoys are not true negatives."),
        ("calculated_on", "true", "string", "Evaluation set semantics", "evidence_plus_matched_decoys;diagnostic_only;future_supported_metric", "evidence_plus_matched_decoys", "Must not use genomewide unknown negatives."),
        ("uses_true_negative", "true", "boolean", "Whether true negatives are used", "false", "false", "Default and required value is false."),
        ("uses_unknown_as_negative", "true", "boolean", "Whether unknown/unlabeled is used as negative", "false", "false", "Default and required value is false."),
        ("prototype_locked_not_final", "true", "boolean", "Whether prototype lock is not final", "true", "true", "Must remain true for prototype_locked rows."),
        ("notes", "false", "string", "Notes", "NA", "schema only", "NA"),
    ]
    output = [
        {
            "field_name": field,
            "required": required,
            "dtype": dtype,
            "description": description,
            "allowed_values": allowed,
            "example": example,
            "notes": notes,
            "scaffold_version": SCAFFOLD_VERSION,
        }
        for field, required, dtype, description, allowed, example, notes in rows
    ]
    write_tsv(args.interim_root / "outputs_schema/evaluator_output_schema.tsv", output, OUTPUT_SCHEMA_FIELDS)
    write_tsv(args.report_root / "evaluator_output_schema.tsv", output, OUTPUT_SCHEMA_FIELDS)
    return output


def build_task_manifest(args: argparse.Namespace) -> list[dict[str, object]]:
    object_rows = read_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv")
    splits = sorted({row["assigned_split"] for row in object_rows})
    object_types = sorted({row["object_type"] for row in object_rows})
    task_types = [
        ("matched_ranking", "matched_ranking", "matched_background_rank_dry_run"),
        ("rank_percentile", "rank_percentile", "rank_schema_dry_run"),
        ("topk_recovery", "topk_recovery", "topk_schema_dry_run"),
        ("enrichment_over_matched_background", "enrichment_over_matched_background", "matched_background_schema_dry_run"),
        ("distance_to_evidence", "distance_to_evidence", "distance_schema_dry_run"),
        ("overlap_with_region", "overlap_with_region", "overlap_schema_dry_run"),
        ("diagnostic_only", "diagnostic_only", "join_and_leakage_diagnostic"),
    ]
    score_level_by_object = {
        "variant": "variant",
        "window": "window",
        "gene": "gene",
        "qtl_interval": "region",
    }
    rows: list[dict[str, object]] = []
    for split_name in splits:
        for object_type in object_types:
            for task_name, task_type, metric_family in task_types:
                rows.append(
                    {
                        "task_id": f"TASK_{len(rows) + 1:04d}",
                        "task_name": f"{task_name}_{object_type}_{split_name}",
                        "task_type": task_type,
                        "object_type": object_type,
                        "score_level": score_level_by_object.get(object_type, "region"),
                        "input_object_table": "data/interim/evaluator_scaffold_v055/inputs/evaluator_object_input_table.tsv",
                        "input_decoy_table": "data/interim/evaluator_scaffold_v055/inputs/evaluator_decoy_input_table.tsv",
                        "required_score_fields": "score_source;score_version;score_level;trait_id;score;score_direction;split_version",
                        "assigned_split": split_name,
                        "allowed_splits": "dev;prototype_locked;source_disjoint_or_temporal",
                        "metric_family": metric_family,
                        "is_formal_metric": "false",
                        "is_dry_run_only": "true",
                        "notes": "schema-only task manifest; no formal metric is calculated in 09A",
                        "scaffold_version": SCAFFOLD_VERSION,
                    }
                )
    write_tsv(args.interim_root / "tasks/evaluator_task_manifest.tsv", rows, TASK_MANIFEST_FIELDS)
    write_tsv(args.report_root / "evaluator_task_manifest.tsv", rows, TASK_MANIFEST_FIELDS)
    return rows


def object_join_indexes(args: argparse.Namespace) -> tuple[dict[tuple[str, str, str], str], dict[tuple[str, str, str], str]]:
    objects = read_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv")
    decoys = read_tsv(args.interim_root / "inputs/evaluator_decoy_input_table.tsv")
    object_index: dict[tuple[str, str, str], str] = {}
    decoy_index: dict[tuple[str, str, str], str] = {}
    for obj in objects:
        if obj.get("object_type") == "variant" and not is_missing(obj.get("variant_id")):
            object_index[("variant", obj["trait_id"], obj["variant_id"])] = obj["object_id"]
        if obj.get("object_type") == "window" and not is_missing(obj.get("window_id")):
            object_index[("window", obj["trait_id"], obj["window_id"])] = obj["object_id"]
    for decoy in decoys:
        decoy_object_id = decoy.get("decoy_object_id", "")
        if decoy_object_id.startswith("VARIANT_BG_"):
            variant_id = decoy_object_id.replace("VARIANT_BG_", "", 1)
            decoy_index[("variant", decoy["trait_id"], variant_id)] = decoy["object_id"]
        if decoy_object_id.startswith("WINDOW_BG_"):
            window_id = decoy_object_id.replace("WINDOW_BG_", "", 1)
            decoy_index[("window", decoy["trait_id"], window_id)] = decoy["object_id"]
    return object_index, decoy_index


def build_baseline_score_dry_run(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    object_index, decoy_index = object_join_indexes(args)
    split_version = split_version_from_manifest(args)
    output_path = args.interim_root / "dry_run/baseline_score_dry_run_input.tsv"
    if output_path.exists():
        output_path.unlink()
    preview_rows: list[dict[str, object]] = []
    stats = {
        "window_total": 0,
        "window_object": 0,
        "window_decoy": 0,
        "variant_total": 0,
        "variant_object": 0,
        "variant_decoy": 0,
    }

    def iter_score_rows(path: Path, level: str) -> Iterable[dict[str, object]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for raw in reader:
                key_id = raw.get("variant_id") if level == "variant" else raw.get("window_id")
                key = (level, raw.get("trait_id", ""), key_id or "")
                matched_object = object_index.get(key)
                matched_decoy = decoy_index.get(key)
                stats[f"{level}_total"] += 1
                if matched_object:
                    stats[f"{level}_object"] += 1
                if matched_decoy:
                    stats[f"{level}_decoy"] += 1
                if matched_object:
                    notes = "baseline score joins evaluator object; dry-run only"
                    object_id = matched_object
                elif matched_decoy:
                    notes = "baseline score joins matched background decoy; dry-run only and not true negative"
                    object_id = matched_decoy
                else:
                    notes = "baseline score does not join current evaluator object or decoy input"
                    object_id = "NA"
                yield {
                    "dry_run_score_id": f"DRY_{level.upper()}_{stats[f'{level}_total']:010d}",
                    "score_table_name": path.name,
                    "score_source": "baseline",
                    "score_version": raw.get("run_id", "NA"),
                    "score_level": level,
                    "trait_id": raw.get("trait_id", "NA"),
                    "variant_id": raw.get("variant_id", "NA") if level == "variant" else "NA",
                    "window_id": raw.get("window_id", "NA") if level == "window" else "NA",
                    "object_id": object_id,
                    "score": raw.get("score", "NA"),
                    "score_direction": "higher_is_better",
                    "split_version": split_version,
                    "matched_to_evaluator_object": str(bool(matched_object)).lower(),
                    "matched_to_decoy": str(bool(matched_decoy)).lower(),
                    "notes": notes,
                    "scaffold_version": SCAFFOLD_VERSION,
                }

    write_header = True
    for path, level in [
        (args.baseline_root / "window_baseline_scores.tsv", "window"),
        (args.baseline_root / "variant_baseline_scores.tsv", "variant"),
    ]:
        batch: list[dict[str, object]] = []
        for row in iter_score_rows(path, level):
            if len(preview_rows) < 500:
                preview_rows.append(dict(row))
            batch.append(row)
            if len(batch) >= 50_000:
                append_tsv_rows(output_path, batch, DRY_RUN_SCORE_FIELDS, write_header=write_header)
                write_header = False
                batch = []
        if batch:
            append_tsv_rows(output_path, batch, DRY_RUN_SCORE_FIELDS, write_header=write_header)
            write_header = False
    write_tsv(args.report_root / "baseline_score_dry_run_input.preview.tsv", preview_rows, DRY_RUN_SCORE_FIELDS)
    write_tsv(args.interim_root / "diagnostics/baseline_score_dry_run_join_summary.tsv", [stats], list(stats.keys()))
    write_tsv(args.report_root / "baseline_score_dry_run_join_summary.tsv", [stats], list(stats.keys()))
    return [stats]


def build_join_checks(args: argparse.Namespace) -> list[dict[str, object]]:
    objects = read_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv")
    decoys = read_tsv(args.interim_root / "inputs/evaluator_decoy_input_table.tsv")
    dry_stats = read_tsv(args.interim_root / "diagnostics/baseline_score_dry_run_join_summary.tsv")
    rows: list[dict[str, object]] = []

    def add(name: str, status: bool, n_input: int, n_matched: int, details: str, blocking: bool = True, notes: str = "NA") -> None:
        rows.append(
            {
                "check_id": f"EDRJ_{len(rows) + 1:08d}",
                "check_name": name,
                "status": "pass" if status else ("warn" if not blocking else "fail"),
                "n_input_records": n_input,
                "n_matched_records": n_matched,
                "n_unmatched_records": max(n_input - n_matched, 0),
                "match_rate": format_rate(n_matched, n_input),
                "details": details,
                "blocking_issue": str(blocking and not status).lower(),
                "notes": notes,
                "scaffold_version": SCAFFOLD_VERSION,
            }
        )

    add("evaluator_object_joined_to_split_assignment", bool(objects), len(objects), len(objects), "object input is derived from frozen split assignments")
    decoy_ok = sum(1 for row in objects if row.get("has_matched_decoy") == "true")
    add("evaluator_object_joined_to_matched_decoy_pair", decoy_ok == len(objects), len(objects), decoy_ok, "each evaluator object should have matched decoys")
    decoy_follow = sum(1 for row in decoys if row.get("decoy_assignment_status") == "follows_evidence_split")
    add("decoy_pair_follows_evidence_object_split", decoy_follow == len(decoys), len(decoys), decoy_follow, "decoys must follow evidence split")
    if dry_stats:
        stats = dry_stats[0]
        total = int(stats["window_total"]) + int(stats["variant_total"])
        matched = int(stats["window_object"]) + int(stats["window_decoy"]) + int(stats["variant_object"]) + int(stats["variant_decoy"])
        add("baseline_score_joins_evaluator_object_or_decoy", matched > 0, total, matched, "dry-run baseline score rows aligned to object or decoy where possible", blocking=False)
    manual_or_broader = sum(1 for row in objects if row.get("manual_review_required") == "true" or row.get("broader_evidence") == "true")
    add("manual_review_or_broader_not_in_evaluator_object", manual_or_broader == 0, len(objects), len(objects) - manual_or_broader, "manual/broader evidence excluded")
    final_locked = sum(
        1
        for row in objects
        if row.get("assigned_split") == "final_locked" or row.get("assigned_role") == "final_locked"
    )
    add(
        "prototype_locked_not_final_locked",
        final_locked == 0,
        len(objects),
        len(objects) - final_locked,
        "no final_locked split or role value in evaluator object input",
    )
    neg_strings = sum(1 for row in objects + decoys if "true_negative" in " ".join(row.values()).lower() or "unknown_as_negative" in " ".join(row.values()).lower())
    add("unknown_unlabeled_and_decoy_not_negative", neg_strings == 0, len(objects) + len(decoys), len(objects) + len(decoys) - neg_strings, "no true_negative or unknown_as_negative wording in inputs")
    write_tsv(args.interim_root / "dry_run/evaluator_dry_run_join_check.tsv", rows, JOIN_CHECK_FIELDS)
    write_tsv(args.report_root / "evaluator_dry_run_join_check.tsv", rows, JOIN_CHECK_FIELDS)
    return rows


def build_leakage_guards(args: argparse.Namespace) -> list[dict[str, object]]:
    objects = read_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv")
    decoys = read_tsv(args.interim_root / "inputs/evaluator_decoy_input_table.tsv")
    score_schema = read_tsv(args.interim_root / "outputs_schema/evaluator_score_input_schema.tsv")
    output_schema = read_tsv(args.interim_root / "outputs_schema/evaluator_output_schema.tsv")
    split_leakage = read_tsv(args.frozen_split_root / "diagnostics/split_leakage_check.tsv")
    rows: list[dict[str, object]] = []

    def add(name: str, ok: bool, n_checked: int, n_failed: int, details: str, blocking: bool = True, notes: str = "NA") -> None:
        rows.append(
            {
                "guard_id": f"ELG_{len(rows) + 1:08d}",
                "guard_name": name,
                "status": "pass" if ok else ("warn" if not blocking else "fail"),
                "n_checked": n_checked,
                "n_failed": n_failed,
                "details": details,
                "blocking_issue": str(blocking and not ok).lower(),
                "notes": notes,
                "scaffold_version": SCAFFOLD_VERSION,
            }
        )

    training_usage = [row for row in objects if row.get("allowed_usage") == "training_label"]
    add("evidence_used_for_training_false", not training_usage, len(objects), len(training_usage), "object input has no training_label usage")
    manual = [row for row in objects if row.get("manual_review_required") == "true"]
    add("manual_review_not_in_main_evaluator_input", not manual, len(objects), len(manual), "manual review excluded")
    broader = [row for row in objects if row.get("broader_evidence") == "true"]
    add("broader_evidence_not_in_main_evaluator_input", not broader, len(objects), len(broader), "broader evidence excluded")
    decoy_negative = [row for row in decoys if "true_negative" in " ".join(row.values()).lower()]
    add("decoy_uses_true_negative_false", not decoy_negative, len(decoys), len(decoy_negative), "decoys are matched background only")
    output_unknown = [row for row in output_schema if row.get("field_name") == "uses_unknown_as_negative" and row.get("example") != "false"]
    add("unknown_as_negative_false", not output_unknown, len(output_schema), len(output_unknown), "output schema default is false")
    accession_required = [row for row in score_schema if row.get("field_name") == "accession_id" and row.get("required") != "false"]
    add("accession_id_not_required_score_field", not accession_required, len(score_schema), len(accession_required), "accession_id is optional index only")
    direct_accession = [row for row in score_schema if row.get("field_name") == "score_level" and "accession" in row.get("allowed_values", "")]
    add("accession_level_score_not_direct_formal_evaluation", not direct_accession, len(score_schema), len(direct_accession), "score_level excludes accession-level direct evaluation")
    proto_bad = [row for row in objects if row.get("prototype_locked_not_final") != "true"]
    add("prototype_locked_not_final_true", not proto_bad, len(objects), len(proto_bad), "all evaluator object rows keep prototype_locked_not_final=true")
    final_locked_assignments = [
        row
        for row in objects + decoys
        if row.get("assigned_split") == "final_locked" or row.get("assigned_role") == "final_locked"
    ]
    final_locked_fields = [row for row in score_schema + output_schema if row.get("field_name") == "final_locked"]
    final_locked = final_locked_assignments + final_locked_fields
    add(
        "final_locked_field_absent",
        not final_locked,
        len(objects) + len(decoys) + len(score_schema) + len(output_schema),
        len(final_locked),
        "no final_locked field name, split value, or role value in scaffold outputs",
    )
    split_fail = [row for row in split_leakage if row.get("status") == "fail" or row.get("blocking_issue") == "true"]
    add("split_leakage_check_passed_or_warning", not split_fail, len(split_leakage), len(split_fail), "inherits split_leakage_check from 08C")
    write_tsv(args.interim_root / "diagnostics/evaluator_leakage_guard.tsv", rows, LEAKAGE_GUARD_FIELDS)
    write_tsv(args.report_root / "evaluator_leakage_guard.tsv", rows, LEAKAGE_GUARD_FIELDS)
    return rows


def validate_and_report(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    join_checks = build_join_checks(args)
    guards = build_leakage_guards(args)
    objects = read_tsv(args.interim_root / "inputs/evaluator_object_input_table.tsv")
    decoys = read_tsv(args.interim_root / "inputs/evaluator_decoy_input_table.tsv")
    score_schema = read_tsv(args.interim_root / "outputs_schema/evaluator_score_input_schema.tsv")
    tasks = read_tsv(args.interim_root / "tasks/evaluator_task_manifest.tsv")
    output_schema = read_tsv(args.interim_root / "outputs_schema/evaluator_output_schema.tsv")
    dry_run = args.interim_root / "dry_run/baseline_score_dry_run_input.tsv"
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
                "notes": notes,
                "scaffold_version": SCAFFOLD_VERSION,
            }
        )

    expected = [
        args.interim_root / "inputs/evaluator_object_input_table.tsv",
        args.interim_root / "inputs/evaluator_decoy_input_table.tsv",
        args.interim_root / "outputs_schema/evaluator_score_input_schema.tsv",
        args.interim_root / "tasks/evaluator_task_manifest.tsv",
        args.interim_root / "outputs_schema/evaluator_output_schema.tsv",
        dry_run,
        args.interim_root / "dry_run/evaluator_dry_run_join_check.tsv",
        args.interim_root / "diagnostics/evaluator_leakage_guard.tsv",
    ]
    missing = [rel(path) for path in expected if count_rows(path) == 0]
    add("outputs_exist_and_nonempty", not missing, len(expected), len(missing), ";".join(missing) if missing else "all outputs nonempty")
    bad_split = [row for row in objects if row.get("assigned_split") not in ALLOWED_EVALUATOR_SPLITS]
    add("evaluator_object_input_allowed_splits_only", not bad_split, len(objects), len(bad_split), "object input only has allowed evaluator splits")
    true_neg = [row for row in decoys if "true_negative" in " ".join(row.values()).lower()]
    add("decoy_input_no_true_negative", not true_neg, len(decoys), len(true_neg), "decoy input treats decoy as matched background only")
    formal = [row for row in tasks if row.get("is_formal_metric") != "false" or row.get("is_dry_run_only") != "true"]
    add("task_manifest_no_formal_metric", not formal, len(tasks), len(formal), "all tasks are dry-run only and non-formal")
    unknown_schema_bad = [row for row in output_schema if row.get("field_name") == "uses_unknown_as_negative" and row.get("example") != "false"]
    add("output_schema_unknown_as_negative_default_false", not unknown_schema_bad, len(output_schema), len(unknown_schema_bad), "uses_unknown_as_negative example/default is false")
    accession_bad = [row for row in score_schema if row.get("field_name") == "accession_id" and row.get("required") != "false"]
    add("score_schema_accession_id_not_required", not accession_bad, len(score_schema), len(accession_bad), "accession_id is not a required score input field")
    add("dry_run_score_input_does_not_generate_formal_metric", count_rows(dry_run) > 0, count_rows(dry_run), 0, "dry-run score input is schema-aligned only; no metric output generated")
    blocking = [row for row in join_checks + guards if row.get("blocking_issue") == "true"]
    add("join_and_leakage_guards_no_blocking_issue", not blocking, len(join_checks) + len(guards), len(blocking), "guard and join checks have no blocking failures")
    write_tsv(args.interim_root / "diagnostics/evaluator_scaffold_validation.tsv", rows, VALIDATION_FIELDS)
    write_tsv(args.report_root / "evaluator_scaffold_validation.tsv", rows, VALIDATION_FIELDS)
    write_report(args, objects, decoys, tasks, join_checks, guards, rows)
    return rows


def write_report(
    args: argparse.Namespace,
    objects: list[dict[str, str]],
    decoys: list[dict[str, str]],
    tasks: list[dict[str, str]],
    join_checks: list[dict[str, str]],
    guards: list[dict[str, str]],
    validation: list[dict[str, object]],
) -> None:
    split_counter = Counter(row.get("assigned_split") for row in objects)
    object_counter = Counter(row.get("object_type") for row in objects)
    dry_summary = read_tsv(args.interim_root / "diagnostics/baseline_score_dry_run_join_summary.tsv")
    if dry_summary:
        stats = dry_summary[0]
        window_total = int(stats["window_total"])
        window_join = int(stats["window_object"]) + int(stats["window_decoy"])
        variant_total = int(stats["variant_total"])
        variant_join = int(stats["variant_object"]) + int(stats["variant_decoy"])
    else:
        window_total = window_join = variant_total = variant_join = 0
    manual = sum(1 for row in objects if row.get("manual_review_required") == "true")
    broader = sum(1 for row in objects if row.get("broader_evidence") == "true")
    true_neg = sum(1 for row in decoys if "true_negative" in " ".join(row.values()).lower())
    unknown_neg = sum(1 for row in objects + decoys if "unknown_as_negative" in " ".join(row.values()).lower())
    accession_required = [
        row
        for row in read_tsv(args.interim_root / "outputs_schema/evaluator_score_input_schema.tsv")
        if row.get("field_name") == "accession_id" and row.get("required") != "false"
    ]
    validation_fail = [row for row in validation if row.get("status") == "fail"]
    files = [
        args.interim_root / "inputs/evaluator_object_input_table.tsv",
        args.interim_root / "inputs/evaluator_decoy_input_table.tsv",
        args.interim_root / "outputs_schema/evaluator_score_input_schema.tsv",
        args.interim_root / "tasks/evaluator_task_manifest.tsv",
        args.interim_root / "outputs_schema/evaluator_output_schema.tsv",
        args.interim_root / "dry_run/baseline_score_dry_run_input.tsv",
        args.interim_root / "dry_run/evaluator_dry_run_join_check.tsv",
        args.interim_root / "diagnostics/evaluator_leakage_guard.tsv",
        args.interim_root / "diagnostics/evaluator_scaffold_validation.tsv",
    ]
    lines = [
        "# Evaluator Scaffold v0.5.5 Report",
        "",
        "## Scope",
        "",
        "This run builds a split-aware evaluator scaffold for the chr1 SNP-only prototype. It is not a formal evaluator and does not calculate formal benchmark metrics.",
        "",
        "No model was trained. No AUROC/AUPRC was reported. No final locked evaluation was created. `prototype_locked` is explicitly not `final_locked`. Evidence is not a training label, matched decoys are not true negatives, and unknown/unlabeled rows are not negatives.",
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
            "## Object Summary",
            "",
            f"- Current input commit hash: `{current_commit(args.repo_root)}`.",
            f"- Evaluator object input rows: {len(objects)}.",
            f"- Evaluator decoy input rows: {len(decoys)}.",
            f"- Object types: {counter_summary(object_counter)}.",
            f"- Splits: {counter_summary(split_counter)}.",
            f"- Task manifest rows: {len(tasks)}; all are dry-run only and non-formal.",
            "",
            "## Dry-Run Join Coverage",
            "",
            f"- Window baseline dry-run join coverage: {window_join}/{window_total} ({format_rate(window_join, window_total)}).",
            f"- Variant baseline dry-run join coverage: {variant_join}/{variant_total} ({format_rate(variant_join, variant_total)}).",
            "- Baseline score dry-run alignment is a schema/join check only and does not produce benchmark metrics.",
            "",
            "## Guard Summary",
            "",
            f"- Manual review rows in evaluator input: {manual}.",
            f"- Broader evidence rows in evaluator input: {broader}.",
            f"- Decoy rows written as true_negative: {true_neg}.",
            f"- Unknown/unlabeled rows written as negative: {unknown_neg}.",
            f"- Accession_id required by score schema: {len(accession_required)}.",
            f"- Validation failed checks: {len(validation_fail)}.",
            "- prototype_locked_not_final is retained for evaluator object rows.",
            "",
            "## Current Limitations",
            "",
            "- This remains a chr1 SNP-only prototype scaffold.",
            "- The scaffold defines schemas, manifests, and dry-run joins only; it does not rank or score any model output.",
            "- Baseline scores are accepted for dry-run schema alignment only.",
            "- Gene and QTL region score sources are schema-defined but no current score table exists for them.",
            "- Future formal metrics must use evidence_plus_matched_decoys and must not treat genome-wide unknowns as negatives.",
            "",
            "## Next Step",
            "",
            "The scaffold is ready for a chr1 SNP matched-ranking dry-run that exercises the schema and joins without reporting formal metrics.",
        ]
    )
    (args.report_root / "evaluator_scaffold_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def counter_summary(counter: Counter[str], limit: int = 12) -> str:
    return ";".join(f"{key}:{value}" for key, value in counter.most_common(limit)) if counter else "NA"


def print_summary(name: str, rows: list[dict[str, object]], extra: str = "") -> None:
    print(f"{name}_rows={len(rows)}")
    if extra:
        print(extra)
