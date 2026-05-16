#!/usr/bin/env python3
"""Build a conservative draft accession mapping table for 3K Rice."""

from __future__ import annotations

import csv
import gzip
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


RAW_ROOT = Path("data/raw")
INTERIM_DIR = Path("data/interim/accession_mapping")
REPORT_DIR = Path("reports/accession_mapping")

NS_MAIN = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

INPUT_SPECS = {
    "core_fam": ("data/raw/variants/snp/core_v0.7.fam.gz", ["core_v0.7", "fam"]),
    "indel_fam": ("data/raw/variants/indel/Nipponbare_indel.fam.gz", ["nipponbare_indel", "fam"]),
    "pruned_fam": ("data/raw/variants/snp/pruned_v2.1/pruned_v2.1.fam", ["pruned_v2.1", "fam"]),
    "qmatrix": ("data/raw/metadata/Qmatrix-k9-3kRG.csv", ["qmatrix", "3krg"]),
    "three_k_list": ("data/raw/accessions/snpseek/3K_list_sra_ids.txt", ["3k_list", "sra"]),
    "genesys": ("data/raw/accessions/genesys/genesys_3k_mcpd_passport.xlsx", ["genesys", "mcpd"]),
    "runinfo": ("data/raw/accessions/ncbi_prjeb6180/PRJEB6180_runinfo.csv", ["prjeb6180", "runinfo"]),
    "phenotype": ("data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx", ["phenotypedata", "xlsx"]),
}

MASTER_FIELDS = [
    "internal_accession_id",
    "genotype_sample_id",
    "snp_core_available",
    "indel_available",
    "pruned_snp_available",
    "qmatrix_available",
    "three_k_dna_iris_unique_id",
    "genetic_stock_varname",
    "normalized_stock_name",
    "stock_name_before_double_colon",
    "parsed_irgc_id",
    "country_origin",
    "sra_accession",
    "run_accessions",
    "experiment_accessions",
    "biosample_ids",
    "library_names",
    "genesys_accenumb",
    "genesys_accename",
    "genesys_origcty",
    "genesys_subtaxa",
    "genesys_doi",
    "genesys_url",
    "phenotype_match_count",
    "best_phenotype_sheet",
    "best_phenotype_row_id",
    "best_phenotype_stock_id",
    "best_phenotype_gs_accno",
    "best_phenotype_name",
    "best_phenotype_source_accno",
    "genotype_mapping_confidence",
    "phenotype_mapping_confidence",
    "mapping_rule",
    "manual_review_flag",
    "usable_for_trait_mapping",
    "notes",
]

GENOTYPE_FIELDS = [
    "genotype_sample_id",
    "snp_core_available",
    "indel_available",
    "pruned_snp_available",
    "qmatrix_available",
    "qmatrix_id",
    "subgroup_max",
    "subgroup_max_prob",
    "source_sets",
    "notes",
]

PHENO_FIELDS = [
    "sheet_name",
    "row_id",
    "stock_id",
    "gs_accno",
    "name",
    "source_accno",
    "raw_accession_value",
    "accession_column",
    "normalized_value",
    "parsed_irgc_id",
    "normalized_name",
    "notes",
]

MATCH_FIELDS = [
    "phenotype_sheet",
    "phenotype_row_id",
    "phenotype_column",
    "phenotype_raw_value",
    "phenotype_normalized_value",
    "candidate_genotype_sample_id",
    "candidate_3k_id",
    "candidate_stock_name",
    "candidate_irgc_id",
    "match_rule",
    "match_confidence",
    "manual_review_flag",
    "notes",
]

REVIEW_FIELDS = [
    "review_id",
    "issue_type",
    "genotype_sample_id",
    "phenotype_sheet",
    "phenotype_row_id",
    "candidate_values",
    "reason",
    "recommended_action",
    "notes",
]

SOURCE_FIELDS = ["source_name", "file_path", "exists", "n_records", "key_columns", "role", "notes"]
COVERAGE_FIELDS = ["metric", "n", "denominator", "percent", "notes"]
CONFIDENCE_FIELDS = ["mapping_type", "confidence", "n", "denominator", "percent", "usable_for_trait_mapping", "notes"]

COUNTRY_TO_CODE = {
    "BANGLADESH": "BGD",
    "CAMBODIA": "KHM",
    "CHINA": "CHN",
    "INDIA": "IND",
    "INDONESIA": "IDN",
    "JAPAN": "JPN",
    "KOREA": "KOR",
    "LAO_PEOPLE'S_DEMOCRATIC_REPUBLIC": "LAO",
    "LAOS": "LAO",
    "MALAYSIA": "MYS",
    "MYANMAR": "MMR",
    "NEPAL": "NPL",
    "PAKISTAN": "PAK",
    "PHILIPPINES": "PHL",
    "SRI_LANKA": "LKA",
    "TAIWAN": "TWN",
    "THAILAND": "THA",
    "VIETNAM": "VNM",
}


def ensure_dirs() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


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


def compact(values: Iterable[object], limit: int = 40, sep: str = ";") -> str:
    seen: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    if len(seen) <= limit:
        return sep.join(seen)
    return sep.join(seen[:limit]) + f"{sep}...(+{len(seen) - limit})"


def basic_normalize(value: object) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"[\s\-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def normalize_loose(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", "", basic_normalize(value))


def parse_irgc(value: object) -> str:
    text = str(value or "").upper()
    match = re.search(r"IRGC[\s_:-]*(\d+)", text)
    if match:
        return f"IRGC_{int(match.group(1))}"
    stripped = str(value or "").strip()
    if re.fullmatch(r"\d{3,6}", stripped):
        return f"IRGC_{int(stripped)}"
    return ""


def stock_name_before_double_colon(value: object) -> str:
    text = str(value or "")
    return text.split("::", 1)[0].strip()


def stock_name_without_irgc_suffix(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"::\s*IRGC[\s_:-]*\d+(?:[-_]\d+)?\s*$", "", text, flags=re.I)
    text = re.sub(r"\bIRGC[\s_:-]*\d+(?:[-_]\d+)?\b", "", text, flags=re.I)
    return text.strip(": _-")


def normalized_stock_name(value: object) -> str:
    return basic_normalize(stock_name_without_irgc_suffix(value))


def is_three_k_id(value: object) -> bool:
    text = basic_normalize(value)
    return bool(re.fullmatch(r"B\d{3,4}", text) or re.fullmatch(r"CX\d+", text) or re.fullmatch(r"IRIS_\d+_\d+", text.replace("-", "_")))


def normalize_country(value: object) -> str:
    text = basic_normalize(value)
    if len(text) == 3 and text.isalpha():
        return text
    return COUNTRY_TO_CODE.get(text, text)


def find_file(expected: str, tokens: list[str]) -> Path:
    path = Path(expected)
    if path.exists():
        return path
    lowered = [token.lower() for token in tokens]
    for candidate in sorted(RAW_ROOT.rglob("*")):
        if candidate.is_file() and all(token in str(candidate).lower() for token in lowered):
            return candidate
    raise FileNotFoundError(f"cannot find input file for {expected}")


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="")
    return path.open("r", encoding="utf-8", errors="replace", newline="")


def read_fam_ids(path: Path) -> list[str]:
    ids: list[str] = []
    with open_text(path) as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) >= 2:
                ids.append(parts[1])
    return ids


def read_qmatrix(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            sample_id = row.get("id", "") or next(iter(row.values()), "")
            rows[sample_id] = row
    return rows


def subgroup_for(row: dict[str, str]) -> tuple[str, str]:
    best_name = ""
    best_value = -1.0
    for key, value in row.items():
        if key == "id":
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric > best_value:
            best_name = key
            best_value = numeric
    return best_name, f"{best_value:.6f}" if best_value >= 0 else ""


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
    for item in root.findall("x:si", NS_MAIN):
        strings.append("".join(node.text or "" for node in item.findall(".//x:t", NS_MAIN)))
    return strings


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", NS_MAIN)).strip()
    value_node = cell.find("x:v", NS_MAIN)
    value = value_node.text if value_node is not None else ""
    if cell_type == "s" and value:
        try:
            return shared_strings[int(value)].strip()
        except (ValueError, IndexError):
            return value.strip()
    return str(value or "").strip()


def sheet_paths(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rid_to_target: dict[str, str] = {}
    for rel in rels.findall("r:Relationship", NS_REL):
        target = rel.attrib.get("Target", "")
        rid_to_target[rel.attrib.get("Id", "")] = target.lstrip("/") if target.startswith("/") else "xl/" + target
    paths: list[tuple[str, str]] = []
    for sheet in workbook.findall(".//x:sheet", NS_MAIN):
        rid = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        if rid in rid_to_target:
            paths.append((sheet.attrib.get("name", "unknown"), rid_to_target[rid]))
    return paths


def read_xlsx_sheets(path: Path) -> list[tuple[str, list[list[str]]]]:
    out: list[tuple[str, list[list[str]]]] = []
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        for sheet_name, sheet_path in sheet_paths(zf):
            root = ET.fromstring(zf.read(sheet_path))
            rows: list[list[str]] = []
            for row in root.findall(".//x:sheetData/x:row", NS_MAIN):
                values: list[str] = []
                for cell in row.findall("x:c", NS_MAIN):
                    idx = col_index(cell.attrib.get("r", ""))
                    while len(values) <= idx:
                        values.append("")
                    values[idx] = cell_value(cell, shared)
                while values and values[-1] == "":
                    values.pop()
                if any(values):
                    rows.append(values)
            out.append((sheet_name, rows))
    return out


def row_to_dict(headers: list[str], row: list[str]) -> dict[str, str]:
    return {header: row[idx] if idx < len(row) else "" for idx, header in enumerate(headers)}


def read_three_k_list(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            raw_id = row.get("3K_DNA_IRIS_UNIQUE_ID", "")
            norm_id = basic_normalize(raw_id)
            stock = row.get("Genetic_Stock_varname", "")
            rows[norm_id] = {
                "three_k_dna_iris_unique_id": raw_id,
                "normalized_3k_id": norm_id,
                "genetic_stock_varname": stock,
                "normalized_stock_name": normalized_stock_name(stock),
                "stock_name_before_double_colon": basic_normalize(stock_name_before_double_colon(stock)),
                "parsed_irgc_id": parse_irgc(stock),
                "country_origin": row.get("Country_Origin_updated", ""),
                "sra_accession": row.get("SRA Accession", ""),
            }
    return rows


def read_runinfo(path: Path) -> dict[str, dict[str, str]]:
    grouped: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sample = row.get("Sample", "")
            if not sample:
                continue
            for source, target in (
                ("Run", "run_accessions"),
                ("Experiment", "experiment_accessions"),
                ("BioSample", "biosample_ids"),
                ("LibraryName", "library_names"),
            ):
                value = row.get(source, "")
                if value:
                    grouped[sample][target].append(value)
    return {sample: {key: compact(values) for key, values in values_by_key.items()} for sample, values_by_key in grouped.items()}


def read_genesys(path: Path) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    rows: list[dict[str, str]] = []
    by_irgc: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for sheet_name, sheet_rows in read_xlsx_sheets(path):
        if sheet_name != "MCPD" or not sheet_rows:
            continue
        headers = sheet_rows[0]
        for row in sheet_rows[1:]:
            item = row_to_dict(headers, row)
            accenumb = item.get("ACCENUMB", "")
            accename = item.get("ACCENAME", "")
            item["genesys_parsed_irgc_id"] = parse_irgc(accenumb) or parse_irgc(accename)
            item["genesys_normalized_name"] = normalized_stock_name(accename)
            item["genesys_url"] = item.get("ACCEURL", "")
            rows.append(item)
            if item["genesys_parsed_irgc_id"]:
                by_irgc[item["genesys_parsed_irgc_id"]].append(item)
            if item["genesys_normalized_name"]:
                by_name[item["genesys_normalized_name"]].append(item)
    return rows, by_irgc, by_name


def phenotype_candidate_columns(headers: list[str]) -> list[int]:
    exact = {"STOCK_ID", "GS_ACCNO", "NAME", "SOURCE_ACCNO"}
    tokens = ("stock", "acc", "accno", "name", "source", "iris", "irgc")
    cols: list[int] = []
    for idx, header in enumerate(headers):
        norm = basic_normalize(header)
        lower = header.lower()
        if norm in exact or any(token in lower for token in tokens):
            cols.append(idx)
    return cols


def value_at(row: list[str], idx: int) -> str:
    return row[idx] if idx < len(row) else ""


def get_by_header(row_map: dict[str, str], *names: str) -> str:
    normalized = {basic_normalize(key): value for key, value in row_map.items()}
    for name in names:
        value = normalized.get(basic_normalize(name), "")
        if value:
            return value
    return ""


def read_phenotype_candidates(path: Path) -> tuple[list[dict[str, object]], dict[tuple[str, str], dict[str, str]]]:
    candidates: list[dict[str, object]] = []
    row_context: dict[tuple[str, str], dict[str, str]] = {}
    for sheet_name, rows in read_xlsx_sheets(path):
        if not rows:
            continue
        headers = rows[0]
        col_indices = phenotype_candidate_columns(headers)
        if not col_indices:
            continue
        for offset, row in enumerate(rows[1:], start=2):
            row_map = row_to_dict(headers, row)
            stock_id = get_by_header(row_map, "STOCK_ID")
            gs_accno = get_by_header(row_map, "GS_ACCNO")
            name = get_by_header(row_map, "NAME")
            source_accno = get_by_header(row_map, "Source_Accno", "SOURCE_ACCNO")
            key = (sheet_name, str(offset))
            row_context[key] = {
                "sheet_name": sheet_name,
                "row_id": str(offset),
                "stock_id": stock_id,
                "gs_accno": gs_accno,
                "name": name,
                "source_accno": source_accno,
            }
            for idx in col_indices:
                raw = value_at(row, idx)
                if raw == "":
                    continue
                column = headers[idx] if idx < len(headers) else f"col_{idx + 1}"
                parsed_irgc = parse_irgc(raw)
                if not parsed_irgc and basic_normalize(column) == "SOURCE_ACCNO" and re.fullmatch(r"\d{3,6}", str(raw).strip()):
                    parsed_irgc = f"IRGC_{int(str(raw).strip())}"
                candidates.append(
                    {
                        "sheet_name": sheet_name,
                        "row_id": offset,
                        "stock_id": stock_id,
                        "gs_accno": gs_accno,
                        "name": name,
                        "source_accno": source_accno,
                        "raw_accession_value": raw,
                        "accession_column": column,
                        "normalized_value": basic_normalize(raw),
                        "parsed_irgc_id": parsed_irgc,
                        "normalized_name": normalized_stock_name(raw),
                        "notes": "accession-like phenotype field only; not trait_value_table",
                    }
                )
    return candidates, row_context


def build_genotype_samples(core_ids: list[str], indel_ids: list[str], pruned_ids: list[str], qmatrix: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    core_set = set(core_ids)
    indel_set = set(indel_ids)
    pruned_set = set(pruned_ids)
    qmatrix_set = set(qmatrix)
    rows: list[dict[str, object]] = []
    for sample_id in sorted(core_set | indel_set | pruned_set | qmatrix_set):
        qrow = qmatrix.get(sample_id, {})
        subgroup, subgroup_prob = subgroup_for(qrow) if qrow else ("", "")
        sources = []
        if sample_id in core_set:
            sources.append("core_snp")
        if sample_id in indel_set:
            sources.append("indel")
        if sample_id in pruned_set:
            sources.append("pruned_snp")
        if sample_id in qmatrix_set:
            sources.append("qmatrix")
        rows.append(
            {
                "genotype_sample_id": sample_id,
                "snp_core_available": "yes" if sample_id in core_set else "no",
                "indel_available": "yes" if sample_id in indel_set else "no",
                "pruned_snp_available": "yes" if sample_id in pruned_set else "no",
                "qmatrix_available": "yes" if sample_id in qmatrix_set else "no",
                "qmatrix_id": qrow.get("id", ""),
                "subgroup_max": subgroup,
                "subgroup_max_prob": subgroup_prob,
                "source_sets": compact(sources),
                "notes": "genotype sample source union",
            }
        )
    return rows


def choose_genesys_match(three_k_row: dict[str, str], by_irgc: dict[str, list[dict[str, str]]], by_name: dict[str, list[dict[str, str]]]) -> tuple[dict[str, str], str, bool]:
    irgc = three_k_row.get("parsed_irgc_id", "")
    name = three_k_row.get("normalized_stock_name", "")
    if irgc and by_irgc.get(irgc):
        matches = by_irgc[irgc]
        return matches[0], "genesys_irgc", len(matches) > 1
    if name and by_name.get(name):
        matches = by_name[name]
        manual = True
        if irgc and any(match.get("genesys_parsed_irgc_id") and match.get("genesys_parsed_irgc_id") != irgc for match in matches):
            manual = True
        return matches[0], "genesys_name", manual
    return {}, "", False


def match_confidence_for_genotype(sample_id: str, three_k_row: dict[str, str], run_row: dict[str, str]) -> str:
    if three_k_row and run_row:
        return "A"
    if three_k_row:
        return "B"
    return "D"


def confidence_rank(value: str) -> int:
    return {"A": 4, "B": 3, "C": 2, "D": 1}.get(value, 0)


def add_index(index: dict[str, set[str]], key: str, sample_id: str) -> None:
    if key:
        index[key].add(sample_id)


def build_match_indexes(master_seed: dict[str, dict[str, object]]) -> dict[str, dict[str, set[str]]]:
    indexes = {
        "exact_3k_id": defaultdict(set),
        "exact_sra_accession": defaultdict(set),
        "exact_irgc_id": defaultdict(set),
        "normalized_stock_name": defaultdict(set),
        "stock_name_before_double_colon": defaultdict(set),
    }
    for sample_id, row in master_seed.items():
        add_index(indexes["exact_3k_id"], basic_normalize(sample_id), sample_id)
        add_index(indexes["exact_3k_id"], basic_normalize(row.get("three_k_dna_iris_unique_id", "")), sample_id)
        add_index(indexes["exact_sra_accession"], basic_normalize(row.get("sra_accession", "")), sample_id)
        add_index(indexes["exact_irgc_id"], str(row.get("parsed_irgc_id", "")), sample_id)
        add_index(indexes["normalized_stock_name"], str(row.get("normalized_stock_name", "")), sample_id)
        add_index(indexes["stock_name_before_double_colon"], str(row.get("stock_name_before_double_colon", "")), sample_id)
    return indexes


def candidate_matches_for_phenotype(candidates: list[dict[str, object]], master_seed: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    indexes = build_match_indexes(master_seed)
    rule_conf = {
        "exact_3k_id": "A",
        "exact_sra_accession": "B",
        "exact_irgc_id": "B",
        "exact_gs_accno": "B",
        "normalized_stock_name": "C",
        "stock_name_before_double_colon": "C",
    }
    matches: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for candidate in candidates:
        raw = str(candidate.get("raw_accession_value", ""))
        norm = str(candidate.get("normalized_value", ""))
        parsed_irgc = str(candidate.get("parsed_irgc_id", ""))
        name = str(candidate.get("normalized_name", ""))
        before_colon = basic_normalize(stock_name_before_double_colon(raw))
        lookups = [
            ("exact_3k_id", norm),
            ("exact_sra_accession", norm),
            ("exact_irgc_id", parsed_irgc),
            ("exact_gs_accno", norm if basic_normalize(candidate.get("accession_column", "")) == "GS_ACCNO" else ""),
            ("normalized_stock_name", name),
            ("stock_name_before_double_colon", before_colon),
        ]
        for rule, key in lookups:
            if not key:
                continue
            for sample_id in indexes.get(rule, {}).get(key, set()):
                row = master_seed[sample_id]
                unique_key = (
                    str(candidate["sheet_name"]),
                    str(candidate["row_id"]),
                    str(candidate["accession_column"]),
                    sample_id,
                    rule,
                )
                if unique_key in seen:
                    continue
                seen.add(unique_key)
                confidence = rule_conf[rule]
                matches.append(
                    {
                        "phenotype_sheet": candidate["sheet_name"],
                        "phenotype_row_id": candidate["row_id"],
                        "phenotype_column": candidate["accession_column"],
                        "phenotype_raw_value": raw,
                        "phenotype_normalized_value": norm,
                        "candidate_genotype_sample_id": sample_id,
                        "candidate_3k_id": row.get("three_k_dna_iris_unique_id", ""),
                        "candidate_stock_name": row.get("genetic_stock_varname", ""),
                        "candidate_irgc_id": row.get("parsed_irgc_id", ""),
                        "match_rule": rule,
                        "match_confidence": confidence,
                        "manual_review_flag": "true" if confidence == "C" else "false",
                        "notes": "C confidence name-based matches cannot enter formal trait mapping without manual review",
                    }
                )
    matches.sort(key=lambda row: (str(row["phenotype_sheet"]), int(row["phenotype_row_id"]), str(row["candidate_genotype_sample_id"]), str(row["match_rule"])))
    return matches


def best_phenotype_match(matches: list[dict[str, object]], row_context: dict[tuple[str, str], dict[str, str]]) -> dict[str, dict[str, object]]:
    by_sample: dict[str, list[dict[str, object]]] = defaultdict(list)
    for match in matches:
        by_sample[str(match["candidate_genotype_sample_id"])].append(match)
    best: dict[str, dict[str, object]] = {}
    for sample_id, sample_matches in by_sample.items():
        sorted_matches = sorted(
            sample_matches,
            key=lambda row: (-confidence_rank(str(row["match_confidence"])), str(row["match_rule"]), str(row["phenotype_sheet"]), int(row["phenotype_row_id"])),
        )
        match = sorted_matches[0]
        context = row_context.get((str(match["phenotype_sheet"]), str(match["phenotype_row_id"])), {})
        best[sample_id] = {**match, **context, "phenotype_match_count": len(sample_matches)}
    return best


def build_manual_review(matches: list[dict[str, object]], master_seed: dict[str, dict[str, object]], row_context: dict[tuple[str, str], dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    review_id = 1
    seen_reviews: set[tuple[str, str, str, str, str, str]] = set()

    def add(issue_type: str, genotype_sample_id: str, phenotype_sheet: str, phenotype_row_id: str, values: str, reason: str, action: str, notes: str = "") -> None:
        nonlocal review_id
        notes = notes or "manual_review_required"
        key = (issue_type, genotype_sample_id, phenotype_sheet, phenotype_row_id, values, reason)
        if key in seen_reviews:
            return
        seen_reviews.add(key)
        rows.append(
            {
                "review_id": f"REVIEW_{review_id:05d}",
                "issue_type": issue_type,
                "genotype_sample_id": genotype_sample_id,
                "phenotype_sheet": phenotype_sheet,
                "phenotype_row_id": phenotype_row_id,
                "candidate_values": values,
                "reason": reason,
                "recommended_action": action,
                "notes": notes,
            }
        )
        review_id += 1

    by_pheno: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    by_genotype: dict[str, list[dict[str, object]]] = defaultdict(list)
    for match in matches:
        by_pheno[(str(match["phenotype_sheet"]), str(match["phenotype_row_id"]))].append(match)
        by_genotype[str(match["candidate_genotype_sample_id"])].append(match)
        if match["match_confidence"] == "C":
            add(
                "name_match_only",
                str(match["candidate_genotype_sample_id"]),
                str(match["phenotype_sheet"]),
                str(match["phenotype_row_id"]),
                str(match["phenotype_raw_value"]),
                "只有 normalized stock name / before-colon name 匹配，缺少 ID 级证据。",
                "人工核对名称、IRGC、country 和 source accession；通过前不得进入 trait_value_table。",
                "C confidence",
            )
        if match["match_rule"] == "exact_irgc_id":
            context = row_context.get((str(match["phenotype_sheet"]), str(match["phenotype_row_id"])), {})
            pheno_name = normalized_stock_name(context.get("name", ""))
            geno_name = str(master_seed[str(match["candidate_genotype_sample_id"])].get("normalized_stock_name", ""))
            if pheno_name and geno_name and pheno_name != geno_name:
                add(
                    "same_irgc_different_name",
                    str(match["candidate_genotype_sample_id"]),
                    str(match["phenotype_sheet"]),
                    str(match["phenotype_row_id"]),
                    f"phenotype_name={context.get('name', '')}; genotype_name={match['candidate_stock_name']}",
                    "IRGC 一致但名称不一致。",
                    "优先保留 IRGC match，但人工检查同义名和来源。",
                )

    for (sheet, row_id), pheno_matches in by_pheno.items():
        sample_ids = sorted({str(match["candidate_genotype_sample_id"]) for match in pheno_matches})
        if len(sample_ids) > 1:
            add(
                "phenotype_row_matches_multiple_genotypes",
                compact(sample_ids, 20),
                sheet,
                row_id,
                compact([str(match["phenotype_raw_value"]) for match in pheno_matches], 20),
                "同一个 phenotype 行匹配多个 genotype sample。",
                "人工确定是否为同义 accession、重复记录或低置信名称冲突。",
            )

    for sample_id, genotype_matches in by_genotype.items():
        phenotype_rows = sorted({f"{match['phenotype_sheet']}:{match['phenotype_row_id']}" for match in genotype_matches})
        if len(phenotype_rows) > 1:
            add(
                "genotype_matches_multiple_phenotype_rows",
                sample_id,
                "",
                "",
                compact(phenotype_rows, 30),
                "同一个 genotype sample 匹配多个 phenotype 行。",
                "人工判断是否为多年/重复 phenotype 记录，构建 trait_state 前必须定义聚合策略。",
            )

    for sample_id, row in master_seed.items():
        genesys_country = normalize_country(row.get("genesys_origcty", ""))
        three_k_country = normalize_country(row.get("country_origin", ""))
        if genesys_country and three_k_country and genesys_country != three_k_country:
            add(
                "genesys_country_differs_from_3k_list",
                sample_id,
                "",
                "",
                f"3K={row.get('country_origin', '')}; Genesys={row.get('genesys_origcty', '')}",
                "Genesys 和 3K_list 的国家字段不同。",
                "人工检查国家编码、来源字段和 accession 同名异物风险。",
            )
        if row.get("genesys_match_rule") == "genesys_name":
            genesys_irgc = str(row.get("genesys_parsed_irgc_id", ""))
            genotype_irgc = str(row.get("parsed_irgc_id", ""))
            if genesys_irgc and genotype_irgc and genesys_irgc != genotype_irgc:
                add(
                    "same_name_different_irgc",
                    sample_id,
                    "",
                    "",
                    f"3K_IRGC={genotype_irgc}; Genesys_IRGC={genesys_irgc}; name={row.get('normalized_stock_name', '')}",
                    "名称一致但 IRGC 不一致。",
                    "不要自动合并；需要人工确认 accession identity。",
                )
    return rows


def confidence_coverage_rows(master_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    genotype_counts = Counter(str(row["genotype_mapping_confidence"]) for row in master_rows)
    phenotype_counts = Counter(str(row["phenotype_mapping_confidence"]) for row in master_rows)
    total = len(master_rows)
    rows: list[dict[str, object]] = []
    for mapping_type, counts in (("genotype", genotype_counts), ("phenotype", phenotype_counts)):
        for conf in ("A", "B", "C", "D"):
            n = counts.get(conf, 0)
            rows.append(
                {
                    "mapping_type": mapping_type,
                    "confidence": conf,
                    "n": n,
                    "denominator": total,
                    "percent": f"{(n / total * 100) if total else 0:.2f}",
                    "usable_for_trait_mapping": "yes" if mapping_type == "phenotype" and conf in {"A", "B"} else "no",
                    "notes": "A/B phenotype mapping can be used for formal trait mapping; C requires manual review; D is unmatched",
                }
            )
    return rows


def coverage_percent(numerator: int, denominator: int) -> str:
    return f"{(numerator / denominator * 100) if denominator else 0:.2f}"


def write_reports(
    paths: dict[str, Path],
    source_rows: list[dict[str, object]],
    genotype_rows: list[dict[str, object]],
    master_rows: list[dict[str, object]],
    matches: list[dict[str, object]],
    manual_rows: list[dict[str, object]],
    three_k_rows: dict[str, dict[str, str]],
    runinfo: dict[str, dict[str, str]],
    genesys_rows: list[dict[str, str]],
    phenotype_candidates: list[dict[str, object]],
) -> None:
    total = len(genotype_rows)
    core = sum(1 for row in genotype_rows if row["snp_core_available"] == "yes")
    indel = sum(1 for row in genotype_rows if row["indel_available"] == "yes")
    pruned = sum(1 for row in genotype_rows if row["pruned_snp_available"] == "yes")
    qmatrix = sum(1 for row in genotype_rows if row["qmatrix_available"] == "yes")
    core_set = {str(row["genotype_sample_id"]) for row in genotype_rows if row["snp_core_available"] == "yes"}
    indel_set = {str(row["genotype_sample_id"]) for row in genotype_rows if row["indel_available"] == "yes"}
    pruned_set = {str(row["genotype_sample_id"]) for row in genotype_rows if row["pruned_snp_available"] == "yes"}
    qmatrix_set = {str(row["genotype_sample_id"]) for row in genotype_rows if row["qmatrix_available"] == "yes"}
    exact_three_k = sum(1 for row in master_rows if row.get("three_k_dna_iris_unique_id"))
    runinfo_matched = sum(1 for row in master_rows if row.get("run_accessions"))
    genesys_matched = sum(1 for row in master_rows if row.get("genesys_accenumb"))
    phenotype_matched = sum(1 for row in master_rows if row.get("phenotype_mapping_confidence") != "D")
    usable = sum(1 for row in master_rows if row.get("usable_for_trait_mapping") == "true")

    genotype_coverage = [
        {"metric": "genotype_union_samples", "n": total, "denominator": total, "percent": "100.00", "notes": "union of core SNP, indel, pruned SNP and Qmatrix IDs"},
        {"metric": "core_snp_samples", "n": core, "denominator": total, "percent": coverage_percent(core, total), "notes": "core_v0.7.fam.gz"},
        {"metric": "indel_samples", "n": indel, "denominator": total, "percent": coverage_percent(indel, total), "notes": "Nipponbare_indel.fam.gz"},
        {"metric": "pruned_snp_samples", "n": pruned, "denominator": total, "percent": coverage_percent(pruned, total), "notes": "pruned_v2.1.fam"},
        {"metric": "qmatrix_samples", "n": qmatrix, "denominator": total, "percent": coverage_percent(qmatrix, total), "notes": "Qmatrix-k9-3kRG.csv"},
        {"metric": "core_snp_intersect_indel", "n": len(core_set & indel_set), "denominator": len(core_set), "percent": coverage_percent(len(core_set & indel_set), len(core_set)), "notes": "intersection over core SNP sample set"},
        {"metric": "core_snp_intersect_qmatrix", "n": len(core_set & qmatrix_set), "denominator": len(core_set), "percent": coverage_percent(len(core_set & qmatrix_set), len(core_set)), "notes": "intersection over core SNP sample set"},
        {"metric": "core_snp_intersect_pruned_snp", "n": len(core_set & pruned_set), "denominator": len(core_set), "percent": coverage_percent(len(core_set & pruned_set), len(core_set)), "notes": "intersection over core SNP sample set"},
        {"metric": "exact_3k_list_match", "n": exact_three_k, "denominator": total, "percent": coverage_percent(exact_three_k, total), "notes": "genotype_sample_id exact match to 3K_DNA_IRIS_UNIQUE_ID"},
        {"metric": "runinfo_matched_by_sra_sample", "n": runinfo_matched, "denominator": total, "percent": coverage_percent(runinfo_matched, total), "notes": "3K_list SRA Accession matched to RunInfo Sample"},
        {"metric": "genesys_matched", "n": genesys_matched, "denominator": total, "percent": coverage_percent(genesys_matched, total), "notes": "matched through IRGC first, then normalized name"},
    ]
    write_tsv(REPORT_DIR / "genotype_mapping_coverage.tsv", genotype_coverage, COVERAGE_FIELDS)

    phenotype_coverage = [
        {"metric": "phenotype_accession_candidate_rows", "n": len(phenotype_candidates), "denominator": len(phenotype_candidates), "percent": "100.00", "notes": "accession-like field values, not trait values"},
        {"metric": "phenotype_candidate_matches", "n": len(matches), "denominator": len(phenotype_candidates), "percent": coverage_percent(len(matches), len(phenotype_candidates)), "notes": "all candidate matches, including C-level name matches"},
        {"metric": "genotype_samples_with_any_phenotype_match", "n": phenotype_matched, "denominator": total, "percent": coverage_percent(phenotype_matched, total), "notes": "A/B/C phenotype mapping"},
        {"metric": "genotype_samples_usable_for_trait_mapping", "n": usable, "denominator": total, "percent": coverage_percent(usable, total), "notes": "only A/B phenotype mapping"},
        {"metric": "manual_review_candidates", "n": len(manual_rows), "denominator": len(matches), "percent": coverage_percent(len(manual_rows), len(matches)), "notes": "review rows can exceed unique candidate matches because multiple issue types may apply"},
    ]
    write_tsv(REPORT_DIR / "phenotype_mapping_coverage.tsv", phenotype_coverage, COVERAGE_FIELDS)
    write_tsv(REPORT_DIR / "mapping_confidence_summary.tsv", confidence_coverage_rows(master_rows), CONFIDENCE_FIELDS)
    write_tsv(REPORT_DIR / "accession_mapping_source_summary.tsv", source_rows, SOURCE_FIELDS)
    write_tsv(REPORT_DIR / "manual_review_candidates_preview.tsv", manual_rows[:200], REVIEW_FIELDS)

    geno_conf = Counter(str(row["genotype_mapping_confidence"]) for row in master_rows)
    pheno_conf = Counter(str(row["phenotype_mapping_confidence"]) for row in master_rows)
    text = f"""# Accession Mapping Summary

## 本次任务目标

本次任务只构建 `accession_mapping_master.tsv` 草稿，用于梳理 genotype sample ID、3K_list_sra_ids、NCBI RunInfo、Genesys MCPD 和 phenotype accession-like fields 的关系。该表不是正式 `accession_table`，不生成 `trait_value_table`，不训练模型，不做 `phenotype prediction`。

## 输入文件

- core SNP FAM：`{paths['core_fam']}`
- indel FAM：`{paths['indel_fam']}`
- pruned SNP FAM：`{paths['pruned_fam']}`
- Qmatrix：`{paths['qmatrix']}`
- 3K_list_sra_ids：`{paths['three_k_list']}`
- NCBI RunInfo：`{paths['runinfo']}`
- Genesys MCPD：`{paths['genesys']}`
- phenotype XLSX：`{paths['phenotype']}`

## Genotype 样本覆盖

genotype union 样本数为 {total}。core SNP 样本数 {core}，indel 样本数 {indel}，pruned SNP 样本数 {pruned}，Qmatrix 样本数 {qmatrix}。core SNP 与 indel 交集为 {len(core_set & indel_set)}，core SNP 与 Qmatrix 交集为 {len(core_set & qmatrix_set)}，core SNP 与 pruned SNP 交集为 {len(core_set & pruned_set)}。

## 3K_list_sra_ids 匹配

`genotype_sample_id` 精确匹配 `3K_DNA_IRIS_UNIQUE_ID` 的样本数为 {exact_three_k} / {total}。该文件是 B001 / CX / IRIS ID 到 stock name 与 SRA accession 的主桥梁。

## RunInfo 匹配

通过 `SRA Accession` ↔ RunInfo `Sample` 匹配到 RunInfo 的 genotype 样本数为 {runinfo_matched} / {total}。一个 SRA Sample 可以对应多个 Run，已在 master 中用分号合并 `run_accessions`、`experiment_accessions`、`biosample_ids` 和 `library_names`。

## Genesys MCPD 匹配

Genesys MCPD 匹配到 {genesys_matched} / {total} 个 genotype 样本。优先使用 IRGC ID 精确匹配，其次才使用 normalized stock name；名称匹配或国家字段冲突进入人工审查。

## Phenotype 匹配

phenotype accession-like candidate 数为 {len(phenotype_candidates)}，候选匹配记录数为 {len(matches)}。有任意 phenotype 匹配的 genotype 样本数为 {phenotype_matched} / {total}，其中 A/B 级可用于 trait mapping 的样本数为 {usable} / {total}。

## 置信度统计

genotype mapping：A={geno_conf.get('A', 0)}，B={geno_conf.get('B', 0)}，C={geno_conf.get('C', 0)}，D={geno_conf.get('D', 0)}。

phenotype mapping：A={pheno_conf.get('A', 0)}，B={pheno_conf.get('B', 0)}，C={pheno_conf.get('C', 0)}，D={pheno_conf.get('D', 0)}。

## 可用于 trait mapping 的样本数

当前 `usable_for_trait_mapping=true` 的样本数为 {usable}。只有 A/B 级 phenotype mapping 可以进入正式 trait_value_table。C 级 name match 只能人工复核，不能直接训练。

## 不能用于 trait mapping 的原因

不能直接用于 trait mapping 的主要原因包括：没有 phenotype accession-like 匹配、只有 normalized stock name 匹配、同一 phenotype 行或同一 genotype 样本存在多重匹配、IRGC 一致但名称不一致、Genesys 与 3K_list country 字段冲突。

## 是否可以进入正式 trait_value_table 构建

当前只能在 A/B 级 phenotype mapping 样本上试做小范围 trait_state prototype。正式 `trait_value_table` 仍需先审查 `manual_review_candidates.tsv`，确认重复 phenotype 记录的聚合策略，并冻结 `accession_mapping_master.tsv` 的高置信子集。

## 下一步建议

优先人工审查 `manual_review_candidates.tsv` 中的 C 级名称匹配和多重匹配；然后生成 high-confidence accession mapping 子集。若 A/B 级 phenotype mapping 覆盖足够，再构建 trait_state 和最小 Task 1 instances；若不足，先补充 accession ID mapping。
"""
    (REPORT_DIR / "accession_mapping_summary.md").write_text(text, encoding="utf-8")


def build_master() -> None:
    ensure_dirs()
    paths = {key: find_file(expected, tokens) for key, (expected, tokens) in INPUT_SPECS.items()}

    core_ids = read_fam_ids(paths["core_fam"])
    indel_ids = read_fam_ids(paths["indel_fam"])
    pruned_ids = read_fam_ids(paths["pruned_fam"])
    qmatrix = read_qmatrix(paths["qmatrix"])
    three_k_rows = read_three_k_list(paths["three_k_list"])
    runinfo = read_runinfo(paths["runinfo"])
    genesys_rows, genesys_by_irgc, genesys_by_name = read_genesys(paths["genesys"])
    phenotype_candidates, phenotype_context = read_phenotype_candidates(paths["phenotype"])

    genotype_rows = build_genotype_samples(core_ids, indel_ids, pruned_ids, qmatrix)
    master_seed: dict[str, dict[str, object]] = {}
    source_rows = [
        {"source_name": "core_v0.7.fam.gz", "file_path": paths["core_fam"], "exists": "yes", "n_records": len(core_ids), "key_columns": "FID,IID", "role": "SNP genotype sample IDs", "notes": "B001-style sample IDs"},
        {"source_name": "Nipponbare_indel.fam.gz", "file_path": paths["indel_fam"], "exists": "yes", "n_records": len(indel_ids), "key_columns": "FID,IID", "role": "indel genotype sample IDs", "notes": "B001-style sample IDs"},
        {"source_name": "pruned_v2.1.fam", "file_path": paths["pruned_fam"], "exists": "yes", "n_records": len(pruned_ids), "key_columns": "FID,IID", "role": "pruned SNP sample IDs", "notes": "B001-style sample IDs"},
        {"source_name": "Qmatrix-k9-3kRG.csv", "file_path": paths["qmatrix"], "exists": "yes", "n_records": len(qmatrix), "key_columns": "id,subgroup proportions", "role": "population structure and genotype ID support", "notes": "not phenotype target"},
        {"source_name": "3K_list_sra_ids.txt", "file_path": paths["three_k_list"], "exists": "yes", "n_records": len(three_k_rows), "key_columns": "3K_DNA_IRIS_UNIQUE_ID,Genetic_Stock_varname,Country_Origin_updated,SRA Accession", "role": "main ID bridge", "notes": "B/CX/IRIS to stock and SRA"},
        {"source_name": "PRJEB6180_runinfo.csv", "file_path": paths["runinfo"], "exists": "yes", "n_records": sum(len(v.get("run_accessions", "").split(";")) for v in runinfo.values()), "key_columns": "Run,Experiment,Sample,BioSample,LibraryName", "role": "SRA/BioSample/Run expansion", "notes": "grouped by Sample"},
        {"source_name": "Genesys MCPD", "file_path": paths["genesys"], "exists": "yes", "n_records": len(genesys_rows), "key_columns": "ACCENUMB,ACCENAME,ORIGCTY,SUBTAXA,DOI,ACCEURL", "role": "passport metadata", "notes": "IRGC/name matching only"},
        {"source_name": "3kRG phenotype XLSX", "file_path": paths["phenotype"], "exists": "yes", "n_records": len(phenotype_candidates), "key_columns": "STOCK_ID,GS_ACCNO,NAME,Source_Accno", "role": "phenotype accession-like candidates", "notes": "not trait_value_table"},
    ]

    for idx, genotype in enumerate(genotype_rows, start=1):
        sample_id = str(genotype["genotype_sample_id"])
        three_k = three_k_rows.get(basic_normalize(sample_id), {})
        sra = three_k.get("sra_accession", "")
        run_row = runinfo.get(sra, {})
        genesys, genesys_rule, genesys_manual = choose_genesys_match(three_k, genesys_by_irgc, genesys_by_name) if three_k else ({}, "", False)
        genotype_conf = match_confidence_for_genotype(sample_id, three_k, run_row)
        seed = {
            "internal_accession_id": f"ACC_{idx:04d}",
            **genotype,
            **three_k,
            "run_accessions": run_row.get("run_accessions", ""),
            "experiment_accessions": run_row.get("experiment_accessions", ""),
            "biosample_ids": run_row.get("biosample_ids", ""),
            "library_names": run_row.get("library_names", ""),
            "genesys_accenumb": genesys.get("ACCENUMB", ""),
            "genesys_accename": genesys.get("ACCENAME", ""),
            "genesys_origcty": genesys.get("ORIGCTY", ""),
            "genesys_subtaxa": genesys.get("SUBTAXA", ""),
            "genesys_doi": genesys.get("DOI", ""),
            "genesys_url": genesys.get("genesys_url", genesys.get("ACCEURL", "")),
            "genesys_parsed_irgc_id": genesys.get("genesys_parsed_irgc_id", ""),
            "genesys_match_rule": genesys_rule,
            "genesys_manual_review": genesys_manual,
            "genotype_mapping_confidence": genotype_conf,
        }
        master_seed[sample_id] = seed

    matches = candidate_matches_for_phenotype(phenotype_candidates, master_seed)
    best_matches = best_phenotype_match(matches, phenotype_context)

    master_rows: list[dict[str, object]] = []
    for sample_id in sorted(master_seed):
        seed = master_seed[sample_id]
        best = best_matches.get(sample_id, {})
        pheno_conf = str(best.get("match_confidence", "D"))
        if not best:
            pheno_conf = "D"
        manual = seed.get("genesys_manual_review", False) or pheno_conf == "C"
        mapping_rules = [str(seed.get("genesys_match_rule", "")), str(best.get("match_rule", ""))]
        notes = []
        if seed.get("genotype_mapping_confidence") == "D":
            notes.append("no exact 3K_list_sra_ids match")
        if pheno_conf == "C":
            notes.append("phenotype name match requires manual review")
        if pheno_conf == "D":
            notes.append("no phenotype accession match")
        row = {
            **seed,
            "phenotype_match_count": best.get("phenotype_match_count", 0),
            "best_phenotype_sheet": best.get("sheet_name", best.get("phenotype_sheet", "")),
            "best_phenotype_row_id": best.get("row_id", best.get("phenotype_row_id", "")),
            "best_phenotype_stock_id": best.get("stock_id", ""),
            "best_phenotype_gs_accno": best.get("gs_accno", ""),
            "best_phenotype_name": best.get("name", ""),
            "best_phenotype_source_accno": best.get("source_accno", ""),
            "phenotype_mapping_confidence": pheno_conf,
            "mapping_rule": compact(mapping_rules),
            "manual_review_flag": "true" if manual else "false",
            "usable_for_trait_mapping": "true" if pheno_conf in {"A", "B"} else "false",
            "notes": compact(notes),
        }
        master_rows.append(row)

    manual_rows = build_manual_review(matches, master_seed, phenotype_context)
    matched_pheno_keys = {(str(match["phenotype_sheet"]), str(match["phenotype_row_id"])) for match in matches}
    unmatched_pheno = [candidate for candidate in phenotype_candidates if (str(candidate["sheet_name"]), str(candidate["row_id"])) not in matched_pheno_keys]

    write_tsv(INTERIM_DIR / "genotype_sample_master.tsv", genotype_rows, GENOTYPE_FIELDS)
    write_tsv(INTERIM_DIR / "phenotype_accession_candidates.tsv", phenotype_candidates, PHENO_FIELDS)
    write_tsv(INTERIM_DIR / "phenotype_to_genotype_candidate_matches.tsv", matches, MATCH_FIELDS)
    write_tsv(INTERIM_DIR / "unmatched_phenotype_accessions.tsv", unmatched_pheno, PHENO_FIELDS)
    write_tsv(INTERIM_DIR / "manual_review_candidates.tsv", manual_rows, REVIEW_FIELDS)
    write_tsv(INTERIM_DIR / "accession_mapping_master.tsv", master_rows, MASTER_FIELDS)

    write_reports(paths, source_rows, genotype_rows, master_rows, matches, manual_rows, three_k_rows, runinfo, genesys_rows, phenotype_candidates)

    print(f"genotype_samples={len(genotype_rows)}")
    print(f"exact_3k_list_matches={sum(1 for row in master_rows if row.get('three_k_dna_iris_unique_id'))}")
    print(f"runinfo_matches={sum(1 for row in master_rows if row.get('run_accessions'))}")
    print(f"genesys_matches={sum(1 for row in master_rows if row.get('genesys_accenumb'))}")
    print(f"phenotype_matches={sum(1 for row in master_rows if row.get('phenotype_mapping_confidence') != 'D')}")
    print(f"usable_for_trait_mapping={sum(1 for row in master_rows if row.get('usable_for_trait_mapping') == 'true')}")
    print(f"manual_review_candidates={len(manual_rows)}")


def main() -> int:
    build_master()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
