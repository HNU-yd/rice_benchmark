#!/usr/bin/env python3
"""Build trait_state prototype tables from high-confidence accession mappings.

Usage:
    python scripts/trait_state/build_trait_state_prototype.py
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
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = REPO_ROOT / "data/interim/accession_mapping/accession_mapping_master.tsv"
PHENOTYPE_XLSX = REPO_ROOT / "data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx"
INTERIM_DIR = REPO_ROOT / "data/interim/trait_state"
REPORT_DIR = REPO_ROOT / "reports/trait_state"
CONFIG_PATH = REPO_ROOT / "configs/trait_state_v0_1.yaml"

NS_MAIN = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

HIGH_CONF_FIELDS = [
    "internal_accession_id",
    "genotype_sample_id",
    "three_k_dna_iris_unique_id",
    "genetic_stock_varname",
    "sra_accession",
    "best_phenotype_sheet",
    "best_phenotype_row_id",
    "best_phenotype_stock_id",
    "best_phenotype_gs_accno",
    "best_phenotype_name",
    "best_phenotype_source_accno",
    "phenotype_mapping_confidence",
    "snp_core_available",
    "indel_available",
    "qmatrix_available",
    "usable_for_snp_trait",
    "usable_for_snp_indel_trait",
    "notes",
]

SUMMARY_FIELDS = ["metric", "n", "denominator", "percent", "notes"]

TRAIT_TABLE_FIELDS = [
    "trait_id",
    "source_sheet",
    "trait_name",
    "trait_type_guess",
    "n_total_accessions",
    "n_non_missing",
    "missing_rate",
    "n_unique_values",
    "numeric_convertible",
    "mean",
    "std",
    "min",
    "q05",
    "q25",
    "median",
    "q75",
    "q95",
    "max",
    "recommended_for_v0_1",
    "recommendation_priority",
    "recommendation_reason",
    "notes",
]

VALUE_TABLE_FIELDS = [
    "trait_id",
    "internal_accession_id",
    "genotype_sample_id",
    "source_sheet",
    "phenotype_row_id",
    "raw_value",
    "numeric_value",
    "normalized_value",
    "missing_flag",
    "trait_type_guess",
    "notes",
]

STATE_TABLE_FIELDS = [
    "trait_id",
    "internal_accession_id",
    "genotype_sample_id",
    "raw_value",
    "numeric_value",
    "normalized_value",
    "trait_group",
    "trait_state",
    "trait_direction",
    "state_rule",
    "notes",
]

RECOMMENDATION_FIELDS = [
    "trait_id",
    "source_sheet",
    "trait_name",
    "trait_type_guess",
    "n_non_missing",
    "missing_rate",
    "recommendation_priority",
    "recommended_for_v0_1",
    "reason",
    "notes",
]

SHEET_SUMMARY_FIELDS = ["sheet_name", "n_rows", "n_cols", "used_for_trait_state", "n_high_confidence_rows", "notes"]

MISSING_VALUES = {"", ".", "-", "NA", "N/A", "NULL", "NONE", "NAN", "MISSING"}
METADATA_COLUMNS = {
    "seqno",
    "stock_id",
    "gs_accno",
    "name",
    "source_accno",
    "cropyear",
    "worksheet",
    "remarks",
    "field name",
    "descriptor",
    "value",
    "value description",
}


@dataclass
class SheetData:
    name: str
    headers: list[str]
    rows_by_number: dict[int, list[str]]
    n_rows: int
    n_cols: int


def ensure_dirs() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


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
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def yes(value: object) -> bool:
    return str(value or "").strip().lower() in {"yes", "true", "1", "y"}


def fmt_number(value: float | None, digits: int = 6) -> str:
    if value is None or math.isnan(value):
        return ""
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return ""
    return fmt_number(numerator / denominator * 100, 4)


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
        if target.startswith("/"):
            target_path = target.lstrip("/")
        else:
            target_path = "xl/" + target
        rid_to_target[rid] = target_path
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
    max_col = 0
    for row in root.findall(".//x:sheetData/x:row", NS_MAIN):
        row_number = int(row.attrib.get("r", "0") or 0)
        values: list[str] = []
        for cell in row.findall("x:c", NS_MAIN):
            idx = col_index(cell.attrib.get("r", "A1"))
            while len(values) <= idx:
                values.append("")
            values[idx] = cell_value(cell, shared_strings)
            max_col = max(max_col, idx + 1)
        rows_by_number[row_number] = values
    header_number = 1 if 1 in rows_by_number else min(rows_by_number, default=0)
    headers = rows_by_number.get(header_number, [])
    while len(headers) < max_col:
        headers.append("")
    return SheetData(
        name=sheet_name,
        headers=headers,
        rows_by_number=rows_by_number,
        n_rows=len(rows_by_number),
        n_cols=max_col,
    )


def read_workbook(path: Path) -> dict[str, SheetData]:
    sheets: dict[str, SheetData] = {}
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        for sheet_name, sheet_path in sheet_paths(zf):
            sheets[sheet_name] = read_sheet(zf, sheet_name, sheet_path, shared)
    return sheets


def is_missing(value: object) -> bool:
    return str(value or "").strip().upper() in MISSING_VALUES


def parse_number(value: object) -> float | None:
    text = str(value or "").strip()
    if is_missing(text):
        return None
    text = text.replace(",", "")
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?", text):
        try:
            return float(text)
        except ValueError:
            return None
    return None


def quantile(sorted_values: list[float], q: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return sorted_values[int(pos)]
    weight = pos - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def mean_std(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, 0.0
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return mean, math.sqrt(variance)


def normalize_identifier(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unnamed"


def normalize_sheet_identifier(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("<", " lt ").replace(">", " gt ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unnamed_sheet"


def trait_id(sheet_name: str, trait_name: str) -> str:
    return f"{normalize_sheet_identifier(sheet_name)}__{normalize_identifier(trait_name)}"


def normalize_state(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    if not text:
        return "missing"
    if re.fullmatch(r"\d+(?:_\d+)?", text):
        return f"value_{text}"
    return text


def is_metadata_column(header: str) -> bool:
    lower = str(header or "").strip().lower()
    if lower in METADATA_COLUMNS:
        return True
    return bool(
        re.search(r"(^|_)id$", lower)
        or "accession" in lower
        or "accno" in lower
        or lower.endswith("_name")
        or lower in {"sample", "source", "year"}
    )


def dictionary_fields(sheets: dict[str, SheetData]) -> tuple[set[str], dict[str, str]]:
    fields: set[str] = set()
    descriptors: dict[str, str] = {}
    for sheet in sheets.values():
        if "dictionary" not in sheet.name.lower():
            continue
        header_to_idx = {name: idx for idx, name in enumerate(sheet.headers)}
        field_idx = header_to_idx.get("Field Name")
        desc_idx = header_to_idx.get("Descriptor")
        if field_idx is None:
            continue
        for row_number, row in sheet.rows_by_number.items():
            if row_number == 1:
                continue
            field = row[field_idx].strip() if field_idx < len(row) else ""
            if not field:
                continue
            fields.add(field)
            if desc_idx is not None and desc_idx < len(row) and row[desc_idx] and field not in descriptors:
                descriptors[field] = row[desc_idx]
    return fields, descriptors


def build_high_confidence_subset(master_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    subset: list[dict[str, str]] = []
    for row in master_rows:
        confidence = row.get("phenotype_mapping_confidence", "")
        usable_for_snp = (
            yes(row.get("usable_for_trait_mapping"))
            and confidence in {"A", "B"}
            and yes(row.get("snp_core_available"))
            and yes(row.get("qmatrix_available"))
        )
        usable_for_snp_indel = usable_for_snp and yes(row.get("indel_available"))
        if not usable_for_snp:
            continue
        out = {field: row.get(field, "") for field in HIGH_CONF_FIELDS}
        out["usable_for_snp_trait"] = "true"
        out["usable_for_snp_indel_trait"] = "true" if usable_for_snp_indel else "false"
        out["notes"] = "A/B high-confidence accession mapping; C/D excluded; trait_state is condition signal only"
        subset.append(out)
    subset.sort(key=lambda x: x["internal_accession_id"])
    return subset


def summarize_high_confidence(master_rows: list[dict[str, str]], subset: list[dict[str, str]]) -> list[dict[str, object]]:
    total = len(master_rows)
    confidence_counts = Counter(row.get("phenotype_mapping_confidence", "") for row in master_rows)
    usable_ab = sum(
        1
        for row in master_rows
        if yes(row.get("usable_for_trait_mapping")) and row.get("phenotype_mapping_confidence") in {"A", "B"}
    )
    snp_indel = sum(1 for row in subset if row.get("usable_for_snp_indel_trait") == "true")
    return [
        {
            "metric": "genotype_union_samples",
            "n": total,
            "denominator": total,
            "percent": "100",
            "notes": "accession_mapping_master.tsv total rows",
        },
        {
            "metric": "phenotype_A_B_usable_mapping",
            "n": usable_ab,
            "denominator": total,
            "percent": percent(usable_ab, total),
            "notes": "A/B high-confidence phenotype mapping before SNP/Qmatrix filter",
        },
        {
            "metric": "high_confidence_snp_qmatrix_subset",
            "n": len(subset),
            "denominator": total,
            "percent": percent(len(subset), total),
            "notes": "usable_for_trait_mapping=true, phenotype confidence A/B, SNP core present, Qmatrix present",
        },
        {
            "metric": "high_confidence_snp_indel_qmatrix_subset",
            "n": snp_indel,
            "denominator": total,
            "percent": percent(snp_indel, total),
            "notes": "same subset with indel_available=true",
        },
        {
            "metric": "excluded_C_level_name_only",
            "n": confidence_counts.get("C", 0),
            "denominator": total,
            "percent": percent(confidence_counts.get("C", 0), total),
            "notes": "C-level candidates require manual review and are excluded",
        },
        {
            "metric": "excluded_D_level_unmapped",
            "n": confidence_counts.get("D", 0),
            "denominator": total,
            "percent": percent(confidence_counts.get("D", 0), total),
            "notes": "D-level unmapped samples are unknown, not negative",
        },
    ]


def row_value(row: list[str], idx: int) -> str:
    return row[idx].strip() if idx < len(row) else ""


def collect_trait_values(
    subset: list[dict[str, str]],
    sheets: dict[str, SheetData],
) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, object]], int]:
    values_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    missing_rows = 0
    rows_per_sheet = Counter(row["best_phenotype_sheet"] for row in subset)
    for accession in subset:
        sheet_name = accession["best_phenotype_sheet"]
        row_text = accession["best_phenotype_row_id"]
        if not row_text:
            missing_rows += 1
            continue
        try:
            row_number = int(float(row_text))
        except ValueError:
            missing_rows += 1
            continue
        sheet = sheets.get(sheet_name)
        if sheet is None or row_number not in sheet.rows_by_number:
            missing_rows += 1
            continue
        source_row = sheet.rows_by_number[row_number]
        for idx, header in enumerate(sheet.headers):
            name = header or f"col_{idx + 1}"
            tid = trait_id(sheet_name, name)
            values_by_trait[tid].append(
                {
                    "trait_id": tid,
                    "source_sheet": sheet_name,
                    "trait_name": name,
                    "internal_accession_id": accession["internal_accession_id"],
                    "genotype_sample_id": accession["genotype_sample_id"],
                    "phenotype_row_id": row_text,
                    "raw_value": row_value(source_row, idx),
                }
            )
    sheet_summary: list[dict[str, object]] = []
    for sheet in sheets.values():
        used = sheet.name in rows_per_sheet
        sheet_summary.append(
            {
                "sheet_name": sheet.name,
                "n_rows": sheet.n_rows,
                "n_cols": sheet.n_cols,
                "used_for_trait_state": "true" if used else "false",
                "n_high_confidence_rows": rows_per_sheet.get(sheet.name, 0),
                "notes": "used through best_phenotype_sheet" if used else "not used by high-confidence accession subset",
            }
        )
    return values_by_trait, sheet_summary, missing_rows


def infer_trait_type(
    trait_name: str,
    raw_values: list[str],
    dictionary_trait_names: set[str],
) -> tuple[str, bool, list[float], list[str]]:
    if is_metadata_column(trait_name):
        return "id_or_metadata", False, [], []
    non_missing = [value for value in raw_values if not is_missing(value)]
    unique_values = sorted(set(non_missing))
    numeric_values = [parse_number(value) for value in non_missing]
    numeric_convertible = bool(non_missing) and all(value is not None for value in numeric_values)
    numeric_clean = [value for value in numeric_values if value is not None]
    if len(unique_values) == 2:
        return "binary", numeric_convertible, numeric_clean, unique_values
    if trait_name in dictionary_trait_names:
        return "categorical", numeric_convertible, numeric_clean, unique_values
    if numeric_convertible and len(unique_values) > 12:
        return "continuous", True, numeric_clean, unique_values
    if non_missing:
        return "categorical", numeric_convertible, numeric_clean, unique_values
    return "categorical", False, [], unique_values


def recommendation(
    trait_type: str,
    n_non_missing: int,
    n_unique: int,
    numeric_convertible: bool,
) -> tuple[str, str, str]:
    if trait_type == "id_or_metadata":
        return "false", "metadata", "ID 或 metadata 字段，不作为 trait_state"
    if trait_type == "continuous" and n_non_missing >= 1000:
        return "true", "P0", "连续性状且非缺失样本数 >= 1000"
    if n_non_missing >= 500 and trait_type in {"continuous", "categorical", "binary"}:
        if trait_type == "continuous" or trait_type == "binary" or n_unique <= 30:
            return "true", "P1", "覆盖度较高，可作为 v0.1-mini 候选 trait_state"
    if n_non_missing == 0:
        return "false", "P2", "当前 high-confidence subset 中无非缺失值"
    if trait_type == "categorical" and not numeric_convertible and n_unique > 30:
        return "false", "P2", "类别过多或解释困难，需人工审查"
    return "false", "P2", "样本数较少或暂不适合进入 v0.1-mini"


def build_trait_stats(
    values_by_trait: dict[str, list[dict[str, str]]],
    dictionary_trait_names: set[str],
    field_descriptors: dict[str, str],
) -> list[dict[str, object]]:
    stats: list[dict[str, object]] = []
    for tid, rows in sorted(values_by_trait.items()):
        source_sheet = rows[0]["source_sheet"]
        name = rows[0]["trait_name"]
        raw_values = [row["raw_value"] for row in rows]
        non_missing = [value for value in raw_values if not is_missing(value)]
        trait_type, numeric_convertible, numeric_values, unique_values = infer_trait_type(
            name, raw_values, dictionary_trait_names
        )
        sorted_numeric = sorted(numeric_values)
        mean, std = mean_std(sorted_numeric)
        rec, priority, reason = recommendation(trait_type, len(non_missing), len(unique_values), numeric_convertible)
        notes = []
        if name in field_descriptors:
            notes.append(field_descriptors[name])
        if trait_type in {"categorical", "binary"} and numeric_convertible:
            notes.append("numeric summary describes encoded category values only")
        if trait_type == "id_or_metadata":
            notes.append("excluded from trait_value_table and trait_state_table")
        stats.append(
            {
                "trait_id": tid,
                "source_sheet": source_sheet,
                "trait_name": name,
                "trait_type_guess": trait_type,
                "n_total_accessions": len(rows),
                "n_non_missing": len(non_missing),
                "missing_rate": fmt_number(1 - len(non_missing) / len(rows), 6) if rows else "",
                "n_unique_values": len(unique_values),
                "numeric_convertible": "true" if numeric_convertible else "false",
                "mean": fmt_number(mean),
                "std": fmt_number(std),
                "min": fmt_number(sorted_numeric[0]) if sorted_numeric else "",
                "q05": fmt_number(quantile(sorted_numeric, 0.05)),
                "q25": fmt_number(quantile(sorted_numeric, 0.25)),
                "median": fmt_number(quantile(sorted_numeric, 0.50)),
                "q75": fmt_number(quantile(sorted_numeric, 0.75)),
                "q95": fmt_number(quantile(sorted_numeric, 0.95)),
                "max": fmt_number(sorted_numeric[-1]) if sorted_numeric else "",
                "recommended_for_v0_1": rec,
                "recommendation_priority": priority,
                "recommendation_reason": reason,
                "notes": "; ".join(notes),
            }
        )
    return stats


def build_value_and_state_tables(
    values_by_trait: dict[str, list[dict[str, str]]],
    stats_by_trait: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    value_rows: list[dict[str, object]] = []
    state_rows: list[dict[str, object]] = []
    binary_maps: dict[str, dict[str, str]] = {}
    thresholds: dict[str, tuple[float | None, float | None]] = {}
    for tid, stats in stats_by_trait.items():
        if stats["trait_type_guess"] == "continuous":
            numeric_values = [
                parse_number(row["raw_value"])
                for row in values_by_trait[tid]
                if parse_number(row["raw_value"]) is not None
            ]
            sorted_numeric = sorted(value for value in numeric_values if value is not None)
            thresholds[tid] = (quantile(sorted_numeric, 0.30), quantile(sorted_numeric, 0.70))
        elif stats["trait_type_guess"] == "binary":
            unique_values = sorted({row["raw_value"] for row in values_by_trait[tid] if not is_missing(row["raw_value"])})
            binary_maps[tid] = {value: f"class_{idx}" for idx, value in enumerate(unique_values)}

    for tid, rows in sorted(values_by_trait.items()):
        stats = stats_by_trait[tid]
        trait_type = str(stats["trait_type_guess"])
        if trait_type == "id_or_metadata":
            continue
        mean = parse_number(stats.get("mean"))
        std = parse_number(stats.get("std"))
        for row in rows:
            raw_value = row["raw_value"]
            missing = is_missing(raw_value)
            numeric = parse_number(raw_value)
            normalized = ""
            if not missing and trait_type == "continuous" and numeric is not None and std not in (None, 0.0):
                normalized = fmt_number((numeric - (mean or 0.0)) / std)
            value_rows.append(
                {
                    "trait_id": tid,
                    "internal_accession_id": row["internal_accession_id"],
                    "genotype_sample_id": row["genotype_sample_id"],
                    "source_sheet": row["source_sheet"],
                    "phenotype_row_id": row["phenotype_row_id"],
                    "raw_value": raw_value,
                    "numeric_value": fmt_number(numeric),
                    "normalized_value": normalized,
                    "missing_flag": "true" if missing else "false",
                    "trait_type_guess": trait_type,
                    "notes": "trait_state condition signal only; not phenotype prediction label",
                }
            )
            if missing:
                continue
            if trait_type == "continuous" and numeric is not None:
                low_cut, high_cut = thresholds.get(tid, (None, None))
                if low_cut is not None and numeric <= low_cut:
                    group = "low"
                    rule = "bottom_30_percent"
                elif high_cut is not None and numeric >= high_cut:
                    group = "high"
                    rule = "top_30_percent"
                else:
                    group = "mid"
                    rule = "middle_40_percent"
                trait_state = group
                direction = group
            elif trait_type == "binary":
                group = binary_maps.get(tid, {}).get(raw_value, normalize_state(raw_value))
                trait_state = group
                direction = "not_applicable"
                rule = "binary_class_value"
            else:
                group = normalize_state(raw_value)
                trait_state = group
                direction = "not_applicable"
                rule = "normalized_category"
            state_rows.append(
                {
                    "trait_id": tid,
                    "internal_accession_id": row["internal_accession_id"],
                    "genotype_sample_id": row["genotype_sample_id"],
                    "raw_value": raw_value,
                    "numeric_value": fmt_number(numeric),
                    "normalized_value": normalized,
                    "trait_group": group,
                    "trait_state": trait_state,
                    "trait_direction": direction,
                    "state_rule": rule,
                    "notes": "trait_state is a model condition signal, not a prediction label",
                }
            )
    return value_rows, state_rows


def recommendation_rows(trait_stats: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in trait_stats:
        if row["trait_type_guess"] == "id_or_metadata":
            continue
        rows.append(
            {
                "trait_id": row["trait_id"],
                "source_sheet": row["source_sheet"],
                "trait_name": row["trait_name"],
                "trait_type_guess": row["trait_type_guess"],
                "n_non_missing": row["n_non_missing"],
                "missing_rate": row["missing_rate"],
                "recommendation_priority": row["recommendation_priority"],
                "recommended_for_v0_1": row["recommended_for_v0_1"],
                "reason": row["recommendation_reason"],
                "notes": row["notes"],
            }
        )
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    rows.sort(
        key=lambda row: (
            priority_order.get(str(row["recommendation_priority"]), 9),
            -int(row["n_non_missing"]),
            str(row["trait_id"]),
        )
    )
    return rows


def compact_traits(rows: list[dict[str, object]], limit: int = 30) -> str:
    names = [f"`{row['trait_id']}`" for row in rows]
    if not names:
        return "无。"
    shown = names[:limit]
    suffix = f"\n\n另有 {len(names) - limit} 个未在此处展开，详见 TSV。" if len(names) > limit else ""
    return "、".join(shown) + "。" + suffix


def write_recommendation_md(path: Path, rec_rows: list[dict[str, object]], metadata_rows: list[dict[str, object]]) -> None:
    recommended = [row for row in rec_rows if row["recommended_for_v0_1"] == "true"]
    paused = [row for row in rec_rows if row["recommended_for_v0_1"] != "true"]
    lines = [
        "# v0.1 Trait Recommendation",
        "",
        "本报告基于 A/B high-confidence accession subset 生成。trait_state 是模型条件输入，不是 phenotype prediction label。",
        "",
        "## 推荐优先进入 v0.1 的 trait",
        "",
        compact_traits(recommended, 40),
        "",
        "## 暂缓 trait",
        "",
        compact_traits(paused, 40),
        "",
        "## 不能作为 trait 的 metadata 字段",
        "",
        compact_traits(metadata_rows, 80),
        "",
        "## 使用口径",
        "",
        "- P0：连续性状，非缺失样本数 >= 1000。",
        "- P1：非缺失样本数 >= 500，且为连续性状或清晰 categorical / binary trait。",
        "- P2：样本数较少、metadata-like、类别过多或暂不适合进入 v0.1-mini。",
        "- C/D 级 accession mapping 样本不进入本推荐。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_config() -> None:
    CONFIG_PATH.write_text(
        """version: v0.1-trait-state-prototype

accession_subset:
  use_confidence_levels: ["A", "B"]
  exclude_confidence_levels: ["C", "D"]
  require_snp_core: true
  require_qmatrix: true

trait_state_rules:
  continuous:
    normalization: "zscore"
    grouping:
      low: "bottom_30_percent"
      mid: "middle_40_percent"
      high: "top_30_percent"
  categorical:
    state: "normalized_category"
  binary:
    state: "class_value"

constraints:
  no_phenotype_prediction: true
  trait_state_is_condition_signal: true
  unknown_not_negative: true
""",
        encoding="utf-8",
    )


def write_main_report(
    path: Path,
    high_conf_rows: list[dict[str, str]],
    high_conf_summary: list[dict[str, object]],
    sheet_summary: list[dict[str, object]],
    trait_stats: list[dict[str, object]],
    rec_rows: list[dict[str, object]],
    missing_source_rows: int,
) -> None:
    non_metadata = [row for row in trait_stats if row["trait_type_guess"] != "id_or_metadata"]
    metadata_rows = [row for row in trait_stats if row["trait_type_guess"] == "id_or_metadata"]
    continuous = [row for row in non_metadata if row["trait_type_guess"] == "continuous"]
    categorical = [row for row in non_metadata if row["trait_type_guess"] == "categorical"]
    binary = [row for row in non_metadata if row["trait_type_guess"] == "binary"]
    recommended = [row for row in rec_rows if row["recommended_for_v0_1"] == "true"]
    snp_indel = sum(1 for row in high_conf_rows if row["usable_for_snp_indel_trait"] == "true")
    used_sheets = [row for row in sheet_summary if row["used_for_trait_state"] == "true"]
    sheet_lines = [
        f"- `{row['sheet_name']}`：high-confidence rows = {row['n_high_confidence_rows']}，rows = {row['n_rows']}，cols = {row['n_cols']}。"
        for row in used_sheets
    ]
    lines = [
        "# Trait State Prototype Report",
        "",
        "## 本次任务目标",
        "",
        "本阶段基于 A/B high-confidence accession mapping 构建 trait_state prototype，冻结可复查的 accession subset，并从 `3kRG_PhenotypeData_v20170411.xlsx` 抽取 trait 值。该阶段不做 phenotype prediction，不训练模型，不构建正式 benchmark schema，也不纳入 C/D 级 accession mapping 样本。",
        "",
        "## High-confidence Accession Subset",
        "",
        f"- high-confidence accession subset 样本数：{len(high_conf_rows)}。",
        f"- 可用于 SNP-only trait prototype 的样本数：{len(high_conf_rows)}。",
        f"- 可用于 SNP+indel trait prototype 的样本数：{snp_indel}。",
        f"- phenotype row 缺失或无法回取的 high-confidence 样本数：{missing_source_rows}。",
        "",
        "## Phenotype Sheet 情况",
        "",
        *sheet_lines,
        "",
        "## Trait 识别结果",
        "",
        f"- 识别到的非 metadata trait 总数：{len(non_metadata)}。",
        f"- 连续性状数量：{len(continuous)}。",
        f"- 分类性状数量：{len(categorical)}。",
        f"- 二分类性状数量：{len(binary)}。",
        f"- ID / metadata 字段数量：{len(metadata_rows)}。",
        "",
        "## 推荐 v0.1 Trait 子集",
        "",
        f"推荐进入 v0.1-mini 的 trait 数：{len(recommended)}。",
        "",
        compact_traits(recommended, 50),
        "",
        "完整推荐表见 `reports/trait_state/v0_1_trait_recommendation.tsv`。",
        "",
        "## Trait_state 构建规则",
        "",
        "- continuous trait：`normalized_value = (value - mean) / std`；按 bottom 30%、middle 40%、top 30% 分为 `low`、`mid`、`high`。",
        "- categorical trait：`trait_state` 使用 normalized category string。",
        "- binary trait：`trait_state` 使用 `class_0` / `class_1`。",
        "- 缺失 trait 值不生成 trait_state 行。",
        "",
        "## 为什么这不是 phenotype prediction",
        "",
        "`trait_state` 是模型条件扰动信号，不是 prediction label。本阶段没有构建 phenotype prediction head，没有训练模型，没有把 accession phenotype value 作为待预测目标，也没有生成 train/val/test split。",
        "",
        "## C/D 级样本为什么不进入 trait_state",
        "",
        "C 级样本只有名称级候选匹配，存在 false genotype-trait pairing 风险；D 级样本缺少可用 phenotype mapping，不能解释为 negative。为保持 benchmark 可审计性，本阶段只使用 A/B accession mapping 样本。",
        "",
        "## 主要风险",
        "",
        "- 3K phenotype 字段大量为编码型 trait，部分 numeric summary 只反映编码值本身，不应解释为生物连续量。",
        "- 不同 sheet 中同名 trait 的测量时期和编码体系可能不同，当前 prototype 保留 `source_sheet` 维度，不做跨 sheet 合并。",
        "- v0.1-mini trait 子集仍需人工审查 trait descriptor、缺失模式和类别含义。",
        "",
        "## 下一步建议",
        "",
        "如果 v0.1 trait 子集足够，则构建 chr1 SNP-only minimal Task 1 instances；否则先人工审查 trait 字段和 accession mapping。",
        "",
        "## 结论",
        "",
        "本阶段只生成 prototype，不是最终 benchmark 表。只有 A/B accession mapping 样本进入 trait_state prototype。trait_state 是条件输入，不是预测目标。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dirs()
    master_rows = read_tsv(MASTER_PATH)
    sheets = read_workbook(PHENOTYPE_XLSX)
    dictionary_trait_names, field_descriptors = dictionary_fields(sheets)

    high_conf_rows = build_high_confidence_subset(master_rows)
    high_conf_summary = summarize_high_confidence(master_rows, high_conf_rows)
    write_tsv(INTERIM_DIR / "high_confidence_accessions.tsv", high_conf_rows, HIGH_CONF_FIELDS)
    write_tsv(REPORT_DIR / "high_confidence_accession_summary.tsv", high_conf_summary, SUMMARY_FIELDS)

    values_by_trait, sheet_summary, missing_source_rows = collect_trait_values(high_conf_rows, sheets)
    trait_stats = build_trait_stats(values_by_trait, dictionary_trait_names, field_descriptors)
    stats_by_trait = {str(row["trait_id"]): row for row in trait_stats}
    value_rows, state_rows = build_value_and_state_tables(values_by_trait, stats_by_trait)
    rec_rows = recommendation_rows(trait_stats)
    metadata_rows = [row for row in trait_stats if row["trait_type_guess"] == "id_or_metadata"]

    write_tsv(INTERIM_DIR / "trait_table_prototype.tsv", trait_stats, TRAIT_TABLE_FIELDS)
    write_tsv(REPORT_DIR / "trait_table_summary.tsv", trait_stats, TRAIT_TABLE_FIELDS)
    write_tsv(INTERIM_DIR / "trait_value_table_prototype.tsv", value_rows, VALUE_TABLE_FIELDS)
    write_tsv(INTERIM_DIR / "trait_state_table_prototype.tsv", state_rows, STATE_TABLE_FIELDS)
    write_tsv(REPORT_DIR / "phenotype_sheet_summary.tsv", sheet_summary, SHEET_SUMMARY_FIELDS)
    write_tsv(REPORT_DIR / "v0_1_trait_recommendation.tsv", rec_rows, RECOMMENDATION_FIELDS)
    write_recommendation_md(REPORT_DIR / "v0_1_trait_recommendation.md", rec_rows, metadata_rows)
    write_main_report(
        REPORT_DIR / "trait_state_prototype_report.md",
        high_conf_rows,
        high_conf_summary,
        sheet_summary,
        trait_stats,
        rec_rows,
        missing_source_rows,
    )
    write_config()

    non_metadata = [row for row in trait_stats if row["trait_type_guess"] != "id_or_metadata"]
    continuous = [row for row in non_metadata if row["trait_type_guess"] == "continuous"]
    categorical = [row for row in non_metadata if row["trait_type_guess"] == "categorical"]
    binary = [row for row in non_metadata if row["trait_type_guess"] == "binary"]
    recommended = [row for row in rec_rows if row["recommended_for_v0_1"] == "true"]
    print(f"high_confidence_accessions={len(high_conf_rows)}")
    print(f"snp_indel_trait_accessions={sum(1 for row in high_conf_rows if row['usable_for_snp_indel_trait'] == 'true')}")
    print(f"traits_non_metadata={len(non_metadata)}")
    print(f"traits_continuous={len(continuous)}")
    print(f"traits_categorical={len(categorical)}")
    print(f"traits_binary={len(binary)}")
    print(f"recommended_v0_1_traits={len(recommended)}")
    print("trait_state_is_condition_signal=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
