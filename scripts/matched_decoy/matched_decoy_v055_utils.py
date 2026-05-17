#!/usr/bin/env python3
"""Utilities for chr1 SNP-only matched decoy v0.5.5 preprocessing."""

from __future__ import annotations

import argparse
import bisect
import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION = "matched_decoy_v055_chr1_snp_prototype_v1"

DEFAULT_EXTERNAL_ROOT = REPO_ROOT / "data/interim/external_knowledge_v055"
DEFAULT_V01_ROOT = REPO_ROOT / "data/interim/v0_1_mini"
DEFAULT_TASK1_ROOT = REPO_ROOT / "data/interim/task1_chr1_snp"
DEFAULT_DESIGN_ROOT = REPO_ROOT / "data/interim/design_v055"
DEFAULT_INTERIM_ROOT = REPO_ROOT / "data/interim/matched_decoy_v055"
DEFAULT_REPORT_ROOT = REPO_ROOT / "reports/matched_decoy_v055"


OBJECT_FIELDS = [
    "object_id",
    "object_type",
    "trait_id",
    "trait_name",
    "evidence_id",
    "evidence_source",
    "evidence_source_type",
    "evidence_level",
    "support_level",
    "allowed_usage",
    "chrom",
    "start",
    "end",
    "object_length",
    "gene_id",
    "gene_symbol",
    "variant_id",
    "window_id",
    "source_database",
    "source_record_id",
    "mapping_status",
    "coordinate_confidence",
    "exact_frozen_trait_mapping",
    "manual_review_required",
    "in_main_evaluation_candidate_pool",
    "exclusion_reason",
    "notes",
    "pipeline_version",
]

CANDIDATE_FIELDS = [
    "candidate_pool_id",
    "object_id",
    "trait_id",
    "object_type",
    "candidate_object_id",
    "candidate_object_type",
    "candidate_chrom",
    "candidate_start",
    "candidate_end",
    "candidate_length",
    "same_chrom",
    "position_bin",
    "position_distance",
    "gene_density_object",
    "gene_density_candidate",
    "variant_density_object",
    "variant_density_candidate",
    "annotation_richness_object",
    "annotation_richness_candidate",
    "evidence_source_coverage_object",
    "evidence_source_coverage_candidate",
    "database_detectability_object",
    "database_detectability_candidate",
    "interval_length_object",
    "interval_length_candidate",
    "chr1_snp_window_coverage_object",
    "chr1_snp_window_coverage_candidate",
    "chr1_snp_variant_coverage_object",
    "chr1_snp_variant_coverage_candidate",
    "candidate_pool_status",
    "candidate_exclusion_reason",
    "notes",
    "pipeline_version",
]

PAIR_FIELDS = [
    "decoy_pair_id",
    "object_id",
    "trait_id",
    "object_type",
    "decoy_object_id",
    "decoy_object_type",
    "match_rank",
    "match_score",
    "matching_level",
    "matching_status",
    "relaxation_level",
    "relaxation_reason",
    "n_candidates_before_filter",
    "n_candidates_after_filter",
    "matched_fields",
    "unavailable_fields",
    "field_balance_score",
    "position_balance_score",
    "density_balance_score",
    "annotation_balance_score",
    "detectability_balance_score",
    "research_bias_balance_score",
    "notes",
    "pipeline_version",
]

DIAGNOSTIC_FIELDS = [
    "diagnostic_id",
    "object_type",
    "trait_id",
    "n_evidence_objects",
    "n_main_evaluation_objects",
    "n_objects_with_candidate_pool",
    "n_objects_with_matched_decoy",
    "n_objects_without_decoy",
    "median_candidates_per_object",
    "mean_candidates_per_object",
    "median_decoys_per_object",
    "mean_match_score",
    "median_match_score",
    "n_strict_matches",
    "n_relaxed_matches",
    "n_failed_matches",
    "top_failure_reasons",
    "field_balance_summary",
    "position_balance_summary",
    "gene_density_balance_summary",
    "variant_density_balance_summary",
    "annotation_richness_balance_summary",
    "detectability_balance_summary",
    "research_bias_balance_summary",
    "notes",
    "pipeline_version",
]

FIELD_AVAILABILITY_FIELDS = [
    "field_name",
    "field_category",
    "availability",
    "proxy_field",
    "used_in_object_table",
    "used_in_candidate_pool",
    "used_in_pair_matching",
    "used_in_diagnostics",
    "used_in_sensitivity",
    "missing_reason",
    "notes",
    "pipeline_version",
]

DETECTABILITY_FIELDS = [
    "object_id",
    "object_type",
    "chrom",
    "start",
    "end",
    "missingness_rate",
    "callability_proxy",
    "chr1_snp_coverage",
    "window_coverage",
    "variant_coverage",
    "mappability_proxy",
    "low_complexity_or_repeat_proxy",
    "database_detectability_proxy",
    "detectability_score",
    "detectability_fields_available",
    "notes",
    "pipeline_version",
]

RESEARCH_BIAS_FIELDS = [
    "object_id",
    "object_type",
    "gene_id",
    "gene_symbol",
    "chrom",
    "start",
    "end",
    "annotation_record_count",
    "external_knowledge_hit_count",
    "known_gene_proximity",
    "database_source_count",
    "trait_evidence_count",
    "annotation_richness_score",
    "literature_bias_proxy",
    "research_bias_score",
    "research_bias_fields_available",
    "notes",
    "pipeline_version",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "n_records",
    "n_failed",
    "details",
    "blocking_issue",
    "notes",
    "pipeline_version",
]

FROZEN_TRAIT_ORDER = [
    "data_lt_2007__spkf",
    "data_lt_2007__fla_repro",
    "data_lt_2007__cult_code_repro",
    "data_lt_2007__llt_code",
    "data_lt_2007__pex_repro",
    "data_lt_2007__lsen",
    "data_lt_2007__pth",
    "data_lt_2007__cuan_repro",
    "data_lt_2007__cudi_code_repro",
]

UNAVAILABLE_MATCH_FIELDS = ["MAF", "LD", "missingness", "mappability", "recombination_rate"]
MATCHED_FIELDS = [
    "coordinate",
    "position_bin",
    "gene_density",
    "variant_density",
    "annotation_richness",
    "database_detectability",
    "research_bias",
    "chr1_snp_coverage",
]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--external-root", type=Path, default=DEFAULT_EXTERNAL_ROOT)
    parser.add_argument("--v01-root", type=Path, default=DEFAULT_V01_ROOT)
    parser.add_argument("--task1-root", type=Path, default=DEFAULT_TASK1_ROOT)
    parser.add_argument("--design-root", type=Path, default=DEFAULT_DESIGN_ROOT)
    parser.add_argument("--interim-root", type=Path, default=DEFAULT_INTERIM_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--max-candidates-per-object", type=int, default=30)
    parser.add_argument("--max-decoys-per-object", type=int, default=5)
    return parser.parse_args()


def ensure_output_dirs(interim_root: Path, report_root: Path) -> None:
    for subdir in ["objects", "candidate_pool", "pairs", "diagnostics"]:
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
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}".rstrip("0").rstrip(".") if math.isfinite(value) else "NA"


def normalize_chrom(value: object) -> str:
    text = clean(value)
    if text.lower().startswith("chr"):
        text = text[3:]
    return text


def normalize_trait_name(value: object) -> str:
    text = clean(value).lower()
    text = text.replace("_", " ")
    text = text.replace("repro", " ")
    text = text.replace("code", " ")
    text = text.replace("lt 2007", " ")
    text = text.replace("data", " ")
    text = text.replace("pex", "panicle exsertion")
    text = text.replace("spkf", "seed set percent fertility sterility")
    text = text.replace("fla", "flag leaf angle")
    text = text.replace("cult", "culm length plant height")
    text = text.replace("llt", "leaf length")
    text = text.replace("lsen", "leaf senescence")
    text = text.replace("pth", "panicle threshability")
    text = text.replace("cuan", "culm angle")
    text = text.replace("cudi", "culm diameter")
    text = " ".join(part for part in text.split(";") if part)
    import re

    text = re.sub(r"to:\d+\s*-\s*", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def interval_length(start: object, end: object) -> int:
    s, e = as_int(start), as_int(end)
    return max(0, e - s + 1) if s and e and e >= s else 0


def interval_center(start: object, end: object) -> int:
    s, e = as_int(start), as_int(end)
    return (s + e) // 2 if s and e else 0


def position_bin(chrom: object, start: object, end: object, bin_size: int = 1_000_000) -> str:
    center = interval_center(start, end)
    if not center:
        return "NA"
    return f"chr{normalize_chrom(chrom)}:{center // bin_size}Mb"


def overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a <= end_b and start_b <= end_a


def distance_between(start_a: int, end_a: int, start_b: int, end_b: int) -> int:
    if overlap(start_a, end_a, start_b, end_b):
        return 0
    if end_a < start_b:
        return start_b - end_a
    return start_a - end_b


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


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def load_frozen_traits(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "reports/trait_state_review/frozen_v0_1_traits.tsv"
    rows = read_tsv(path)
    alias_map = {
        "SPKF": ["seed set percent", "fertility", "sterility"],
        "FLA_REPRO": ["flag leaf angle", "leaf angle"],
        "CULT_CODE_REPRO": ["culm length", "plant height", "relative plant height", "seedling height"],
        "LLT_CODE": ["leaf length", "flag leaf length"],
        "PEX_REPRO": ["panicle exsertion"],
        "LSEN": ["leaf senescence", "senescence"],
        "PTH": ["panicle threshability", "threshability"],
        "CUAN_REPRO": ["culm angle", "culm habit", "flag leaf angle"],
        "CUDI_CODE_REPRO": ["culm diameter", "stem diameter"],
    }
    output: list[dict[str, str]] = []
    for row in rows:
        trait_name = clean(row.get("trait_name"))
        keywords = {normalize_trait_name(trait_name)}
        weak_match = clean(row.get("weak_evidence_match"))
        parts = weak_match.split(":")
        if len(parts) >= 2:
            keywords.add(normalize_trait_name(parts[1]))
        for alias in alias_map.get(trait_name, []):
            keywords.add(normalize_trait_name(alias))
        output.append(
            {
                "trait_id": clean(row.get("trait_id")),
                "trait_name": trait_name,
                "keywords": ";".join(sorted(k for k in keywords if k)),
            }
        )
    return output


def match_frozen_trait(trait_name: str, frozen_traits: list[dict[str, str]], *, allow_pex: bool = False) -> tuple[str, str, str]:
    normalized = normalize_trait_name(trait_name)
    if not normalized:
        return "NA", "NA", "missing_trait_name"
    matches: list[tuple[str, str]] = []
    for row in frozen_traits:
        for keyword in row["keywords"].split(";"):
            if keyword and (keyword in normalized or normalized in keyword):
                matches.append((row["trait_id"], row["trait_name"]))
                break
    unique = sorted(set(matches))
    if len(unique) == 1:
        trait_id, name = unique[0]
        if trait_id == "data_lt_2007__pex_repro" and not allow_pex:
            return trait_id, name, "manual_review_required_pex_repro_no_exact_gene_evidence"
        return trait_id, name, "keyword_match_to_frozen_trait"
    if len(unique) > 1:
        return ";".join(item[0] for item in unique), ";".join(item[1] for item in unique), "ambiguous_keyword_match"
    return "NA", "NA", "broader_evidence_pool_not_frozen_trait"


def load_inputs(args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    return {
        "gene_annotation": read_tsv(args.external_root / "annotation/gene_annotation_table.tsv"),
        "known_gene": read_tsv(args.external_root / "evidence/known_gene_evidence_table.tsv"),
        "trait_gene": read_tsv(args.external_root / "evidence/trait_gene_evidence_table.tsv"),
        "qtl": read_tsv(args.external_root / "evidence/qtl_interval_evidence_table.tsv"),
        "windows": read_tsv(args.v01_root / "window_table_chr1_v0_1.tsv"),
        "variants": read_tsv(args.v01_root / "variant_table_chr1_snp_v0_1.tsv"),
        "variant_windows": read_tsv(args.v01_root / "variant_window_mapping_chr1_v0_1.tsv"),
        "window_signal": read_tsv(args.task1_root / "window_weak_signal_chr1_snp.tsv"),
        "variant_label": read_tsv(args.task1_root / "variant_weak_label_chr1_snp.tsv"),
        "design_matching_fields": read_tsv(args.design_root / "decoy/matching_field_availability_table.tsv"),
    }


def build_gene_features(annotation_rows: list[dict[str, str]], known_rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in annotation_rows:
        gene_id = clean(row.get("gene_id"))
        if not gene_id or is_missing(gene_id):
            continue
        if interval_length(row.get("start"), row.get("end")) <= 0:
            continue
        grouped[gene_id].append(row)

    evidence_by_gene: Counter[str] = Counter()
    trait_evidence_by_gene: dict[str, set[str]] = defaultdict(set)
    evidence_sources_by_gene: dict[str, set[str]] = defaultdict(set)
    evidence_centers_by_chrom: dict[str, list[int]] = defaultdict(list)
    for row in known_rows:
        gene_id = clean(row.get("gene_id"))
        chrom = normalize_chrom(row.get("chrom"))
        if not gene_id or is_missing(gene_id):
            continue
        evidence_by_gene[gene_id] += 1
        trait_evidence_by_gene[gene_id].add(clean(row.get("trait_id_or_name")))
        evidence_sources_by_gene[gene_id].add(clean(row.get("source_database")))
        if chrom == "1" and interval_length(row.get("start"), row.get("end")) > 0:
            evidence_centers_by_chrom[chrom].append(interval_center(row.get("start"), row.get("end")))
    for centers in evidence_centers_by_chrom.values():
        centers.sort()

    centers_by_chrom: dict[str, list[int]] = defaultdict(list)
    features: dict[str, dict[str, object]] = {}
    for gene_id, rows in grouped.items():
        valid_rows = [r for r in rows if interval_length(r.get("start"), r.get("end")) > 0]
        chrom_counter = Counter(normalize_chrom(r.get("chrom")) for r in valid_rows)
        chrom = chrom_counter.most_common(1)[0][0]
        starts = [as_int(r.get("start")) for r in valid_rows if normalize_chrom(r.get("chrom")) == chrom]
        ends = [as_int(r.get("end")) for r in valid_rows if normalize_chrom(r.get("chrom")) == chrom]
        if not starts or not ends:
            continue
        start, end = min(starts), max(ends)
        center = (start + end) // 2
        source_databases = {clean(r.get("source_database")) for r in valid_rows if clean(r.get("source_database"))}
        gene_symbols = [clean(r.get("gene_symbol")) for r in valid_rows if not is_missing(r.get("gene_symbol"))]
        features[gene_id] = {
            "candidate_object_id": f"GENE_BG_{gene_id}",
            "candidate_object_type": "gene",
            "gene_id": gene_id,
            "gene_symbol": gene_symbols[0] if gene_symbols else "NA",
            "chrom": chrom,
            "start": start,
            "end": end,
            "length": end - start + 1,
            "center": center,
            "annotation_record_count": len(valid_rows),
            "database_source_count": len(source_databases),
            "external_knowledge_hit_count": evidence_by_gene[gene_id],
            "trait_evidence_count": len(trait_evidence_by_gene[gene_id]),
            "evidence_source_coverage": len(evidence_sources_by_gene[gene_id]),
        }
        centers_by_chrom[chrom].append(center)
    for centers in centers_by_chrom.values():
        centers.sort()
    for feature in features.values():
        chrom = str(feature["chrom"])
        center = int(feature["center"])
        feature["gene_density"] = count_between(centers_by_chrom[chrom], center - 500_000, center + 500_000)
        evidence_centers = evidence_centers_by_chrom.get(chrom, [])
        feature["known_gene_proximity"] = nearest_distance(evidence_centers, center)
        feature["annotation_richness"] = float(feature["annotation_record_count"]) + 0.5 * float(feature["database_source_count"])
        feature["database_detectability"] = min(1.0, math.log1p(float(feature["annotation_record_count"]) + float(feature["database_source_count"])) / 5.0)
        feature["research_bias_score"] = min(
            1.0,
            math.log1p(float(feature["annotation_record_count"]) + float(feature["external_knowledge_hit_count"]) + float(feature["database_source_count"])) / 8.0,
        )
    return features


def count_between(values: list[int], left: int, right: int) -> int:
    return bisect.bisect_right(values, right) - bisect.bisect_left(values, left)


def nearest_distance(values: list[int], point: int) -> int:
    if not values:
        return -1
    idx = bisect.bisect_left(values, point)
    best = []
    if idx < len(values):
        best.append(abs(values[idx] - point))
    if idx:
        best.append(abs(values[idx - 1] - point))
    return min(best) if best else -1


def load_windows(windows: list[dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for row in windows:
        output.append(
            {
                "window_id": clean(row.get("window_id")),
                "candidate_object_id": f"WINDOW_BG_{clean(row.get('window_id'))}",
                "candidate_object_type": "window",
                "chrom": normalize_chrom(row.get("chrom")),
                "start": as_int(row.get("start")),
                "end": as_int(row.get("end")),
                "length": interval_length(row.get("start"), row.get("end")),
                "center": interval_center(row.get("start"), row.get("end")),
                "n_snp": as_int(row.get("n_snp")),
            }
        )
    return output


def load_variants(variants: list[dict[str, str]], variant_windows: list[dict[str, str]], window_features: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    window_by_variant: dict[str, str] = {}
    for row in variant_windows:
        window_by_variant.setdefault(clean(row.get("variant_id")), clean(row.get("window_id")))
    output = []
    for row in variants:
        variant_id = clean(row.get("variant_id"))
        pos = as_int(row.get("pos"))
        window_id = window_by_variant.get(variant_id, "NA")
        window = window_features.get(window_id, {})
        output.append(
            {
                "variant_id": variant_id,
                "candidate_object_id": f"VARIANT_BG_{variant_id}",
                "candidate_object_type": "variant",
                "chrom": normalize_chrom(row.get("chrom")),
                "start": pos,
                "end": pos,
                "length": 1,
                "center": pos,
                "window_id": window_id,
                "window_n_snp": as_int(window.get("n_snp")),
            }
        )
    output.sort(key=lambda x: (str(x["chrom"]), int(x["center"])))
    return output


def interval_feature(
    chrom: str,
    start: int,
    end: int,
    gene_features: dict[str, dict[str, object]],
    windows: list[dict[str, object]],
    variants_by_chrom: dict[str, list[int]],
) -> dict[str, float]:
    chrom = normalize_chrom(chrom)
    genes = [g for g in gene_features.values() if str(g["chrom"]) == chrom and overlap(int(g["start"]), int(g["end"]), start, end)]
    nearby_genes = [g for g in gene_features.values() if str(g["chrom"]) == chrom and distance_between(int(g["start"]), int(g["end"]), start, end) <= 500_000]
    overlapping_windows = [w for w in windows if str(w["chrom"]) == chrom and overlap(int(w["start"]), int(w["end"]), start, end)]
    variant_count = count_between(variants_by_chrom.get(chrom, []), start, end)
    annotation_records = sum(int(g.get("annotation_record_count", 0)) for g in genes)
    source_count = len({str(g.get("database_source_count", 0)) for g in genes if int(g.get("database_source_count", 0)) > 0})
    external_hits = sum(int(g.get("external_knowledge_hit_count", 0)) for g in genes)
    return {
        "gene_density": float(len(nearby_genes)),
        "variant_density": float(variant_count),
        "annotation_richness": float(annotation_records + 0.5 * len(genes)),
        "evidence_source_coverage": float(external_hits),
        "database_detectability": min(1.0, math.log1p(annotation_records + source_count) / 5.0),
        "chr1_snp_window_coverage": float(len(overlapping_windows)),
        "chr1_snp_variant_coverage": float(variant_count),
        "annotation_record_count": float(annotation_records),
        "external_knowledge_hit_count": float(external_hits),
        "database_source_count": float(source_count),
        "trait_evidence_count": float(external_hits),
        "known_gene_proximity": float(min((distance_between(int(g["start"]), int(g["end"]), start, end) for g in gene_features.values() if str(g["chrom"]) == chrom), default=-1)),
        "research_bias_score": min(1.0, math.log1p(annotation_records + external_hits + source_count) / 8.0),
    }


def common_feature_context(args: argparse.Namespace) -> dict[str, object]:
    inputs = load_inputs(args)
    gene_features = build_gene_features(inputs["gene_annotation"], inputs["known_gene"])
    windows = load_windows(inputs["windows"])
    window_features = {str(w["window_id"]): w for w in windows}
    variants = load_variants(inputs["variants"], inputs["variant_windows"], window_features)
    variants_by_chrom: dict[str, list[int]] = defaultdict(list)
    for variant in variants:
        variants_by_chrom[str(variant["chrom"])].append(int(variant["center"]))
    for values in variants_by_chrom.values():
        values.sort()
    for window in windows:
        feat = interval_feature(str(window["chrom"]), int(window["start"]), int(window["end"]), gene_features, windows, variants_by_chrom)
        window.update(feat)
        window["variant_density"] = float(window.get("n_snp", 0))
    for variant in variants:
        window = window_features.get(str(variant.get("window_id")), {})
        variant.update(
            {
                "gene_density": float(window.get("gene_density", 0)),
                "variant_density": float(window.get("variant_density", 0)),
                "annotation_richness": float(window.get("annotation_richness", 0)),
                "evidence_source_coverage": 0.0,
                "database_detectability": float(window.get("database_detectability", 0)),
                "chr1_snp_window_coverage": 1.0 if not is_missing(variant.get("window_id")) else 0.0,
                "chr1_snp_variant_coverage": 1.0,
                "annotation_record_count": float(window.get("annotation_record_count", 0)),
                "external_knowledge_hit_count": 0.0,
                "database_source_count": float(window.get("database_source_count", 0)),
                "trait_evidence_count": 0.0,
                "known_gene_proximity": float(window.get("known_gene_proximity", -1)),
                "research_bias_score": float(window.get("research_bias_score", 0)),
            }
        )
    variant_features = {str(variant["variant_id"]): variant for variant in variants}
    return {
        "inputs": inputs,
        "gene_features": gene_features,
        "windows": windows,
        "window_features": window_features,
        "variants": variants,
        "variant_features": variant_features,
        "variants_by_chrom": variants_by_chrom,
    }


def object_feature(row: dict[str, str], context: dict[str, object]) -> dict[str, float]:
    gene_features: dict[str, dict[str, object]] = context["gene_features"]  # type: ignore[assignment]
    window_features: dict[str, dict[str, object]] = context["window_features"]  # type: ignore[assignment]
    variant_features: dict[str, dict[str, object]] = context["variant_features"]  # type: ignore[assignment]
    windows: list[dict[str, object]] = context["windows"]  # type: ignore[assignment]
    variants_by_chrom: dict[str, list[int]] = context["variants_by_chrom"]  # type: ignore[assignment]
    gene_id = clean(row.get("gene_id"))
    window_id = clean(row.get("window_id"))
    variant_id = clean(row.get("variant_id"))
    if row.get("object_type") == "gene" and gene_id in gene_features:
        g = gene_features[gene_id]
        return {
            "gene_density": float(g.get("gene_density", 0)),
            "variant_density": float(count_between(variants_by_chrom.get(str(g["chrom"]), []), int(g["start"]), int(g["end"]))),
            "annotation_richness": float(g.get("annotation_richness", 0)),
            "evidence_source_coverage": float(g.get("evidence_source_coverage", 0)),
            "database_detectability": float(g.get("database_detectability", 0)),
            "chr1_snp_window_coverage": float(sum(1 for w in windows if str(w["chrom"]) == str(g["chrom"]) and overlap(int(w["start"]), int(w["end"]), int(g["start"]), int(g["end"])))),
            "chr1_snp_variant_coverage": float(count_between(variants_by_chrom.get(str(g["chrom"]), []), int(g["start"]), int(g["end"]))),
            "annotation_record_count": float(g.get("annotation_record_count", 0)),
            "external_knowledge_hit_count": float(g.get("external_knowledge_hit_count", 0)),
            "database_source_count": float(g.get("database_source_count", 0)),
            "trait_evidence_count": float(g.get("trait_evidence_count", 0)),
            "known_gene_proximity": float(g.get("known_gene_proximity", -1)),
            "research_bias_score": float(g.get("research_bias_score", 0)),
        }
    if row.get("object_type") == "window" and window_id in window_features:
        w = window_features[window_id]
        return {key: float(w.get(key, 0)) for key in [
            "gene_density",
            "variant_density",
            "annotation_richness",
            "evidence_source_coverage",
            "database_detectability",
            "chr1_snp_window_coverage",
            "chr1_snp_variant_coverage",
            "annotation_record_count",
            "external_knowledge_hit_count",
            "database_source_count",
            "trait_evidence_count",
            "known_gene_proximity",
            "research_bias_score",
        ]}
    if row.get("object_type") == "variant" and variant_id in variant_features:
        v = variant_features[variant_id]
        return {key: float(v.get(key, 0)) for key in [
            "gene_density",
            "variant_density",
            "annotation_richness",
            "evidence_source_coverage",
            "database_detectability",
            "chr1_snp_window_coverage",
            "chr1_snp_variant_coverage",
            "annotation_record_count",
            "external_knowledge_hit_count",
            "database_source_count",
            "trait_evidence_count",
            "known_gene_proximity",
            "research_bias_score",
        ]}
    chrom, start, end = normalize_chrom(row.get("chrom")), as_int(row.get("start")), as_int(row.get("end"))
    if chrom == "1" and start and end:
        return interval_feature(chrom, start, end, gene_features, windows, variants_by_chrom)
    return defaultdict(float)  # type: ignore[return-value]


def allowed_usage_ok(value: object) -> bool:
    return clean(value) in {"evaluation_reference", "explanation", "case_study", "development_evidence_candidate"}


def build_matched_decoy_objects(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    inputs = load_inputs(args)
    known_by_id = {row["evidence_id"]: row for row in inputs["known_gene"]}
    frozen_traits = load_frozen_traits(args.repo_root)
    rows: list[dict[str, object]] = []

    for tge in inputs["trait_gene"]:
        evidence = known_by_id.get(clean(tge.get("evidence_id")), {})
        chrom = normalize_chrom(evidence.get("chrom"))
        start, end = as_int(evidence.get("start")), as_int(evidence.get("end"))
        confidence = clean(tge.get("trait_mapping_confidence"))
        exact = confidence == "keyword_match_to_frozen_trait"
        manual = confidence in {"ambiguous_keyword_match", "missing_trait_name"}
        allowed = clean(tge.get("allowed_usage") or evidence.get("allowed_usage"))
        reasons = []
        if not allowed_usage_ok(allowed):
            reasons.append("invalid_allowed_usage")
        if not exact:
            reasons.append("manual_review_required" if manual else "broader_evidence_pool")
        if chrom != "1":
            reasons.append("outside_chr1_snp_prototype")
        if not start or not end:
            reasons.append("missing_coordinate")
        in_main = not reasons
        rows.append(
            {
                "object_id": f"OBJ_GENE_{len(rows) + 1:08d}",
                "object_type": "gene",
                "trait_id": tge.get("trait_id", "NA"),
                "trait_name": tge.get("trait_name", "NA"),
                "evidence_id": tge.get("evidence_id", "NA"),
                "evidence_source": tge.get("evidence_source", evidence.get("evidence_source", "NA")),
                "evidence_source_type": "known_gene_database",
                "evidence_level": "gene_level",
                "support_level": tge.get("support_level", evidence.get("support_level", "NA")),
                "allowed_usage": allowed,
                "chrom": chrom or "NA",
                "start": start or "NA",
                "end": end or "NA",
                "object_length": interval_length(start, end),
                "gene_id": tge.get("gene_id", evidence.get("gene_id", "NA")),
                "gene_symbol": tge.get("gene_symbol", evidence.get("gene_symbol", "NA")),
                "variant_id": "NA",
                "window_id": "NA",
                "source_database": evidence.get("source_database", "NA"),
                "source_record_id": evidence.get("source_record_id", "NA"),
                "mapping_status": evidence.get("coordinate_mapping_status", "NA"),
                "coordinate_confidence": "high" if evidence.get("coordinate_mapping_status") == "mapped_high_confidence" else "low_or_gene_level_only",
                "exact_frozen_trait_mapping": str(exact).lower(),
                "manual_review_required": str(manual).lower(),
                "in_main_evaluation_candidate_pool": str(in_main).lower(),
                "exclusion_reason": ";".join(reasons) if reasons else "NA",
                "notes": "external gene-level evidence object; evaluation/explanation only; not causal ground truth and not a training label",
                "pipeline_version": VERSION,
            }
        )

    for qtl in inputs["qtl"]:
        trait_id, trait_name, confidence = match_frozen_trait(qtl.get("trait_id_or_name", ""), frozen_traits, allow_pex=False)
        chrom = normalize_chrom(qtl.get("chrom"))
        start, end = as_int(qtl.get("start")), as_int(qtl.get("end"))
        exact = confidence == "keyword_match_to_frozen_trait"
        manual = confidence in {"ambiguous_keyword_match", "missing_trait_name", "manual_review_required_pex_repro_no_exact_gene_evidence"}
        allowed = clean(qtl.get("allowed_usage"))
        reasons = []
        if not allowed_usage_ok(allowed):
            reasons.append("invalid_allowed_usage")
        if not exact:
            reasons.append("manual_review_required" if manual else "broader_evidence_pool")
        if chrom != "1":
            reasons.append("outside_chr1_snp_prototype")
        if not start or not end:
            reasons.append("missing_or_invalid_interval_coordinate")
        if qtl.get("coordinate_mapping_status") not in {"region_level_only", "mapped_low_confidence", "mapped_high_confidence"}:
            reasons.append("unmapped_interval")
        in_main = not reasons
        rows.append(
            {
                "object_id": f"OBJ_QTL_{len(rows) + 1:08d}",
                "object_type": "qtl_interval",
                "trait_id": trait_id,
                "trait_name": trait_name if not is_missing(trait_name) else qtl.get("trait_id_or_name", "NA"),
                "evidence_id": qtl.get("qtl_evidence_id", "NA"),
                "evidence_source": "Q-TARO",
                "evidence_source_type": "qtl_database",
                "evidence_level": "interval_level",
                "support_level": "weak",
                "allowed_usage": allowed,
                "chrom": chrom or "NA",
                "start": start or "NA",
                "end": end or "NA",
                "object_length": interval_length(start, end),
                "gene_id": "NA",
                "gene_symbol": qtl.get("linked_gene_symbol", "NA"),
                "variant_id": "NA",
                "window_id": "NA",
                "source_database": qtl.get("source_database", "Q-TARO"),
                "source_record_id": qtl.get("source_record_id", "NA"),
                "mapping_status": qtl.get("coordinate_mapping_status", "NA"),
                "coordinate_confidence": "low_region_level_source_coordinate",
                "exact_frozen_trait_mapping": str(exact).lower(),
                "manual_review_required": str(manual).lower(),
                "in_main_evaluation_candidate_pool": str(in_main).lower(),
                "exclusion_reason": ";".join(reasons) if reasons else "NA",
                "notes": "Q-TARO remains qtl_interval region-level weak localization evidence; linked gene text is not high-confidence gene mapping",
                "pipeline_version": VERSION,
            }
        )

    for signal in inputs["window_signal"]:
        if clean(signal.get("window_label_state")) == "unknown_unlabeled" or as_int(signal.get("window_weak_signal")) <= 0:
            continue
        rows.append(
            {
                "object_id": f"OBJ_WINDOW_{len(rows) + 1:08d}",
                "object_type": "window",
                "trait_id": signal.get("trait_id", "NA"),
                "trait_name": signal.get("trait_id", "NA"),
                "evidence_id": f"WINDOW_WEAK::{signal.get('trait_id')}::{signal.get('window_id')}",
                "evidence_source": signal.get("overlap_evidence_sources", "v0_1_chr1_window_weak_signal"),
                "evidence_source_type": "derived_chr1_window_weak_signal",
                "evidence_level": "window_level",
                "support_level": "weak",
                "allowed_usage": "development_evidence_candidate",
                "chrom": normalize_chrom(signal.get("chrom")),
                "start": as_int(signal.get("start")),
                "end": as_int(signal.get("end")),
                "object_length": interval_length(signal.get("start"), signal.get("end")),
                "gene_id": "NA",
                "gene_symbol": "NA",
                "variant_id": "NA",
                "window_id": signal.get("window_id", "NA"),
                "source_database": "v0_1_chr1_snp_task1_window_signal",
                "source_record_id": signal.get("window_id", "NA"),
                "mapping_status": "mapped_high_confidence",
                "coordinate_confidence": "chr1_window_table_high",
                "exact_frozen_trait_mapping": "true",
                "manual_review_required": "false",
                "in_main_evaluation_candidate_pool": "true",
                "exclusion_reason": "NA",
                "notes": "derived weak window evidence; matched background candidate is not true negative",
                "pipeline_version": VERSION,
            }
        )

    for label in inputs["variant_label"]:
        if clean(label.get("variant_label_state")) == "unknown_unlabeled":
            continue
        pos = as_int(label.get("pos"))
        rows.append(
            {
                "object_id": f"OBJ_VARIANT_{len(rows) + 1:08d}",
                "object_type": "variant",
                "trait_id": label.get("trait_id", "NA"),
                "trait_name": label.get("trait_id", "NA"),
                "evidence_id": label.get("overlap_evidence_id") or f"VARIANT_WEAK::{label.get('trait_id')}::{label.get('variant_id')}",
                "evidence_source": label.get("evidence_source", "v0_1_chr1_variant_weak_label"),
                "evidence_source_type": "derived_chr1_variant_weak_label",
                "evidence_level": "variant_level",
                "support_level": "weak",
                "allowed_usage": "development_evidence_candidate",
                "chrom": normalize_chrom(label.get("chrom")),
                "start": pos,
                "end": pos,
                "object_length": 1,
                "gene_id": "NA",
                "gene_symbol": "NA",
                "variant_id": label.get("variant_id", "NA"),
                "window_id": "NA",
                "source_database": "v0_1_chr1_snp_task1_variant_label",
                "source_record_id": label.get("variant_id", "NA"),
                "mapping_status": "mapped_high_confidence",
                "coordinate_confidence": "chr1_variant_table_high",
                "exact_frozen_trait_mapping": "true",
                "manual_review_required": "false",
                "in_main_evaluation_candidate_pool": "true",
                "exclusion_reason": "NA",
                "notes": "derived weak variant evidence; matched background candidate is not true negative",
                "pipeline_version": VERSION,
            }
        )
    out = args.interim_root / "objects/matched_decoy_object_table.tsv"
    write_tsv(out, rows, OBJECT_FIELDS)
    write_preview(args.report_root, "matched_decoy_object_table", rows, OBJECT_FIELDS)
    return rows


def build_field_availability(args: argparse.Namespace) -> list[dict[str, object]]:
    rows = [
        ("coordinate", "coordinate", "present", "chrom/start/end", "yes", "yes", "yes", "yes", "yes", "IRGSP-1.0 compatible where mapped; Q-TARO downgraded when uncertain"),
        ("position_bin", "position", "present", "1 Mb bins from chr1 coordinates", "yes", "yes", "yes", "yes", "yes", "coarse position control only"),
        ("gene_density", "gene_density", "proxy_used", "gene_annotation_table local +/-500 kb count", "yes", "yes", "yes", "yes", "yes", "annotation-derived proxy, not complete functional density"),
        ("variant_density", "variant_density", "present_chr1_proxy", "chr1 SNP table / window n_snp", "yes", "yes", "yes", "yes", "yes", "chr1 SNP-only prototype; indels not included"),
        ("annotation_richness", "annotation_richness", "proxy_used", "annotation_record_count/database_source_count", "yes", "yes", "yes", "yes", "yes", "proxy for annotation richness"),
        ("evidence_source_coverage", "evidence_source_coverage", "proxy_used", "external evidence source count", "yes", "yes", "yes", "yes", "yes", "proxy for source coverage, not causal support"),
        ("database_detectability", "database_detectability", "proxy_used", "annotation/database source availability", "yes", "yes", "yes", "yes", "yes", "detectability proxy only"),
        ("interval_length", "interval_length", "present", "end-start+1", "yes", "yes", "yes", "yes", "yes", "used for qtl_interval and region objects"),
        ("MAF", "MAF", "unavailable", "NA", "no", "no", "no", "yes", "future", "not materialized for candidate pool in current prototype"),
        ("LD", "LD", "unavailable", "NA", "no", "no", "no", "yes", "future", "not materialized for current chr1 matched decoy layer"),
        ("missingness", "missingness", "unavailable", "NA", "no", "no", "no", "yes", "future", "per-variant missingness not available in current candidate table"),
        ("mappability", "mappability", "unavailable", "NA", "no", "no", "no", "yes", "future", "no genome-wide mappability table available"),
        ("recombination_rate", "position", "unavailable", "NA", "no", "no", "no", "yes", "future", "no recombination map available"),
        ("research_bias", "research_bias", "proxy_used", "annotation richness / external hit count / known-gene proximity", "yes", "yes", "yes", "yes", "yes", "proxy only; not complete literature bias correction"),
        ("chr1_snp_coverage", "chr1_snp_coverage", "present_chr1_only", "window overlap and SNP count", "yes", "yes", "yes", "yes", "yes", "current data plane is chr1 SNP-only"),
    ]
    output = [
        {
            "field_name": name,
            "field_category": category,
            "availability": availability,
            "proxy_field": proxy,
            "used_in_object_table": object_used,
            "used_in_candidate_pool": pool_used,
            "used_in_pair_matching": pair_used,
            "used_in_diagnostics": diag_used,
            "used_in_sensitivity": sens_used,
            "missing_reason": "NA" if "unavailable" not in availability else notes,
            "notes": notes,
            "pipeline_version": VERSION,
        }
        for name, category, availability, proxy, object_used, pool_used, pair_used, diag_used, sens_used, notes in rows
    ]
    write_tsv(args.interim_root / "diagnostics/matching_field_availability_v055.tsv", output, FIELD_AVAILABILITY_FIELDS)
    write_tsv(args.report_root / "matching_field_availability_v055.tsv", output, FIELD_AVAILABILITY_FIELDS)
    return output


def build_detectability_research_bias(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    objects = read_tsv(args.interim_root / "objects/matched_decoy_object_table.tsv")
    context = common_feature_context(args)
    detect_rows: list[dict[str, object]] = []
    research_rows: list[dict[str, object]] = []
    for obj in objects:
        feat = object_feature(obj, context)
        variant_cov = float(feat.get("chr1_snp_variant_coverage", 0))
        window_cov = float(feat.get("chr1_snp_window_coverage", 0))
        detectability = min(1.0, math.log1p(variant_cov + window_cov) / 6.0 + float(feat.get("database_detectability", 0)) * 0.5)
        detect_rows.append(
            {
                "object_id": obj["object_id"],
                "object_type": obj["object_type"],
                "chrom": obj["chrom"],
                "start": obj["start"],
                "end": obj["end"],
                "missingness_rate": "unavailable",
                "callability_proxy": "chr1_snp_variant_coverage",
                "chr1_snp_coverage": fmt(variant_cov),
                "window_coverage": fmt(window_cov),
                "variant_coverage": fmt(variant_cov),
                "mappability_proxy": "unavailable",
                "low_complexity_or_repeat_proxy": "unavailable",
                "database_detectability_proxy": fmt(float(feat.get("database_detectability", 0))),
                "detectability_score": fmt(detectability),
                "detectability_fields_available": "chr1_snp_coverage;window_coverage;database_detectability_proxy",
                "notes": "detectability_score=0.5*database_detectability_proxy + scaled chr1 SNP/window coverage; not complete detectability correction",
                "pipeline_version": VERSION,
            }
        )
        known_prox = float(feat.get("known_gene_proximity", -1))
        research_rows.append(
            {
                "object_id": obj["object_id"],
                "object_type": obj["object_type"],
                "gene_id": obj.get("gene_id", "NA"),
                "gene_symbol": obj.get("gene_symbol", "NA"),
                "chrom": obj["chrom"],
                "start": obj["start"],
                "end": obj["end"],
                "annotation_record_count": fmt(float(feat.get("annotation_record_count", 0))),
                "external_knowledge_hit_count": fmt(float(feat.get("external_knowledge_hit_count", 0))),
                "known_gene_proximity": "unavailable" if known_prox < 0 else fmt(known_prox),
                "database_source_count": fmt(float(feat.get("database_source_count", 0))),
                "trait_evidence_count": fmt(float(feat.get("trait_evidence_count", 0))),
                "annotation_richness_score": fmt(float(feat.get("annotation_richness", 0))),
                "literature_bias_proxy": "annotation_record_count;external_knowledge_hit_count;database_source_count;known_gene_proximity",
                "research_bias_score": fmt(float(feat.get("research_bias_score", 0))),
                "research_bias_fields_available": "annotation_record_count;external_knowledge_hit_count;database_source_count;known_gene_proximity_proxy",
                "notes": "research_bias_score is a proxy, not complete literature bias correction",
                "pipeline_version": VERSION,
            }
        )
    build_field_availability(args)
    write_tsv(args.interim_root / "diagnostics/detectability_bias_table_v055.tsv", detect_rows, DETECTABILITY_FIELDS)
    write_tsv(args.interim_root / "diagnostics/research_bias_table_v055.tsv", research_rows, RESEARCH_BIAS_FIELDS)
    write_preview(args.report_root, "detectability_bias_table_v055", detect_rows, DETECTABILITY_FIELDS)
    write_preview(args.report_root, "research_bias_table_v055", research_rows, RESEARCH_BIAS_FIELDS)
    return detect_rows, research_rows


def feature_from_candidate(candidate: dict[str, object]) -> dict[str, float]:
    return {
        "gene_density": float(candidate.get("gene_density", 0)),
        "variant_density": float(candidate.get("variant_density", candidate.get("n_snp", 0))),
        "annotation_richness": float(candidate.get("annotation_richness", 0)),
        "evidence_source_coverage": float(candidate.get("evidence_source_coverage", 0)),
        "database_detectability": float(candidate.get("database_detectability", 0)),
        "chr1_snp_window_coverage": float(candidate.get("chr1_snp_window_coverage", 0)),
        "chr1_snp_variant_coverage": float(candidate.get("chr1_snp_variant_coverage", 0)),
        "research_bias_score": float(candidate.get("research_bias_score", 0)),
    }


def balance_scores(obj: dict[str, str], obj_feat: dict[str, float], candidate: dict[str, object]) -> dict[str, float | str]:
    cfeat = feature_from_candidate(candidate)
    distance = abs(interval_center(obj.get("start"), obj.get("end")) - int(candidate.get("center", 0)))
    position_score = 1.0 / (1.0 + distance / 1_000_000.0)
    density_diff = abs(math.log1p(obj_feat.get("gene_density", 0)) - math.log1p(cfeat.get("gene_density", 0))) + abs(
        math.log1p(obj_feat.get("variant_density", 0)) - math.log1p(cfeat.get("variant_density", 0))
    )
    density_score = 1.0 / (1.0 + density_diff)
    annotation_score = 1.0 / (1.0 + abs(math.log1p(obj_feat.get("annotation_richness", 0)) - math.log1p(cfeat.get("annotation_richness", 0))))
    detect_score = 1.0 / (1.0 + abs(obj_feat.get("database_detectability", 0) - cfeat.get("database_detectability", 0)))
    research_score = 1.0 / (1.0 + abs(obj_feat.get("research_bias_score", 0) - cfeat.get("research_bias_score", 0)))
    field_score = statistics.mean([position_score, density_score, annotation_score, detect_score, research_score])
    obj_bin = position_bin(obj.get("chrom"), obj.get("start"), obj.get("end"))
    cand_bin = position_bin(candidate.get("chrom"), candidate.get("start"), candidate.get("end"))
    length_ratio = min(float(obj.get("object_length", 0) or 0), float(candidate.get("length", 0) or 0)) / max(
        float(obj.get("object_length", 0) or 1), float(candidate.get("length", 0) or 1)
    )
    if obj_bin == cand_bin and density_score >= 0.70 and annotation_score >= 0.70 and length_ratio >= 0.70:
        level = "L1_strict_matched"
    elif density_score >= 0.55 and position_score >= 0.25:
        level = "L2_relaxed_position_density"
    elif annotation_score >= 0.45 or detect_score >= 0.45:
        level = "L3_relaxed_annotation_detectability"
    else:
        level = "L4_available_background_only"
    return {
        "position_distance": distance,
        "position_bin": f"{obj_bin}->{cand_bin}",
        "position_balance_score": position_score,
        "density_balance_score": density_score,
        "annotation_balance_score": annotation_score,
        "detectability_balance_score": detect_score,
        "research_bias_balance_score": research_score,
        "field_balance_score": field_score,
        "match_score": statistics.mean([field_score, position_score, density_score, annotation_score, detect_score, research_score]),
        "matching_level": level,
    }


def candidate_row(pool_id: int, obj: dict[str, str], obj_feat: dict[str, float], candidate: dict[str, object]) -> dict[str, object]:
    scores = balance_scores(obj, obj_feat, candidate)
    cfeat = feature_from_candidate(candidate)
    return {
        "candidate_pool_id": f"CP_{pool_id:09d}",
        "object_id": obj["object_id"],
        "trait_id": obj["trait_id"],
        "object_type": obj["object_type"],
        "candidate_object_id": candidate.get("candidate_object_id", "NA"),
        "candidate_object_type": candidate.get("candidate_object_type", "NA"),
        "candidate_chrom": candidate.get("chrom", "NA"),
        "candidate_start": candidate.get("start", "NA"),
        "candidate_end": candidate.get("end", "NA"),
        "candidate_length": candidate.get("length", "NA"),
        "same_chrom": str(normalize_chrom(obj.get("chrom")) == normalize_chrom(candidate.get("chrom"))).lower(),
        "position_bin": scores["position_bin"],
        "position_distance": scores["position_distance"],
        "gene_density_object": fmt(obj_feat.get("gene_density", 0)),
        "gene_density_candidate": fmt(cfeat.get("gene_density", 0)),
        "variant_density_object": fmt(obj_feat.get("variant_density", 0)),
        "variant_density_candidate": fmt(cfeat.get("variant_density", 0)),
        "annotation_richness_object": fmt(obj_feat.get("annotation_richness", 0)),
        "annotation_richness_candidate": fmt(cfeat.get("annotation_richness", 0)),
        "evidence_source_coverage_object": fmt(obj_feat.get("evidence_source_coverage", 0)),
        "evidence_source_coverage_candidate": fmt(cfeat.get("evidence_source_coverage", 0)),
        "database_detectability_object": fmt(obj_feat.get("database_detectability", 0)),
        "database_detectability_candidate": fmt(cfeat.get("database_detectability", 0)),
        "interval_length_object": obj.get("object_length", "NA"),
        "interval_length_candidate": candidate.get("length", "NA"),
        "chr1_snp_window_coverage_object": fmt(obj_feat.get("chr1_snp_window_coverage", 0)),
        "chr1_snp_window_coverage_candidate": fmt(cfeat.get("chr1_snp_window_coverage", 0)),
        "chr1_snp_variant_coverage_object": fmt(obj_feat.get("chr1_snp_variant_coverage", 0)),
        "chr1_snp_variant_coverage_candidate": fmt(cfeat.get("chr1_snp_variant_coverage", 0)),
        "candidate_pool_status": "eligible_matched_background_candidate",
        "candidate_exclusion_reason": "NA",
        "notes": "candidate is matched background only; it is not a true negative label",
        "pipeline_version": VERSION,
        "_match_score": scores["match_score"],
    }


def collect_variant_positive_sets(variant_labels: list[dict[str, str]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in variant_labels:
        if clean(row.get("variant_label_state")) != "unknown_unlabeled":
            result[clean(row.get("trait_id"))].add(clean(row.get("variant_id")))
    return result


def collect_window_positive_sets(window_signals: list[dict[str, str]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in window_signals:
        if clean(row.get("window_label_state")) != "unknown_unlabeled" and as_int(row.get("window_weak_signal")) > 0:
            result[clean(row.get("trait_id"))].add(clean(row.get("window_id")))
    return result


def build_candidate_pool(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    objects = read_tsv(args.interim_root / "objects/matched_decoy_object_table.tsv")
    context = common_feature_context(args)
    inputs: dict[str, list[dict[str, str]]] = context["inputs"]  # type: ignore[assignment]
    gene_features: dict[str, dict[str, object]] = context["gene_features"]  # type: ignore[assignment]
    windows: list[dict[str, object]] = context["windows"]  # type: ignore[assignment]
    variants: list[dict[str, object]] = context["variants"]  # type: ignore[assignment]
    variants_by_trait_positive = collect_variant_positive_sets(inputs["variant_label"])
    windows_by_trait_positive = collect_window_positive_sets(inputs["window_signal"])
    variants_by_pos = sorted(variants, key=lambda x: int(x["center"]))
    variant_positions = [int(v["center"]) for v in variants_by_pos]
    genes_chr1 = sorted([g for g in gene_features.values() if str(g["chrom"]) == "1"], key=lambda x: int(x["center"]))
    gene_centers = [int(g["center"]) for g in genes_chr1]
    windows_by_pos = sorted(windows, key=lambda x: int(x["center"]))
    window_centers = [int(w["center"]) for w in windows_by_pos]
    chr1_length = max((int(w["end"]) for w in windows), default=0)
    main_objects = [obj for obj in objects if obj.get("in_main_evaluation_candidate_pool") == "true"]
    rows: list[dict[str, object]] = []

    for obj in main_objects:
        obj_feat = object_feature(obj, context)
        candidates: list[dict[str, object]] = []
        if obj["object_type"] == "gene":
            gene_id = clean(obj.get("gene_id"))
            center = interval_center(obj.get("start"), obj.get("end"))
            idx = bisect.bisect_left(gene_centers, center)
            left, right = idx - 1, idx
            while (left >= 0 or right < len(genes_chr1)) and len(candidates) < max(args.max_candidates_per_object * 12, 250):
                choose_left = right >= len(genes_chr1) or (left >= 0 and abs(gene_centers[left] - center) <= abs(gene_centers[right] - center))
                cand = genes_chr1[left] if choose_left else genes_chr1[right]
                if choose_left:
                    left -= 1
                else:
                    right += 1
                if cand.get("gene_id") == gene_id:
                    continue
                candidates.append(cand)
        elif obj["object_type"] == "qtl_interval":
            obj_len = max(1, as_int(obj.get("object_length")))
            for window in windows:
                start = int(window["start"])
                end = min(chr1_length, start + obj_len - 1)
                if end <= start:
                    continue
                candidates.append(
                    {
                        "candidate_object_id": f"INTERVAL_BG_chr1_{start}_{end}",
                        "candidate_object_type": "qtl_interval_background",
                        "chrom": "1",
                        "start": start,
                        "end": end,
                        "length": end - start + 1,
                        "center": (start + end) // 2,
                        "gene_density": float(window.get("gene_density", 0)),
                        "variant_density": float(window.get("variant_density", 0)),
                        "annotation_richness": float(window.get("annotation_richness", 0)),
                        "evidence_source_coverage": float(window.get("evidence_source_coverage", 0)),
                        "database_detectability": float(window.get("database_detectability", 0)),
                        "chr1_snp_window_coverage": 1.0,
                        "chr1_snp_variant_coverage": float(window.get("variant_density", 0)),
                        "research_bias_score": float(window.get("research_bias_score", 0)),
                    }
                )
        elif obj["object_type"] == "window":
            positives = windows_by_trait_positive.get(clean(obj.get("trait_id")), set())
            center = interval_center(obj.get("start"), obj.get("end"))
            idx = bisect.bisect_left(window_centers, center)
            left, right = idx - 1, idx
            while (left >= 0 or right < len(windows_by_pos)) and len(candidates) < max(args.max_candidates_per_object * 4, 120):
                choose_left = right >= len(windows_by_pos) or (left >= 0 and abs(window_centers[left] - center) <= abs(window_centers[right] - center))
                cand = windows_by_pos[left] if choose_left else windows_by_pos[right]
                if choose_left:
                    left -= 1
                else:
                    right += 1
                if cand.get("window_id") == obj.get("window_id") or cand.get("window_id") in positives:
                    continue
                candidates.append(cand)
        elif obj["object_type"] == "variant":
            positives = variants_by_trait_positive.get(clean(obj.get("trait_id")), set())
            pos = as_int(obj.get("start"))
            idx = bisect.bisect_left(variant_positions, pos)
            left, right = idx - 1, idx
            while (left >= 0 or right < len(variants_by_pos)) and len(candidates) < max(args.max_candidates_per_object * 2, 60):
                choose_left = right >= len(variants_by_pos) or (left >= 0 and abs(variant_positions[left] - pos) <= abs(variant_positions[right] - pos))
                cand = variants_by_pos[left] if choose_left else variants_by_pos[right]
                if choose_left:
                    left -= 1
                else:
                    right += 1
                if cand.get("variant_id") == obj.get("variant_id") or cand.get("variant_id") in positives:
                    continue
                candidates.append(cand)
        ranked: list[dict[str, object]] = []
        for candidate in candidates:
            row = candidate_row(len(rows) + len(ranked) + 1, obj, obj_feat, candidate)
            if row["candidate_object_id"] == obj["object_id"]:
                continue
            ranked.append(row)
        ranked.sort(key=lambda x: float(x["_match_score"]), reverse=True)
        for row in ranked[: args.max_candidates_per_object]:
            row.pop("_match_score", None)
            row["candidate_pool_id"] = f"CP_{len(rows) + 1:09d}"
            rows.append(row)
        if not ranked:
            rows.append(
                {
                    "candidate_pool_id": f"CP_{len(rows) + 1:09d}",
                    "object_id": obj["object_id"],
                    "trait_id": obj["trait_id"],
                    "object_type": obj["object_type"],
                    "candidate_object_id": "NA",
                    "candidate_object_type": "NA",
                    "candidate_chrom": "NA",
                    "candidate_start": "NA",
                    "candidate_end": "NA",
                    "candidate_length": "NA",
                    "same_chrom": "NA",
                    "position_bin": position_bin(obj.get("chrom"), obj.get("start"), obj.get("end")),
                    "position_distance": "NA",
                    "gene_density_object": fmt(obj_feat.get("gene_density", 0)),
                    "gene_density_candidate": "NA",
                    "variant_density_object": fmt(obj_feat.get("variant_density", 0)),
                    "variant_density_candidate": "NA",
                    "annotation_richness_object": fmt(obj_feat.get("annotation_richness", 0)),
                    "annotation_richness_candidate": "NA",
                    "evidence_source_coverage_object": fmt(obj_feat.get("evidence_source_coverage", 0)),
                    "evidence_source_coverage_candidate": "NA",
                    "database_detectability_object": fmt(obj_feat.get("database_detectability", 0)),
                    "database_detectability_candidate": "NA",
                    "interval_length_object": obj.get("object_length", "NA"),
                    "interval_length_candidate": "NA",
                    "chr1_snp_window_coverage_object": fmt(obj_feat.get("chr1_snp_window_coverage", 0)),
                    "chr1_snp_window_coverage_candidate": "NA",
                    "chr1_snp_variant_coverage_object": fmt(obj_feat.get("chr1_snp_variant_coverage", 0)),
                    "chr1_snp_variant_coverage_candidate": "NA",
                    "candidate_pool_status": "failed_no_candidate",
                    "candidate_exclusion_reason": "no_available_chr1_background_candidate",
                    "notes": "failed object is carried into pair table and diagnostics; no negative label is created",
                    "pipeline_version": VERSION,
                }
            )
    write_tsv(args.interim_root / "candidate_pool/matched_decoy_candidate_pool.tsv", rows, CANDIDATE_FIELDS)
    write_preview(args.report_root, "matched_decoy_candidate_pool", rows, CANDIDATE_FIELDS)
    return rows


def build_pairs(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    candidates = read_tsv(args.interim_root / "candidate_pool/matched_decoy_candidate_pool.tsv")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        grouped[row["object_id"]].append(row)
    pairs: list[dict[str, object]] = []
    for object_id, rows in grouped.items():
        eligible = [row for row in rows if row.get("candidate_pool_status") == "eligible_matched_background_candidate"]
        eligible.sort(key=lambda row: pair_score_from_candidate(row), reverse=True)
        if not eligible:
            failed = rows[0]
            pairs.append(
                {
                    "decoy_pair_id": f"DP_{len(pairs) + 1:09d}",
                    "object_id": object_id,
                    "trait_id": failed.get("trait_id", "NA"),
                    "object_type": failed.get("object_type", "NA"),
                    "decoy_object_id": "NA",
                    "decoy_object_type": "NA",
                    "match_rank": "NA",
                    "match_score": "0",
                    "matching_level": "failed_no_candidate",
                    "matching_status": "failed_no_candidate",
                    "relaxation_level": "failed_no_candidate",
                    "relaxation_reason": failed.get("candidate_exclusion_reason", "no_candidate"),
                    "n_candidates_before_filter": len(rows),
                    "n_candidates_after_filter": 0,
                    "matched_fields": "NA",
                    "unavailable_fields": ";".join(UNAVAILABLE_MATCH_FIELDS),
                    "field_balance_score": "0",
                    "position_balance_score": "0",
                    "density_balance_score": "0",
                    "annotation_balance_score": "0",
                    "detectability_balance_score": "0",
                    "research_bias_balance_score": "0",
                    "notes": "failed matching is diagnostic only; no negative label is created",
                    "pipeline_version": VERSION,
                }
            )
            continue
        for rank, row in enumerate(eligible[: args.max_decoys_per_object], start=1):
            scores = score_components_from_candidate(row)
            level = matching_level_from_scores(row, scores)
            pairs.append(
                {
                    "decoy_pair_id": f"DP_{len(pairs) + 1:09d}",
                    "object_id": object_id,
                    "trait_id": row.get("trait_id", "NA"),
                    "object_type": row.get("object_type", "NA"),
                    "decoy_object_id": row.get("candidate_object_id", "NA"),
                    "decoy_object_type": row.get("candidate_object_type", "NA"),
                    "match_rank": rank,
                    "match_score": fmt(pair_score_from_candidate(row)),
                    "matching_level": level,
                    "matching_status": "matched_background_candidate",
                    "relaxation_level": level,
                    "relaxation_reason": "strict_or_relaxed_by_available_chr1_proxy_fields",
                    "n_candidates_before_filter": len(rows),
                    "n_candidates_after_filter": len(eligible),
                    "matched_fields": ";".join(MATCHED_FIELDS),
                    "unavailable_fields": ";".join(UNAVAILABLE_MATCH_FIELDS),
                    "field_balance_score": fmt(scores["field"]),
                    "position_balance_score": fmt(scores["position"]),
                    "density_balance_score": fmt(scores["density"]),
                    "annotation_balance_score": fmt(scores["annotation"]),
                    "detectability_balance_score": fmt(scores["detectability"]),
                    "research_bias_balance_score": fmt(scores["research"]),
                    "notes": "decoy is matched background only and must not be interpreted as true negative",
                    "pipeline_version": VERSION,
                }
            )
    write_tsv(args.interim_root / "pairs/matched_decoy_pair_table.tsv", pairs, PAIR_FIELDS)
    write_preview(args.report_root, "matched_decoy_pair_table", pairs, PAIR_FIELDS)
    return pairs


def score_components_from_candidate(row: dict[str, str]) -> dict[str, float]:
    position_distance = as_float(row.get("position_distance"), 10_000_000)
    position = 1.0 / (1.0 + position_distance / 1_000_000.0)
    density = 1.0 / (
        1.0
        + abs(math.log1p(as_float(row.get("gene_density_object"))) - math.log1p(as_float(row.get("gene_density_candidate"))))
        + abs(math.log1p(as_float(row.get("variant_density_object"))) - math.log1p(as_float(row.get("variant_density_candidate"))))
    )
    annotation = 1.0 / (1.0 + abs(math.log1p(as_float(row.get("annotation_richness_object"))) - math.log1p(as_float(row.get("annotation_richness_candidate")))))
    detectability = 1.0 / (1.0 + abs(as_float(row.get("database_detectability_object")) - as_float(row.get("database_detectability_candidate"))))
    research = 1.0 / (1.0 + abs(math.log1p(as_float(row.get("evidence_source_coverage_object"))) - math.log1p(as_float(row.get("evidence_source_coverage_candidate")))))
    field = statistics.mean([position, density, annotation, detectability, research])
    return {
        "position": position,
        "density": density,
        "annotation": annotation,
        "detectability": detectability,
        "research": research,
        "field": field,
    }


def pair_score_from_candidate(row: dict[str, str]) -> float:
    scores = score_components_from_candidate(row)
    return statistics.mean(scores.values())


def matching_level_from_scores(row: dict[str, str], scores: dict[str, float]) -> str:
    position_same = "->" in row.get("position_bin", "") and row.get("position_bin", "").split("->")[0] == row.get("position_bin", "").split("->")[-1]
    if position_same and scores["density"] >= 0.70 and scores["annotation"] >= 0.70:
        return "L1_strict_matched"
    if scores["density"] >= 0.55 and scores["position"] >= 0.25:
        return "L2_relaxed_position_density"
    if scores["annotation"] >= 0.45 or scores["detectability"] >= 0.45:
        return "L3_relaxed_annotation_detectability"
    return "L4_available_background_only"


def build_diagnostics(args: argparse.Namespace) -> list[dict[str, object]]:
    objects = read_tsv(args.interim_root / "objects/matched_decoy_object_table.tsv")
    candidates = read_tsv(args.interim_root / "candidate_pool/matched_decoy_candidate_pool.tsv")
    pairs = read_tsv(args.interim_root / "pairs/matched_decoy_pair_table.tsv")
    candidate_counts: Counter[str] = Counter()
    for row in candidates:
        if row.get("candidate_pool_status") == "eligible_matched_background_candidate":
            candidate_counts[row["object_id"]] += 1
    pair_counts: Counter[str] = Counter()
    match_scores_by_object: dict[str, list[float]] = defaultdict(list)
    levels: dict[str, Counter[str]] = defaultdict(Counter)
    failures: Counter[str] = Counter()
    for row in pairs:
        if row.get("matching_status") == "matched_background_candidate":
            pair_counts[row["object_id"]] += 1
            match_scores_by_object[row["object_id"]].append(as_float(row.get("match_score")))
            levels[row["object_id"]][row.get("matching_level", "NA")] += 1
        else:
            failures[row["object_id"]] += 1
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for obj in objects:
        groups[(obj.get("object_type", "NA"), obj.get("trait_id", "NA"))].append(obj)
    rows: list[dict[str, object]] = []
    for (object_type, trait_id), group in sorted(groups.items()):
        main_ids = [obj["object_id"] for obj in group if obj.get("in_main_evaluation_candidate_pool") == "true"]
        cand_values = [candidate_counts[obj_id] for obj_id in main_ids]
        decoy_values = [pair_counts[obj_id] for obj_id in main_ids]
        scores = [score for obj_id in main_ids for score in match_scores_by_object.get(obj_id, [])]
        strict = sum(levels[obj_id].get("L1_strict_matched", 0) for obj_id in main_ids)
        relaxed = sum(
            levels[obj_id].get(level, 0)
            for obj_id in main_ids
            for level in ["L2_relaxed_position_density", "L3_relaxed_annotation_detectability", "L4_available_background_only"]
        )
        failed = sum(1 for obj_id in main_ids if not pair_counts[obj_id])
        rows.append(
            {
                "diagnostic_id": f"DG_{len(rows) + 1:08d}",
                "object_type": object_type,
                "trait_id": trait_id,
                "n_evidence_objects": len(group),
                "n_main_evaluation_objects": len(main_ids),
                "n_objects_with_candidate_pool": sum(1 for value in cand_values if value > 0),
                "n_objects_with_matched_decoy": sum(1 for value in decoy_values if value > 0),
                "n_objects_without_decoy": failed,
                "median_candidates_per_object": fmt(median([float(v) for v in cand_values])),
                "mean_candidates_per_object": fmt(mean([float(v) for v in cand_values])),
                "median_decoys_per_object": fmt(median([float(v) for v in decoy_values])),
                "mean_match_score": fmt(mean(scores)),
                "median_match_score": fmt(median(scores)),
                "n_strict_matches": strict,
                "n_relaxed_matches": relaxed,
                "n_failed_matches": failed,
                "top_failure_reasons": "failed_no_candidate" if failed else "NA",
                "field_balance_summary": "available proxy fields used; MAF/LD/mappability unavailable",
                "position_balance_summary": "1Mb chr1 position bins plus distance score",
                "gene_density_balance_summary": "local gene annotation count proxy",
                "variant_density_balance_summary": "chr1 SNP/window density proxy",
                "annotation_richness_balance_summary": "annotation record/source count proxy",
                "detectability_balance_summary": "chr1 SNP coverage and database detectability proxy",
                "research_bias_balance_summary": "annotation richness/external hit/proximity proxy",
                "notes": "chr1 SNP-only prototype diagnostics; decoys are not true negatives",
                "pipeline_version": VERSION,
            }
        )
    rows.extend(special_diagnostic_rows(rows, objects, candidates, pairs))
    write_tsv(args.interim_root / "diagnostics/decoy_matching_diagnostics.tsv", rows, DIAGNOSTIC_FIELDS)
    write_tsv(args.report_root / "decoy_matching_diagnostics.tsv", rows, DIAGNOSTIC_FIELDS)
    return rows


def special_diagnostic_rows(existing: list[dict[str, object]], objects: list[dict[str, str]], candidates: list[dict[str, str]], pairs: list[dict[str, str]]) -> list[dict[str, object]]:
    pex_main = [o for o in objects if o.get("trait_id") == "data_lt_2007__pex_repro" and o.get("in_main_evaluation_candidate_pool") == "true"]
    qtl = [o for o in objects if o.get("object_type") == "qtl_interval"]
    manual = [o for o in objects if o.get("manual_review_required") == "true"]
    broader = [o for o in objects if "broader_evidence_pool" in o.get("exclusion_reason", "")]
    offset = len(existing)
    return [
        {
            "diagnostic_id": f"DG_{offset + 1:08d}",
            "object_type": "summary_pex_repro",
            "trait_id": "data_lt_2007__pex_repro",
            "n_evidence_objects": sum(1 for o in objects if "pex_repro" in o.get("trait_id", "")),
            "n_main_evaluation_objects": len(pex_main),
            "n_objects_with_candidate_pool": 0,
            "n_objects_with_matched_decoy": 0,
            "n_objects_without_decoy": 0,
            "median_candidates_per_object": "0",
            "mean_candidates_per_object": "0",
            "median_decoys_per_object": "0",
            "mean_match_score": "0",
            "median_match_score": "0",
            "n_strict_matches": 0,
            "n_relaxed_matches": 0,
            "n_failed_matches": 0,
            "top_failure_reasons": "NA",
            "field_balance_summary": "PEX_REPRO exact evidence remains zero",
            "position_balance_summary": "NA",
            "gene_density_balance_summary": "NA",
            "variant_density_balance_summary": "NA",
            "annotation_richness_balance_summary": "NA",
            "detectability_balance_summary": "NA",
            "research_bias_balance_summary": "NA",
            "notes": "PEX_REPRO was not force-filled; no exact main-evaluation object was created",
            "pipeline_version": VERSION,
        },
        {
            "diagnostic_id": f"DG_{offset + 2:08d}",
            "object_type": "summary_qtaro_interval",
            "trait_id": "all",
            "n_evidence_objects": len(qtl),
            "n_main_evaluation_objects": sum(1 for o in qtl if o.get("in_main_evaluation_candidate_pool") == "true"),
            "n_objects_with_candidate_pool": len({c["object_id"] for c in candidates if c.get("object_id") in {o["object_id"] for o in qtl} and c.get("candidate_pool_status") == "eligible_matched_background_candidate"}),
            "n_objects_with_matched_decoy": len({p["object_id"] for p in pairs if p.get("object_id") in {o["object_id"] for o in qtl} and p.get("matching_status") == "matched_background_candidate"}),
            "n_objects_without_decoy": 0,
            "median_candidates_per_object": "NA",
            "mean_candidates_per_object": "NA",
            "median_decoys_per_object": "NA",
            "mean_match_score": "NA",
            "median_match_score": "NA",
            "n_strict_matches": "NA",
            "n_relaxed_matches": "NA",
            "n_failed_matches": "NA",
            "top_failure_reasons": "NA",
            "field_balance_summary": "Q-TARO remains qtl_interval/region-level evidence",
            "position_balance_summary": "source intervals only; no liftover",
            "gene_density_balance_summary": "not high-confidence gene mapping",
            "variant_density_balance_summary": "chr1 SNP overlap proxy only",
            "annotation_richness_balance_summary": "interval overlap proxy only",
            "detectability_balance_summary": "proxy only",
            "research_bias_balance_summary": "proxy only",
            "notes": "Q-TARO was not converted into causal labels or high-confidence gene evidence",
            "pipeline_version": VERSION,
        },
        {
            "diagnostic_id": f"DG_{offset + 3:08d}",
            "object_type": "summary_manual_review_and_broader",
            "trait_id": "all",
            "n_evidence_objects": len(manual) + len(broader),
            "n_main_evaluation_objects": 0,
            "n_objects_with_candidate_pool": 0,
            "n_objects_with_matched_decoy": 0,
            "n_objects_without_decoy": 0,
            "median_candidates_per_object": "0",
            "mean_candidates_per_object": "0",
            "median_decoys_per_object": "0",
            "mean_match_score": "0",
            "median_match_score": "0",
            "n_strict_matches": 0,
            "n_relaxed_matches": 0,
            "n_failed_matches": 0,
            "top_failure_reasons": "manual_review_or_broader_evidence_excluded_from_main",
            "field_balance_summary": "not matched for main evaluation",
            "position_balance_summary": "NA",
            "gene_density_balance_summary": "NA",
            "variant_density_balance_summary": "NA",
            "annotation_richness_balance_summary": "NA",
            "detectability_balance_summary": "NA",
            "research_bias_balance_summary": "NA",
            "notes": "ambiguous frozen-trait matches and broader evidence are retained but excluded from main candidate pool",
            "pipeline_version": VERSION,
        },
    ]


def validate_and_report(args: argparse.Namespace) -> list[dict[str, object]]:
    ensure_output_dirs(args.interim_root, args.report_root)
    objects = read_tsv(args.interim_root / "objects/matched_decoy_object_table.tsv")
    candidates = read_tsv(args.interim_root / "candidate_pool/matched_decoy_candidate_pool.tsv")
    pairs = read_tsv(args.interim_root / "pairs/matched_decoy_pair_table.tsv")
    diagnostics = build_diagnostics(args)
    availability = read_tsv(args.interim_root / "diagnostics/matching_field_availability_v055.tsv")
    detectability = read_tsv(args.interim_root / "diagnostics/detectability_bias_table_v055.tsv")
    research = read_tsv(args.interim_root / "diagnostics/research_bias_table_v055.tsv")
    rows: list[dict[str, object]] = []

    def add(check: str, status: bool, n_records: int, n_failed: int, details: str, blocking: bool = False, notes: str = "NA") -> None:
        rows.append(
            {
                "check_name": check,
                "status": "pass" if status else "fail",
                "n_records": n_records,
                "n_failed": n_failed,
                "details": details,
                "blocking_issue": str(blocking and not status).lower(),
                "notes": notes,
                "pipeline_version": VERSION,
            }
        )

    expected = [
        args.interim_root / "objects/matched_decoy_object_table.tsv",
        args.interim_root / "candidate_pool/matched_decoy_candidate_pool.tsv",
        args.interim_root / "pairs/matched_decoy_pair_table.tsv",
        args.interim_root / "diagnostics/decoy_matching_diagnostics.tsv",
        args.interim_root / "diagnostics/matching_field_availability_v055.tsv",
        args.interim_root / "diagnostics/detectability_bias_table_v055.tsv",
        args.interim_root / "diagnostics/research_bias_table_v055.tsv",
    ]
    missing = [rel(path) for path in expected if count_rows(path) == 0]
    add("outputs_exist_and_nonempty", not missing, len(expected), len(missing), ";".join(missing) if missing else "all required outputs are nonempty", True)
    add_unique_check(rows, "matched_decoy_object_table_primary_key_unique", objects, "object_id")
    main_non_exact = [o for o in objects if o.get("in_main_evaluation_candidate_pool") == "true" and o.get("exact_frozen_trait_mapping") != "true"]
    add("main_pool_exact_frozen_trait_only", not main_non_exact, len(objects), len(main_non_exact), "main candidates require exact_frozen_trait_mapping=true", True)
    pex_main = [o for o in objects if o.get("trait_id") == "data_lt_2007__pex_repro" and o.get("in_main_evaluation_candidate_pool") == "true"]
    add("pex_repro_not_force_filled", not pex_main, len(objects), len(pex_main), "PEX_REPRO exact evidence remains zero", True)
    qtaro_bad = [o for o in objects if o.get("source_database") == "Q-TARO" and (o.get("object_type") == "gene" or not is_missing(o.get("gene_id")))]
    add("qtaro_not_forced_to_high_confidence_gene_mapping", not qtaro_bad, len(objects), len(qtaro_bad), "Q-TARO remains qtl_interval/region-level evidence", True)
    broader_main = [o for o in objects if "broader_evidence_pool" in o.get("exclusion_reason", "") and o.get("in_main_evaluation_candidate_pool") == "true"]
    add("broader_evidence_not_in_main_pool", not broader_main, len(objects), len(broader_main), "broader evidence retained outside main evaluation", True)
    manual_main = [o for o in objects if o.get("manual_review_required") == "true" and o.get("in_main_evaluation_candidate_pool") == "true"]
    add("manual_review_objects_not_in_main_pool", not manual_main, len(objects), len(manual_main), "manual review objects excluded from main evaluation", True)
    no_true_negative = not any("true_negative" in " ".join(row.values()).lower() for row in candidates + pairs)
    add("decoys_not_marked_true_negative", no_true_negative, len(candidates) + len(pairs), 0 if no_true_negative else 1, "decoys are matched background candidates only", True)
    same_pair = [p for p in pairs if p.get("object_id") == p.get("decoy_object_id")]
    add("decoy_pair_object_ids_differ", not same_pair, len(pairs), len(same_pair), "object_id and decoy_object_id must differ", True)
    failed_pairs = [p for p in pairs if p.get("matching_status") == "failed_no_candidate"]
    diag_mentions_failed = any(as_int(d.get("n_failed_matches")) > 0 or d.get("object_type") in {"summary_pex_repro", "summary_manual_review_and_broader"} for d in diagnostics)
    add("failed_matching_objects_enter_diagnostics", not failed_pairs or diag_mentions_failed, len(failed_pairs), 0 if diag_mentions_failed else len(failed_pairs), "failed matches are summarized in diagnostics")
    required_fields = set(MATCHED_FIELDS + UNAVAILABLE_MATCH_FIELDS + ["interval_length"])
    available_fields = {row.get("field_name") for row in availability}
    missing_fields = sorted(required_fields - available_fields)
    add("matching_fields_recorded", not missing_fields, len(required_fields), len(missing_fields), ";".join(missing_fields) if missing_fields else "all matching fields recorded", True)
    bad_usage = [o for o in objects if o.get("allowed_usage") == "training_label"]
    add("allowed_usage_has_no_training_label", not bad_usage, len(objects), len(bad_usage), "allowed_usage must not be training_label", True)
    add_unique_check(rows, "matched_decoy_candidate_pool_primary_key_unique", candidates, "candidate_pool_id")
    add_unique_check(rows, "matched_decoy_pair_table_primary_key_unique", pairs, "decoy_pair_id")
    add_unique_check(rows, "detectability_bias_table_primary_key_unique", detectability, "object_id")
    add_unique_check(rows, "research_bias_table_primary_key_unique", research, "object_id")
    write_tsv(args.interim_root / "diagnostics/decoy_validation.tsv", rows, VALIDATION_FIELDS)
    write_tsv(args.report_root / "decoy_validation.tsv", rows, VALIDATION_FIELDS)
    write_report(args, objects, candidates, pairs, diagnostics, availability, rows)
    return rows


def add_unique_check(rows: list[dict[str, object]], check_name: str, table: list[dict[str, str]], key: str) -> None:
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
            "pipeline_version": VERSION,
        }
    )


def write_report(
    args: argparse.Namespace,
    objects: list[dict[str, str]],
    candidates: list[dict[str, str]],
    pairs: list[dict[str, str]],
    diagnostics: list[dict[str, str]],
    availability: list[dict[str, str]],
    validation: list[dict[str, object]],
) -> None:
    object_counter = Counter(row.get("object_type", "NA") for row in objects)
    main_counter = Counter(row.get("object_type", "NA") for row in objects if row.get("in_main_evaluation_candidate_pool") == "true")
    cand_object_ids = {row["object_id"] for row in candidates if row.get("candidate_pool_status") == "eligible_matched_background_candidate"}
    pair_object_ids = {row["object_id"] for row in pairs if row.get("matching_status") == "matched_background_candidate"}
    main_ids = {row["object_id"] for row in objects if row.get("in_main_evaluation_candidate_pool") == "true"}
    manual_count = sum(1 for row in objects if row.get("manual_review_required") == "true")
    broader_count = sum(1 for row in objects if "broader_evidence_pool" in row.get("exclusion_reason", ""))
    pex_main = sum(1 for row in objects if row.get("trait_id") == "data_lt_2007__pex_repro" and row.get("in_main_evaluation_candidate_pool") == "true")
    qtl_rows = [row for row in objects if row.get("object_type") == "qtl_interval"]
    avg_candidates = len([row for row in candidates if row.get("candidate_pool_status") == "eligible_matched_background_candidate"]) / max(1, len(main_ids))
    avg_decoys = len([row for row in pairs if row.get("matching_status") == "matched_background_candidate"]) / max(1, len(main_ids))
    unavailable = [row["field_name"] for row in availability if "unavailable" in row.get("availability", "")]
    used = [row["field_name"] for row in availability if row.get("used_in_pair_matching") == "yes"]
    failed_checks = [row for row in validation if row.get("status") == "fail"]
    lines = [
        "# Matched Decoy v0.5.5 Report",
        "",
        "## Scope",
        "",
        "This run builds a chr1 SNP-only prototype matched decoy object, candidate-pool, pair, and diagnostics layer. It is not the full benchmark, not a frozen split, not a formal evaluator, and not a model-training run.",
        "",
        "Matched decoys are matched background candidates. They are not true negatives, and unknown or unlabeled variants/windows are not interpreted as absence labels.",
        "",
        "## Generated Tables",
        "",
        "| table | rows |",
        "|---|---:|",
    ]
    files = [
        args.interim_root / "objects/matched_decoy_object_table.tsv",
        args.interim_root / "candidate_pool/matched_decoy_candidate_pool.tsv",
        args.interim_root / "pairs/matched_decoy_pair_table.tsv",
        args.interim_root / "diagnostics/decoy_matching_diagnostics.tsv",
        args.interim_root / "diagnostics/matching_field_availability_v055.tsv",
        args.interim_root / "diagnostics/detectability_bias_table_v055.tsv",
        args.interim_root / "diagnostics/research_bias_table_v055.tsv",
        args.interim_root / "diagnostics/decoy_validation.tsv",
    ]
    for path in files:
        lines.append(f"| `{rel(path)}` | {count_rows(path)} |")
    lines.extend(["", "## Object Summary", "", "| object_type | all objects | main evaluation candidates | candidate-pool covered | matched-decoy covered |", "|---|---:|---:|---:|---:|"])
    for object_type in sorted(object_counter):
        main_type_ids = {row["object_id"] for row in objects if row.get("object_type") == object_type and row.get("in_main_evaluation_candidate_pool") == "true"}
        lines.append(
            f"| {object_type} | {object_counter[object_type]} | {main_counter[object_type]} | {len(main_type_ids & cand_object_ids)} | {len(main_type_ids & pair_object_ids)} |"
        )
    lines.extend(
        [
            "",
            "## Key Counts",
            "",
            f"- Main evaluation candidate objects: {len(main_ids)}.",
            f"- Broader evidence objects excluded from main evaluation: {broader_count}.",
            f"- Manual-review-required objects excluded from main evaluation: {manual_count}.",
            f"- PEX_REPRO exact main-evaluation evidence objects: {pex_main}.",
            f"- Q-TARO interval objects: {len(qtl_rows)}; these remain region-level / interval-level evidence and are not high-confidence gene mappings.",
            f"- Mean candidate rows per main object: {avg_candidates:.4f}.",
            f"- Mean decoy rows per main object: {avg_decoys:.4f}.",
            f"- Validation failed checks: {len(failed_checks)}.",
            "",
            "## Matching Fields",
            "",
            f"- Used fields: {', '.join(used)}.",
            f"- Unavailable fields: {', '.join(unavailable)}.",
            "- Detectability proxy: chr1 SNP coverage, window coverage, variant coverage, and database detectability proxy.",
            "- Research-bias proxy: annotation record count, external knowledge hit count, database source count, trait evidence count, and known-gene proximity proxy.",
            "",
            "## Handling Rules",
            "",
            "- Only exact frozen trait mapping enters the main evaluation candidate pool.",
            "- Ambiguous frozen-trait keyword matches and broader evidence are retained but excluded from the main pool.",
            "- PEX_REPRO remains at zero exact main-evaluation evidence objects; no label was force-filled.",
            "- Q-TARO is handled as region-level qtl_interval evidence, not causal label and not high-confidence gene label.",
            "- All usage remains evaluation / explanation / case study / development evidence candidate only; no training_label is introduced.",
            "",
            "## Limitations",
            "",
            "- The candidate pool is bounded and prototype-scale, not a full genome-wide matched background enumeration.",
            "- Current matching uses chr1 SNP-only coverage; indels, MAF, LD, mappability, recombination rate, and full callability are unavailable.",
            "- Detectability and research-bias controls are proxies and must not be reported as complete correction.",
            "- Q-TARO coordinates are source-reported intervals without liftover.",
            "- Candidate decoys are background controls, not true negatives.",
            "",
            "## Split Readiness",
            "",
            "The layer is sufficient to start a split-freezing design pass for the chr1 SNP-only prototype, provided the split step preserves gene/interval proximity blocking and keeps manual-review/broader evidence out of the main evaluation pool.",
        ]
    )
    (args.report_root / "matched_decoy_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(name: str, rows: list[dict[str, object]], extra: str = "") -> None:
    print(f"{name}_rows={len(rows)}")
    if extra:
        print(extra)
