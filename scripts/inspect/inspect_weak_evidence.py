#!/usr/bin/env python3
"""Inspect Phase 3C weak localization evidence candidates."""

from __future__ import annotations

import csv
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from inventory_utils import compact_list, unique_preserve, write_tsv


REPORT_DIR = Path("reports/weak_evidence_inventory")
QTARO_INTERIM_DIR = Path("data/interim/evidence/qtaro")
ORYZABASE_INTERIM_DIR = Path("data/interim/evidence/oryzabase")

QTARO_ZIP = Path("data/raw/evidence/qtl/qtaro/qtaro_sjis.zip")
QTARO_MEMBER = "qtaro_sjis.csv"
QTARO_EXTRACTED = QTARO_INTERIM_DIR / QTARO_MEMBER
QTARO_UTF8 = QTARO_INTERIM_DIR / f"{QTARO_MEMBER}.utf8"

ORYZABASE_TSV = Path("data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv")


QTARO_INVENTORY_FIELDS = [
    "source_file",
    "extracted_file",
    "utf8_file",
    "encoding_source",
    "n_rows",
    "n_cols",
    "columns",
    "qtl_name_column",
    "trait_column",
    "major_category_column",
    "trait_category_column",
    "chr_column",
    "genome_start_column",
    "genome_end_column",
    "marker_column",
    "lod_column",
    "reference_column",
    "evidence_tier",
    "notes",
]

QTARO_TRAIT_FIELDS = [
    "major_category",
    "trait_category",
    "trait",
    "n_qtl_rows",
    "chrom_values",
    "example_qtl_names",
    "example_references",
    "evidence_tier",
    "notes",
]

ORYZABASE_INVENTORY_FIELDS = [
    "source_file",
    "appears_html",
    "n_rows",
    "n_cols",
    "columns",
    "gene_symbol_column",
    "gene_name_column",
    "trait_id_column",
    "trait_class_column",
    "rap_id_column",
    "msu_id_column",
    "chromosome_column",
    "trait_ontology_column",
    "plant_ontology_column",
    "gene_ontology_column",
    "evidence_tier",
    "notes",
]

ORYZABASE_TRAIT_FIELDS = [
    "trait_class",
    "n_gene_rows",
    "n_gene_symbols",
    "n_rap_ids",
    "n_msu_ids",
    "chrom_values",
    "example_gene_symbols",
    "example_rap_ids",
    "example_trait_ontology",
    "evidence_tier",
    "notes",
]

COLUMN_FIELDS = [
    "column_index",
    "column_name",
    "non_empty_count",
    "example_values",
    "role_guess",
    "notes",
]


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    QTARO_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    ORYZABASE_INTERIM_DIR.mkdir(parents=True, exist_ok=True)


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def cell(row: dict[str, str], column: str) -> str:
    return str(row.get(column, "") or "").strip()


def find_column(columns: Iterable[str], *candidates: str) -> str:
    normalized = {normalize_name(column): column for column in columns}
    for candidate in candidates:
        key = normalize_name(candidate)
        if key in normalized:
            return normalized[key]
    for column in columns:
        name = normalize_name(column)
        if any(normalize_name(candidate) in name for candidate in candidates):
            return column
    return ""


def guess_role(column: str) -> str:
    name = normalize_name(column)
    checks = [
        ("qtlname", "qtl_or_gene_name"),
        ("qtlgene", "qtl_or_gene_name"),
        ("genesymbol", "gene_symbol"),
        ("rapid", "rap_id"),
        ("msuid", "msu_id"),
        ("chromosomeno", "chromosome"),
        ("chr", "chromosome"),
        ("genomestart", "genome_start"),
        ("genomeend", "genome_end"),
        ("traitontology", "trait_ontology"),
        ("traitclass", "trait_class"),
        ("character", "trait_or_character"),
        ("reference", "reference"),
        ("lod", "lod_score"),
        ("marker", "marker"),
    ]
    for token, role in checks:
        if token in name:
            return role
    return "unclassified"


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    sample = text[:8192]
    dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        return list(reader.fieldnames or []), list(reader)


def read_tsv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def sample_values(rows: list[dict[str, str]], column: str, limit: int = 5) -> str:
    return compact_list(unique_preserve([cell(row, column) for row in rows], limit), limit)


def write_column_inventory(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    column_rows = []
    for index, column in enumerate(columns, start=1):
        values = [cell(row, column) for row in rows]
        column_rows.append(
            {
                "column_index": index,
                "column_name": column,
                "non_empty_count": sum(1 for value in values if value),
                "example_values": sample_values(rows, column),
                "role_guess": guess_role(column),
                "notes": "field inventory only; not a benchmark schema",
            }
        )
    write_tsv(path, column_rows, COLUMN_FIELDS)


def convert_qtaro_to_utf8() -> str:
    if not QTARO_ZIP.exists():
        raise FileNotFoundError(f"Q-TARO archive not found: {QTARO_ZIP}")
    with zipfile.ZipFile(QTARO_ZIP) as archive:
        if QTARO_MEMBER not in archive.namelist():
            raise FileNotFoundError(f"{QTARO_MEMBER} not found in {QTARO_ZIP}")
        raw_bytes = archive.read(QTARO_MEMBER)
    QTARO_EXTRACTED.write_bytes(raw_bytes)

    encoding_used = ""
    for encoding in ("shift_jis", "cp932", "utf-8"):
        try:
            text = raw_bytes.decode(encoding)
            encoding_used = encoding
            break
        except UnicodeDecodeError:
            continue
    if not encoding_used:
        text = raw_bytes.decode("shift_jis", errors="replace")
        encoding_used = "shift_jis_with_replacement"
    QTARO_UTF8.write_text(text, encoding="utf-8", newline="")
    return encoding_used


def inspect_qtaro() -> dict[str, object]:
    encoding_used = convert_qtaro_to_utf8()
    columns, rows = read_csv_rows(QTARO_UTF8)
    write_column_inventory(REPORT_DIR / "qtaro_columns.tsv", columns, rows)

    qtl_name_col = find_column(columns, "QTL/Gene", "QTL name", "qtl")
    trait_col = find_column(columns, "Character", "Trait")
    major_category_col = find_column(columns, "Major category")
    trait_category_col = find_column(columns, "Category of object character")
    chr_col = find_column(columns, "Chr", "chromosome")
    genome_start_col = find_column(columns, "Genome start")
    genome_end_col = find_column(columns, "Genome end")
    marker_col = find_column(columns, "Marker")
    lod_col = find_column(columns, "LOD")
    reference_col = find_column(columns, "Reference")

    inventory_row = {
        "source_file": str(QTARO_ZIP),
        "extracted_file": str(QTARO_EXTRACTED),
        "utf8_file": str(QTARO_UTF8),
        "encoding_source": encoding_used,
        "n_rows": len(rows),
        "n_cols": len(columns),
        "columns": compact_list(columns, 80),
        "qtl_name_column": qtl_name_col,
        "trait_column": trait_col,
        "major_category_column": major_category_col,
        "trait_category_column": trait_category_col,
        "chr_column": chr_col,
        "genome_start_column": genome_start_col,
        "genome_end_column": genome_end_col,
        "marker_column": marker_col,
        "lod_column": lod_col,
        "reference_column": reference_col,
        "evidence_tier": "Tier 4 QTL interval",
        "notes": "Q-TARO is weak localization evidence only; coordinate build remains to be confirmed",
    }
    write_tsv(REPORT_DIR / "qtaro_inventory.tsv", [inventory_row], QTARO_INVENTORY_FIELDS)

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            cell(row, major_category_col) if major_category_col else "",
            cell(row, trait_category_col) if trait_category_col else "",
            cell(row, trait_col) if trait_col else "",
        )
        groups[key].append(row)

    summary_rows = []
    for (major_category, trait_category, trait), group_rows in sorted(groups.items()):
        summary_rows.append(
            {
                "major_category": major_category,
                "trait_category": trait_category,
                "trait": trait,
                "n_qtl_rows": len(group_rows),
                "chrom_values": compact_list(sorted({cell(row, chr_col) for row in group_rows if chr_col and cell(row, chr_col)}), 30),
                "example_qtl_names": compact_list(
                    unique_preserve([cell(row, qtl_name_col) for row in group_rows if qtl_name_col], 5),
                    5,
                ),
                "example_references": compact_list(
                    unique_preserve([cell(row, reference_col) for row in group_rows if reference_col], 3),
                    3,
                ),
                "evidence_tier": "Tier 4 QTL interval",
                "notes": "trait summary for inventory only; not causal ground truth",
            }
        )
    summary_rows.sort(key=lambda row: (-int(row["n_qtl_rows"]), row["major_category"], row["trait_category"], row["trait"]))
    write_tsv(REPORT_DIR / "qtaro_trait_summary.tsv", summary_rows, QTARO_TRAIT_FIELDS)
    return {"columns": columns, "rows": rows, "inventory": inventory_row, "summary_rows": summary_rows}


def appears_html(path: Path) -> bool:
    return b"<html" in path.read_bytes()[:2048].lower()


def inspect_oryzabase() -> dict[str, object]:
    if not ORYZABASE_TSV.exists():
        raise FileNotFoundError(f"Oryzabase gene list not found: {ORYZABASE_TSV}")
    columns, rows = read_tsv_rows(ORYZABASE_TSV)
    write_column_inventory(REPORT_DIR / "oryzabase_columns.tsv", columns, rows)

    gene_symbol_col = find_column(columns, "CGSNL Gene Symbol", "Gene Symbol")
    gene_name_col = find_column(columns, "CGSNL Gene Name", "Gene Name")
    trait_id_col = find_column(columns, "Trait Gene Id")
    trait_class_col = find_column(columns, "Trait Class")
    rap_id_col = find_column(columns, "RAP ID")
    msu_id_col = find_column(columns, "MSU ID")
    chromosome_col = find_column(columns, "Chromosome No.", "Chromosome")
    trait_ontology_col = find_column(columns, "Trait Ontology")
    plant_ontology_col = find_column(columns, "Plant Ontology")
    gene_ontology_col = find_column(columns, "Gene Ontology")

    inventory_row = {
        "source_file": str(ORYZABASE_TSV),
        "appears_html": "yes" if appears_html(ORYZABASE_TSV) else "no",
        "n_rows": len(rows),
        "n_cols": len(columns),
        "columns": compact_list(columns, 80),
        "gene_symbol_column": gene_symbol_col,
        "gene_name_column": gene_name_col,
        "trait_id_column": trait_id_col,
        "trait_class_column": trait_class_col,
        "rap_id_column": rap_id_col,
        "msu_id_column": msu_id_col,
        "chromosome_column": chromosome_col,
        "trait_ontology_column": trait_ontology_col,
        "plant_ontology_column": plant_ontology_col,
        "gene_ontology_column": gene_ontology_col,
        "evidence_tier": "Tier 1 known/cloned trait gene",
        "notes": "Oryzabase gene-trait entries are weak localization evidence only; gene coordinate mapping remains downstream work",
    }
    write_tsv(REPORT_DIR / "oryzabase_inventory.tsv", [inventory_row], ORYZABASE_INVENTORY_FIELDS)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[cell(row, trait_class_col) if trait_class_col else ""].append(row)

    summary_rows = []
    for trait_class, group_rows in sorted(grouped.items()):
        gene_symbols = [cell(row, gene_symbol_col) for row in group_rows if gene_symbol_col]
        rap_ids = [cell(row, rap_id_col) for row in group_rows if rap_id_col]
        msu_ids = [cell(row, msu_id_col) for row in group_rows if msu_id_col]
        trait_ontology = [cell(row, trait_ontology_col) for row in group_rows if trait_ontology_col]
        summary_rows.append(
            {
                "trait_class": trait_class or "unclassified",
                "n_gene_rows": len(group_rows),
                "n_gene_symbols": len({value for value in gene_symbols if value}),
                "n_rap_ids": len({value for value in rap_ids if value}),
                "n_msu_ids": len({value for value in msu_ids if value}),
                "chrom_values": compact_list(
                    sorted({cell(row, chromosome_col) for row in group_rows if chromosome_col and cell(row, chromosome_col)}),
                    30,
                ),
                "example_gene_symbols": compact_list(unique_preserve(gene_symbols, 5), 5),
                "example_rap_ids": compact_list(unique_preserve(rap_ids, 5), 5),
                "example_trait_ontology": compact_list(unique_preserve(trait_ontology, 3), 3),
                "evidence_tier": "Tier 1 known/cloned trait gene",
                "notes": "trait-gene summary for inventory only; not causal ground truth",
            }
        )
    summary_rows.sort(key=lambda row: (-int(row["n_gene_rows"]), row["trait_class"]))
    write_tsv(REPORT_DIR / "oryzabase_trait_gene_summary.tsv", summary_rows, ORYZABASE_TRAIT_FIELDS)
    return {"columns": columns, "rows": rows, "inventory": inventory_row, "summary_rows": summary_rows}


def gwas_like_raw_files() -> list[str]:
    keywords = ("gwas", "lead", "significant", "association", "ricevarmap")
    files = []
    raw_root = Path("data/raw")
    if not raw_root.exists():
        return files
    for path in sorted(raw_root.rglob("*")):
        if path.is_file() and any(keyword in str(path).lower() for keyword in keywords):
            files.append(str(path))
    return files


def write_gwas_status() -> None:
    files = gwas_like_raw_files()
    file_line = compact_list(files, 20) if files else "未发现文件名包含 gwas/lead/significant/association/ricevarmap 的本地 raw 文件。"
    text = f"""# GWAS Lead SNP 状态

## 当前结论

当前没有可靠、可追溯、可直接纳入的 GWAS lead SNP raw file。本次 Phase 3C 不下载新的 GWAS 文件，也不从论文或网页中临时抽取 lead SNP。

本地 raw data 关键字扫描结果：{file_line}

## 对 v0.1-mini 的影响

GWAS lead SNP 缺口不阻塞 v0.1-mini。v0.1-mini 可以先使用 Oryzabase known/cloned trait genes 和 Q-TARO QTL intervals 作为 `weak localization evidence` 候选来源。

## 后续处理

v0.2-core 应在完成 3K phenotype、core SNP genotype、Qmatrix 和 accession mapping 对齐后，自行计算 GWAS lead SNP 或 window-level signal map。自计算 GWAS 仍然只能作为 `weak localization evidence`，不能写成 `causal ground truth`。未被 GWAS/QTL/known genes 覆盖的 variant 或 window 仍然是 unknown，不能当作 negative。
"""
    (REPORT_DIR / "gwas_lead_snp_status.md").write_text(text, encoding="utf-8")


def count_numeric_positions(rows: list[dict[str, str]], column: str) -> int:
    if not column:
        return 0
    return sum(1 for row in rows if cell(row, column).isdigit())


def write_report(qtaro: dict[str, object], oryzabase: dict[str, object]) -> None:
    qtaro_inventory = qtaro["inventory"]
    oryzabase_inventory = oryzabase["inventory"]
    qtaro_rows = qtaro["rows"]
    qtaro_start_col = str(qtaro_inventory.get("genome_start_column", ""))
    qtaro_end_col = str(qtaro_inventory.get("genome_end_column", ""))
    gwas_files = gwas_like_raw_files()
    gwas_scan = "未发现本地 GWAS lead SNP 候选文件。" if not gwas_files else f"发现 {len(gwas_files)} 个候选文件名，需要人工审阅。"
    text = f"""# Phase 3C Weak Evidence Inventory 报告

## 任务目标

本次任务只登记和检查已有 weak evidence raw files：Oryzabase known/cloned trait gene list 与 Q-TARO QTL interval archive。所有结果只用于判断后续是否可构建 `weak localization evidence`，不生成正式 `weak_evidence_table`，不定义 benchmark schema，不构建 split，不运行 model。

## 已检查文件

- Oryzabase：`{ORYZABASE_TSV}`
- Q-TARO：`{QTARO_ZIP}`
- Q-TARO UTF-8 中间文件：`{QTARO_UTF8}`

`data/raw/` 与 `data/interim/` 仍然由 `.gitignore` 排除，不进入 git。

## Q-TARO 检查结果

Q-TARO 可读取，原始 CSV 已从 SHIFT_JIS 转为 UTF-8。当前记录数为 {qtaro_inventory["n_rows"]}，字段数为 {qtaro_inventory["n_cols"]}。

关键字段识别结果：

- QTL name：`{qtaro_inventory["qtl_name_column"]}`
- trait / character：`{qtaro_inventory["trait_column"]}`
- major category：`{qtaro_inventory["major_category_column"]}`
- trait category：`{qtaro_inventory["trait_category_column"]}`
- chromosome：`{qtaro_inventory["chr_column"]}`
- genome start：`{qtaro_inventory["genome_start_column"]}`，可解析为整数的行数 {count_numeric_positions(qtaro_rows, qtaro_start_col)}
- genome end：`{qtaro_inventory["genome_end_column"]}`，可解析为整数的行数 {count_numeric_positions(qtaro_rows, qtaro_end_col)}
- reference：`{qtaro_inventory["reference_column"]}`

Q-TARO 当前定位为 Tier 4 QTL interval evidence。coordinate build 仍需后续确认，因此不能直接作为 `causal ground truth`。

## Oryzabase 检查结果

Oryzabase gene list 可读取，当前记录数为 {oryzabase_inventory["n_rows"]}，字段数为 {oryzabase_inventory["n_cols"]}，HTML 检测结果为 `{oryzabase_inventory["appears_html"]}`。

关键字段识别结果：

- gene symbol：`{oryzabase_inventory["gene_symbol_column"]}`
- RAP ID：`{oryzabase_inventory["rap_id_column"]}`
- MSU ID：`{oryzabase_inventory["msu_id_column"]}`
- chromosome：`{oryzabase_inventory["chromosome_column"]}`
- trait class：`{oryzabase_inventory["trait_class_column"]}`
- Trait Ontology：`{oryzabase_inventory["trait_ontology_column"]}`

Oryzabase 当前定位为 Tier 1 known/cloned trait gene evidence。后续仍需把 RAP/MSU/gene symbol 映射到 IRGSP-1.0 reference coordinates。

## GWAS Lead SNP 状态

{gwas_scan}

GWAS lead SNP 缺口不阻塞 v0.1-mini。v0.2-core 应在完成 3K phenotype、core SNP genotype、Qmatrix 和 accession mapping 对齐后自跑 GWAS。自计算 GWAS 仍然只是 `weak localization evidence`。

## Evidence Tier 小结

- Tier 1 known/cloned trait gene：Oryzabase，可进入后续候选 weak evidence 整理。
- Tier 4 QTL interval：Q-TARO，可进入后续候选 weak evidence 整理，但 coordinate build 必须确认。
- Tier 2 self-computed GWAS lead SNP：当前不存在，后续 v0.2-core 自跑。

## v0.1-mini 支持结论

v0.1-mini 可以使用 Tier 1 Oryzabase known genes 与 Tier 4 Q-TARO QTL intervals 作为候选 `weak localization evidence` 来源。GWAS lead SNP 后续自跑，不作为当前阻塞项。

## 风险与下一步

- `weak localization evidence` 不能写成 `causal ground truth`。
- `unknown != negative`：没有 evidence 覆盖的 SNP/indel 或 window 不等于 negative。
- 下一步需要确认 Oryzabase gene ID 到 reference coordinate 的映射，以及 Q-TARO interval 的 reference build / coordinate convention。
- 后续构建正式 evidence 表前，需要加入 provenance、trait specificity、coordinate build、evidence tier 和 leakage flag。
"""
    (REPORT_DIR / "weak_evidence_inventory_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    ensure_dirs()
    qtaro = inspect_qtaro()
    oryzabase = inspect_oryzabase()
    write_gwas_status()
    write_report(qtaro, oryzabase)
    print(
        "weak_evidence_inventory="
        f"qtaro_rows:{qtaro['inventory']['n_rows']},"
        f"oryzabase_rows:{oryzabase['inventory']['n_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
