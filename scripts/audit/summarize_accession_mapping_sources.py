#!/usr/bin/env python3
"""Summarize accession mapping source files and missing data priorities."""

from __future__ import annotations

import csv
import gzip
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


RAW_ROOT = Path("data/raw")
REPORT_DIR = Path("reports/current_data_status")

STATUS_FIELDS = [
    "source_name",
    "expected_file",
    "found_file",
    "exists",
    "n_rows_or_records",
    "key_columns",
    "role_in_mapping",
    "status",
    "notes",
]

MISSING_FIELDS = [
    "missing_item",
    "importance",
    "blocks_v0_1",
    "blocks_v0_2",
    "can_be_generated_in_house",
    "recommended_action",
    "notes",
]

NS_MAIN = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}


SOURCE_SPECS = [
    {
        "source_name": "SNP-Seek 3K_list_sra_ids",
        "expected_file": "data/raw/accessions/snpseek/3K_list_sra_ids.txt",
        "search_tokens": ["3k_list", "sra"],
        "role_in_mapping": "主桥梁：genotype/IRIS-style ID、stock name、country、SRA accession",
        "notes": "需要检查该表与 B001-style PLINK IDs 的连接路径。",
    },
    {
        "source_name": "Genesys MCPD passport",
        "expected_file": "data/raw/accessions/genesys/genesys_3k_mcpd_passport.xlsx",
        "search_tokens": ["genesys", "mcpd"],
        "role_in_mapping": "passport / IRGC / variety name / origin 补充",
        "notes": "用于补充种质名称、IRGC/passport 字段和地理来源，不替代 genotype sample ID。",
    },
    {
        "source_name": "NCBI PRJEB6180 RunInfo",
        "expected_file": "data/raw/accessions/ncbi_prjeb6180/PRJEB6180_runinfo.csv",
        "search_tokens": ["prjeb6180", "runinfo"],
        "role_in_mapping": "SRA / BioSample / Run / Experiment 补充",
        "notes": "用于把 SRA accession 展开到 Run、BioSample 和测序批次。",
    },
    {
        "source_name": "SNP PLINK core_v0.7 fam",
        "expected_file": "data/raw/variants/snp/core_v0.7.fam.gz",
        "search_tokens": ["core_v0.7", "fam"],
        "role_in_mapping": "SNP genotype sample ID 主来源",
        "notes": "B001-style IDs；需要与 Qmatrix、indel fam 和 3K_list_sra_ids 对齐。",
    },
    {
        "source_name": "indel PLINK Nipponbare_indel fam",
        "expected_file": "data/raw/variants/indel/Nipponbare_indel.fam.gz",
        "search_tokens": ["nipponbare_indel", "fam"],
        "role_in_mapping": "indel genotype sample ID 主来源",
        "notes": "B001-style IDs；需要与 SNP fam 检查样本集合和顺序。",
    },
    {
        "source_name": "Qmatrix population structure",
        "expected_file": "data/raw/metadata/Qmatrix-k9-3kRG.csv",
        "search_tokens": ["qmatrix", "3krg"],
        "role_in_mapping": "B001-style genotype sample ID 与群体结构 covariate 来源",
        "notes": "后续自跑 GWAS 的 covariate 候选。",
    },
    {
        "source_name": "3K phenotype XLSX",
        "expected_file": "data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx",
        "search_tokens": ["phenotypedata", "xlsx"],
        "role_in_mapping": "trait_state 来源",
        "notes": "只能用于 trait_state 构建，不能作为 phenotype prediction target。",
    },
    {
        "source_name": "pruned SNP PLINK fam",
        "expected_file": "data/raw/variants/snp/pruned_v2.1/pruned_v2.1.fam",
        "search_tokens": ["pruned_v2.1", "fam"],
        "role_in_mapping": "pruned SNP / LD-pruned sample ID 补充",
        "notes": "可用于自跑 GWAS 或降维检查，但不替代 core SNP backbone。",
    },
]


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
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


def compact(values: list[str], limit: int = 12) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return ",".join(seen)
    return ",".join(seen[:limit]) + f",...(+{len(seen) - limit})"


def find_similar(tokens: list[str]) -> Path | None:
    if not RAW_ROOT.exists():
        return None
    lowered_tokens = [token.lower() for token in tokens]
    for path in sorted(RAW_ROOT.rglob("*")):
        if path.is_file():
            text = str(path).lower()
            if all(token in text for token in lowered_tokens):
                return path
    return None


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="")
    return path.open("r", encoding="utf-8", errors="replace", newline="")


def summarize_delimited(path: Path) -> tuple[int, str]:
    with open_text(path) as handle:
        sample = handle.read(4096)
        handle.seek(0)
        delimiter = "\t" if "\t" in sample.splitlines()[0] else ","
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return 0, ""
        n_rows = sum(1 for _ in reader)
    return n_rows, compact([value.strip() for value in header], 24)


def summarize_fam(path: Path) -> tuple[int, str]:
    with open_text(path) as handle:
        n_rows = sum(1 for _ in handle)
    return n_rows, "FID,IID,paternal_id,maternal_id,sex,phenotype"


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
    values: list[str] = []
    for item in root.findall("x:si", NS_MAIN):
        values.append("".join(node.text or "" for node in item.findall(".//x:t", NS_MAIN)))
    return values


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", NS_MAIN)).strip()
    node = cell.find("x:v", NS_MAIN)
    value = node.text if node is not None else ""
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


def summarize_xlsx(path: Path) -> tuple[int, str]:
    total_rows = 0
    best_headers: list[str] = []
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        for _, sheet_path in sheet_paths(zf):
            root = ET.fromstring(zf.read(sheet_path))
            rows = []
            for row in root.findall(".//x:sheetData/x:row", NS_MAIN):
                values: list[str] = []
                for cell in row.findall("x:c", NS_MAIN):
                    idx = col_index(cell.attrib.get("r", ""))
                    while len(values) <= idx:
                        values.append("")
                    values[idx] = cell_value(cell, shared)
                if any(values):
                    rows.append(values)
            total_rows += len(rows)
            if rows and len(rows[0]) > len(best_headers):
                best_headers = rows[0]
    return total_rows, compact(best_headers, 24)


def summarize_file(path: Path) -> tuple[int, str]:
    lower = path.name.lower()
    if lower.endswith((".fam", ".fam.gz")):
        return summarize_fam(path)
    if lower.endswith(".xlsx"):
        return summarize_xlsx(path)
    if lower.endswith((".csv", ".tsv", ".txt")):
        return summarize_delimited(path)
    return 0, ""


def write_priority_report(rows: list[dict[str, object]]) -> None:
    by_name = {str(row["source_name"]): row for row in rows}

    def status(name: str) -> str:
        row = by_name.get(name, {})
        return f"{row.get('status', 'missing')}；records={row.get('n_rows_or_records', '')}"

    text = f"""# Accession Mapping Source 优先级报告

## 当前结论

当前可以开始构建 `accession_mapping_master.tsv` 的第一版草稿，但不能直接进入正式 benchmark instance 构建。原因是 genotype 侧 B001-style sample IDs 已经来自 PLINK fam 与 Qmatrix，SRA / stock / passport 侧也有本地来源；但 B001、IRIS/GS accession、stock name、SRA accession、BioSample 和 phenotype `STOCK_ID` / `GS_ACCNO` 的高置信关系仍需要逐步核验。

## 主桥梁与补充来源

`3K_list_sra_ids.txt` 是 genotype ID / IRIS-style ID ↔ stock name ↔ SRA accession 的主桥梁。本地状态：{status('SNP-Seek 3K_list_sra_ids')}。

Genesys MCPD 是 passport / IRGC / name 补充。本地状态：{status('Genesys MCPD passport')}。

NCBI RunInfo 是 SRA / BioSample / Run 补充。本地状态：{status('NCBI PRJEB6180 RunInfo')}。

Qmatrix 和 PLINK fam 是 genotype sample ID 的主来源。本地状态：SNP fam {status('SNP PLINK core_v0.7 fam')}；indel fam {status('indel PLINK Nipponbare_indel fam')}；Qmatrix {status('Qmatrix population structure')}。

phenotype XLSX 是 trait_state 的来源，但不能当 phenotype prediction target。本地状态：{status('3K phenotype XLSX')}。

## 必须优先检查的 ID 关系

1. `core_v0.7.fam.gz` / `Nipponbare_indel.fam.gz` / `Qmatrix-k9-3kRG.csv` 之间的 B001-style sample ID 集合与顺序。
2. B001-style sample ID 到 `3K_list_sra_ids.txt` 中 IRIS/stock/SRA 字段的连接路径。
3. phenotype XLSX 中 `STOCK_ID`、`GS_ACCNO`、`NAME`、`Source_Accno` 与 SNP-Seek / Genesys / RunInfo 的关系。
4. `SRA Accession` 到 NCBI RunInfo 中 `Sample`、`BioSample`、`Run`、`Experiment` 的一对多关系。
5. Genesys MCPD 中 accession name、IRGC/passport 字段与 phenotype name/source accession 的同义词关系。

## 当前可执行动作

下一步应构建 `accession_mapping_master.tsv` 草稿，并为每一条映射记录保留 source、match rule、confidence、manual_review_required 和 conflict flag。高置信 mapping 完成前，不应生成正式 trait-conditioned benchmark instances。
"""
    (REPORT_DIR / "accession_mapping_priority_report.md").write_text(text, encoding="utf-8")


def missing_rows() -> list[dict[str, object]]:
    return [
        {
            "missing_item": "标准 accession ID master table",
            "importance": "highest",
            "blocks_v0_1": "yes",
            "blocks_v0_2": "yes",
            "can_be_generated_in_house": "yes",
            "recommended_action": "build accession_mapping_master.tsv first",
            "notes": "当前最阻塞；没有该表就不能可靠连接 trait_state 与 genotype accession context。",
        },
        {
            "missing_item": "trait accession 与 genotype sample 的高置信 mapping",
            "importance": "highest",
            "blocks_v0_1": "yes",
            "blocks_v0_2": "yes",
            "can_be_generated_in_house": "yes",
            "recommended_action": "join PLINK/Qmatrix/SNP-Seek/Genesys/RunInfo/phenotype and flag confidence",
            "notes": "阻塞 trait-conditioned instances；不能用模糊 name match 直接生成标签。",
        },
        {
            "missing_item": "正式 trait_value_table",
            "importance": "high",
            "blocks_v0_1": "yes",
            "blocks_v0_2": "yes",
            "can_be_generated_in_house": "yes",
            "recommended_action": "derive only after accession mapping and trait dictionary review",
            "notes": "trait table 可以进入 trait_state 构建，但不做 phenotype prediction。",
        },
        {
            "missing_item": "GWAS lead SNP / significant SNP",
            "importance": "medium_high",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "yes",
            "recommended_action": "self-compute after accession mapping with genotype + phenotype + Qmatrix",
            "notes": "重要但不阻塞 v0.1；自跑 GWAS 仍然只是 weak localization evidence。",
        },
        {
            "missing_item": "更多文献级 trait-specific evidence",
            "importance": "medium",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "partly",
            "recommended_action": "curate after provenance and leakage fields are defined",
            "notes": "可增强 case study 和解释层；不得写成 causal ground truth。",
        },
        {
            "missing_item": "RAP / MSU / Gramene ID mapping",
            "importance": "medium_high",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "partly",
            "recommended_action": "collect RAP-DB / MSU / Gramene cross-reference tables",
            "notes": "主要影响 gene explanation 和 Oryzabase gene coordinate mapping，不阻塞 v0.1 skeleton。",
        },
        {
            "missing_item": "功能注释增强层",
            "importance": "medium",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "partly",
            "recommended_action": "collect funRiceGenes, RAP-DB function, GO/ontology after core mapping",
            "notes": "用于 candidate gene explanation，不替代 3K genotype backbone。",
        },
        {
            "missing_item": "表达 / 多组学增强数据",
            "importance": "low_medium",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "no",
            "recommended_action": "defer until core benchmark table is stable",
            "notes": "增强层，不阻塞 v0.1 / v0.2。",
        },
        {
            "missing_item": "Sanciangco / Dataverse GWAS raw result files",
            "importance": "medium",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "not_needed_for_v0_2",
            "recommended_action": "defer large downloads; keep metadata only",
            "notes": "下载失败不阻塞当前阶段；后续优先自跑 GWAS。",
        },
        {
            "missing_item": "新增 accession / pruned SNP raw files 的 checksum 与 manifest 补登记",
            "importance": "high",
            "blocks_v0_1": "no",
            "blocks_v0_2": "no",
            "can_be_generated_in_house": "yes",
            "recommended_action": "register checksums before using these files as reproducible inputs",
            "notes": "04C 只统计现状；正式使用 Genesys、RunInfo、3K_list_sra_ids 或 pruned PLINK 前必须补登记。",
        },
    ]


def write_missing_report(rows: list[dict[str, object]]) -> None:
    blocking = [row["missing_item"] for row in rows if row["blocks_v0_1"] == "yes"]
    nonblocking = [row["missing_item"] for row in rows if row["blocks_v0_1"] != "yes"]
    text = f"""# 缺失数据优先级报告

## 阻塞项

当前阻塞 v0.1 的缺失项是：{compact([str(item) for item in blocking], 20)}。

其中最优先的是 `accession_mapping_master.tsv` 与 trait accession 到 genotype sample 的高置信 mapping。没有这一步，trait-conditioned SNP/indel localization 的 accession context 不能可靠构建。

## 非阻塞项

不阻塞 v0.1 的缺失项包括：{compact([str(item) for item in nonblocking], 20)}。

GWAS lead SNP / significant SNP 重要，但可以在 accession mapping 完成后用 3K phenotype、core SNP genotype 和 Qmatrix 自跑，作为 Tier 2 `weak localization evidence`。RAP / MSU / Gramene ID mapping 和功能注释主要影响解释层，不阻塞 v0.1 skeleton。表达和多组学数据属于增强层，应暂缓。

## 当前策略

先做 accession mapping，再做 trait_state 和最小 benchmark 输入表。不要因为 Dataverse GWAS 下载失败而阻塞当前阶段，也不要把 Oryzabase、Q-TARO 或后续自跑 GWAS 写成 `causal ground truth`。
"""
    (REPORT_DIR / "missing_data_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for spec in SOURCE_SPECS:
        expected = Path(str(spec["expected_file"]))
        found = expected if expected.exists() else find_similar(list(spec["search_tokens"]))
        exists = found is not None and found.exists()
        n_rows = 0
        key_columns = ""
        if exists and found is not None:
            n_rows, key_columns = summarize_file(found)
        rows.append(
            {
                "source_name": spec["source_name"],
                "expected_file": spec["expected_file"],
                "found_file": str(found) if found else "",
                "exists": "yes" if exists else "no",
                "n_rows_or_records": n_rows,
                "key_columns": key_columns,
                "role_in_mapping": spec["role_in_mapping"],
                "status": "present" if exists else "missing",
                "notes": spec["notes"],
            }
        )

    missing = missing_rows()
    write_tsv(REPORT_DIR / "accession_mapping_source_status.tsv", rows, STATUS_FIELDS)
    write_tsv(REPORT_DIR / "missing_data_priority.tsv", missing, MISSING_FIELDS)
    write_priority_report(rows)
    write_missing_report(missing)
    print(f"accession_mapping_sources={len(rows)}")
    print(f"accession_mapping_sources_present={sum(1 for row in rows if row['exists'] == 'yes')}")
    print(f"missing_priority_items={len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
