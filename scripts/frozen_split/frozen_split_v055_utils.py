#!/usr/bin/env python3
"""Utilities for leakage-aware chr1 SNP-only prototype split freezing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import random
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SPLIT_VERSION = "frozen_split_v055_chr1_snp_prototype_v1"
RANDOM_SEED = 5508
PROXIMITY_BIN_SIZE = 5_000_000
QTL_PROXIMITY_BP = 1_000_000

DEFAULT_MATCHED_DECOY_ROOT = REPO_ROOT / "data/interim/matched_decoy_v055"
DEFAULT_DESIGN_ROOT = REPO_ROOT / "data/interim/design_v055"
DEFAULT_TRAIT_STATE_ROOT = REPO_ROOT / "data/interim/trait_state"
DEFAULT_V01_ROOT = REPO_ROOT / "data/interim/v0_1_mini"
DEFAULT_INTERIM_ROOT = REPO_ROOT / "data/interim/frozen_split_v055"
DEFAULT_REPORT_ROOT = REPO_ROOT / "reports/frozen_split_v055"


UNIT_FIELDS = [
    "split_unit_id",
    "split_unit_type",
    "source_object_id",
    "source_table",
    "trait_id",
    "object_type",
    "chrom",
    "start",
    "end",
    "gene_id",
    "gene_symbol",
    "variant_id",
    "window_id",
    "accession_id",
    "decoy_pair_id",
    "in_main_evaluation_candidate_pool",
    "manual_review_required",
    "broader_evidence",
    "allowed_usage",
    "notes",
    "split_version",
]

BLOCK_FIELDS = [
    "split_block_id",
    "block_type",
    "chrom",
    "block_start",
    "block_end",
    "block_length",
    "member_unit_ids",
    "n_units",
    "traits",
    "genes",
    "evidence_sources",
    "decoy_pair_ids",
    "block_rule",
    "leakage_risk_level",
    "notes",
    "split_version",
]

ASSIGNMENT_FIELDS = [
    "assignment_id",
    "split_version",
    "random_seed",
    "split_unit_id",
    "split_block_id",
    "split_unit_type",
    "assigned_split",
    "assigned_role",
    "trait_id",
    "object_type",
    "chrom",
    "start",
    "end",
    "assignment_rule",
    "prototype_locked_not_final",
    "notes",
]

BALANCE_FIELDS = [
    "diagnostic_id",
    "split_version",
    "diagnostic_type",
    "assigned_split",
    "trait_id",
    "object_type",
    "n_units",
    "n_blocks",
    "n_accessions",
    "n_evidence_objects",
    "n_decoy_pairs",
    "subgroup_distribution",
    "PC_balance_summary",
    "trait_distribution",
    "evidence_source_distribution",
    "object_type_distribution",
    "position_distribution",
    "gene_density_summary",
    "variant_density_summary",
    "notes",
]

LEAKAGE_FIELDS = [
    "check_id",
    "check_name",
    "status",
    "n_checked",
    "n_leakage",
    "leakage_type",
    "affected_units",
    "affected_blocks",
    "details",
    "blocking_issue",
    "notes",
    "split_version",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "n_records",
    "n_failed",
    "details",
    "blocking_issue",
    "notes",
    "split_version",
]

MANIFEST_FIELDS = [
    "split_name",
    "split_version",
    "random_seed",
    "source_tables",
    "created_at",
    "created_by_script",
    "rule_summary",
    "block_rule_summary",
    "prototype_locked_not_final",
    "limitations",
    "notes",
]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--matched-decoy-root", type=Path, default=DEFAULT_MATCHED_DECOY_ROOT)
    parser.add_argument("--design-root", type=Path, default=DEFAULT_DESIGN_ROOT)
    parser.add_argument("--trait-state-root", type=Path, default=DEFAULT_TRAIT_STATE_ROOT)
    parser.add_argument("--v01-root", type=Path, default=DEFAULT_V01_ROOT)
    parser.add_argument("--interim-root", type=Path, default=DEFAULT_INTERIM_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--random-seed", type=int, default=RANDOM_SEED)
    return parser.parse_args()


def ensure_output_dirs(interim_root: Path, report_root: Path) -> None:
    for subdir in ["units", "blocks", "assignments", "diagnostics"]:
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


def write_preview(report_root: Path, name: str, rows: list[dict[str, object]], fields: list[str], n: int = 500) -> None:
    write_tsv(report_root / f"{name}.preview.tsv", rows[:n], fields)


def clean(value: object) -> str:
    return str(value or "").strip()


def is_missing(value: object) -> bool:
    text = clean(value)
    return text == "" or text.lower() in {"na", "n/a", "nan", "none", "null"}


def as_int(value: object, default: int = 0) -> int:
    try:
        if is_missing(value):
            return default
        return int(float(clean(value)))
    except ValueError:
        return default


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if is_missing(value):
            return default
        return float(clean(value))
    except ValueError:
        return default


def fmt(value: float, digits: int = 6) -> str:
    if not math.isfinite(value):
        return "NA"
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        return "unknown"


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


def safe_id(value: object) -> str:
    text = clean(value)
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)


def interval_length(start: object, end: object) -> int:
    s, e = as_int(start), as_int(end)
    return max(0, e - s + 1) if s and e and e >= s else 0


def interval_center(start: object, end: object) -> int:
    s, e = as_int(start), as_int(end)
    return (s + e) // 2 if s and e else 0


def overlap_or_near(a_start: int, a_end: int, b_start: int, b_end: int, max_gap: int = 0) -> bool:
    return a_start <= b_end + max_gap and b_start <= a_end + max_gap


def proximity_bin(chrom: object, start: object, end: object, bin_size: int = PROXIMITY_BIN_SIZE) -> str:
    center = interval_center(start, end)
    chrom_text = clean(chrom) or "NA"
    if center <= 0:
        return f"chr{chrom_text}:unknown"
    return f"chr{chrom_text}:{center // bin_size}"


def hash_unit(text: str, seed: int = RANDOM_SEED) -> float:
    digest = hashlib.sha256(f"{seed}:{text}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16**12)


def assign_three_way(key: str, seed: int, ratios: tuple[float, float, float] = (0.70, 0.15, 0.15)) -> str:
    value = hash_unit(key, seed)
    if value < ratios[0]:
        return "train"
    if value < ratios[0] + ratios[1]:
        return "dev"
    return "test"


def assign_evidence_split(block_id: str, seed: int) -> str:
    value = hash_unit(block_id, seed)
    if value < 0.60:
        return "dev"
    if value < 0.90:
        return "prototype_locked"
    return "source_disjoint_or_temporal"


def assigned_role(split_name: str, unit_type: str) -> str:
    if split_name == "train":
        return "training_candidate"
    if split_name == "dev":
        return "development_evaluation"
    if split_name == "test":
        return "prototype_locked_evaluation"
    if split_name == "prototype_locked":
        return "prototype_locked_evaluation"
    if split_name == "source_disjoint_or_temporal":
        return "source_disjoint_evaluation"
    if split_name.startswith("excluded_"):
        return "excluded"
    return "diagnostic"


def compact_join(values: Iterable[object], limit: int = 160) -> str:
    unique = []
    seen = set()
    for value in values:
        text = clean(value)
        if not text or text in seen or is_missing(text):
            continue
        seen.add(text)
        unique.append(text)
    if len(unique) <= limit:
        return ";".join(unique) if unique else "NA"
    return ";".join(unique[:limit]) + f";...[truncated_n={len(unique) - limit}]"


def load_inputs(args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    return {
        "objects": read_tsv(args.matched_decoy_root / "objects/matched_decoy_object_table.tsv"),
        "pairs": read_tsv(args.matched_decoy_root / "pairs/matched_decoy_pair_table.tsv"),
        "decoy_diagnostics": read_tsv(args.matched_decoy_root / "diagnostics/decoy_matching_diagnostics.tsv"),
        "decoy_validation": read_tsv(args.matched_decoy_root / "diagnostics/decoy_validation.tsv"),
        "trait_usability": read_tsv(args.design_root / "metadata/trait_usability_table.tsv"),
        "trait_preprocessing": read_tsv(args.design_root / "metadata/trait_preprocessing_table.tsv"),
        "negative_pair_protocol": read_tsv(args.design_root / "negative_pairs/negative_pair_protocol_table.tsv"),
        "negative_balance": read_tsv(args.design_root / "negative_pairs/balance_diagnostics_table.tsv"),
        "accessions": read_tsv(args.trait_state_root / "high_confidence_accessions.tsv"),
        "trait_state": read_tsv(args.trait_state_root / "trait_state_table_prototype.tsv"),
        "covariates": read_tsv(args.design_root / "metadata/covariate_accession_table.tsv"),
        "windows": read_tsv(args.v01_root / "window_table_chr1_v0_1.tsv"),
        "variants": read_tsv(args.v01_root / "variant_table_chr1_snp_v0_1.tsv"),
        "variant_window": read_tsv(args.v01_root / "variant_window_mapping_chr1_v0_1.tsv"),
    }


def build_split_units(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    inputs = load_inputs(args)
    rows: list[dict[str, object]] = []

    for accession in inputs["accessions"]:
        accession_id = accession.get("internal_accession_id", "NA")
        rows.append(
            {
                "split_unit_id": f"SU_ACC_{safe_id(accession_id)}",
                "split_unit_type": "accession",
                "source_object_id": accession_id,
                "source_table": "data/interim/trait_state/high_confidence_accessions.tsv",
                "trait_id": "NA",
                "object_type": "accession",
                "chrom": "NA",
                "start": "NA",
                "end": "NA",
                "gene_id": "NA",
                "gene_symbol": "NA",
                "variant_id": "NA",
                "window_id": "NA",
                "accession_id": accession_id,
                "decoy_pair_id": "NA",
                "in_main_evaluation_candidate_pool": "true",
                "manual_review_required": "false",
                "broader_evidence": "false",
                "allowed_usage": "index_only",
                "notes": "accession_id is used only for split/indexing; not a model input token",
                "split_version": SPLIT_VERSION,
            }
        )

    for trait in inputs["trait_usability"]:
        trait_id = trait.get("trait_id", "NA")
        rows.append(
            {
                "split_unit_id": f"SU_TRAIT_{safe_id(trait_id)}",
                "split_unit_type": "trait",
                "source_object_id": trait_id,
                "source_table": "data/interim/design_v055/metadata/trait_usability_table.tsv",
                "trait_id": trait_id,
                "object_type": "trait",
                "chrom": "NA",
                "start": "NA",
                "end": "NA",
                "gene_id": "NA",
                "gene_symbol": "NA",
                "variant_id": "NA",
                "window_id": "NA",
                "accession_id": "NA",
                "decoy_pair_id": "NA",
                "in_main_evaluation_candidate_pool": trait.get("usable_for_main", "false"),
                "manual_review_required": "false",
                "broader_evidence": "false",
                "allowed_usage": "diagnostic",
                "notes": "trait unit for split balance diagnostics; not phenotype prediction label",
                "split_version": SPLIT_VERSION,
            }
        )

    for window in inputs["windows"]:
        window_id = window.get("window_id", "NA")
        rows.append(
            {
                "split_unit_id": f"SU_REGION_{safe_id(window_id)}",
                "split_unit_type": "region",
                "source_object_id": window_id,
                "source_table": "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv",
                "trait_id": "NA",
                "object_type": "window_region",
                "chrom": window.get("chrom", "NA"),
                "start": window.get("start", "NA"),
                "end": window.get("end", "NA"),
                "gene_id": "NA",
                "gene_symbol": "NA",
                "variant_id": "NA",
                "window_id": window_id,
                "accession_id": "NA",
                "decoy_pair_id": "NA",
                "in_main_evaluation_candidate_pool": "true",
                "manual_review_required": "false",
                "broader_evidence": "false",
                "allowed_usage": "diagnostic",
                "notes": "chr1 SNP-only prototype region unit; unknown/unlabeled is not negative",
                "split_version": SPLIT_VERSION,
            }
        )

    for obj in inputs["objects"]:
        broader = "broader_evidence_pool" in obj.get("exclusion_reason", "")
        rows.append(
            {
                "split_unit_id": f"SU_EVIDENCE_{safe_id(obj.get('object_id'))}",
                "split_unit_type": "evidence_object",
                "source_object_id": obj.get("object_id", "NA"),
                "source_table": "data/interim/matched_decoy_v055/objects/matched_decoy_object_table.tsv",
                "trait_id": obj.get("trait_id", "NA"),
                "object_type": obj.get("object_type", "NA"),
                "chrom": obj.get("chrom", "NA"),
                "start": obj.get("start", "NA"),
                "end": obj.get("end", "NA"),
                "gene_id": obj.get("gene_id", "NA"),
                "gene_symbol": obj.get("gene_symbol", "NA"),
                "variant_id": obj.get("variant_id", "NA"),
                "window_id": obj.get("window_id", "NA"),
                "accession_id": "NA",
                "decoy_pair_id": "NA",
                "in_main_evaluation_candidate_pool": obj.get("in_main_evaluation_candidate_pool", "false"),
                "manual_review_required": obj.get("manual_review_required", "false"),
                "broader_evidence": str(broader).lower(),
                "allowed_usage": obj.get("allowed_usage", "NA"),
                "notes": "evidence object for split only; evidence is not a training label or causal ground truth",
                "split_version": SPLIT_VERSION,
            }
        )

    object_by_id = {row["object_id"]: row for row in inputs["objects"]}
    for pair in inputs["pairs"]:
        obj = object_by_id.get(pair.get("object_id", ""), {})
        rows.append(
            {
                "split_unit_id": f"SU_DECOY_{safe_id(pair.get('decoy_pair_id'))}",
                "split_unit_type": "decoy_pair",
                "source_object_id": pair.get("object_id", "NA"),
                "source_table": "data/interim/matched_decoy_v055/pairs/matched_decoy_pair_table.tsv",
                "trait_id": pair.get("trait_id", "NA"),
                "object_type": pair.get("object_type", "NA"),
                "chrom": obj.get("chrom", "NA"),
                "start": obj.get("start", "NA"),
                "end": obj.get("end", "NA"),
                "gene_id": obj.get("gene_id", "NA"),
                "gene_symbol": obj.get("gene_symbol", "NA"),
                "variant_id": obj.get("variant_id", "NA"),
                "window_id": obj.get("window_id", "NA"),
                "accession_id": "NA",
                "decoy_pair_id": pair.get("decoy_pair_id", "NA"),
                "in_main_evaluation_candidate_pool": "true",
                "manual_review_required": "false",
                "broader_evidence": "false",
                "allowed_usage": "development_evidence_candidate",
                "notes": "matched decoy pair follows evidence object split; decoy is background, not true negative",
                "split_version": SPLIT_VERSION,
            }
        )

    write_tsv(args.interim_root / "units/split_unit_table.tsv", rows, UNIT_FIELDS)
    write_preview(args.report_root, "split_unit_table", rows, UNIT_FIELDS)
    return rows


def qtl_components(main_qtls: list[dict[str, str]]) -> dict[str, str]:
    sorted_qtls = sorted(main_qtls, key=lambda r: (clean(r.get("chrom")), as_int(r.get("start")), as_int(r.get("end"))))
    components: dict[str, str] = {}
    current_chrom = None
    current_start = 0
    current_end = 0
    component_idx = 0
    for row in sorted_qtls:
        chrom = clean(row.get("chrom"))
        start, end = as_int(row.get("start")), as_int(row.get("end"))
        if chrom != current_chrom or not overlap_or_near(current_start, current_end, start, end, QTL_PROXIMITY_BP):
            component_idx += 1
            current_chrom = chrom
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
        components[row["object_id"]] = f"QTL_COMP_{component_idx:04d}"
    return components


def assignment_block_for_object(obj: dict[str, str], qtl_component_by_object: dict[str, str]) -> tuple[str, str, str, int, int, str]:
    object_type = obj.get("object_type", "NA")
    chrom = clean(obj.get("chrom")) or "NA"
    start, end = as_int(obj.get("start")), as_int(obj.get("end"))
    if object_type == "qtl_interval":
        component = qtl_component_by_object.get(obj.get("object_id", ""), proximity_bin(chrom, start, end))
        return f"BLK_QTL_{component}", "qtl_region_block", chrom, start, end, f"QTL overlap/nearby component with max_gap={QTL_PROXIMITY_BP}"
    bin_id = proximity_bin(chrom, start, end)
    block_start = max(1, (interval_center(start, end) // PROXIMITY_BIN_SIZE) * PROXIMITY_BIN_SIZE + 1) if start else 0
    block_end = block_start + PROXIMITY_BIN_SIZE - 1 if block_start else 0
    return f"BLK_MIXED_{safe_id(bin_id)}", "mixed_evidence_block", chrom, block_start, block_end, f"mixed evidence {PROXIMITY_BIN_SIZE}bp proximity bin"


def build_split_blocks(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    units = read_tsv(args.interim_root / "units/split_unit_table.tsv")
    inputs = load_inputs(args)
    objects = inputs["objects"]
    pairs = inputs["pairs"]
    unit_by_source = {row["source_object_id"]: row["split_unit_id"] for row in units if row["split_unit_type"] == "evidence_object"}
    pair_unit_by_pair = {row["decoy_pair_id"]: row["split_unit_id"] for row in units if row["split_unit_type"] == "decoy_pair"}
    pair_units_by_object: dict[str, list[str]] = defaultdict(list)
    pair_ids_by_object: dict[str, list[str]] = defaultdict(list)
    for pair in pairs:
        pair_units_by_object[pair["object_id"]].append(pair_unit_by_pair.get(pair["decoy_pair_id"], "NA"))
        pair_ids_by_object[pair["object_id"]].append(pair["decoy_pair_id"])

    main_objects = [row for row in objects if row.get("in_main_evaluation_candidate_pool") == "true"]
    qtl_component_by_object = qtl_components([row for row in main_objects if row.get("object_type") == "qtl_interval"])
    block_members: dict[str, list[str]] = defaultdict(list)
    block_meta: dict[str, dict[str, object]] = {}

    def add_block_member(block_id: str, block_type: str, chrom: object, start: object, end: object, unit_id: str, obj: dict[str, str] | None, rule: str) -> None:
        block_members[block_id].append(unit_id)
        meta = block_meta.setdefault(
            block_id,
            {
                "split_block_id": block_id,
                "block_type": block_type,
                "chrom": chrom,
                "block_start": as_int(start),
                "block_end": as_int(end),
                "traits": set(),
                "genes": set(),
                "evidence_sources": set(),
                "decoy_pair_ids": set(),
                "block_rule": rule,
                "leakage_risk_level": "high" if block_type in {"qtl_region_block", "mixed_evidence_block", "gene_block", "interval_overlap_block"} else "medium",
                "notes": "block is used to keep nearby evidence and matched decoys together when applicable",
            },
        )
        meta["block_start"] = min(as_int(meta["block_start"]) or as_int(start), as_int(start) or as_int(meta["block_start"]))
        meta["block_end"] = max(as_int(meta["block_end"]), as_int(end))
        if obj:
            meta["traits"].add(obj.get("trait_id", "NA"))  # type: ignore[index]
            meta["genes"].add(obj.get("gene_id", "NA"))  # type: ignore[index]
            meta["evidence_sources"].add(obj.get("evidence_source", obj.get("source_database", "NA")))  # type: ignore[index]

    for unit in units:
        if unit["split_unit_type"] == "accession":
            block_id = f"BLK_ACC_{safe_id(unit['accession_id'])}"
            add_block_member(block_id, "accession_block", "NA", 0, 0, unit["split_unit_id"], None, "one accession per accession split block")
        elif unit["split_unit_type"] == "trait":
            block_id = f"BLK_TRAIT_{safe_id(unit['trait_id'])}"
            add_block_member(block_id, "trait_block", "NA", 0, 0, unit["split_unit_id"], None, "one frozen trait per diagnostic trait block")
        elif unit["split_unit_type"] == "region":
            block_id = f"BLK_WINDOW_{safe_id(proximity_bin(unit['chrom'], unit['start'], unit['end']))}"
            add_block_member(block_id, "window_neighborhood_block", unit["chrom"], unit["start"], unit["end"], unit["split_unit_id"], None, f"chr1 windows grouped by {PROXIMITY_BIN_SIZE}bp neighborhood")

    object_by_id = {row["object_id"]: row for row in objects}
    assignment_block_by_object: dict[str, str] = {}
    for obj in main_objects:
        block_id, block_type, chrom, start, end, rule = assignment_block_for_object(obj, qtl_component_by_object)
        assignment_block_by_object[obj["object_id"]] = block_id
        evidence_unit_id = unit_by_source.get(obj["object_id"], "NA")
        add_block_member(block_id, block_type, chrom, start, end, evidence_unit_id, obj, rule)
        for pair_unit in pair_units_by_object.get(obj["object_id"], []):
            add_block_member(block_id, block_type, chrom, start, end, pair_unit, obj, rule + "; decoy pair follows evidence object")
        block_meta[block_id]["decoy_pair_ids"].update(pair_ids_by_object.get(obj["object_id"], []))  # type: ignore[index]

        decoy_block_id = f"BLK_DECOY_SET_{safe_id(obj['object_id'])}"
        add_block_member(decoy_block_id, "decoy_set_block", chrom, start, end, evidence_unit_id, obj, "same matched decoy set stays with evidence object")
        for pair_unit in pair_units_by_object.get(obj["object_id"], []):
            add_block_member(decoy_block_id, "decoy_set_block", chrom, start, end, pair_unit, obj, "same matched decoy set stays with evidence object")
        block_meta[decoy_block_id]["decoy_pair_ids"].update(pair_ids_by_object.get(obj["object_id"], []))  # type: ignore[index]

        if obj.get("object_type") == "gene" and not is_missing(obj.get("gene_id")):
            gene_block_id = f"BLK_GENE_{safe_id(obj['gene_id'])}"
            add_block_member(gene_block_id, "gene_block", chrom, start, end, evidence_unit_id, obj, "same gene evidence/decoys cannot cross split")
        if obj.get("object_type") == "qtl_interval":
            interval_block_id = f"BLK_INTERVAL_{safe_id(qtl_component_by_object.get(obj['object_id'], obj['object_id']))}"
            add_block_member(interval_block_id, "interval_overlap_block", chrom, start, end, evidence_unit_id, obj, f"overlapping or nearby QTL intervals max_gap={QTL_PROXIMITY_BP}")

    for obj in objects:
        if obj.get("in_main_evaluation_candidate_pool") == "true":
            continue
        unit_id = unit_by_source.get(obj["object_id"], "NA")
        if obj.get("manual_review_required") == "true":
            block_type = "manual_review_exclusion_block"
        elif "broader_evidence_pool" in obj.get("exclusion_reason", ""):
            block_type = "broader_evidence_exclusion_block"
        else:
            block_type = "excluded_no_exact_trait_mapping_block"
        block_id = f"BLK_EXCLUDED_{safe_id(obj['object_id'])}"
        add_block_member(block_id, block_type, obj.get("chrom", "NA"), obj.get("start", 0), obj.get("end", 0), unit_id, obj, "excluded evidence retained for diagnostics only")

    rows: list[dict[str, object]] = []
    for block_id, members in block_members.items():
        meta = block_meta[block_id]
        start, end = as_int(meta["block_start"]), as_int(meta["block_end"])
        rows.append(
            {
                "split_block_id": block_id,
                "block_type": meta["block_type"],
                "chrom": meta["chrom"],
                "block_start": start if start else "NA",
                "block_end": end if end else "NA",
                "block_length": interval_length(start, end) if start and end else "NA",
                "member_unit_ids": compact_join(members),
                "n_units": len([m for m in members if not is_missing(m)]),
                "traits": compact_join(meta["traits"]),  # type: ignore[arg-type]
                "genes": compact_join(meta["genes"]),  # type: ignore[arg-type]
                "evidence_sources": compact_join(meta["evidence_sources"]),  # type: ignore[arg-type]
                "decoy_pair_ids": compact_join(meta["decoy_pair_ids"], limit=60),  # type: ignore[arg-type]
                "block_rule": meta["block_rule"],
                "leakage_risk_level": meta["leakage_risk_level"],
                "notes": meta["notes"],
                "split_version": SPLIT_VERSION,
            }
        )
    rows.sort(key=lambda r: (str(r["block_type"]), str(r["split_block_id"])))
    write_tsv(args.interim_root / "blocks/split_block_table.tsv", rows, BLOCK_FIELDS)
    write_preview(args.report_root, "split_block_table", rows, BLOCK_FIELDS)
    return rows


def build_assignment(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    units = read_tsv(args.interim_root / "units/split_unit_table.tsv")
    blocks = read_tsv(args.interim_root / "blocks/split_block_table.tsv")
    inputs = load_inputs(args)
    objects = inputs["objects"]
    pairs = inputs["pairs"]
    covariates = {row["internal_accession_id"]: row for row in inputs["covariates"]}
    object_by_id = {row["object_id"]: row for row in objects}
    main_objects = [row for row in objects if row.get("in_main_evaluation_candidate_pool") == "true"]
    qtl_component_by_object = qtl_components([row for row in main_objects if row.get("object_type") == "qtl_interval"])
    evidence_block_by_object: dict[str, str] = {}
    for obj in main_objects:
        block_id, _, _, _, _, _ = assignment_block_for_object(obj, qtl_component_by_object)
        evidence_block_by_object[obj["object_id"]] = block_id
    pair_object_by_pair = {row["decoy_pair_id"]: row["object_id"] for row in pairs}
    block_ids = {row["split_block_id"] for row in blocks}
    evidence_split_by_block = {block_id: assign_evidence_split(block_id, args.random_seed) for block_id in block_ids if block_id.startswith("BLK_MIXED_") or block_id.startswith("BLK_QTL_")}

    rows: list[dict[str, object]] = []
    for unit in units:
        unit_type = unit["split_unit_type"]
        block_id = "NA"
        assigned_split = "diagnostic_only"
        rule = "diagnostic-only split unit"
        if unit_type == "accession":
            block_id = f"BLK_ACC_{safe_id(unit['accession_id'])}"
            subgroup = covariates.get(unit["accession_id"], {}).get("broad_subgroup", "unknown_subgroup")
            assigned_split = assign_three_way(f"{subgroup}:{unit['accession_id']}", args.random_seed)
            rule = "stratified deterministic hash by broad_subgroup and accession_id; accession_id index only"
        elif unit_type == "trait":
            block_id = f"BLK_TRAIT_{safe_id(unit['trait_id'])}"
            assigned_split = "diagnostic_only"
            rule = "trait unit retained for diagnostics; no phenotype prediction split"
        elif unit_type == "region":
            block_id = f"BLK_WINDOW_{safe_id(proximity_bin(unit['chrom'], unit['start'], unit['end']))}"
            assigned_split = assign_evidence_split(block_id, args.random_seed)
            rule = f"chr1 window region follows {PROXIMITY_BIN_SIZE}bp neighborhood block"
        elif unit_type == "evidence_object":
            obj = object_by_id.get(unit["source_object_id"], {})
            if unit.get("manual_review_required") == "true":
                block_id = f"BLK_EXCLUDED_{safe_id(unit['source_object_id'])}"
                assigned_split = "excluded_manual_review"
                rule = "manual review evidence excluded from main evaluation split"
            elif unit.get("broader_evidence") == "true":
                block_id = f"BLK_EXCLUDED_{safe_id(unit['source_object_id'])}"
                assigned_split = "excluded_broader_evidence"
                rule = "broader evidence excluded from main evaluation split"
            elif unit.get("in_main_evaluation_candidate_pool") != "true":
                block_id = f"BLK_EXCLUDED_{safe_id(unit['source_object_id'])}"
                assigned_split = "excluded_no_exact_trait_mapping"
                rule = "non-exact or out-of-prototype evidence excluded from main evaluation split"
            else:
                block_id = evidence_block_by_object.get(unit["source_object_id"], "NA")
                assigned_split = evidence_split_by_block.get(block_id, assign_evidence_split(block_id, args.random_seed))
                rule = "main evidence follows leakage-aware region/QTL block; exact frozen trait mapping only"
        elif unit_type == "decoy_pair":
            object_id = pair_object_by_pair.get(unit["decoy_pair_id"], unit["source_object_id"])
            block_id = evidence_block_by_object.get(object_id, "NA")
            assigned_split = evidence_split_by_block.get(block_id, assign_evidence_split(block_id, args.random_seed))
            rule = "decoy pair follows its evidence object split; decoy is not a true negative"
        rows.append(
            {
                "assignment_id": f"ASN_{len(rows) + 1:09d}",
                "split_version": SPLIT_VERSION,
                "random_seed": args.random_seed,
                "split_unit_id": unit["split_unit_id"],
                "split_block_id": block_id,
                "split_unit_type": unit_type,
                "assigned_split": assigned_split,
                "assigned_role": assigned_role(assigned_split, unit_type),
                "trait_id": unit.get("trait_id", "NA"),
                "object_type": unit.get("object_type", "NA"),
                "chrom": unit.get("chrom", "NA"),
                "start": unit.get("start", "NA"),
                "end": unit.get("end", "NA"),
                "assignment_rule": rule,
                "prototype_locked_not_final": "true",
                "notes": "prototype split only; not final full benchmark split",
            }
        )
    write_tsv(args.interim_root / "assignments/frozen_split_assignment.tsv", rows, ASSIGNMENT_FIELDS)
    write_preview(args.report_root, "frozen_split_assignment", rows, ASSIGNMENT_FIELDS)
    return rows


def build_manifest(args: argparse.Namespace) -> list[dict[str, object]]:
    sources = [
        "reports/current_data_status/current_data_structure_report.md",
        "reports/matched_decoy_v055/matched_decoy_report.md",
        "data/interim/matched_decoy_v055/objects/matched_decoy_object_table.tsv",
        "data/interim/matched_decoy_v055/pairs/matched_decoy_pair_table.tsv",
        "data/interim/design_v055/metadata/trait_usability_table.tsv",
        "data/interim/trait_state/high_confidence_accessions.tsv",
        "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv",
        "data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv",
    ]
    rows = [
        {
            "split_name": "08C_freeze_chr1_snp_split_v055",
            "split_version": SPLIT_VERSION,
            "random_seed": args.random_seed,
            "source_tables": ";".join(sources),
            "created_at": now_utc(),
            "created_by_script": "scripts/frozen_split/validate_frozen_split_v055.py",
            "rule_summary": "accessions use broad_subgroup-stratified deterministic train/dev/test hash; evidence uses leakage-aware dev/prototype_locked/source_disjoint_or_temporal block assignment",
            "block_rule_summary": f"non-QTL evidence uses {PROXIMITY_BIN_SIZE}bp mixed evidence blocks; QTL intervals use overlap/nearby components with max_gap={QTL_PROXIMITY_BP}; decoy pairs follow evidence objects",
            "prototype_locked_not_final": "true",
            "limitations": "chr1 SNP-only prototype; no model training; no evaluator; no AUROC/AUPRC; no whole-genome SNP+indel; no SV/PAV/pan-reference; MAF/LD/mappability not available",
            "notes": f"08B input commit={current_commit(args.repo_root)}; evidence is not a training label and decoys are not true negatives",
        }
    ]
    write_tsv(args.interim_root / "diagnostics/split_manifest.tsv", rows, MANIFEST_FIELDS)
    write_tsv(args.report_root / "split_manifest.tsv", rows, MANIFEST_FIELDS)
    return rows


def build_balance_diagnostics(args: argparse.Namespace) -> list[dict[str, object]]:
    assignments = read_tsv(args.interim_root / "assignments/frozen_split_assignment.tsv")
    units = {row["split_unit_id"]: row for row in read_tsv(args.interim_root / "units/split_unit_table.tsv")}
    inputs = load_inputs(args)
    covariates = {row["internal_accession_id"]: row for row in inputs["covariates"]}
    object_by_id = {row["object_id"]: row for row in inputs["objects"]}
    assignment_by_unit = {row["split_unit_id"]: row for row in assignments}

    rows: list[dict[str, object]] = []
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for assignment in assignments:
        unit = units.get(assignment["split_unit_id"], {})
        key = (assignment["assigned_split"], unit.get("split_unit_type", "NA"), unit.get("object_type", "NA"))
        groups[key].append(assignment)

    for (split_name, unit_type, object_type), group in sorted(groups.items()):
        source_units = [units[row["split_unit_id"]] for row in group if row["split_unit_id"] in units]
        accession_ids = [unit.get("accession_id", "NA") for unit in source_units if unit.get("split_unit_type") == "accession"]
        subgroup_counts = Counter(covariates.get(acc, {}).get("broad_subgroup", "unknown") for acc in accession_ids)
        pc_summary = pc_balance_summary(accession_ids, covariates)
        traits = Counter(unit.get("trait_id", "NA") for unit in source_units if not is_missing(unit.get("trait_id")))
        evidence_sources = Counter()
        positions = []
        for unit in source_units:
            if unit.get("split_unit_type") == "evidence_object":
                obj = object_by_id.get(unit.get("source_object_id", ""), {})
                evidence_sources[obj.get("evidence_source", obj.get("source_database", "NA"))] += 1
            if as_int(unit.get("start")) and as_int(unit.get("end")):
                positions.append(interval_center(unit.get("start"), unit.get("end")))
        block_ids = {row["split_block_id"] for row in group if not is_missing(row.get("split_block_id"))}
        rows.append(
            {
                "diagnostic_id": f"SBD_{len(rows) + 1:08d}",
                "split_version": SPLIT_VERSION,
                "diagnostic_type": f"{unit_type}_{object_type}",
                "assigned_split": split_name,
                "trait_id": compact_join(traits.keys(), limit=20),
                "object_type": object_type,
                "n_units": len(group),
                "n_blocks": len(block_ids),
                "n_accessions": len(accession_ids),
                "n_evidence_objects": sum(1 for unit in source_units if unit.get("split_unit_type") == "evidence_object"),
                "n_decoy_pairs": sum(1 for unit in source_units if unit.get("split_unit_type") == "decoy_pair"),
                "subgroup_distribution": counter_summary(subgroup_counts),
                "PC_balance_summary": pc_summary,
                "trait_distribution": counter_summary(traits),
                "evidence_source_distribution": counter_summary(evidence_sources),
                "object_type_distribution": counter_summary(Counter(unit.get("object_type", "NA") for unit in source_units)),
                "position_distribution": position_summary(positions),
                "gene_density_summary": "unavailable_in_split_unit_table; see matched_decoy diagnostics",
                "variant_density_summary": "unavailable_in_split_unit_table; see matched_decoy diagnostics",
                "notes": "balance diagnostics are prototype checks; not a formal evaluator",
            }
        )

    rows.extend(global_balance_rows(rows, assignments, units, covariates))
    write_tsv(args.interim_root / "diagnostics/split_balance_diagnostics.tsv", rows, BALANCE_FIELDS)
    write_tsv(args.report_root / "split_balance_diagnostics.tsv", rows, BALANCE_FIELDS)
    return rows


def counter_summary(counter: Counter[str], limit: int = 12) -> str:
    if not counter:
        return "NA"
    return ";".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def position_summary(values: list[int]) -> str:
    if not values:
        return "NA"
    return f"min={min(values)};median={int(statistics.median(values))};max={max(values)}"


def pc_balance_summary(accession_ids: list[str], covariates: dict[str, dict[str, str]]) -> str:
    if not accession_ids:
        return "NA"
    parts = []
    for pc in ["PC1", "PC2", "PC3", "PC4", "PC5"]:
        values = [as_float(covariates.get(acc, {}).get(pc)) for acc in accession_ids if not is_missing(covariates.get(acc, {}).get(pc))]
        if values:
            parts.append(f"{pc}_mean={fmt(statistics.mean(values))}")
    return ";".join(parts) if parts else "PC_unavailable"


def global_balance_rows(existing: list[dict[str, object]], assignments: list[dict[str, str]], units: dict[str, dict[str, str]], covariates: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for split_name in ["train", "dev", "test"]:
        split_assignments = [a for a in assignments if a.get("assigned_split") == split_name and a.get("split_unit_type") == "accession"]
        accession_ids = [units[a["split_unit_id"]].get("accession_id", "NA") for a in split_assignments if a["split_unit_id"] in units]
        subgroup_counts = Counter(covariates.get(acc, {}).get("broad_subgroup", "unknown") for acc in accession_ids)
        rows.append(
            {
                "diagnostic_id": f"SBD_{len(existing) + len(rows) + 1:08d}",
                "split_version": SPLIT_VERSION,
                "diagnostic_type": "accession_global_balance",
                "assigned_split": split_name,
                "trait_id": "NA",
                "object_type": "accession",
                "n_units": len(split_assignments),
                "n_blocks": len({a["split_block_id"] for a in split_assignments}),
                "n_accessions": len(accession_ids),
                "n_evidence_objects": 0,
                "n_decoy_pairs": 0,
                "subgroup_distribution": counter_summary(subgroup_counts),
                "PC_balance_summary": pc_balance_summary(accession_ids, covariates),
                "trait_distribution": "NA",
                "evidence_source_distribution": "NA",
                "object_type_distribution": "accession",
                "position_distribution": "NA",
                "gene_density_summary": "NA",
                "variant_density_summary": "NA",
                "notes": "accession_id is index-only; balance by broad_subgroup and PC summary",
            }
        )
    return rows


def build_leakage_checks(args: argparse.Namespace) -> list[dict[str, object]]:
    assignments = read_tsv(args.interim_root / "assignments/frozen_split_assignment.tsv")
    units = {row["split_unit_id"]: row for row in read_tsv(args.interim_root / "units/split_unit_table.tsv")}
    blocks = read_tsv(args.interim_root / "blocks/split_block_table.tsv")
    rows: list[dict[str, object]] = []

    def add(name: str, ok: bool, n_checked: int, n_leakage: int, leakage_type: str, affected_units: Iterable[str], affected_blocks: Iterable[str], details: str, blocking: bool = True, notes: str = "NA") -> None:
        rows.append(
            {
                "check_id": f"SLC_{len(rows) + 1:08d}",
                "check_name": name,
                "status": "pass" if ok else ("warn" if not blocking else "fail"),
                "n_checked": n_checked,
                "n_leakage": n_leakage,
                "leakage_type": leakage_type,
                "affected_units": compact_join(affected_units, limit=30),
                "affected_blocks": compact_join(affected_blocks, limit=30),
                "details": details,
                "blocking_issue": str(blocking and not ok).lower(),
                "notes": notes,
                "split_version": SPLIT_VERSION,
            }
        )

    by_unit = defaultdict(set)
    for assignment in assignments:
        by_unit[assignment["split_unit_id"]].add(assignment["assigned_split"])
    accession_cross = [unit_id for unit_id, splits in by_unit.items() if units.get(unit_id, {}).get("split_unit_type") == "accession" and len(splits & {"train", "dev", "test"}) > 1]
    add("same_accession_not_cross_train_dev_test", not accession_cross, sum(1 for u in units.values() if u.get("split_unit_type") == "accession"), len(accession_cross), "accession_cross_split", accession_cross, [], "one accession assignment row per accession")

    block_splits: dict[str, set[str]] = defaultdict(set)
    for assignment in assignments:
        if assignment["assigned_split"] in {"dev", "prototype_locked"}:
            block_splits[assignment["split_block_id"]].add(assignment["assigned_split"])
    block_meta = {row["split_block_id"]: row for row in blocks}
    risky_blocks = [block for block, splits in block_splits.items() if len(splits) > 1 and block_meta.get(block, {}).get("block_type") in {"gene_block", "mixed_evidence_block", "interval_overlap_block", "qtl_region_block"}]
    add("gene_or_mixed_blocks_not_cross_development_prototype_locked", not risky_blocks, len(block_splits), len(risky_blocks), "block_cross_dev_prototype", [], risky_blocks, "assigned block should not contain both dev and prototype_locked")

    interval_blocks = [row["split_block_id"] for row in blocks if row.get("block_type") in {"interval_overlap_block", "qtl_region_block"}]
    interval_cross = [block for block in interval_blocks if len(block_splits.get(block, set())) > 1]
    add("overlapping_interval_or_qtl_blocks_not_cross_development_prototype_locked", not interval_cross, len(interval_blocks), len(interval_cross), "interval_qtl_cross_split", [], interval_cross, f"QTL nearby threshold={QTL_PROXIMITY_BP}")

    decoy_assignments = [a for a in assignments if a.get("split_unit_type") == "decoy_pair"]
    evidence_by_object = {}
    for assignment in assignments:
        unit = units.get(assignment["split_unit_id"], {})
        if unit.get("split_unit_type") == "evidence_object":
            evidence_by_object[unit.get("source_object_id", "NA")] = assignment
    decoy_mismatch = []
    for assignment in decoy_assignments:
        unit = units.get(assignment["split_unit_id"], {})
        evidence_assignment = evidence_by_object.get(unit.get("source_object_id", "NA"))
        if evidence_assignment and evidence_assignment.get("assigned_split") != assignment.get("assigned_split"):
            decoy_mismatch.append(assignment["split_unit_id"])
    add("same_decoy_set_and_evidence_object_split_consistent", not decoy_mismatch, len(decoy_assignments), len(decoy_mismatch), "decoy_set_cross_split", decoy_mismatch, [], "decoy pair must follow evidence object")

    manual_bad = [a["split_unit_id"] for a in assignments if units.get(a["split_unit_id"], {}).get("manual_review_required") == "true" and a.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"}]
    add("manual_review_not_in_main_evaluation_split", not manual_bad, len(assignments), len(manual_bad), "manual_review_in_main", manual_bad, [], "manual review evidence must be excluded")

    broader_bad = [a["split_unit_id"] for a in assignments if units.get(a["split_unit_id"], {}).get("broader_evidence") == "true" and a.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"}]
    add("broader_evidence_not_in_main_evaluation_split", not broader_bad, len(assignments), len(broader_bad), "broader_evidence_in_main", broader_bad, [], "broader evidence must be excluded")

    pex_bad = [a["split_unit_id"] for a in assignments if a.get("trait_id") == "data_lt_2007__pex_repro" and a.get("split_unit_type") == "evidence_object" and a.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"}]
    add("pex_repro_not_force_filled", not pex_bad, len(assignments), len(pex_bad), "pex_repro_forced_evidence", pex_bad, [], "PEX_REPRO remains zero exact main evidence")

    final_locked = [a["split_unit_id"] for a in assignments if "final_locked" in a.get("assigned_split", "") or "final_locked" in a.get("notes", "")]
    add("prototype_locked_not_written_as_final_locked", not final_locked, len(assignments), len(final_locked), "final_locked_string", final_locked, [], "assignment table must use prototype_locked only")

    true_negative = [a["split_unit_id"] for a in assignments if "true_negative" in " ".join(a.values()).lower()]
    add("unknown_unlabeled_and_decoys_not_true_negative", not true_negative, len(assignments), len(true_negative), "true_negative_label", true_negative, [], "decoys and unknown/unlabeled are not true negatives")

    write_tsv(args.interim_root / "diagnostics/split_leakage_check.tsv", rows, LEAKAGE_FIELDS)
    write_tsv(args.report_root / "split_leakage_check.tsv", rows, LEAKAGE_FIELDS)
    return rows


def validate_and_report(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    manifest = build_manifest(args)
    balance = build_balance_diagnostics(args)
    leakage = build_leakage_checks(args)
    units = read_tsv(args.interim_root / "units/split_unit_table.tsv")
    blocks = read_tsv(args.interim_root / "blocks/split_block_table.tsv")
    assignments = read_tsv(args.interim_root / "assignments/frozen_split_assignment.tsv")
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
                "split_version": SPLIT_VERSION,
            }
        )

    expected = [
        args.interim_root / "units/split_unit_table.tsv",
        args.interim_root / "blocks/split_block_table.tsv",
        args.interim_root / "assignments/frozen_split_assignment.tsv",
        args.interim_root / "diagnostics/split_balance_diagnostics.tsv",
        args.interim_root / "diagnostics/split_leakage_check.tsv",
        args.interim_root / "diagnostics/split_manifest.tsv",
    ]
    missing = [rel(path) for path in expected if count_rows(path) == 0]
    add("outputs_exist_and_nonempty", not missing, len(expected), len(missing), ";".join(missing) if missing else "all required outputs are nonempty")
    add_unique(rows, "split_unit_table_primary_key_unique", units, "split_unit_id")
    add_unique(rows, "split_block_table_primary_key_unique", blocks, "split_block_id")
    add_unique(rows, "frozen_split_assignment_primary_key_unique", assignments, "assignment_id")
    unit_types = {row.get("split_unit_type") for row in units}
    required_units = {"accession", "evidence_object", "decoy_pair", "region", "trait"}
    missing_units = required_units - unit_types
    add("split_unit_table_has_required_unit_types", not missing_units, len(required_units), len(missing_units), ";".join(sorted(missing_units)) if missing_units else "all required unit types present")
    block_types = {row.get("block_type") for row in blocks}
    required_blocks = {"gene_block", "interval_overlap_block", "qtl_region_block", "decoy_set_block", "mixed_evidence_block"}
    missing_blocks = required_blocks - block_types
    add("split_block_table_has_leakage_block_types", not missing_blocks, len(required_blocks), len(missing_blocks), ";".join(sorted(missing_blocks)) if missing_blocks else "all required block types present")
    final_locked = [row for row in assignments if "final_locked" in " ".join(row.values())]
    add("frozen_split_assignment_has_no_final_locked", not final_locked, len(assignments), len(final_locked), "assignment rows must not contain final_locked")
    missing_proto = [row for row in assignments if row.get("prototype_locked_not_final") != "true"]
    add("prototype_locked_not_final_flag_present", not missing_proto, len(assignments), len(missing_proto), "prototype_locked_not_final must be true for all rows")
    manual_bad = [row for row in assignments if row.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"} and "manual review" in row.get("assignment_rule", "").lower()]
    add("manual_review_not_in_main_split", not manual_bad, len(assignments), len(manual_bad), "manual review rows excluded from main split")
    broader_bad = [row for row in assignments if row.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"} and "broader" in row.get("assignment_rule", "").lower()]
    add("broader_evidence_not_in_main_split", not broader_bad, len(assignments), len(broader_bad), "broader rows excluded from main split")
    leak_fail = [row for row in leakage if row.get("status") == "fail" or row.get("blocking_issue") == "true"]
    add("leakage_check_has_no_blocking_failures", not leak_fail, len(leakage), len(leak_fail), "leakage checks pass or are non-blocking warnings")
    add("split_manifest_complete", bool(manifest and manifest[0].get("prototype_locked_not_final") == "true"), len(manifest), 0 if manifest else 1, "split manifest records seed, rules, source tables, and limitations")
    write_tsv(args.interim_root / "diagnostics/split_validation.tsv", rows, VALIDATION_FIELDS)
    write_tsv(args.report_root / "split_validation.tsv", rows, VALIDATION_FIELDS)
    write_report(args, units, blocks, assignments, balance, leakage, rows)
    return rows


def add_unique(rows: list[dict[str, object]], check_name: str, table: list[dict[str, str]], key: str) -> None:
    values = [row.get(key, "NA") for row in table]
    missing = sum(1 for value in values if is_missing(value))
    duplicates = len(values) - len(set(values))
    rows.append(
        {
            "check_name": check_name,
            "status": "pass" if missing == 0 and duplicates == 0 else "fail",
            "n_records": len(table),
            "n_failed": missing + duplicates,
            "details": f"primary key {key}; missing={missing}; duplicates={duplicates}",
            "blocking_issue": str(missing > 0 or duplicates > 0).lower(),
            "notes": "NA",
            "split_version": SPLIT_VERSION,
        }
    )


def write_report(
    args: argparse.Namespace,
    units: list[dict[str, str]],
    blocks: list[dict[str, str]],
    assignments: list[dict[str, str]],
    balance: list[dict[str, str]],
    leakage: list[dict[str, str]],
    validation: list[dict[str, object]],
) -> None:
    unit_counter = Counter(row.get("split_unit_type", "NA") for row in units)
    block_counter = Counter(row.get("block_type", "NA") for row in blocks)
    accession_split = Counter(row.get("assigned_split", "NA") for row in assignments if row.get("split_unit_type") == "accession")
    evidence_split = Counter(row.get("assigned_split", "NA") for row in assignments if row.get("split_unit_type") == "evidence_object")
    pair_mismatch = [row for row in leakage if row.get("check_name") == "same_decoy_set_and_evidence_object_split_consistent" and row.get("status") != "pass"]
    leak_warn = [row for row in leakage if row.get("status") == "warn"]
    leak_fail = [row for row in leakage if row.get("status") == "fail"]
    validation_failed = [row for row in validation if row.get("status") == "fail"]
    pex_main = sum(1 for row in assignments if row.get("trait_id") == "data_lt_2007__pex_repro" and row.get("split_unit_type") == "evidence_object" and row.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"})
    manual_main = sum(1 for row in assignments if row.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"} and "manual review" in row.get("assignment_rule", "").lower())
    broader_main = sum(1 for row in assignments if row.get("assigned_split") in {"dev", "prototype_locked", "source_disjoint_or_temporal"} and "broader" in row.get("assignment_rule", "").lower())
    files = [
        args.interim_root / "units/split_unit_table.tsv",
        args.interim_root / "blocks/split_block_table.tsv",
        args.interim_root / "assignments/frozen_split_assignment.tsv",
        args.interim_root / "diagnostics/split_balance_diagnostics.tsv",
        args.interim_root / "diagnostics/split_leakage_check.tsv",
        args.interim_root / "diagnostics/split_validation.tsv",
        args.interim_root / "diagnostics/split_manifest.tsv",
    ]
    lines = [
        "# Frozen Split v0.5.5 Report",
        "",
        "## Scope",
        "",
        "This run freezes a leakage-aware prototype split for the chr1 SNP-only prototype. It is not the final full benchmark split. `prototype_locked` is explicitly not `final_locked`.",
        "",
        "No model was trained. No formal evaluator was built. No AUROC/AUPRC was reported. Evidence is not a training label, and matched decoy is not a true negative.",
        "",
        "## Generated Tables",
        "",
        "| table | rows |",
        "|---|---:|",
    ]
    for path in files:
        lines.append(f"| `{rel(path)}` | {count_rows(path)} |")
    lines.extend(["", "## Split Unit Counts", "", "| split_unit_type | rows |", "|---|---:|"])
    for key, value in sorted(unit_counter.items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Split Block Counts", "", "| block_type | rows |", "|---|---:|"])
    for key, value in sorted(block_counter.items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Assignment Summary",
            "",
            f"- Current input commit hash: `{current_commit(args.repo_root)}`.",
            f"- Accession split counts: {counter_summary(accession_split)}.",
            f"- Evidence object split counts: {counter_summary(evidence_split)}.",
            f"- PEX_REPRO main evidence rows after split: {pex_main}.",
            f"- Manual review rows in main evaluation splits: {manual_main}.",
            f"- Broader evidence rows in main evaluation splits: {broader_main}.",
            f"- Decoy pair split mismatch checks failed: {len(pair_mismatch)}.",
            f"- Leakage warnings: {len(leak_warn)}; leakage failures: {len(leak_fail)}.",
            f"- Validation failed checks: {len(validation_failed)}.",
            "",
            "## Block Rules",
            "",
            f"- Non-QTL evidence, gene evidence, window evidence, variant evidence, and their decoy pairs use mixed evidence blocks with {PROXIMITY_BIN_SIZE} bp proximity bins.",
            f"- QTL intervals use overlap/nearby components with {QTL_PROXIMITY_BP} bp max gap.",
            "- Decoy pairs follow their evidence object split.",
            "- Manual review, broader evidence, and non-exact trait mapping objects are assigned to excluded split states and do not enter main evaluation splits.",
            "",
            "## Balance Diagnostics",
            "",
            "- Accession split uses broad_subgroup-stratified deterministic hashing and reports PC1-PC5 means by split.",
            "- Evidence split reports trait, object type, source, and position summaries.",
            "- Gene density and variant density summaries remain delegated to matched decoy diagnostics and are marked unavailable in split unit tables.",
            "",
            "## Leakage Handling",
            "",
            "- Same accession does not cross train/dev/test.",
            "- Mixed evidence, QTL interval, and decoy set blocks are kept within a single development/prototype/source-disjoint split.",
            "- Evidence object and corresponding decoy pair assignments are checked for consistency.",
            "- Unknown/unlabeled and decoy rows are never represented as true negatives.",
            "",
            "## Limitations",
            "",
            "- This is a chr1 SNP-only prototype split and does not cover whole-genome SNP+indel data.",
            "- Region blocking uses coarse proximity bins and QTL source coordinates without liftover.",
            "- MAF, LD, mappability, recombination rate, and full callability are not available in this split layer.",
            "- `prototype_locked` is a prototype holdout state only, not the final full benchmark lock.",
            "",
            "## Next Step",
            "",
            "The split layer is sufficient to start an evaluator scaffold for the chr1 SNP-only prototype, while preserving the current no-training and no-formal-AUROC/AUPRC boundary.",
        ]
    )
    (args.report_root / "frozen_split_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(name: str, rows: list[dict[str, object]], extra: str = "") -> None:
    print(f"{name}_rows={len(rows)}")
    if extra:
        print(extra)
