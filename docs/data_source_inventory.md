# Data Source Inventory

## Phase 1 目标

Phase 1 的目标是建立 `manifest/source_inventory.tsv`，先确认第一版 3K Rice benchmark 需要哪些候选数据源、每类数据可能从哪里获取、当前核验状态是什么、下载和使用风险是什么，以及后续可能进入哪些 benchmark 表。

本阶段不下载数据。本阶段不设计最终 schema。本阶段不根据理想情况假设数据格式。后续 schema 必须服从真实下载数据。

## 为什么必须先做 source inventory

本项目的核心原则是：先确认 3K Rice 有什么，再决定 benchmark 怎么落表。

如果跳过 source inventory，后续很容易出现以下问题：

- accession metadata、SNP genotype、indel genotype 和 trait table 无法对齐。
- SNP 与 indel 使用不同 reference build 或不同 accession ID。
- weak localization evidence 被误写成 `causal ground truth`。
- unknown / unlabeled variants 被误当作 negative。
- 下载脚本直接依赖未验证 URL 或 mirror，导致不可复现。
- schema 基于理想格式设计，无法承接真实下载数据。

## 7 类必需数据源

Phase 1 至少登记以下 7 类数据源：

1. `accession_metadata`：用于 accession_table、ID mapping、subpopulation、country/region、sample quality 和 split construction。
2. `snp_genotype`：用于 variant_table、snp_table、genotype_table、MAF/missing rate/LD 统计和 SNP-only benchmark。
3. `indel_genotype`：用于 indel_table、joint SNP+indel benchmark、Task 2 hidden genotype evaluation 和后续 edit_operation_table。
4. `reference_genome`：用于 window_table、reference_window sequence extraction、variant coordinate context 和 Evo2 window embedding。
5. `gene_annotation`：用于 gene density、distance_to_nearest_gene、nearest known gene baseline、matched decoy matching features 和 candidate_gene_ranking_table。
6. `trait_table`：只用于构建 trait_state，不用于 `phenotype prediction`。
7. `weak_evidence`：包括 known trait genes、GWAS lead SNPs、QTL intervals、LD blocks / credible intervals 和 trait-gene/pathway evidence，只能作为 `weak localization evidence`。

## P0 / P1 / P2 优先级定义

- P0：第一版 benchmark 必须确认的数据源。缺少 P0 数据源时，不应进入 raw data download 或 schema 设计。
- P1：第一版重要但可在 P0 后补充的数据源，主要用于 annotation、explanation、baseline feature 或范围扩展。
- P2：case study、supplementary demo 或边界记录用途的数据源，不应阻塞主 benchmark。

## 每类数据后续用于哪些 benchmark 表

- `accession_metadata`：`accession_table`、ID mapping、split metadata。
- `snp_genotype`：`variant_table`、`snp_table`、`genotype_table`。
- `indel_genotype`：`variant_table`、`indel_table`、`genotype_table`、后续 `edit_operation_table`。
- `reference_genome`：`window_table`、reference_window sequence extraction。
- `gene_annotation`：`gene_annotation_table`、`candidate_gene_ranking_table`、matched decoy matching features。
- `trait_table`：`trait_table`、`trait_value_table`、`trait_state_table`。
- `weak_evidence`：`weak_evidence_table`、`target_signal_table`、window-level soft signal、case study explanation。

## 当前已登记候选来源摘要

当前 `source_inventory.tsv` 登记了以下候选来源：

- AWS Open Data Registry / `s3://3kricegenome/`：候选 3K Rice SNP、indel、BAM/VCF 相关来源。当前只记录 metadata 和访问入口，不下载文件。
- SNP-Seek / IRRI mirror：候选 accession metadata、phenotype/passport metadata、SNP genotype 和 indel genotype 来源。原入口当前显示临时离线，需要使用 mirror 或后续恢复的正式入口核验。
- 42basepairs 3K Rice mirror：候选 S3 文件目录浏览来源，可辅助发现 `snpseek-dl` 目录和 core SNP archive，但必须做 checksum/version validation。
- NCBI Datasets / NCBI RefSeq annotation：候选 IRGSP-1.0 reference genome 和 gene annotation 来源。
- RAP-DB / Ensembl Plants：候选 IRGSP-1.0 gene annotation、RAP gene ID 和功能注释来源。
- MBKbase phenotype：候选 Rice3K phenotype 覆盖和 overlap 审核来源。
- Q-TARO、Oryzabase、OGRO、RiceVarMap、Gramene 和文献 supplementary：候选 weak localization evidence 来源。
- RPAN / 3K pan-genome resources：只作为 excluded_for_v1 边界记录，不进入第一版主 benchmark。

## 当前最大风险

当前最大风险包括：

- SNP-Seek 原始入口临时离线，mirror 的性能、版本和导出功能需要人工确认。
- SNP genotype 与 indel genotype 的精确文件路径、版本号、reference build、坐标命名和 checksum 还未冻结。
- accession metadata、trait table、SNP genotype 与 indel genotype 之间可能存在 accession ID 不一致。
- trait / phenotype tables 只能构建 trait_state，不能被误用于 `phenotype prediction`。
- GWAS/QTL/known genes 只能作为 `weak localization evidence`，不能被写成 `causal ground truth`。
- 大文件下载需要 Phase 2 专门处理断点续传、checksum、manifest 和 raw data 防误提交。

## Phase 2 下载前必须人工确认的问题

进入 Phase 2 前必须人工确认：

- 每个 P0 source 的 URL、S3 path 或 database export 方法是否可访问。
- SNP genotype 与 indel genotype 是否使用同一 reference build 和 accession ID。
- reference genome FASTA 的版本、chromosome naming convention 和 checksum。
- accession metadata 是否包含 accession_id、variety name、sample_id、subpopulation 和 country/region。
- trait table 是否能映射到 genotype accession，且每个 trait 有足够 overlap。
- indel 数据是否包含 insertion / deletion 的 ref / alt allele，能否支持后续 `edit_operation_table`。
- weak evidence 的 trait-specific provenance、coordinate build 和 leakage 风险。
- 所有下载文件是否都能登记到 `manifest/download_manifest.tsv` 和 `checksum_table.tsv`。

