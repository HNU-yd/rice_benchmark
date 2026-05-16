#!/usr/bin/env python3
"""Inspect 3K Rice phenotype XLSX without treating traits as prediction targets."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from inventory_utils import INTERIM_DIR, RAW_ROOT, REPORT_DIR, compact_list, ensure_dirs, unique_preserve, write_tsv


TRAIT_FIELDS = [
    "sheet_name",
    "n_rows",
    "n_cols",
    "columns",
    "candidate_accession_columns",
    "candidate_trait_columns",
    "n_candidate_accessions",
    "notes",
]
ACCESSION_FIELDS = ["source_file", "sheet_name", "accession_candidate", "accession_column", "row_id"]

NS_MAIN = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
NS_DOC_REL = {"r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def col_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref.upper())
    if not letters:
        return 0
    value = 0
    for char in letters.group(0):
        value = value * 26 + ord(char) - ord("A") + 1
    return value - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("x:si", NS_MAIN):
        texts = [node.text or "" for node in si.findall(".//x:t", NS_MAIN)]
        strings.append("".join(texts))
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
        rid = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        path = rid_to_target.get(rid)
        if path:
            sheets.append((name, path))
    return sheets


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", NS_MAIN)).strip()
    value_node = cell.find("x:v", NS_MAIN)
    value = value_node.text if value_node is not None else ""
    if cell_type == "s" and value != "":
        try:
            return shared_strings[int(value)].strip()
        except (ValueError, IndexError):
            return value.strip()
    return str(value or "").strip()


def read_sheet(zf: zipfile.ZipFile, path: str, shared_strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(zf.read(path))
    rows: list[list[str]] = []
    for row in root.findall(".//x:sheetData/x:row", NS_MAIN):
        values: list[str] = []
        for cell in row.findall("x:c", NS_MAIN):
            ref = cell.attrib.get("r", "")
            idx = col_index(ref)
            while len(values) <= idx:
                values.append("")
            values[idx] = cell_value(cell, shared_strings)
        while values and values[-1] == "":
            values.pop()
        rows.append(values)
    return rows


def candidate_accession_columns(headers: list[str], sheet_name: str) -> list[int]:
    if any(token in sheet_name.lower() for token in ("readme", "dictionary", "annotation", "sheet1")):
        return []
    strong_tokens = ("stock_id", "gs_accno", "source_accno", "accession", "accno", "iris", "sample", "variety")
    indices: list[int] = []
    for idx, header in enumerate(headers):
        lower = header.lower().strip()
        if lower == "name" or any(token in lower for token in strong_tokens):
            indices.append(idx)
    return indices[:6]


def inspect_workbook(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows_out: list[dict[str, object]] = []
    accession_rows: list[dict[str, object]] = []
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        for sheet_name, sheet_path in sheet_paths(zf):
            rows = read_sheet(zf, sheet_path, shared)
            non_empty_rows = [row for row in rows if any(cell != "" for cell in row)]
            headers = non_empty_rows[0] if non_empty_rows else []
            max_cols = max((len(row) for row in non_empty_rows), default=0)
            accession_col_indices = candidate_accession_columns(headers, sheet_name)
            accession_col_names = [headers[idx] if idx < len(headers) else f"col_{idx + 1}" for idx in accession_col_indices]
            trait_col_names: list[str] = []
            for idx in range(max_cols):
                if idx in accession_col_indices:
                    continue
                name = headers[idx] if idx < len(headers) and headers[idx] else f"col_{idx + 1}"
                non_missing = sum(1 for row in non_empty_rows[1:] if idx < len(row) and row[idx] != "")
                if non_missing:
                    trait_col_names.append(name)
            accession_values: set[str] = set()
            for row_idx, row in enumerate(non_empty_rows[1:], start=2):
                for idx, col_name in zip(accession_col_indices, accession_col_names):
                    if idx < len(row) and row[idx]:
                        accession_values.add(row[idx])
                        accession_rows.append(
                            {
                                "source_file": str(path),
                                "sheet_name": sheet_name,
                                "accession_candidate": row[idx],
                                "accession_column": col_name,
                                "row_id": row_idx,
                            }
                        )
            rows_out.append(
                {
                    "sheet_name": sheet_name,
                    "n_rows": len(non_empty_rows),
                    "n_cols": max_cols,
                    "columns": compact_list(headers, 80),
                    "candidate_accession_columns": compact_list(accession_col_names, 20),
                    "candidate_trait_columns": compact_list(trait_col_names, 80),
                    "n_candidate_accessions": len(accession_values),
                    "notes": "trait table is for trait_state construction only; not phenotype prediction",
                }
            )
    return rows_out, accession_rows


def main() -> int:
    ensure_dirs()
    rows: list[dict[str, object]] = []
    accession_rows: list[dict[str, object]] = []
    for path in sorted((RAW_ROOT / "traits").glob("*.xlsx")):
        sheet_rows, sheet_accessions = inspect_workbook(path)
        rows.extend(sheet_rows)
        accession_rows.extend(sheet_accessions)
    write_tsv(REPORT_DIR / "trait_table_inventory.tsv", rows, TRAIT_FIELDS)
    write_tsv(INTERIM_DIR / "trait_accessions.tsv", accession_rows, ACCESSION_FIELDS)
    print(f"trait_sheets={len(rows)}")
    print(f"trait_accession_candidates={len(unique_preserve(row['accession_candidate'] for row in accession_rows))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
