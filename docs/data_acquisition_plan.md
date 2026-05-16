# 数据获取计划

本文档记录 Phase 0 到 Phase 1 的数据获取计划。当前不定义 download scripts、download commands、data schemas 或 processing logic。

## Phase 1 需要确认的数据类别

1. 3K Rice accession metadata。
2. 3K Rice SNP genotype data。
3. 3K Rice indel genotype data。
4. Nipponbare / IRGSP reference genome FASTA。
5. gene annotation / functional annotation。
6. 只用于构建 trait_state 的 trait / phenotype tables。
7. `weak localization evidence`：
   - known trait genes / cloned genes
   - GWAS lead SNPs / significant SNPs
   - QTL intervals
   - 可用时的 LD blocks / credible intervals
   - trait-gene annotation / pathway evidence

## 获取规则

只有在 `source_inventory.tsv` 创建并审阅后，才允许开始下载。

后续 Phase 中，raw data 必须存放在 `data/raw/` 下。

每个下载文件都必须登记 URL/access method、source version、checksum、file size 和 download time。

Phase 0 不创建 `data/raw/` 或其他 raw-data 目录，除非该目录已经存在。

## Phase 1 结果引用

Phase 1 只产生 `manifest/source_inventory.tsv`，不下载数据。

Phase 2 只有在 `source_inventory.tsv` 人工审阅后才能开始。

下载脚本必须使用 `source_inventory.tsv` 中经过确认的数据源。

所有下载文件必须进入 `manifest/download_manifest.tsv` 和 `checksum_table.tsv`。

Phase 1 的风险说明见 `docs/data_download_risk_notes.md`。当前 source inventory 的主体说明见 `docs/data_source_inventory.md`。

## Phase 2A 下载前核验

Phase 2A 只做 raw data download preflight，不下载大文件。

Phase 2A 产生：

- `manifest/preflight_verified_sources.tsv`
- `manifest/download_manifest.tsv`
- `manifest/checksum_table.tsv`
- `docs/download_plan.md`
- `docs/raw_data_layout.md`
- `docs/preflight_source_review.md`
- `reports/download_preflight/preflight_report.md`

Phase 2B 只有在 `manual_confirmation_required.tsv` 和 `preflight_verified_sources.tsv` 人工审阅后才能开始。

## Phase 2D 快速下载结果引用

Phase 2D 已按快速下载任务下载公开可访问的 3K Rice raw data。下载结果不改变 benchmark 边界：第一版仍限定为 3K Rice、SNP / indel，不做 `phenotype prediction`，weak evidence 只能作为 `weak localization evidence`。

当前下载结果见：

- `reports/fast_download/fast_download_report.md`
- `reports/fast_download/auto_download_candidates.tsv`
- `reports/fast_download/downloaded_files.tsv`
- `manifest/download_manifest.tsv`
- `manifest/checksum_table.tsv`

下一步必须做 raw data inventory，重点检查 accession metadata、SNP genotype、indel genotype、trait table 和 IRGSP-1.0 reference build 是否可对齐。不能在 inventory 前假设 accession overlap 已成立。

## Phase 3 raw data inventory 结果引用

Phase 3 已对下载后的 raw data 做轻量 inventory。当前结论是：

- IRGSP-1.0 FASTA 与 GFF3 使用一致的 RefSeq `NC_*` seqid。
- SNP / indel PLINK 文件使用 numeric chromosome values，需要建立 chromosome naming mapping。
- SNP core PLINK 与 indel PLINK 的 B001-style sample IDs 高度重合。
- trait table 的 accession-like 字段与 genotype B001-style IDs 尚未直接对齐，需要 accession mapping。
- `RICE_RP.tar.gz` 主要包含 PLINK bed/bim/fam，没有独立 passport metadata 表。

详细结果见 `reports/raw_data_inventory/raw_data_inventory_report.md`。
