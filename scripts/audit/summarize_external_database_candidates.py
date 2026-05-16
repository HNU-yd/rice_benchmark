#!/usr/bin/env python3
"""Write external rice database collection plan and project status summary."""

from __future__ import annotations

import csv
from pathlib import Path


CURRENT_DIR = Path("reports/current_data_status")
EXTERNAL_DIR = Path("reports/external_database_plan")
DATAVERSE_DIR = Path("reports/dataverse_sanciangco")

EXTERNAL_FIELDS = [
    "database_name",
    "url",
    "data_type",
    "main_use",
    "priority",
    "download_status",
    "expected_files",
    "expected_format",
    "blocks_current_phase",
    "risk",
    "recommended_next_action",
    "notes",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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


def external_rows() -> list[dict[str, object]]:
    sanciangco_status = "metadata_checked" if (DATAVERSE_DIR / "HGRSJG_dataset_metadata.json").exists() else "failed"
    return [
        {
            "database_name": "RAP-DB",
            "url": "https://rapdb.dna.affrc.go.jp/",
            "data_type": "gene annotation; RAP ID; gene function; curated genes; ID mapping",
            "main_use": "IRGSP-1.0 gene annotation, RAP/MSU/RefSeq bridge, candidate gene explanation",
            "priority": "high",
            "download_status": "not_started",
            "expected_files": "gene annotation tables; ID conversion tables; functional annotation",
            "expected_format": "GFF3/TSV/HTML export",
            "blocks_current_phase": "no",
            "risk": "URL/export route and release version must be pinned; ID mapping may conflict with NCBI/RAP/MSU names",
            "recommended_next_action": "metadata_check_first",
            "notes": "第一优先；补 gene coordinate 和 explanation，不替代 3K genotype backbone。",
        },
        {
            "database_name": "funRiceGenes",
            "url": "https://funricegenes.github.io/",
            "data_type": "functionally characterized rice genes; cloned gene evidence; literature evidence",
            "main_use": "known gene evidence, gene function, candidate gene explanation",
            "priority": "high",
            "download_status": "not_started",
            "expected_files": "gene list; function table; literature provenance",
            "expected_format": "TSV/CSV/HTML export",
            "blocks_current_phase": "no",
            "risk": "gene ID namespace and update version must be documented",
            "recommended_next_action": "metadata_check_first",
            "notes": "第一优先；与 Oryzabase 合并时必须保留 provenance 和 evidence tier。",
        },
        {
            "database_name": "Oryzabase",
            "url": "https://shigen.nig.ac.jp/rice/oryzabase/",
            "data_type": "known/cloned trait genes; trait ontology; gene-trait annotation",
            "main_use": "Tier 1 weak localization evidence and candidate gene explanation",
            "priority": "high",
            "download_status": "downloaded",
            "expected_files": "OryzabaseGeneListEn.tsv",
            "expected_format": "TSV",
            "blocks_current_phase": "no",
            "risk": "RAP/MSU/gene symbol coordinate mapping remains unresolved",
            "recommended_next_action": "download_now",
            "notes": "已有 raw file；继续整理字段和 gene coordinate mapping。",
        },
        {
            "database_name": "Q-TARO",
            "url": "https://dbarchive.biosciencedbc.jp/en/qtaro/desc.html",
            "data_type": "QTL interval; trait category; literature reference",
            "main_use": "Tier 4 weak localization evidence and window-level support",
            "priority": "high",
            "download_status": "downloaded",
            "expected_files": "qtaro_sjis.zip",
            "expected_format": "SHIFT_JIS CSV archive",
            "blocks_current_phase": "no",
            "risk": "coordinate build and interval convention must be confirmed",
            "recommended_next_action": "download_now",
            "notes": "已有 raw file；不能作为 causal ground truth。",
        },
        {
            "database_name": "RiceVarMap / RiceVarMap2",
            "url": "https://ricevarmap.ncpgr.cn/",
            "data_type": "external SNP/indel variation; allele frequency; variant annotation",
            "main_use": "external variant knowledge and candidate variant explanation",
            "priority": "medium_high",
            "download_status": "not_started",
            "expected_files": "variant annotation; allele frequency; trait association pages if available",
            "expected_format": "database export/TSV/VCF-like annotation",
            "blocks_current_phase": "no",
            "risk": "Do not merge genotype matrix into 3K backbone; accession/source compatibility must be reviewed",
            "recommended_next_action": "metadata_check_first",
            "notes": "作为 external knowledge / annotation / evidence layer，而不是替代 3K genotype backbone。",
        },
        {
            "database_name": "Rice Genome Annotation Project / MSU",
            "url": "http://rice.uga.edu/",
            "data_type": "MSU gene model; MSU locus ID; RAP-MSU mapping",
            "main_use": "legacy literature ID support and RAP/MSU bridge",
            "priority": "medium_high",
            "download_status": "not_started",
            "expected_files": "MSU gene annotation; ID mapping tables",
            "expected_format": "GFF3/TSV",
            "blocks_current_phase": "no",
            "risk": "legacy build/version must be reconciled with IRGSP-1.0 and RAP/RefSeq IDs",
            "recommended_next_action": "metadata_check_first",
            "notes": "第二优先；主要解决 literature ID compatibility。",
        },
        {
            "database_name": "Ensembl Plants / Gramene",
            "url": "https://plants.ensembl.org/Oryza_sativa/Info/Index; https://www.gramene.org/",
            "data_type": "gene annotation; cross-reference; GO/ontology; gene ID mapping",
            "main_use": "RAP/MSU/Ensembl/RefSeq cross-reference and ontology layer",
            "priority": "medium",
            "download_status": "not_started",
            "expected_files": "xref tables; GFF3/GTF; GO/ontology annotations",
            "expected_format": "TSV/GFF3/GTF/BioMart export",
            "blocks_current_phase": "no",
            "risk": "release drift can change gene IDs; version pinning required",
            "recommended_next_action": "metadata_check_first",
            "notes": "第二优先；补充 gene explanation 和 ontology。",
        },
        {
            "database_name": "MBKbase-rice",
            "url": "https://www.mbkbase.org/rice/",
            "data_type": "germplasm information; known alleles; phenotype; gene expression; multi-omics",
            "main_use": "germplasm annotation, known allele evidence, expression/multi-omics explanation",
            "priority": "medium",
            "download_status": "not_started",
            "expected_files": "germplasm table; known allele table; expression metadata",
            "expected_format": "database export/TSV/HTML",
            "blocks_current_phase": "no",
            "risk": "Do not import external phenotypes as benchmark target; accession compatibility unclear",
            "recommended_next_action": "metadata_check_first",
            "notes": "第三优先；作为解释层，不替代主 genotype/trait backbone。",
        },
        {
            "database_name": "Lin et al. 2020 PNAS",
            "url": "https://www.pnas.org/",
            "data_type": "hybrid rice yield / heterosis external evidence; heterotic loci",
            "main_use": "yield-related case study and external validation evidence",
            "priority": "medium",
            "download_status": "not_started",
            "expected_files": "paper supplementary tables; loci lists",
            "expected_format": "PDF/XLSX/TSV supplementary",
            "blocks_current_phase": "no",
            "risk": "Trait/panel overlap and evidence leakage must be reviewed manually",
            "recommended_next_action": "metadata_check_first",
            "notes": "第三优先；只做 case study/external evidence。",
        },
        {
            "database_name": "Sanciangco Harvard Dataverse",
            "url": "https://doi.org/10.7910/DVN/HGRSJG",
            "data_type": "external GWAS evidence; SNP/indel association results; LD-pruned PLINK",
            "main_use": "historical trait GWAS and comparison evidence",
            "priority": "medium",
            "download_status": sanciangco_status,
            "expected_files": "GWAS csv.gz result files; LD-pruned PLINK; trait tables",
            "expected_format": "CSV.GZ/PLINK/TAB",
            "blocks_current_phase": "no",
            "risk": "Large files and external panel can create leakage; current raw download failed/deferred",
            "recommended_next_action": "defer",
            "notes": "保留 metadata；当前不阻塞主流程，优先自跑 3K GWAS。",
        },
    ]


def compact(values: list[str], limit: int = 12) -> str:
    clean = [value for value in values if value]
    if len(clean) <= limit:
        return ",".join(clean)
    return ",".join(clean[:limit]) + f",...(+{len(clean) - limit})"


def write_collection_plan(rows: list[dict[str, object]]) -> None:
    first = [str(row["database_name"]) for row in rows if row["priority"] == "high"]
    second = [str(row["database_name"]) for row in rows if row["priority"] in {"medium_high", "medium"} and row["recommended_next_action"] != "defer"]
    defer = [str(row["database_name"]) for row in rows if row["recommended_next_action"] == "defer"]
    text = f"""# 外部水稻数据库搜集策略

## 为什么现在搜集其他数据库

当前 3K Rice genotype、phenotype、reference、annotation、Qmatrix、Oryzabase、Q-TARO 和 accession mapping 原始来源已经基本落地。下一步要构建 `accession_mapping_master.tsv` 和最小 benchmark 输入表，因此需要提前明确哪些外部数据库用于补 gene ID、trait-gene evidence、QTL evidence、functional annotation 和解释层。

## 为什么不扩成多数据集 genotype benchmark

第一版 benchmark 的主位数据仍然是 3K Rice accession-level SNP/indel genotype backbone。RiceVarMap、MBKbase、Dataverse 或其他数据库的 genotype / phenotype 不应直接混入主 backbone，否则会引入 panel 差异、coordinate build 差异、trait leakage 和 label provenance 混乱。

## Backbone 与 knowledge layer 的区别

3K Rice genotype backbone 提供 sample、SNP/indel 和 reference window 的主坐标系统。外部数据库只作为 knowledge layer：补充 gene ID mapping、function、ontology、known genes、QTL、external association evidence 和 candidate gene explanation。外部 evidence 只能作为 `weak localization evidence`，不能作为 `causal ground truth`。

## 数据库补充内容

- RAP-DB：IRGSP-1.0 gene annotation、RAP ID、function、RAP/MSU/RefSeq bridge。
- funRiceGenes：functionally characterized rice genes、cloned gene evidence、literature provenance。
- Oryzabase / Q-TARO：当前已有，继续整理为 Tier 1 / Tier 4 weak evidence 候选。
- RiceVarMap / RiceVarMap2：外部 variant annotation、allele frequency 和 candidate variant explanation。
- MSU / Ensembl Plants / Gramene：MSU/RAP/Ensembl/RefSeq cross-reference、GO 和 ontology。
- MBKbase-rice：germplasm、known allele、expression/multi-omics explanation。
- Lin et al. 2020 PNAS：hybrid yield / heterosis case study evidence。
- Sanciangco Dataverse：external GWAS evidence metadata，当前 raw 大文件 defer。

## 下载优先级

第一优先：accession ID mapping files、funRiceGenes、RAP-DB gene annotation / mapping、Oryzabase / Q-TARO 已有整理。当前清单：{compact(first, 20)}。

第二优先：RiceVarMap / RiceVarMap2 variation annotation、MSU / Gramene / Ensembl ID mapping。当前清单：{compact(second, 20)}。

第三优先：MBKbase known allele / expression、Lin2020 PNAS hybrid-yield external evidence。

暂缓：{compact(defer, 20)}，以及 pan-genome / SV / CNV 数据和 multi-species 数据。

## 当前不进入第一版的数据

SV、PAV、CNV、pan-genome 专用数据、多物种 genotype benchmark、外部 phenotype prediction target、大规模 raw reads、FASTQ、BAM、CRAM、SRA 下载都不进入第一版主流程。

## 下一步下载顺序

1. 先完成 `accession_mapping_master.tsv`，固定 accession/source/provenance 字段。
2. metadata check RAP-DB 和 funRiceGenes，优先下载小型 gene/function/ID mapping 表。
3. metadata check MSU、Gramene、Ensembl Plants 的 ID cross-reference。
4. metadata check RiceVarMap/RiceVarMap2 的 annotation export，明确不导入其 genotype matrix。
5. Dataverse GWAS 大文件继续 defer；v0.2-core 优先自跑 3K GWAS。
"""
    (EXTERNAL_DIR / "external_database_collection_plan.md").write_text(text, encoding="utf-8")


def write_project_summary() -> None:
    raw_rows = read_tsv(CURRENT_DIR / "current_raw_file_summary.tsv")
    category_rows = read_tsv(CURRENT_DIR / "current_data_category_summary.tsv")
    accession_rows = read_tsv(CURRENT_DIR / "accession_mapping_source_status.tsv")
    checksum_rows = read_tsv(CURRENT_DIR / "current_manifest_checksum_status.tsv")
    missing_rows = read_tsv(CURRENT_DIR / "missing_data_priority.tsv")
    total_size = sum(int(row.get("file_size_bytes") or 0) for row in raw_rows)
    present_categories = [row.get("data_category", "") for row in category_rows if row.get("status") in {"present", "metadata_only"}]
    missing_blockers = [row.get("missing_item", "") for row in missing_rows if row.get("blocks_v0_1") == "yes"]
    missing_checksums = [row for row in checksum_rows if row.get("status") != "registered"]
    source_status = {row.get("source_name", ""): row for row in accession_rows}
    text = f"""# 项目当前数据状态总报告

## 当前已下载的 3K Rice 数据

当前 `data/raw/` 下共有 {len(raw_rows)} 个文件，总大小约 {total_size / (1024 ** 3):.2f} GiB。已覆盖的数据类别包括：{compact(present_categories, 40)}。

主要 3K Rice backbone 资产包括 reference FASTA、GFF3 annotation、SNP genotype、indel genotype、pruned SNP、Qmatrix、3K phenotype XLSX、SNP-Seek SRA list、Genesys MCPD 和 NCBI RunInfo。

## 当前 weak evidence

当前已下载并登记 Oryzabase known/cloned trait gene list 与 Q-TARO QTL interval archive。v0.1 可以使用 Oryzabase + Q-TARO 做 `weak localization evidence` 候选。它们不能写成 `causal ground truth`，未覆盖的 variant/window 仍然是 unknown，不能当作 negative。

## accession mapping 状态

本地 accession mapping 来源已经比较齐全，但高置信 master table 尚未构建。`3K_list_sra_ids.txt`、Genesys MCPD、NCBI RunInfo、PLINK fam、Qmatrix 和 phenotype XLSX 均已存在。当前最优先事项是构建 `accession_mapping_master.tsv`。

关键来源状态：

- SNP-Seek 3K_list_sra_ids：{source_status.get('SNP-Seek 3K_list_sra_ids', {}).get('status', 'missing')}
- Genesys MCPD：{source_status.get('Genesys MCPD passport', {}).get('status', 'missing')}
- NCBI RunInfo：{source_status.get('NCBI PRJEB6180 RunInfo', {}).get('status', 'missing')}
- SNP PLINK fam：{source_status.get('SNP PLINK core_v0.7 fam', {}).get('status', 'missing')}
- indel PLINK fam：{source_status.get('indel PLINK Nipponbare_indel fam', {}).get('status', 'missing')}
- Qmatrix：{source_status.get('Qmatrix population structure', {}).get('status', 'missing')}
- phenotype XLSX：{source_status.get('3K phenotype XLSX', {}).get('status', 'missing')}

## genotype 数据状态

SNP genotype 和 indel genotype backbone 已在本地。SNP `core_v0.7.*` 与 indel `Nipponbare_indel.*` 可以作为 v0.1/v0.2 的主要候选，但仍需验证 sample set、sample order、chromosome naming 和 coordinate mapping。pruned SNP / LD-pruned PLINK 资产可作为后续 GWAS 或 QC 辅助。

## trait 数据状态

3K phenotype XLSX 已在本地，后续只能用于构建 `trait_state` 和 trait-conditioned query，不做 `phenotype prediction`，不做 trait classification。trait accession 到 genotype sample 的 mapping 完成前，不应生成正式 benchmark instances。

## 当前缺失数据

当前缺失项中阻塞 v0.1 的是：{compact(missing_blockers, 20)}。

GWAS lead SNP、更多文献级 evidence、RAP/MSU/Gramene ID mapping、功能注释增强层、表达/多组学数据都不阻塞当前阶段。Dataverse GWAS 下载失败不阻塞当前阶段。

## manifest / checksum 状态

当前 raw 文件中已有 {len(checksum_rows) - len(missing_checksums)} 个文件登记 checksum，{len(missing_checksums)} 个文件仍缺 checksum/manifest 补登记。缺口主要来自新落地的 accession mapping 文件和 pruned SNP 文件。04C 只做统计，不修改 manifest；正式使用这些文件前必须补登记 checksum。

## 外部数据库路线

外部数据库应作为知识层，而不是替代 3K Rice genotype backbone。第一优先是 accession ID mapping files、funRiceGenes、RAP-DB gene annotation / mapping，以及继续整理已有 Oryzabase / Q-TARO。第二优先是 RiceVarMap / RiceVarMap2 variation annotation 和 MSU / Gramene / Ensembl ID mapping。第三优先是 MBKbase、Lin2020 PNAS 与 Sanciangco Dataverse metadata。

## 下一步

下一步最优先创建 Phase 4D / Phase 5 prompt：构建 `accession_mapping_master.tsv` 草稿，固定 ID 字段、source、match rule、confidence 和 manual review flag。v0.2 可以在 accession mapping 完成后自跑 GWAS 生成 Tier 2 `weak localization evidence`。
"""
    (CURRENT_DIR / "project_data_status_summary.md").write_text(text, encoding="utf-8")


def main() -> int:
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    rows = external_rows()
    write_tsv(EXTERNAL_DIR / "external_database_inventory.tsv", rows, EXTERNAL_FIELDS)
    write_collection_plan(rows)
    write_project_summary()
    print(f"external_database_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
