#!/usr/bin/env python3
"""Inspect Phase 7A external knowledge files and write integration reports.

Inputs:
  data/raw/external_knowledge/
  reports/external_knowledge/*/*_download_log.tsv

Outputs:
  reports/external_knowledge/summary/external_knowledge_file_inventory.tsv
  reports/external_knowledge/summary/external_knowledge_download_failures.tsv
  reports/external_knowledge/summary/external_knowledge_schema_preview.tsv
  reports/external_knowledge/summary/external_knowledge_integration_plan.tsv
  reports/external_knowledge/summary/external_knowledge_07a_report.md

Usage:
  python scripts/external_knowledge/inspect_external_knowledge_files.py
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from external_knowledge_utils import (
    REPO_ROOT,
    DOWNLOAD_LOG_COLUMNS,
    detect_columns,
    detect_delimiter,
    guess_format,
    read_tsv,
    rel_path,
    text_open,
    write_tsv,
)


RAW_ROOT = REPO_ROOT / "data/raw/external_knowledge"
REPORT_ROOT = REPO_ROOT / "reports/external_knowledge"
SUMMARY_DIR = REPORT_ROOT / "summary"

FILE_INVENTORY_COLUMNS = [
    "source_database",
    "local_path",
    "file_name",
    "file_size_bytes",
    "format_guess",
    "download_status",
    "checksum_sha256",
    "data_category",
    "notes",
]

FAILURE_COLUMNS = [
    "source_database",
    "download_id",
    "url",
    "local_path",
    "download_status",
    "notes",
]

SCHEMA_COLUMNS = [
    "source_database",
    "local_path",
    "n_rows",
    "n_cols",
    "columns",
    "id_columns_detected",
    "trait_columns_detected",
    "gene_symbol_columns_detected",
    "rap_id_columns_detected",
    "msu_id_columns_detected",
    "go_columns_detected",
    "notes",
]

INTEGRATION_COLUMNS = [
    "source_database",
    "file_name",
    "integration_layer",
    "main_use",
    "priority",
    "requires_coordinate_mapping",
    "requires_gene_id_mapping",
    "can_enter_v0_1",
    "can_enter_v0_2",
    "notes",
]

POSITIVE_LAYERS = {
    "external_gene_annotation": "gene_annotation_layer",
    "external_known_gene_evidence": "known_gene_evidence_layer",
    "external_gene_id_mapping": "gene_id_mapping_layer",
    "external_functional_annotation": "functional_annotation_layer",
}


def download_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(REPORT_ROOT.glob("*/*_download_log.tsv")):
        rows.extend(read_tsv(path, DOWNLOAD_LOG_COLUMNS))
    return rows


def inventory_rows(log_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in log_rows:
        local_path = REPO_ROOT / row["local_path"]
        file_size = local_path.stat().st_size if local_path.exists() else ""
        rows.append(
            {
                "source_database": row["source_database"],
                "local_path": row["local_path"],
                "file_name": local_path.name,
                "file_size_bytes": file_size,
                "format_guess": guess_format(local_path),
                "download_status": row["download_status"],
                "checksum_sha256": row["checksum_sha256"],
                "data_category": row["data_category"],
                "notes": row["notes"],
            }
        )
    return rows


def failure_rows(log_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    failures = []
    for row in log_rows:
        if row["download_status"] != "downloaded":
            failures.append(
                {
                    "source_database": row["source_database"],
                    "download_id": row["download_id"],
                    "url": row["url"],
                    "local_path": row["local_path"],
                    "download_status": row["download_status"],
                    "notes": row["notes"],
                }
            )
    return failures


def json_preview(path: Path) -> tuple[int, list[str], str]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    rows: list[Any]
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        list_values = [value for value in data.values() if isinstance(value, list)]
        rows = list_values[0] if list_values else [data]
    else:
        rows = []
    columns: list[str] = []
    for item in rows[:200]:
        if isinstance(item, dict):
            for key in item:
                if key not in columns:
                    columns.append(key)
    return len(rows), columns, "json list/dict preview"


def delimited_preview(path: Path) -> tuple[int, list[str], str]:
    with text_open(path) as handle:
        sample_lines: list[str] = []
        n_rows = 0
        for line in handle:
            if line.startswith("#") and path.name.lower().endswith((".gff.gz", ".gff3.gz", ".gtf.gz")):
                continue
            if line.strip():
                sample_lines.append(line.rstrip("\n"))
                n_rows += 1
            if len(sample_lines) >= 200:
                break
    if not sample_lines:
        return 0, [], "empty or comment-only preview"
    delimiter = detect_delimiter(sample_lines[0])
    if path.name.lower().endswith((".gff.gz", ".gff3.gz", ".gtf.gz")):
        columns = ["seqid", "source", "type", "start", "end", "score", "strand", "phase", "attributes"]
    else:
        first = sample_lines[0]
        columns = first.split(delimiter)
        if len(columns) <= 1 or all(column.strip() == "" for column in columns):
            columns = [f"col_{index + 1}" for index in range(max(len(first.split(delimiter)), 1))]
        else:
            data_like = sum(1 for column in columns if column.replace(".", "", 1).isdigit())
            if data_like >= max(1, len(columns) // 2):
                columns = [f"col_{index + 1}" for index in range(len(columns))]
    total_rows = 0
    with text_open(path) as handle:
        for line in handle:
            if path.name.lower().endswith((".gff.gz", ".gff3.gz", ".gtf.gz")) and line.startswith("#"):
                continue
            if line.strip():
                total_rows += 1
    return total_rows, columns, f"delimiter={delimiter!r}"


def schema_preview_row(row: dict[str, str]) -> dict[str, object] | None:
    if row["download_status"] != "downloaded":
        return None
    path = REPO_ROOT / row["local_path"]
    fmt = guess_format(path)
    readable = (
        fmt in {"tsv.gz", "txt.gz", "gff.gz", "gff3.gz", "gtf.gz", "txt", "tsv", "csv", "gff", "gff3", "gtf", "json"}
        or path.suffix.lower() in {".txt", ".tsv", ".csv", ".json"}
    )
    if not readable:
        return {
            "source_database": row["source_database"],
            "local_path": row["local_path"],
            "n_rows": "",
            "n_cols": "",
            "columns": "",
            "id_columns_detected": "",
            "trait_columns_detected": "",
            "gene_symbol_columns_detected": "",
            "rap_id_columns_detected": "",
            "msu_id_columns_detected": "",
            "go_columns_detected": "",
            "notes": f"format {fmt} not parsed in 07A schema preview",
        }
    try:
        if fmt == "json" or path.suffix.lower() == ".json":
            n_rows, columns, notes = json_preview(path)
        else:
            n_rows, columns, notes = delimited_preview(path)
    except Exception as exc:
        return {
            "source_database": row["source_database"],
            "local_path": row["local_path"],
            "n_rows": "",
            "n_cols": "",
            "columns": "",
            "id_columns_detected": "",
            "trait_columns_detected": "",
            "gene_symbol_columns_detected": "",
            "rap_id_columns_detected": "",
            "msu_id_columns_detected": "",
            "go_columns_detected": "",
            "notes": f"schema preview failed: {exc}",
        }
    return {
        "source_database": row["source_database"],
        "local_path": row["local_path"],
        "n_rows": n_rows,
        "n_cols": len(columns),
        "columns": ";".join(columns[:80]),
        "id_columns_detected": detect_columns(columns, ["id", "locus", "accession", "transcript", "model"]),
        "trait_columns_detected": detect_columns(columns, ["trait", "phenotype", "keyword", "to"]),
        "gene_symbol_columns_detected": detect_columns(columns, ["symbol", "gene_symbols", "gene symbol", "name"]),
        "rap_id_columns_detected": detect_columns(columns, ["rap", "os0", "os01", "os02", "transcript"]),
        "msu_id_columns_detected": detect_columns(columns, ["msu", "loc_os", "locus"]),
        "go_columns_detected": detect_columns(columns, ["go", "goslim", "ontology"]),
        "notes": notes,
    }


def schema_preview_rows(log_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for row in log_rows:
        preview = schema_preview_row(row)
        if preview is not None:
            rows.append(preview)
    return rows


def integration_layer(row: dict[str, str]) -> tuple[str, str, str, str, str, str, str]:
    file_name = Path(row["local_path"]).name
    category = row["data_category"]
    role = row["file_role"]
    layer = POSITIVE_LAYERS.get(category, "candidate_gene_explanation_layer")
    main_use = "外部知识库 metadata"
    priority = "P2"
    requires_coordinate_mapping = "false"
    requires_gene_id_mapping = "true"
    can_enter_v0_1 = "false"
    can_enter_v0_2 = "true"
    notes = "external evidence / annotation / explanation only"

    if file_name.lower().endswith((".html", ".shtml", ".js", ".pdf")):
        layer = "candidate_gene_explanation_layer"
        main_use = "metadata, citation, help, and provenance"
        priority = "P2"
        requires_coordinate_mapping = "false"
        requires_gene_id_mapping = "false"
        can_enter_v0_1 = "false"
    elif "gff" in file_name.lower() or "gtf" in file_name.lower():
        layer = "gene_annotation_layer"
        main_use = "提供 gene model 坐标和 annotation scaffold"
        priority = "P0"
        requires_coordinate_mapping = "true"
        requires_gene_id_mapping = "true"
        can_enter_v0_1 = "true"
    elif "rap-msu" in file_name.lower() or "faminfo" in file_name.lower():
        layer = "gene_id_mapping_layer"
        main_use = "RAP-DB / MSU / gene family ID harmonization"
        priority = "P0"
        requires_gene_id_mapping = "true"
        can_enter_v0_1 = "true"
    elif "curated" in file_name.lower() or "agri" in file_name.lower() or "geneinfo" in file_name.lower():
        layer = "known_gene_evidence_layer"
        main_use = "known gene / agriculturally important gene evidence"
        priority = "P1"
        requires_gene_id_mapping = "true"
        can_enter_v0_1 = "true"
    elif "annotation" in file_name.lower() or "brief" in file_name.lower():
        layer = "gene_annotation_layer"
        main_use = "gene functional annotation and description"
        priority = "P0"
        can_enter_v0_1 = "true"
    elif "keyword" in file_name.lower() or "goslim" in file_name.lower() or "functional" in file_name.lower():
        layer = "functional_annotation_layer"
        main_use = "functional keyword / GO annotation"
        priority = "P1"
        can_enter_v0_1 = "true"
    return layer, main_use, priority, requires_coordinate_mapping, requires_gene_id_mapping, can_enter_v0_1, can_enter_v0_2, notes


def integration_plan_rows(log_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in log_rows:
        if row["download_status"] != "downloaded":
            continue
        layer, main_use, priority, requires_coord, requires_id, v01, v02, notes = integration_layer(row)
        rows.append(
            {
                "source_database": row["source_database"],
                "file_name": Path(row["local_path"]).name,
                "integration_layer": layer,
                "main_use": main_use,
                "priority": priority,
                "requires_coordinate_mapping": requires_coord,
                "requires_gene_id_mapping": requires_id,
                "can_enter_v0_1": v01,
                "can_enter_v0_2": v02,
                "notes": notes,
            }
        )
    return rows


def summarize_by_database(rows: list[dict[str, str]]) -> dict[str, Counter[str]]:
    summary: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        summary[row["source_database"]][row["download_status"]] += 1
    return summary


def names_for_layer(plan_rows: list[dict[str, object]], layer: str) -> list[str]:
    return [f"`{row['file_name']}`" for row in plan_rows if row["integration_layer"] == layer and row["can_enter_v0_1"] == "true"]


def write_report(
    log_rows: list[dict[str, str]],
    inventory: list[dict[str, object]],
    failures: list[dict[str, object]],
    schema_rows: list[dict[str, object]],
    plan_rows: list[dict[str, object]],
) -> None:
    summary = summarize_by_database(log_rows)
    annotation = names_for_layer(plan_rows, "gene_annotation_layer")
    known = names_for_layer(plan_rows, "known_gene_evidence_layer")
    mapping = names_for_layer(plan_rows, "gene_id_mapping_layer")
    metadata = [f"`{row['file_name']}`" for row in plan_rows if row["can_enter_v0_1"] == "false"]
    lines = [
        "# Phase 7A External Rice Knowledge Collection Report",
        "",
        "## 本次任务目标",
        "",
        "本阶段补充 RAP-DB、funRiceGenes 和 MSU / Rice Genome Annotation Project 的第一批外部水稻知识库，用于后续 annotation layer、known gene evidence layer、gene ID mapping layer 和 candidate gene explanation layer。本阶段不训练模型，不构建 Task 1 instances，不构建 matched decoy。",
        "",
        "## 当前项目状态",
        "",
        "当前 3K Rice 主线已经完成 accession mapping master、trait_state prototype、frozen v0.1 traits、chr1 SNP-only Task 1 instances，以及 minimal evaluator / baseline prototype。07A 是外部知识库补充阶段，不改变 3K genotype backbone，也不扩展到 phenotype prediction 或 trait classification。",
        "",
        "## 为什么在 06A 后补充外部数据库",
        "",
        "06A 显示 `genomic_position` baseline 明显高于 random，说明当前 weak evidence 存在坐标位置偏倚。补充外部 gene annotation、known gene 和 ID mapping 后，可以把 weak evidence 与 gene coordinates、gene IDs 和 functional annotations 分开审查，并为 matched decoy、region holdout 和 shuffled position control 提供基础。",
        "",
        "## 下载结果概览",
        "",
        "| source_database | downloaded | failed | skipped |",
        "|---|---:|---:|---:|",
    ]
    for source in ["RAP-DB", "funRiceGenes", "MSU_RGAP"]:
        counter = summary.get(source, Counter())
        lines.append(f"| {source} | {counter.get('downloaded', 0)} | {counter.get('failed', 0)} | {counter.get('skipped', 0)} |")
    lines.extend(
        [
            "",
            "## RAP-DB 下载和字段审查结果",
            "",
            "RAP-DB 已保存 IRGSP-1.0 download page、versioned download JavaScript、representative annotation TSV、representative transcript exon GTF、RAP-MSU mapping、transcript evidence mapping、curated genes JSON 和 agronomically important genes JSON。字段审查已写入 `external_knowledge_schema_preview.tsv`。",
            "",
            "## funRiceGenes 下载和字段审查结果",
            "",
            "funRiceGenes 已保存 static home page、Shiny page、cloned gene table、gene family table、keyword table、literature table、interaction network PDF 和 help manual。可解析表格进入 schema preview；PDF 只作为 metadata 和解释材料。",
            "",
            "## MSU / RGAP 下载和字段审查结果",
            "",
            "MSU / RGAP 已保存 batch download page、Release 7 download page、all_models GFF3、functional annotation、locus brief info、GO Slim annotation 和 legacy index。GFF3 与 annotation tables 可用于后续 gene annotation layer。",
            "",
            "## 结果分析",
            "",
            "本阶段下载到的文件能够覆盖三类后续关键需求：第一，RAP-DB 和 MSU / RGAP 提供 gene model 坐标与 annotation scaffold；第二，RAP-MSU mapping 和 funRiceGenes gene family table 提供 gene ID harmonization 基础；第三，RAP-DB curated/agri genes 与 funRiceGenes cloned gene table 提供 known gene evidence 和 candidate gene explanation 线索。HTML、JS 和 PDF 文件主要用于 provenance、citation、manual interpretation，不应直接作为 evidence label。",
            "",
            "## 可以进入 annotation layer 的文件",
            "",
            "、".join(annotation) if annotation else "本阶段未确认可直接进入 annotation layer 的文件。",
            "",
            "## 可以进入 known gene evidence layer 的文件",
            "",
            "、".join(known) if known else "本阶段未确认可直接进入 known gene evidence layer 的文件。",
            "",
            "## 可以进入 gene ID mapping layer 的文件",
            "",
            "、".join(mapping) if mapping else "本阶段未确认可直接进入 gene ID mapping layer 的文件。",
            "",
            "## 暂时只作为 metadata 的文件",
            "",
            "、".join(metadata) if metadata else "无。",
            "",
            "## 失败或需要人工下载的文件",
            "",
            "本阶段失败或 skipped 记录数为 " + str(len(failures)) + "。详见 `external_knowledge_download_failures.tsv`。",
            "",
            "## 与 Oryzabase / Q-TARO 的互补关系",
            "",
            "Oryzabase / Q-TARO 当前主要作为 trait-gene 或 QTL interval weak localization evidence。RAP-DB、funRiceGenes 和 MSU / RGAP 提供 gene model、gene ID mapping、known gene evidence、functional annotations 和 literature provenance，可用于解释 candidate regions、统一 RAP/MSU IDs，并帮助设计 matched decoy。",
            "",
            "## 为什么这些外部数据库不替代 3K genotype backbone",
            "",
            "这些外部数据库不是 3K Rice accession-level genotype 数据，也不提供本项目主 benchmark 的 accession-specific SNP/indel backbone。它们只能作为 evidence / annotation / explanation layer，不能替代 3K genotype backbone。",
            "",
            "## 风险解释",
            "",
            "- RAP-DB、MSU / RGAP 和 funRiceGenes 使用的 gene ID、reference build 和坐标体系需要统一校验，不能直接混用。",
            "- known gene / curated gene / cloned gene 只能作为 weak localization evidence 或 explanation，不能写成 causal ground truth。",
            "- 没有 evidence 的 gene、window 或 variant 仍然是 `unknown_unlabeled`，不能当作 negative。",
            "- HTML、JS、PDF 只适合作为 provenance metadata，不能直接进入 scoring label。",
            "- 07A 未下载 RiceVarMap、MBKbase、Lin2020、Sanciangco Dataverse；这些数据源仍在后续阶段处理。",
            "",
            "## 下一步如何整理成统一外部知识层",
            "",
            "下一步应把 RAP-DB / MSU gene models 规范化为统一 gene coordinate table，把 RAP-MSU mapping 和 funRiceGenes IDs 规范化为 gene ID mapping layer，把 curated/agri/cloned gene 信息规范化为 known gene evidence layer，再基于这些层构建 matched decoy 和 frozen split。",
            "",
            "## 下一步工程任务",
            "",
            "1. 解析 RAP-DB / MSU GFF、GTF 和 annotation tables，生成统一 gene coordinate table。",
            "2. 解析 RAP-MSU mapping、funRiceGenes gene IDs 和 gene family IDs，生成 gene ID mapping layer。",
            "3. 解析 RAP-DB curated/agri genes 和 funRiceGenes cloned gene table，生成 known gene evidence layer。",
            "4. 将外部知识层与 Oryzabase / Q-TARO weak evidence 对齐，形成 candidate gene explanation layer。",
            "5. 基于统一 gene / evidence 层构建 matched decoy 和 frozen split。",
            "",
            "## 结论",
            "",
            "外部数据库只作为 evidence / annotation / explanation layer。不能把 known gene / QTL / annotation 写成 causal ground truth。不能把没有 evidence 的区域当 negative。",
        ]
    )
    (SUMMARY_DIR / "external_knowledge_07a_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    log_rows = download_logs()
    inventory = inventory_rows(log_rows)
    failures = failure_rows(log_rows)
    schema_rows = schema_preview_rows(log_rows)
    plan_rows = integration_plan_rows(log_rows)

    write_tsv(SUMMARY_DIR / "external_knowledge_file_inventory.tsv", inventory, FILE_INVENTORY_COLUMNS)
    write_tsv(SUMMARY_DIR / "external_knowledge_download_failures.tsv", failures, FAILURE_COLUMNS)
    write_tsv(SUMMARY_DIR / "external_knowledge_schema_preview.tsv", schema_rows, SCHEMA_COLUMNS)
    write_tsv(SUMMARY_DIR / "external_knowledge_integration_plan.tsv", plan_rows, INTEGRATION_COLUMNS)
    write_report(log_rows, inventory, failures, schema_rows, plan_rows)

    print(f"external_knowledge_files={len(inventory)}")
    print(f"external_knowledge_failures={len(failures)}")
    print(f"external_knowledge_schema_previews={len(schema_rows)}")
    print(f"external_knowledge_integration_rows={len(plan_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
