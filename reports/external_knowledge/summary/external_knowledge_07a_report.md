# Phase 7A External Rice Knowledge Collection Report

## 本次任务目标

本阶段补充 RAP-DB、funRiceGenes 和 MSU / Rice Genome Annotation Project 的第一批外部水稻知识库，用于后续 annotation layer、known gene evidence layer、gene ID mapping layer 和 candidate gene explanation layer。本阶段不训练模型，不构建 Task 1 instances，不构建 matched decoy。

## 当前项目状态

当前 3K Rice 主线已经完成 accession mapping master、trait_state prototype、frozen v0.1 traits、chr1 SNP-only Task 1 instances，以及 minimal evaluator / baseline prototype。07A 是外部知识库补充阶段，不改变 3K genotype backbone，也不扩展到 phenotype prediction 或 trait classification。

## 为什么在 06A 后补充外部数据库

06A 显示 `genomic_position` baseline 明显高于 random，说明当前 weak evidence 存在坐标位置偏倚。补充外部 gene annotation、known gene 和 ID mapping 后，可以把 weak evidence 与 gene coordinates、gene IDs 和 functional annotations 分开审查，并为 matched decoy、region holdout 和 shuffled position control 提供基础。

## 下载结果概览

| source_database | downloaded | failed | skipped |
|---|---:|---:|---:|
| RAP-DB | 10 | 0 | 0 |
| funRiceGenes | 8 | 0 | 0 |
| MSU_RGAP | 7 | 0 | 0 |

## RAP-DB 下载和字段审查结果

RAP-DB 已保存 IRGSP-1.0 download page、versioned download JavaScript、representative annotation TSV、representative transcript exon GTF、RAP-MSU mapping、transcript evidence mapping、curated genes JSON 和 agronomically important genes JSON。字段审查已写入 `external_knowledge_schema_preview.tsv`。

## funRiceGenes 下载和字段审查结果

funRiceGenes 已保存 static home page、Shiny page、cloned gene table、gene family table、keyword table、literature table、interaction network PDF 和 help manual。可解析表格进入 schema preview；PDF 只作为 metadata 和解释材料。

## MSU / RGAP 下载和字段审查结果

MSU / RGAP 已保存 batch download page、Release 7 download page、all_models GFF3、functional annotation、locus brief info、GO Slim annotation 和 legacy index。GFF3 与 annotation tables 可用于后续 gene annotation layer。

## 结果分析

本阶段下载到的文件能够覆盖三类后续关键需求：第一，RAP-DB 和 MSU / RGAP 提供 gene model 坐标与 annotation scaffold；第二，RAP-MSU mapping 和 funRiceGenes gene family table 提供 gene ID harmonization 基础；第三，RAP-DB curated/agri genes 与 funRiceGenes cloned gene table 提供 known gene evidence 和 candidate gene explanation 线索。HTML、JS 和 PDF 文件主要用于 provenance、citation、manual interpretation，不应直接作为 evidence label。

## 可以进入 annotation layer 的文件

`osa1_r7.all_models.gff3.gz`、`osa1_r7.all_models.functional_annotation.txt.gz`、`osa1_r7.locus_brief_info.txt.gz`、`IRGSP-1.0_representative_annotation_2026-02-05.tsv.gz`、`IRGSP-1.0_representative_transcript_exon_2026-02-05.gtf.gz`

## 可以进入 known gene evidence layer 的文件

`geneInfo.table.txt`、`curated_genes.json`、`agri_genes.json`

## 可以进入 gene ID mapping layer 的文件

`famInfo.table.txt`、`RAP-MSU_2026-02-05.txt.gz`

## 暂时只作为 metadata 的文件

`funricegenes_home.html`、`funricegenes_shiny_home.html`、`reference.table.txt`、`net.pdf`、`help.pdf`、`downloads_gad.shtml`、`download_osa1r7.shtml`、`legacy_annotation_dbs_index.html`、`irgsp1_download_page.html`、`download.99861702.js`、`IRGSP-1.0_transcript-evidence_2012-04-11.txt.gz`、`curated_gene_list.html`、`agri_gene_list.html`

## 失败或需要人工下载的文件

本阶段失败或 skipped 记录数为 0。详见 `external_knowledge_download_failures.tsv`。

## 与 Oryzabase / Q-TARO 的互补关系

Oryzabase / Q-TARO 当前主要作为 trait-gene 或 QTL interval weak localization evidence。RAP-DB、funRiceGenes 和 MSU / RGAP 提供 gene model、gene ID mapping、known gene evidence、functional annotations 和 literature provenance，可用于解释 candidate regions、统一 RAP/MSU IDs，并帮助设计 matched decoy。

## 为什么这些外部数据库不替代 3K genotype backbone

这些外部数据库不是 3K Rice accession-level genotype 数据，也不提供本项目主 benchmark 的 accession-specific SNP/indel backbone。它们只能作为 evidence / annotation / explanation layer，不能替代 3K genotype backbone。

## 风险解释

- RAP-DB、MSU / RGAP 和 funRiceGenes 使用的 gene ID、reference build 和坐标体系需要统一校验，不能直接混用。
- known gene / curated gene / cloned gene 只能作为 weak localization evidence 或 explanation，不能写成 causal ground truth。
- 没有 evidence 的 gene、window 或 variant 仍然是 `unknown_unlabeled`，不能当作 negative。
- HTML、JS、PDF 只适合作为 provenance metadata，不能直接进入 scoring label。
- 07A 未下载 RiceVarMap、MBKbase、Lin2020、Sanciangco Dataverse；这些数据源仍在后续阶段处理。

## 下一步如何整理成统一外部知识层

下一步应把 RAP-DB / MSU gene models 规范化为统一 gene coordinate table，把 RAP-MSU mapping 和 funRiceGenes IDs 规范化为 gene ID mapping layer，把 curated/agri/cloned gene 信息规范化为 known gene evidence layer，再基于这些层构建 matched decoy 和 frozen split。

## 下一步工程任务

1. 解析 RAP-DB / MSU GFF、GTF 和 annotation tables，生成统一 gene coordinate table。
2. 解析 RAP-MSU mapping、funRiceGenes gene IDs 和 gene family IDs，生成 gene ID mapping layer。
3. 解析 RAP-DB curated/agri genes 和 funRiceGenes cloned gene table，生成 known gene evidence layer。
4. 将外部知识层与 Oryzabase / Q-TARO weak evidence 对齐，形成 candidate gene explanation layer。
5. 基于统一 gene / evidence 层构建 matched decoy 和 frozen split。

## 结论

外部数据库只作为 evidence / annotation / explanation layer。不能把 known gene / QTL / annotation 写成 causal ground truth。不能把没有 evidence 的区域当 negative。
