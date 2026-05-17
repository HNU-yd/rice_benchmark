#!/usr/bin/env python3
"""Build design v0.5.5 trait/covariate protocol tables.

Usage:
    python scripts/trait_state/build_design_v055_tables.py

This script does not modify raw data. It turns the current frozen v0.1 trait
state prototype and population covariates into v0.5.5-aligned audit/protocol
tables for trait usability, preprocessing, matching field availability, and
negative-pair candidate pools.
"""

from __future__ import annotations

import csv
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]

FROZEN_TRAIT_IDS = REPO_ROOT / "data/interim/trait_state_review/frozen_v0_1_trait_ids.txt"
TRAIT_TABLE = REPO_ROOT / "data/interim/trait_state/trait_table_prototype.tsv"
TRAIT_VALUE_TABLE = REPO_ROOT / "data/interim/trait_state/trait_value_table_prototype.tsv"
TRAIT_STATE_TABLE = REPO_ROOT / "data/interim/trait_state/trait_state_table_prototype.tsv"
HIGH_CONFIDENCE_ACCESSIONS = REPO_ROOT / "data/interim/trait_state/high_confidence_accessions.tsv"
ACCESSION_MAPPING_MASTER = REPO_ROOT / "data/interim/accession_mapping/accession_mapping_master.tsv"
PHENOTYPE_XLSX = REPO_ROOT / "data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx"
QMATRIX = REPO_ROOT / "data/raw/metadata/Qmatrix-k9-3kRG.csv"
PCA_EIGENVEC = REPO_ROOT / "data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.eigenvec"
KINSHIP_MATRIX = REPO_ROOT / "data/raw/variants/snp/pruned_v2.1/kinship/result.cXX.txt.bz2"

INTERIM_ROOT = REPO_ROOT / "data/interim/design_v055"
METADATA_DIR = INTERIM_ROOT / "metadata"
DECOY_DIR = INTERIM_ROOT / "decoy"
NEGATIVE_PAIR_DIR = INTERIM_ROOT / "negative_pairs"
QC_DIR = INTERIM_ROOT / "qc_diagnostics"
REPORT_DIR = REPO_ROOT / "reports/current_data_status"

VERSION = "design_v0.5.5_data_protocol_v1"
MIN_MAIN_ACCESSIONS = 1000
MIN_STRATUM_SIZE = 50
PREFERRED_STRATUM_SIZE = 100
MIN_NEGATIVE_POOL_L1 = 20
MIN_NEGATIVE_POOL_RELAXED = 10
PC_DISTANCE_COLUMNS = ["PC1", "PC2", "PC3", "PC4", "PC5"]
PC_COLUMNS = [f"PC{i}" for i in range(1, 13)]

NS_MAIN = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

MISSING_VALUES = {"", ".", "-", "NA", "N/A", "NULL", "NONE", "NAN", "MISSING"}

COVARIATE_FIELDS = [
    "internal_accession_id",
    "genotype_sample_id",
    "phenotype_source_sheet",
    "phenotype_row_id",
    "qmatrix_available",
    "broad_subgroup",
    "broad_subgroup_score",
    "qmatrix_max_component",
    "pc_available",
    *PC_COLUMNS,
    "country_origin",
    "genesys_origcty",
    "genesys_subtaxa",
    "cropyear",
    "cropyear_status",
    "run_count",
    "library_count",
    "exact_library_batch_status",
    "notes",
]

TRAIT_USABILITY_FIELDS = [
    "trait_id",
    "trait_name",
    "n_accessions",
    "subgroup_min_size",
    "subgroup_median_size",
    "cropyear_coverage",
    "missing_rate",
    "pc_association_score",
    "source_sheet",
    "usable_for_main",
    "usable_for_challenge",
    "usable_for_case_only",
    "exclusion_reason",
    "notes",
]

TRAIT_PREPROCESSING_FIELDS = [
    "trait_id",
    "raw_value_field",
    "normalization_method",
    "residualization_method",
    "covariates_used",
    "subgroup_handling",
    "PC_covariates",
    "source_sheet_handling",
    "CROPYEAR_handling",
    "missingness_handling",
    "trait_group_threshold",
    "trait_direction_rule",
    "trait_residual_version",
    "preprocessing_notes",
]

MATCHING_FIELD_AVAILABILITY_FIELDS = [
    "field_name",
    "availability",
    "proxy_field",
    "used_in_matching",
    "used_in_sensitivity",
    "missing_reason",
    "notes",
]

NEGATIVE_PAIR_FIELDS = [
    "trait_id",
    "positive_accession_id",
    "negative_accession_id",
    "positive_trait_state",
    "negative_trait_state",
    "same_subgroup",
    "PC_distance",
    "same_source_sheet",
    "CROPYEAR_status",
    "candidate_pool_size",
    "negative_level",
    "relaxation_reason",
    "balance_diagnostics_id",
    "notes",
]

CANDIDATE_POOL_FIELDS = [
    "trait_id",
    "positive_accession_id",
    "positive_trait_state",
    "source_sheet",
    "broad_subgroup",
    "l1_same_subgroup_pool_size",
    "l2_trait_source_pool_size",
    "l3_trait_pool_size",
    "selected_negative_level",
    "selected_candidate_pool_size",
    "relaxation_reason",
]

BALANCE_DIAGNOSTICS_FIELDS = [
    "balance_diagnostics_id",
    "trait_id",
    "positive_accession_id",
    "negative_accession_id",
    "positive_subgroup",
    "negative_subgroup",
    "positive_cropyear_status",
    "negative_cropyear_status",
    "positive_cropyear",
    "negative_cropyear",
    "positive_country_origin",
    "negative_country_origin",
    "positive_subtaxa",
    "negative_subtaxa",
    "PC_distance",
    "negative_level",
    "notes",
]

CANDIDATE_POOL_SUMMARY_FIELDS = [
    "trait_id",
    "n_positive_rows",
    "median_l1_pool_size",
    "rows_l1_pool_lt_20",
    "rows_l1_pool_lt_10",
    "selected_L1",
    "selected_L2",
    "selected_L3",
    "selected_no_pair",
    "median_selected_pc_distance",
    "notes",
]

VALIDATION_FIELDS = ["check_name", "status", "observed", "expected", "notes"]

GENERATED_TABLE_SCHEMA_FIELDS = [
    "table_path",
    "field_name",
    "description",
    "required",
    "notes",
]

FIELD_DESCRIPTIONS = {
    "internal_accession_id": "Repository-stable accession identifier used as a join key.",
    "genotype_sample_id": "3K genotype sample identifier.",
    "phenotype_source_sheet": "Source phenotype worksheet linked to the accession.",
    "phenotype_row_id": "Excel row number in the source phenotype worksheet.",
    "qmatrix_available": "Whether Qmatrix population structure values are available.",
    "broad_subgroup": "Broad subgroup inferred from maximum Qmatrix component.",
    "broad_subgroup_score": "Maximum Qmatrix component value for the selected subgroup.",
    "qmatrix_max_component": "Name of the Qmatrix component with maximum value.",
    "pc_available": "Whether PC fields used for matching are available.",
    "country_origin": "Country origin proxy from accession mapping.",
    "genesys_origcty": "Genesys MCPD country code.",
    "genesys_subtaxa": "Genesys MCPD SUBTAXA value.",
    "cropyear": "Phenotype CROPYEAR value when available.",
    "cropyear_status": "known or unknown_env; unknown_env is not a shared environment label.",
    "run_count": "Number of linked SRA run accessions.",
    "library_count": "Number of linked sequencing library names.",
    "exact_library_batch_status": "Whether exact LibraryName is available for QC-only use.",
    "trait_id": "Frozen trait identifier.",
    "trait_name": "Human-readable trait name.",
    "n_accessions": "Number of non-missing accessions for the trait.",
    "subgroup_min_size": "Minimum trait x broad_subgroup stratum size.",
    "subgroup_median_size": "Median trait x broad_subgroup stratum size.",
    "cropyear_coverage": "Fraction of non-missing trait rows with known CROPYEAR.",
    "missing_rate": "Missing fraction among high-confidence accession rows for the trait.",
    "pc_association_score": "Maximum eta-squared association between trait_state and PC1-PC5.",
    "source_sheet": "Phenotype source sheet for the trait.",
    "usable_for_main": "Whether the trait passes current main benchmark usability thresholds.",
    "usable_for_challenge": "Whether the trait is demoted to challenge use.",
    "usable_for_case_only": "Whether the trait is limited to case-only use.",
    "exclusion_reason": "Reason for excluding or demoting a trait, if any.",
    "raw_value_field": "Input field used as raw trait value.",
    "normalization_method": "Frozen trait_state normalization or category encoding rule.",
    "residualization_method": "Frozen residualization rule for this processing version.",
    "covariates_used": "Covariates used in trait value transformation, if any.",
    "subgroup_handling": "How broad subgroup is handled for matching/diagnostics.",
    "PC_covariates": "How PC covariates are handled.",
    "source_sheet_handling": "How phenotype source sheets are handled.",
    "CROPYEAR_handling": "How CROPYEAR is handled.",
    "missingness_handling": "How missing trait values are handled.",
    "trait_group_threshold": "Rule for trait group/state bins.",
    "trait_direction_rule": "Frozen trait direction rule.",
    "trait_residual_version": "Version identifier for residual or no-residual trait_state.",
    "preprocessing_notes": "Additional preprocessing restrictions and notes.",
    "field_name": "Name of the matching/covariate/schema field.",
    "availability": "Current availability state for the field.",
    "proxy_field": "Concrete source/proxy used for the field.",
    "used_in_matching": "How the field is used in matching.",
    "used_in_sensitivity": "How the field is used in sensitivity analysis.",
    "missing_reason": "Why the field is missing or incomplete.",
    "positive_accession_id": "Accession carrying the observed trait_state.",
    "negative_accession_id": "Accession selected as mismatched trait_state pair.",
    "positive_trait_state": "Observed trait_state for the positive accession.",
    "negative_trait_state": "Mismatched trait_state for the selected accession.",
    "same_subgroup": "Whether selected pair has the same broad subgroup.",
    "PC_distance": "Euclidean distance across PC1-PC5.",
    "same_source_sheet": "Whether selected pair has the same source sheet.",
    "CROPYEAR_status": "Pairwise CROPYEAR relation.",
    "candidate_pool_size": "Number of eligible candidates in the selected level.",
    "negative_level": "L1/L2/L3 protocol level for the selected mismatched pair.",
    "relaxation_reason": "Reason hard constraints were relaxed, if any.",
    "balance_diagnostics_id": "Stable identifier linking selected pair to balance diagnostics.",
    "l1_same_subgroup_pool_size": "Number of same trait/source/subgroup mismatched-state candidates.",
    "l2_trait_source_pool_size": "Number of same trait/source mismatched-state candidates.",
    "l3_trait_pool_size": "Number of same trait mismatched-state candidates.",
    "selected_negative_level": "Selected L1/L2/L3/no_pair level.",
    "selected_candidate_pool_size": "Candidate pool size for the selected level.",
    "positive_subgroup": "Positive accession broad subgroup.",
    "negative_subgroup": "Selected accession broad subgroup.",
    "positive_cropyear_status": "Positive accession CROPYEAR status.",
    "negative_cropyear_status": "Selected accession CROPYEAR status.",
    "positive_cropyear": "Positive accession CROPYEAR.",
    "negative_cropyear": "Selected accession CROPYEAR.",
    "positive_country_origin": "Positive accession country origin proxy.",
    "negative_country_origin": "Selected accession country origin proxy.",
    "positive_subtaxa": "Positive accession SUBTAXA proxy.",
    "negative_subtaxa": "Selected accession SUBTAXA proxy.",
    "n_positive_rows": "Number of positive trait-state rows summarized.",
    "median_l1_pool_size": "Median L1 candidate pool size.",
    "rows_l1_pool_lt_20": "Rows whose L1 candidate pool is below 20.",
    "rows_l1_pool_lt_10": "Rows whose L1 candidate pool is below 10.",
    "selected_L1": "Rows selected at L1.",
    "selected_L2": "Rows selected at L2.",
    "selected_L3": "Rows selected at L3.",
    "selected_no_pair": "Rows without a selected pair.",
    "median_selected_pc_distance": "Median PC1-PC5 distance among selected pairs.",
    "check_name": "Validation check name.",
    "status": "Validation status.",
    "observed": "Observed validation value.",
    "expected": "Expected validation value.",
    "notes": "Additional table-specific notes.",
    "table_path": "Generated table path relative to repository root.",
    "description": "Field description.",
    "required": "Whether the field is required by this schema.",
}


@dataclass
class SheetData:
    name: str
    headers: list[str]
    rows_by_number: dict[int, list[str]]


def ensure_dirs() -> None:
    for path in (METADATA_DIR, DECOY_DIR, NEGATIVE_PAIR_DIR, QC_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def read_tsv(path: Path) -> list[dict[str, str]]:
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
                if value is None or value == "":
                    normalized[field] = "NA"
                else:
                    normalized[field] = value
            writer.writerow(normalized)


def read_frozen_trait_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def clean(value: object) -> str:
    return str(value or "").strip()


def is_missing(value: object) -> bool:
    return clean(value).upper() in MISSING_VALUES


def yes(value: object) -> bool:
    return clean(value).lower() in {"yes", "true", "1", "y"}


def fmt_float(value: float | None, digits: int = 6) -> str:
    if value is None or math.isnan(value) or math.isinf(value):
        return ""
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def fmt_percent(numerator: int, denominator: int, digits: int = 4) -> str:
    if denominator == 0:
        return ""
    return fmt_float(numerator / denominator, digits)


def count_semicolon_list(value: str) -> int:
    if is_missing(value):
        return 0
    return len([part for part in value.split(";") if part.strip()])


def col_index(cell_ref: str) -> int:
    match = re.match(r"[A-Z]+", cell_ref.upper())
    if not match:
        return 0
    value = 0
    for char in match.group(0):
        value = value * 26 + ord(char) - ord("A") + 1
    return value - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("x:si", NS_MAIN):
        strings.append("".join(node.text or "" for node in si.findall(".//x:t", NS_MAIN)))
    return strings


def sheet_paths(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rid_to_target: dict[str, str] = {}
    for rel in rels.findall("r:Relationship", NS_REL):
        rid = rel.attrib.get("Id", "")
        target = rel.attrib.get("Target", "")
        rid_to_target[rid] = target.lstrip("/") if target.startswith("/") else f"xl/{target}"

    sheets: list[tuple[str, str]] = []
    for sheet in workbook.findall(".//x:sheet", NS_MAIN):
        name = sheet.attrib.get("name", "unknown")
        rid = sheet.attrib.get(f"{{{DOC_REL_NS}}}id", "")
        path = rid_to_target.get(rid)
        if path:
            sheets.append((name, path))
    return sheets


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", NS_MAIN)).strip()
    value = cell.findtext("x:v", default="", namespaces=NS_MAIN)
    if cell_type == "s" and value != "":
        try:
            return shared_strings[int(value)].strip()
        except (ValueError, IndexError):
            return value.strip()
    return str(value or "").strip()


def read_sheet(zf: zipfile.ZipFile, sheet_name: str, sheet_path: str, shared_strings: list[str]) -> SheetData:
    root = ET.fromstring(zf.read(sheet_path))
    rows_by_number: dict[int, list[str]] = {}
    for row in root.findall(".//x:sheetData/x:row", NS_MAIN):
        row_number = int(row.attrib.get("r", "0") or 0)
        values: list[str] = []
        for cell in row.findall("x:c", NS_MAIN):
            idx = col_index(cell.attrib.get("r", "A1"))
            while len(values) <= idx:
                values.append("")
            values[idx] = cell_value(cell, shared_strings)
        rows_by_number[row_number] = values

    headers = rows_by_number.get(1, [])
    return SheetData(name=sheet_name, headers=headers, rows_by_number=rows_by_number)


def read_phenotype_sheets(path: Path) -> dict[str, SheetData]:
    with zipfile.ZipFile(path) as zf:
        shared_strings = read_shared_strings(zf)
        return {
            name: read_sheet(zf, name, sheet_path, shared_strings)
            for name, sheet_path in sheet_paths(zf)
        }


def load_cropyear_by_sheet_row(path: Path) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for sheet_name, sheet in read_phenotype_sheets(path).items():
        header_map = {header.strip().lower(): idx for idx, header in enumerate(sheet.headers)}
        crop_idx = header_map.get("cropyear")
        if crop_idx is None:
            continue
        for row_number, values in sheet.rows_by_number.items():
            if row_number == 1:
                continue
            cropyear = values[crop_idx] if crop_idx < len(values) else ""
            result[(sheet_name, str(row_number))] = clean(cropyear)
    return result


def load_qmatrix(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        components = [field for field in (reader.fieldnames or []) if field != "id"]
        for row in reader:
            values: list[tuple[str, float]] = []
            for component in components:
                try:
                    values.append((component, float(row.get(component, "") or 0.0)))
                except ValueError:
                    values.append((component, 0.0))
            best_component, best_score = max(values, key=lambda item: item[1]) if values else ("", 0.0)
            rows[clean(row.get("id"))] = {
                "broad_subgroup": best_component,
                "broad_subgroup_score": fmt_float(best_score),
                "qmatrix_max_component": best_component,
            }
    return rows


def load_pca(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        header = handle.readline().strip().split()
        for line in handle:
            parts = line.strip().split()
            if not parts:
                continue
            row = dict(zip(header, parts))
            sample_id = clean(row.get("IID") or row.get("FID"))
            rows[sample_id] = {pc: row.get(pc, "") for pc in PC_COLUMNS}
    return rows


def pc_vector(row: dict[str, str], columns: list[str] = PC_DISTANCE_COLUMNS) -> tuple[float, ...] | None:
    values: list[float] = []
    for column in columns:
        try:
            values.append(float(row.get(column, "")))
        except (TypeError, ValueError):
            return None
    return tuple(values)


def euclidean(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def eta_squared_by_group(values: list[float], groups: list[str]) -> float | None:
    if len(values) < 2 or len(values) != len(groups):
        return None
    grand_mean = sum(values) / len(values)
    total_ss = sum((value - grand_mean) ** 2 for value in values)
    if total_ss == 0:
        return 0.0
    grouped: dict[str, list[float]] = defaultdict(list)
    for value, group in zip(values, groups):
        grouped[group].append(value)
    between_ss = 0.0
    for group_values in grouped.values():
        group_mean = sum(group_values) / len(group_values)
        between_ss += len(group_values) * (group_mean - grand_mean) ** 2
    return between_ss / total_ss


def build_covariate_accession_table(
    high_confidence_rows: list[dict[str, str]],
    master_by_accession: dict[str, dict[str, str]],
    qmatrix_by_sample: dict[str, dict[str, str]],
    pca_by_sample: dict[str, dict[str, str]],
    cropyear_by_sheet_row: dict[tuple[str, str], str],
) -> list[dict[str, str]]:
    covariate_rows: list[dict[str, str]] = []
    for row in high_confidence_rows:
        accession_id = clean(row.get("internal_accession_id"))
        sample_id = clean(row.get("genotype_sample_id"))
        master = master_by_accession.get(accession_id, {})
        qrow = qmatrix_by_sample.get(sample_id, {})
        pcrow = pca_by_sample.get(sample_id, {})
        source_sheet = clean(row.get("best_phenotype_sheet"))
        phenotype_row_id = clean(row.get("best_phenotype_row_id"))
        cropyear = cropyear_by_sheet_row.get((source_sheet, phenotype_row_id), "")
        cropyear_status = "known" if not is_missing(cropyear) else "unknown_env"
        library_count = count_semicolon_list(master.get("library_names", ""))
        run_count = count_semicolon_list(master.get("run_accessions", ""))

        out = {
            "internal_accession_id": accession_id,
            "genotype_sample_id": sample_id,
            "phenotype_source_sheet": source_sheet,
            "phenotype_row_id": phenotype_row_id,
            "qmatrix_available": "yes" if qrow else "no",
            "broad_subgroup": qrow.get("broad_subgroup", "unknown_subgroup"),
            "broad_subgroup_score": qrow.get("broad_subgroup_score", ""),
            "qmatrix_max_component": qrow.get("qmatrix_max_component", ""),
            "pc_available": "yes" if all(pcrow.get(pc) for pc in PC_DISTANCE_COLUMNS) else "no",
            "country_origin": clean(master.get("country_origin")),
            "genesys_origcty": clean(master.get("genesys_origcty")),
            "genesys_subtaxa": clean(master.get("genesys_subtaxa")),
            "cropyear": cropyear,
            "cropyear_status": cropyear_status,
            "run_count": str(run_count),
            "library_count": str(library_count),
            "exact_library_batch_status": "available_for_qc_only_not_hard_matching" if library_count else "missing",
            "notes": "covariates are for matching, diagnostics, and sensitivity; accession ID is not a model token",
        }
        for pc in PC_COLUMNS:
            out[pc] = pcrow.get(pc, "")
        covariate_rows.append(out)
    return covariate_rows


def merge_trait_rows(
    frozen_trait_ids: list[str],
    trait_value_rows: list[dict[str, str]],
    trait_state_rows: list[dict[str, str]],
    covariate_by_accession: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    state_by_key = {
        (row.get("trait_id", ""), row.get("internal_accession_id", "")): row
        for row in trait_state_rows
        if row.get("trait_id") in frozen_trait_ids
    }
    merged: list[dict[str, str]] = []
    for value_row in trait_value_rows:
        trait_id = value_row.get("trait_id", "")
        accession_id = value_row.get("internal_accession_id", "")
        if trait_id not in frozen_trait_ids or yes(value_row.get("missing_flag")):
            continue
        covariate = covariate_by_accession.get(accession_id, {})
        state = state_by_key.get((trait_id, accession_id), {})
        out = dict(value_row)
        out.update({f"cov_{key}": value for key, value in covariate.items()})
        out["trait_group"] = state.get("trait_group", "")
        out["trait_state"] = state.get("trait_state", state.get("trait_group", ""))
        out["trait_direction"] = state.get("trait_direction", "not_applicable")
        out["state_rule"] = state.get("state_rule", "")
        merged.append(out)
    return merged


def build_trait_usability_table(
    frozen_trait_ids: list[str],
    trait_table_rows: list[dict[str, str]],
    trait_value_rows: list[dict[str, str]],
    merged_trait_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    trait_meta = {row.get("trait_id", ""): row for row in trait_table_rows}
    values_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    merged_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in trait_value_rows:
        if row.get("trait_id") in frozen_trait_ids:
            values_by_trait[row.get("trait_id", "")].append(row)
    for row in merged_trait_rows:
        merged_by_trait[row.get("trait_id", "")].append(row)

    usability_rows: list[dict[str, str]] = []
    for trait_id in frozen_trait_ids:
        all_rows = values_by_trait.get(trait_id, [])
        nonmissing_rows = merged_by_trait.get(trait_id, [])
        meta = trait_meta.get(trait_id, {})
        n_total = len(all_rows)
        n_nonmissing = len(nonmissing_rows)
        missing_rate = (n_total - n_nonmissing) / n_total if n_total else 1.0
        subgroup_counts = Counter(
            row.get("cov_broad_subgroup", "unknown_subgroup") or "unknown_subgroup"
            for row in nonmissing_rows
        )
        subgroup_sizes = list(subgroup_counts.values())
        crop_known = sum(1 for row in nonmissing_rows if row.get("cov_cropyear_status") == "known")
        pc_scores: list[float] = []
        groups = [row.get("trait_state", "") for row in nonmissing_rows]
        for pc in PC_DISTANCE_COLUMNS:
            values: list[float] = []
            valid_groups: list[str] = []
            for row, group in zip(nonmissing_rows, groups):
                try:
                    values.append(float(row.get(f"cov_{pc}", "")))
                    valid_groups.append(group)
                except (TypeError, ValueError):
                    continue
            score = eta_squared_by_group(values, valid_groups)
            if score is not None:
                pc_scores.append(score)
        pc_association_score = max(pc_scores) if pc_scores else None
        source_sheets = sorted({row.get("source_sheet", "") for row in all_rows if row.get("source_sheet")})
        subgroup_min = min(subgroup_sizes) if subgroup_sizes else 0
        subgroup_median = median(subgroup_sizes) if subgroup_sizes else 0

        usable_main = (
            n_nonmissing >= MIN_MAIN_ACCESSIONS
            and subgroup_min >= MIN_STRATUM_SIZE
            and missing_rate <= 0.20
        )
        exclusion_parts: list[str] = []
        if n_nonmissing < MIN_MAIN_ACCESSIONS:
            exclusion_parts.append("n_accessions_below_main_threshold")
        if subgroup_min < MIN_STRATUM_SIZE:
            exclusion_parts.append("subgroup_min_size_below_50")
        if missing_rate > 0.20:
            exclusion_parts.append("missing_rate_above_20_percent")

        notes = [
            f"subgroups={len(subgroup_counts)}",
            "CROPYEAR is a weak environment proxy only",
            "PC score is max eta^2 for trait_state across PC1-PC5",
        ]
        if pc_association_score is not None and pc_association_score >= 0.25:
            notes.append("high PC association; require PC/subgroup balance diagnostics")

        usability_rows.append(
            {
                "trait_id": trait_id,
                "trait_name": meta.get("trait_name", ""),
                "n_accessions": str(n_nonmissing),
                "subgroup_min_size": str(subgroup_min),
                "subgroup_median_size": fmt_float(float(subgroup_median), 2),
                "cropyear_coverage": fmt_percent(crop_known, n_nonmissing),
                "missing_rate": fmt_float(missing_rate),
                "pc_association_score": fmt_float(pc_association_score),
                "source_sheet": ";".join(source_sheets),
                "usable_for_main": "true" if usable_main else "false",
                "usable_for_challenge": "false" if usable_main else "true",
                "usable_for_case_only": "false",
                "exclusion_reason": ";".join(exclusion_parts),
                "notes": "; ".join(notes),
            }
        )
    return usability_rows


def build_trait_preprocessing_table(
    frozen_trait_ids: list[str],
    trait_table_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    trait_meta = {row.get("trait_id", ""): row for row in trait_table_rows}
    rows: list[dict[str, str]] = []
    for trait_id in frozen_trait_ids:
        meta = trait_meta.get(trait_id, {})
        trait_type = clean(meta.get("trait_type_guess")).lower()
        if trait_type == "binary":
            normalization_method = "binary_class_value"
            trait_group_threshold = "observed class values from frozen trait_state prototype"
        elif trait_type == "categorical":
            normalization_method = "normalized_category"
            trait_group_threshold = "observed categorical states from frozen trait_state prototype"
        else:
            normalization_method = "zscore_if_continuous_available"
            trait_group_threshold = "bottom_30_mid_40_top_30_if_continuous"

        rows.append(
            {
                "trait_id": trait_id,
                "raw_value_field": "raw_value",
                "normalization_method": normalization_method,
                "residualization_method": "none_for_current_v0_1_categorical_binary_frozen_traits",
                "covariates_used": "none_in_trait_value_transformation; subgroup/PC/CROPYEAR/country/SUBTAXA used for matching and diagnostics only",
                "subgroup_handling": "broad_subgroup is hard constraint or balance field; minimum stratum size 50, preferred 100+",
                "PC_covariates": "PC1-PC5 continuous distance for kNN matching; no exact PC strata",
                "source_sheet_handling": "same source_sheet hard constraint when multiple source sheets exist",
                "CROPYEAR_handling": "known year may be soft priority; missing kept as unknown_env; never treated as same environment",
                "missingness_handling": "missing trait rows excluded from trait_state; missing/unknown is not a negative label",
                "trait_group_threshold": trait_group_threshold,
                "trait_direction_rule": "not_applicable_for_current_categorical_binary_traits",
                "trait_residual_version": "v0.55_no_numeric_residual_current_frozen_traits",
                "preprocessing_notes": "trait_state remains a condition signal, not a phenotype prediction target; external evidence not used",
            }
        )
    return rows


def availability(covered: int, total: int) -> str:
    if total == 0 or covered == 0:
        return "missing"
    if covered == total:
        return "present"
    return f"partial:{covered}/{total}"


def build_matching_field_availability_table(covariate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    total = len(covariate_rows)
    qmatrix = sum(1 for row in covariate_rows if row.get("qmatrix_available") == "yes")
    pc = sum(1 for row in covariate_rows if row.get("pc_available") == "yes")
    cropyear = sum(1 for row in covariate_rows if row.get("cropyear_status") == "known")
    country = sum(1 for row in covariate_rows if not is_missing(row.get("country_origin")))
    subtaxa = sum(1 for row in covariate_rows if not is_missing(row.get("genesys_subtaxa")))
    library = sum(1 for row in covariate_rows if int(row.get("library_count", "0") or 0) > 0)

    return [
        {
            "field_name": "trait_id",
            "availability": "present",
            "proxy_field": "trait_value_table.trait_id",
            "used_in_matching": "yes_hard_constraint",
            "used_in_sensitivity": "yes",
            "missing_reason": "",
            "notes": "main negative pairs stay within the same trait_id",
        },
        {
            "field_name": "source_sheet",
            "availability": "present",
            "proxy_field": "trait_value_table.source_sheet",
            "used_in_matching": "yes_hard_when_multiple_sources",
            "used_in_sensitivity": "yes",
            "missing_reason": "",
            "notes": "current frozen traits all use Data < 2007",
        },
        {
            "field_name": "broad_subgroup",
            "availability": availability(qmatrix, total),
            "proxy_field": "Qmatrix max component",
            "used_in_matching": "yes_hard_or_balance",
            "used_in_sensitivity": "yes",
            "missing_reason": "",
            "notes": "derived from Qmatrix-k9; not a model identity token",
        },
        {
            "field_name": "PC1_PC5",
            "availability": availability(pc, total),
            "proxy_field": "pruned_v2.1 PCA eigenvec",
            "used_in_matching": "yes_continuous_distance",
            "used_in_sensitivity": "yes",
            "missing_reason": "",
            "notes": "used as continuous Euclidean distance; never exact PC strata",
        },
        {
            "field_name": "kinship",
            "availability": "present_raw_matrix",
            "proxy_field": "pruned_v2.1 kinship/result.cXX.txt.bz2",
            "used_in_matching": "no",
            "used_in_sensitivity": "yes_lmm_or_covariance_baseline",
            "missing_reason": "" if KINSHIP_MATRIX.exists() else "kinship matrix missing",
            "notes": "large matrix is registered but not loaded into hard strata",
        },
        {
            "field_name": "CROPYEAR",
            "availability": availability(cropyear, total),
            "proxy_field": "3k phenotype CROPYEAR",
            "used_in_matching": "soft_priority_only",
            "used_in_sensitivity": "yes",
            "missing_reason": "no complete site/location/season table",
            "notes": "unknown_env is retained and is not interpreted as same environment",
        },
        {
            "field_name": "country_origin",
            "availability": availability(country, total),
            "proxy_field": "accession_mapping_master.country_origin",
            "used_in_matching": "no_hard_global",
            "used_in_sensitivity": "yes_balance_diagnostic",
            "missing_reason": "",
            "notes": "too sparse for exact global strata",
        },
        {
            "field_name": "SUBTAXA",
            "availability": availability(subtaxa, total),
            "proxy_field": "Genesys SUBTAXA",
            "used_in_matching": "no_hard_global",
            "used_in_sensitivity": "yes_balance_diagnostic",
            "missing_reason": "",
            "notes": "partly redundant with broad subgroup and can create small layers",
        },
        {
            "field_name": "exact_library_batch",
            "availability": availability(library, total),
            "proxy_field": "RunInfo/LibraryName via accession_mapping_master.library_names",
            "used_in_matching": "no",
            "used_in_sensitivity": "qc_only",
            "missing_reason": "",
            "notes": "exact library names are not used for residualization or hard pairing",
        },
        {
            "field_name": "mappability",
            "availability": "missing",
            "proxy_field": "",
            "used_in_matching": "no",
            "used_in_sensitivity": "no",
            "missing_reason": "no genome-wide mappability table in current data",
            "notes": "must be recorded as unavailable for detectability matching",
        },
        {
            "field_name": "variant_callability",
            "availability": "partial_proxy",
            "proxy_field": "variant missingness/QC summaries where available",
            "used_in_matching": "future_decoy_only",
            "used_in_sensitivity": "future",
            "missing_reason": "not yet materialized as genome-wide decoy field",
            "notes": "do not claim full detectability control yet",
        },
        {
            "field_name": "research_bias",
            "availability": "partial_proxy",
            "proxy_field": "annotation richness / known-gene proximity not yet unified",
            "used_in_matching": "future_decoy_only",
            "used_in_sensitivity": "future",
            "missing_reason": "external knowledge not yet integrated into unified gene table",
            "notes": "recorded before matched decoy construction",
        },
    ]


def candidate_key(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("trait_id", ""), row.get("internal_accession_id", ""))


def select_nearest_pc(
    positive: dict[str, str],
    candidates: list[dict[str, str]],
    covariate_by_accession: dict[str, dict[str, str]],
) -> tuple[dict[str, str] | None, float | None]:
    positive_cov = covariate_by_accession.get(positive.get("internal_accession_id", ""), {})
    positive_pc = pc_vector(positive_cov)
    best_candidate: dict[str, str] | None = None
    best_distance: float | None = None
    fallback = sorted(candidates, key=lambda row: row.get("internal_accession_id", ""))
    if fallback:
        best_candidate = fallback[0]
    if positive_pc is None:
        return best_candidate, None

    for candidate in fallback:
        candidate_cov = covariate_by_accession.get(candidate.get("internal_accession_id", ""), {})
        candidate_pc = pc_vector(candidate_cov)
        if candidate_pc is None:
            continue
        distance = euclidean(positive_pc, candidate_pc)
        if best_distance is None or distance < best_distance:
            best_candidate = candidate
            best_distance = distance
    return best_candidate, best_distance


def cropyear_status(left: dict[str, str], right: dict[str, str]) -> str:
    left_status = left.get("cropyear_status", "unknown_env")
    right_status = right.get("cropyear_status", "unknown_env")
    if left_status != "known" or right_status != "known":
        if left_status == "unknown_env" and right_status == "unknown_env":
            return "both_unknown_env_not_equivalent"
        return "one_unknown_env"
    if left.get("cropyear", "") == right.get("cropyear", ""):
        return "same_known_year"
    return "different_known_year"


def build_negative_pair_tables(
    merged_trait_rows: list[dict[str, str]],
    covariate_by_accession: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    rows_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in merged_trait_rows:
        rows_by_trait[row.get("trait_id", "")].append(row)

    pair_rows: list[dict[str, str]] = []
    pool_rows: list[dict[str, str]] = []
    balance_rows: list[dict[str, str]] = []

    for trait_id, trait_rows in rows_by_trait.items():
        for positive in sorted(trait_rows, key=lambda row: row.get("internal_accession_id", "")):
            accession_id = positive.get("internal_accession_id", "")
            positive_state = positive.get("trait_state", "")
            positive_source = positive.get("source_sheet", "")
            positive_cov = covariate_by_accession.get(accession_id, {})
            positive_subgroup = positive_cov.get("broad_subgroup", "unknown_subgroup")

            different_state = [
                row for row in trait_rows
                if row.get("internal_accession_id") != accession_id
                and row.get("trait_state", "") != positive_state
            ]
            l1_candidates = [
                row for row in different_state
                if row.get("source_sheet", "") == positive_source
                and covariate_by_accession.get(row.get("internal_accession_id", ""), {}).get("broad_subgroup", "unknown_subgroup") == positive_subgroup
            ]
            l2_candidates = [
                row for row in different_state
                if row.get("source_sheet", "") == positive_source
            ]
            l3_candidates = different_state

            negative_level = "no_pair"
            relaxation_reason = "no_mismatched_trait_state_candidate"
            selected_pool: list[dict[str, str]] = []
            if len(l1_candidates) >= MIN_NEGATIVE_POOL_L1:
                negative_level = "L1_main_hard_negative"
                relaxation_reason = "none"
                selected_pool = l1_candidates
            elif len(l2_candidates) >= MIN_NEGATIVE_POOL_RELAXED:
                negative_level = "L2_relaxed_hard_negative"
                relaxation_reason = "l1_same_subgroup_pool_below_20"
                selected_pool = l2_candidates
            elif l3_candidates:
                negative_level = "L3_covariate_balanced_negative"
                relaxation_reason = "l1_l2_candidate_pool_below_threshold"
                selected_pool = l3_candidates

            selected, pc_distance = select_nearest_pc(positive, selected_pool, covariate_by_accession)
            candidate_pool_size = len(selected_pool)
            balance_id = f"BD_{trait_id}_{accession_id}"

            selected_cov = covariate_by_accession.get(selected.get("internal_accession_id", ""), {}) if selected else {}
            same_subgroup = (
                "yes"
                if selected and selected_cov.get("broad_subgroup", "unknown_subgroup") == positive_subgroup
                else "no"
            )
            same_source = "yes" if selected and selected.get("source_sheet", "") == positive_source else "no"

            pair_rows.append(
                {
                    "trait_id": trait_id,
                    "positive_accession_id": accession_id,
                    "negative_accession_id": selected.get("internal_accession_id", "") if selected else "",
                    "positive_trait_state": positive_state,
                    "negative_trait_state": selected.get("trait_state", "") if selected else "",
                    "same_subgroup": same_subgroup if selected else "",
                    "PC_distance": fmt_float(pc_distance),
                    "same_source_sheet": same_source if selected else "",
                    "CROPYEAR_status": cropyear_status(positive_cov, selected_cov) if selected else "",
                    "candidate_pool_size": str(candidate_pool_size),
                    "negative_level": negative_level,
                    "relaxation_reason": relaxation_reason,
                    "balance_diagnostics_id": balance_id if selected else "",
                    "notes": "negative means mismatched trait_state pair for training; not a variant/window negative label",
                }
            )
            pool_rows.append(
                {
                    "trait_id": trait_id,
                    "positive_accession_id": accession_id,
                    "positive_trait_state": positive_state,
                    "source_sheet": positive_source,
                    "broad_subgroup": positive_subgroup,
                    "l1_same_subgroup_pool_size": str(len(l1_candidates)),
                    "l2_trait_source_pool_size": str(len(l2_candidates)),
                    "l3_trait_pool_size": str(len(l3_candidates)),
                    "selected_negative_level": negative_level,
                    "selected_candidate_pool_size": str(candidate_pool_size),
                    "relaxation_reason": relaxation_reason,
                }
            )
            if selected:
                balance_rows.append(
                    {
                        "balance_diagnostics_id": balance_id,
                        "trait_id": trait_id,
                        "positive_accession_id": accession_id,
                        "negative_accession_id": selected.get("internal_accession_id", ""),
                        "positive_subgroup": positive_subgroup,
                        "negative_subgroup": selected_cov.get("broad_subgroup", "unknown_subgroup"),
                        "positive_cropyear_status": positive_cov.get("cropyear_status", "unknown_env"),
                        "negative_cropyear_status": selected_cov.get("cropyear_status", "unknown_env"),
                        "positive_cropyear": positive_cov.get("cropyear", ""),
                        "negative_cropyear": selected_cov.get("cropyear", ""),
                        "positive_country_origin": positive_cov.get("country_origin", ""),
                        "negative_country_origin": selected_cov.get("country_origin", ""),
                        "positive_subtaxa": positive_cov.get("genesys_subtaxa", ""),
                        "negative_subtaxa": selected_cov.get("genesys_subtaxa", ""),
                        "PC_distance": fmt_float(pc_distance),
                        "negative_level": negative_level,
                        "notes": "CROPYEAR/country/SUBTAXA are diagnostics or soft constraints unless candidate pools support stricter matching",
                    }
                )
    summary_rows = summarize_candidate_pools(pool_rows, pair_rows)
    return pair_rows, pool_rows, balance_rows, summary_rows


def summarize_candidate_pools(
    pool_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    pools_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    pairs_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pool_rows:
        pools_by_trait[row.get("trait_id", "")].append(row)
    for row in pair_rows:
        pairs_by_trait[row.get("trait_id", "")].append(row)

    summary: list[dict[str, str]] = []
    for trait_id in sorted(pools_by_trait):
        trait_pools = pools_by_trait[trait_id]
        trait_pairs = pairs_by_trait.get(trait_id, [])
        l1_sizes = [int(row.get("l1_same_subgroup_pool_size", "0") or 0) for row in trait_pools]
        level_counts = Counter(row.get("negative_level", "") for row in trait_pairs)
        pc_distances: list[float] = []
        for row in trait_pairs:
            try:
                pc_distances.append(float(row.get("PC_distance", "")))
            except (TypeError, ValueError):
                continue
        summary.append(
            {
                "trait_id": trait_id,
                "n_positive_rows": str(len(trait_pools)),
                "median_l1_pool_size": fmt_float(float(median(l1_sizes)) if l1_sizes else None, 2),
                "rows_l1_pool_lt_20": str(sum(1 for size in l1_sizes if size < MIN_NEGATIVE_POOL_L1)),
                "rows_l1_pool_lt_10": str(sum(1 for size in l1_sizes if size < MIN_NEGATIVE_POOL_RELAXED)),
                "selected_L1": str(level_counts.get("L1_main_hard_negative", 0)),
                "selected_L2": str(level_counts.get("L2_relaxed_hard_negative", 0)),
                "selected_L3": str(level_counts.get("L3_covariate_balanced_negative", 0)),
                "selected_no_pair": str(level_counts.get("no_pair", 0)),
                "median_selected_pc_distance": fmt_float(float(median(pc_distances)) if pc_distances else None),
                "notes": "candidate pools require mismatched trait_state within the same trait; L4 controls are not generated here",
            }
        )
    return summary


def covariate_coverage_rows(covariate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    total = len(covariate_rows)
    fields = [
        ("qmatrix", sum(1 for row in covariate_rows if row.get("qmatrix_available") == "yes"), "Qmatrix-k9-3kRG.csv"),
        ("PC1_PC12", sum(1 for row in covariate_rows if row.get("pc_available") == "yes"), "pca_pruned_v2.1.eigenvec"),
        ("CROPYEAR", sum(1 for row in covariate_rows if row.get("cropyear_status") == "known"), "3kRG phenotype XLSX CROPYEAR"),
        ("country_origin", sum(1 for row in covariate_rows if not is_missing(row.get("country_origin"))), "accession mapping country_origin"),
        ("Genesys_SUBTAXA", sum(1 for row in covariate_rows if not is_missing(row.get("genesys_subtaxa"))), "Genesys MCPD SUBTAXA"),
        ("library_names", sum(1 for row in covariate_rows if int(row.get("library_count", "0") or 0) > 0), "NCBI RunInfo LibraryName"),
    ]
    return [
        {
            "field_name": field,
            "availability": availability(covered, total),
            "proxy_field": proxy,
            "used_in_matching": "see_v055_matching_field_availability_table",
            "used_in_sensitivity": "see_v055_matching_field_availability_table",
            "missing_reason": "",
            "notes": f"coverage_fraction={fmt_percent(covered, total)}",
        }
        for field, covered, proxy in fields
    ]


def build_validation_rows(
    frozen_trait_ids: list[str],
    usability_rows: list[dict[str, str]],
    preprocessing_rows: list[dict[str, str]],
    merged_trait_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    matching_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    checks = [
        {
            "check_name": "frozen_traits_have_usability_rows",
            "status": "pass" if len(usability_rows) == len(frozen_trait_ids) else "fail",
            "observed": str(len(usability_rows)),
            "expected": str(len(frozen_trait_ids)),
            "notes": "",
        },
        {
            "check_name": "frozen_traits_have_preprocessing_rows",
            "status": "pass" if len(preprocessing_rows) == len(frozen_trait_ids) else "fail",
            "observed": str(len(preprocessing_rows)),
            "expected": str(len(frozen_trait_ids)),
            "notes": "",
        },
        {
            "check_name": "negative_pair_rows_match_nonmissing_trait_rows",
            "status": "pass" if len(pair_rows) == len(merged_trait_rows) else "fail",
            "observed": str(len(pair_rows)),
            "expected": str(len(merged_trait_rows)),
            "notes": "negative pair means mismatched trait_state pair, not unlabeled variant negative",
        },
        {
            "check_name": "no_L4_controls_in_main_negative_pair_table",
            "status": "pass" if all("L4" not in row.get("negative_level", "") for row in pair_rows) else "fail",
            "observed": str(sum(1 for row in pair_rows if "L4" in row.get("negative_level", ""))),
            "expected": "0",
            "notes": "L4 controls are diagnostic-only and not generated for main training pairs",
        },
        {
            "check_name": "pc_not_used_as_exact_strata",
            "status": "pass" if any(row.get("field_name") == "PC1_PC5" and row.get("used_in_matching") == "yes_continuous_distance" for row in matching_rows) else "fail",
            "observed": "continuous_distance",
            "expected": "continuous_distance",
            "notes": "",
        },
        {
            "check_name": "all_main_traits_usable",
            "status": "pass" if all(row.get("usable_for_main") == "true" for row in usability_rows) else "warn",
            "observed": str(sum(1 for row in usability_rows if row.get("usable_for_main") == "true")),
            "expected": str(len(frozen_trait_ids)),
            "notes": "warn would mean a frozen trait should be demoted before main training",
        },
    ]
    return checks


def build_generated_table_schema_rows() -> list[dict[str, str]]:
    table_fields = {
        "data/interim/design_v055/metadata/covariate_accession_table.tsv": COVARIATE_FIELDS,
        "data/interim/design_v055/metadata/trait_usability_table.tsv": TRAIT_USABILITY_FIELDS,
        "data/interim/design_v055/metadata/trait_preprocessing_table.tsv": TRAIT_PREPROCESSING_FIELDS,
        "data/interim/design_v055/decoy/matching_field_availability_table.tsv": MATCHING_FIELD_AVAILABILITY_FIELDS,
        "data/interim/design_v055/negative_pairs/negative_pair_protocol_table.tsv": NEGATIVE_PAIR_FIELDS,
        "data/interim/design_v055/negative_pairs/candidate_pool_size_table.tsv": CANDIDATE_POOL_FIELDS,
        "data/interim/design_v055/negative_pairs/balance_diagnostics_table.tsv": BALANCE_DIAGNOSTICS_FIELDS,
        "data/interim/design_v055/qc_diagnostics/negative_pair_candidate_pool_summary.tsv": CANDIDATE_POOL_SUMMARY_FIELDS,
        "data/interim/design_v055/qc_diagnostics/v055_data_processing_validation.tsv": VALIDATION_FIELDS,
        "data/interim/design_v055/qc_diagnostics/v055_generated_table_schema.tsv": GENERATED_TABLE_SCHEMA_FIELDS,
    }
    rows: list[dict[str, str]] = []
    optional_fields = {
        "exclusion_reason",
        "missing_reason",
        "negative_accession_id",
        "negative_trait_state",
        "PC_distance",
        "relaxation_reason",
        "notes",
    }
    for table_path, fields in table_fields.items():
        for field in fields:
            rows.append(
                {
                    "table_path": table_path,
                    "field_name": field,
                    "description": FIELD_DESCRIPTIONS.get(field, "Project-specific protocol field."),
                    "required": "false" if field in optional_fields else "true",
                    "notes": f"schema_version={VERSION}",
                }
            )
    return rows


def write_report(
    covariate_rows: list[dict[str, str]],
    usability_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
    validation_rows: list[dict[str, str]],
) -> None:
    total_pairs = len(pair_rows)
    level_counts = Counter(row.get("negative_level", "") for row in pair_rows)
    crop_known = sum(1 for row in covariate_rows if row.get("cropyear_status") == "known")
    pc_available = sum(1 for row in covariate_rows if row.get("pc_available") == "yes")
    q_available = sum(1 for row in covariate_rows if row.get("qmatrix_available") == "yes")
    main_usable = sum(1 for row in usability_rows if row.get("usable_for_main") == "true")
    fail_checks = [row for row in validation_rows if row.get("status") == "fail"]
    warn_checks = [row for row in validation_rows if row.get("status") == "warn"]

    lines = [
        "# Design v0.5.5 Data Processing Report",
        "",
        "## Scope",
        "",
        "This run aligns the current `rice_benchmark` frozen v0.1 trait data with the v0.5.5 design documents. It materializes data-driven covariate availability, trait usability, trait preprocessing, matching-field availability, and main negative-pair protocol tables.",
        "",
        "This run does not train a model, does not build phenotype prediction targets, does not use GWAS/QTL/known-gene evidence as training labels, and does not turn unknown variants/windows into negatives.",
        "",
        "## Generated Tables",
        "",
        f"- `data/interim/design_v055/metadata/covariate_accession_table.tsv`: {len(covariate_rows)} high-confidence accession covariate rows.",
        f"- `data/interim/design_v055/metadata/trait_usability_table.tsv`: {len(usability_rows)} frozen trait usability rows.",
        f"- `data/interim/design_v055/metadata/trait_preprocessing_table.tsv`: {len(usability_rows)} frozen trait preprocessing rows.",
        f"- `data/interim/design_v055/decoy/matching_field_availability_table.tsv`: matching and detectability field status before decoy construction.",
        f"- `data/interim/design_v055/negative_pairs/negative_pair_protocol_table.tsv`: {total_pairs} main mismatched trait-state pair rows.",
        f"- `data/interim/design_v055/negative_pairs/candidate_pool_size_table.tsv`: row-level candidate pool sizes.",
        f"- `data/interim/design_v055/negative_pairs/balance_diagnostics_table.tsv`: row-level subgroup/PC/CROPYEAR/source diagnostics for selected pairs.",
        "- `data/interim/design_v055/qc_diagnostics/v055_generated_table_schema.tsv`: schema records for all generated v0.5.5 protocol tables.",
        "",
        "Review copies of the small protocol and summary tables were written to `reports/current_data_status/v055_*.tsv`.",
        "",
        "## Covariate Coverage",
        "",
        f"- Qmatrix broad subgroup coverage: {q_available} / {len(covariate_rows)} accessions.",
        f"- PC1-PC12 coverage: {pc_available} / {len(covariate_rows)} accessions.",
        f"- CROPYEAR known coverage: {crop_known} / {len(covariate_rows)} accessions; missing CROPYEAR is retained as `unknown_env`.",
        "- Exact sequencing `LibraryName` remains QC-only and is not used as a residualization or hard pairing stratum.",
        "",
        "## Trait Usability",
        "",
        f"- Frozen traits assessed: {len(usability_rows)}.",
        f"- Usable for main under current thresholds: {main_usable} / {len(usability_rows)}.",
        "- Current frozen traits are categorical/binary, so numeric residualization is not applied in this processing pass.",
        "- Trait states remain condition signals; they are not phenotype prediction labels.",
        "",
        "## Negative Pair Protocol",
        "",
        f"- Main mismatched trait-state pairs generated: {total_pairs}.",
        f"- L1 main hard negative rows: {level_counts.get('L1_main_hard_negative', 0)}.",
        f"- L2 relaxed hard negative rows: {level_counts.get('L2_relaxed_hard_negative', 0)}.",
        f"- L3 covariate-balanced negative rows: {level_counts.get('L3_covariate_balanced_negative', 0)}.",
        f"- Rows without a pair: {level_counts.get('no_pair', 0)}.",
        "- L4 random/shuffled controls are intentionally not generated here because v0.5.5 defines them as diagnostic-only.",
        "",
        "## Candidate Pool Summary",
        "",
        "| trait_id | n rows | median L1 pool | L1 pool < 20 | selected L1 | selected L2 | selected L3 | no pair |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {trait_id} | {n_positive_rows} | {median_l1_pool_size} | {rows_l1_pool_lt_20} | {selected_L1} | {selected_L2} | {selected_L3} | {selected_no_pair} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Failed checks: {len(fail_checks)}.",
            f"- Warning checks: {len(warn_checks)}.",
            "",
            "## Risks And Next Engineering Tasks",
            "",
            "- `CROPYEAR` is only a weak environment proxy; the project still lacks a complete site/location/season table.",
            "- Detectability and research-bias matching fields are only partial or missing; matched decoy construction must keep these fields marked unavailable until unified tables exist.",
            "- Kinship is present as a large raw matrix but is not loaded into hard strata; use it only for LMM/covariance baselines or sensitivity analyses.",
            "- Next step: integrate external knowledge into a unified gene annotation / known-gene evidence / gene-ID mapping layer, then construct matched decoy and frozen splits.",
        ]
    )
    (REPORT_DIR / "v055_data_processing_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dirs()
    frozen_trait_ids = read_frozen_trait_ids(FROZEN_TRAIT_IDS)
    high_confidence_rows = read_tsv(HIGH_CONFIDENCE_ACCESSIONS)
    master_by_accession = {
        row.get("internal_accession_id", ""): row
        for row in read_tsv(ACCESSION_MAPPING_MASTER)
    }
    qmatrix_by_sample = load_qmatrix(QMATRIX)
    pca_by_sample = load_pca(PCA_EIGENVEC)
    cropyear_by_sheet_row = load_cropyear_by_sheet_row(PHENOTYPE_XLSX)

    covariate_rows = build_covariate_accession_table(
        high_confidence_rows,
        master_by_accession,
        qmatrix_by_sample,
        pca_by_sample,
        cropyear_by_sheet_row,
    )
    covariate_by_accession = {row["internal_accession_id"]: row for row in covariate_rows}

    trait_table_rows = read_tsv(TRAIT_TABLE)
    trait_value_rows = read_tsv(TRAIT_VALUE_TABLE)
    trait_state_rows = read_tsv(TRAIT_STATE_TABLE)
    merged_trait_rows = merge_trait_rows(
        frozen_trait_ids,
        trait_value_rows,
        trait_state_rows,
        covariate_by_accession,
    )

    usability_rows = build_trait_usability_table(
        frozen_trait_ids,
        trait_table_rows,
        trait_value_rows,
        merged_trait_rows,
    )
    preprocessing_rows = build_trait_preprocessing_table(frozen_trait_ids, trait_table_rows)
    matching_rows = build_matching_field_availability_table(covariate_rows)
    covariate_coverage = covariate_coverage_rows(covariate_rows)
    pair_rows, pool_rows, balance_rows, summary_rows = build_negative_pair_tables(
        merged_trait_rows,
        covariate_by_accession,
    )
    validation_rows = build_validation_rows(
        frozen_trait_ids,
        usability_rows,
        preprocessing_rows,
        merged_trait_rows,
        pair_rows,
        matching_rows,
    )

    write_tsv(METADATA_DIR / "covariate_accession_table.tsv", covariate_rows, COVARIATE_FIELDS)
    write_tsv(METADATA_DIR / "trait_usability_table.tsv", usability_rows, TRAIT_USABILITY_FIELDS)
    write_tsv(METADATA_DIR / "trait_preprocessing_table.tsv", preprocessing_rows, TRAIT_PREPROCESSING_FIELDS)
    write_tsv(DECOY_DIR / "matching_field_availability_table.tsv", matching_rows, MATCHING_FIELD_AVAILABILITY_FIELDS)
    write_tsv(NEGATIVE_PAIR_DIR / "negative_pair_protocol_table.tsv", pair_rows, NEGATIVE_PAIR_FIELDS)
    write_tsv(NEGATIVE_PAIR_DIR / "candidate_pool_size_table.tsv", pool_rows, CANDIDATE_POOL_FIELDS)
    write_tsv(NEGATIVE_PAIR_DIR / "balance_diagnostics_table.tsv", balance_rows, BALANCE_DIAGNOSTICS_FIELDS)
    write_tsv(QC_DIR / "negative_pair_candidate_pool_summary.tsv", summary_rows, CANDIDATE_POOL_SUMMARY_FIELDS)
    write_tsv(QC_DIR / "v055_data_processing_validation.tsv", validation_rows, VALIDATION_FIELDS)
    schema_rows = build_generated_table_schema_rows()
    write_tsv(QC_DIR / "v055_generated_table_schema.tsv", schema_rows, GENERATED_TABLE_SCHEMA_FIELDS)

    write_tsv(REPORT_DIR / "v055_trait_usability_table.tsv", usability_rows, TRAIT_USABILITY_FIELDS)
    write_tsv(REPORT_DIR / "v055_trait_preprocessing_table.tsv", preprocessing_rows, TRAIT_PREPROCESSING_FIELDS)
    write_tsv(REPORT_DIR / "v055_matching_field_availability_table.tsv", matching_rows, MATCHING_FIELD_AVAILABILITY_FIELDS)
    write_tsv(REPORT_DIR / "v055_covariate_field_availability_table.tsv", covariate_coverage, MATCHING_FIELD_AVAILABILITY_FIELDS)
    write_tsv(REPORT_DIR / "v055_negative_pair_candidate_pool_summary.tsv", summary_rows, CANDIDATE_POOL_SUMMARY_FIELDS)
    write_tsv(REPORT_DIR / "v055_data_processing_validation.tsv", validation_rows, VALIDATION_FIELDS)
    write_tsv(REPORT_DIR / "v055_generated_table_schema.tsv", schema_rows, GENERATED_TABLE_SCHEMA_FIELDS)
    write_report(covariate_rows, usability_rows, pair_rows, summary_rows, validation_rows)

    print(f"version={VERSION}")
    print(f"covariate_accession_rows={len(covariate_rows)}")
    print(f"frozen_traits={len(frozen_trait_ids)}")
    print(f"frozen_trait_nonmissing_rows={len(merged_trait_rows)}")
    print(f"negative_pair_rows={len(pair_rows)}")
    print(f"validation_failed={sum(1 for row in validation_rows if row['status'] == 'fail')}")
    print(f"validation_warn={sum(1 for row in validation_rows if row['status'] == 'warn')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
