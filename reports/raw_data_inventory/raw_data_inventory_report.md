# Phase 3 Raw Data Inventory 报告

## 1. 本次 inventory 目标

本次任务只检查已经落盘的 raw data，不继续下载，不构建 benchmark schema，不训练模型，不生成 split、evaluator 或 Evo2 代码。目标是判断 reference、annotation、SNP genotype、indel genotype、trait table 和 accession metadata 是否具备进入 v0.1-mini / v0.2-core 的基本条件。

## 2. 已检查的数据目录

已检查 `data/raw/reference/`、`data/raw/annotation/`、`data/raw/accessions/`、`data/raw/variants/`、`data/raw/traits/`、`data/raw/metadata/`、`data/raw/listings/`，并读取 `manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv`。

## 3. raw 文件总数和总大小

`data/raw` 当前文件数为 65，登记大小合计约 3.51 GiB。完整清单见 `raw_file_inventory.tsv`。

## 4. reference FASTA 结果

FASTA inventory 识别到 58 条 sequence，其中 RefSeq primary chromosome 为 12 条，命名为 `NC_029256.1` 到 `NC_029267.1`。其余为 unplaced scaffold。该 reference 可作为 IRGSP-1.0 reference window 来源。

## 5. GFF3 annotation 结果

GFF3 inventory 识别到 58 个 seqid。GFF3 seqid 使用与 FASTA 相同的 RefSeq accession-style 命名，因此 FASTA 与 GFF3 可以直接按 seqid 对齐。

## 6. SNP genotype 结果

VCF 检查识别到 2 个 `.vcf.gz` 文件；这些 VCF header 中 sample count 很低或为 dummy sample，不应直接作为 accession-level genotype 主输入。SNP PLINK 检查识别到 1 个 SNP PLINK group，其中 `core_v0.7.*` 提供 B001-style sample IDs 和 BIM variant coordinates，更适合作为 v0.1-mini 起点。

## 7. indel genotype 结果

indel PLINK 检查识别到 1 个 indel group，主要是 `Nipponbare_indel.*.gz`。其 FAM sample IDs 与 SNP core PLINK 同为 B001-style，适合在 v0.2-core 中纳入，但需要先验证 sample order 和 accession provenance。

## 8. trait table 结果

trait table inventory 识别到 8 个 sheet。XLSX 中可抽取 accession-like 字段和 trait-like 字段，但当前不能把 trait values 当作 phenotype prediction target，只能用于后续构建 `trait_state`。

## 9. accession metadata 结果

`RICE_RP.tar.gz` 内只发现 PLINK `bed/bim/fam` 成员，没有发现独立 passport/variety metadata 表。已抽取小型 FAM 文件到 `data/interim/inventory/extracted_metadata/`。`Qmatrix-k9-3kRG.csv` 提供 B001-style ID 和 subpopulation proportion，可与 genotype FAM 做直接 overlap。

## 10. accession overlap 结果

pairwise overlap 已写入 `accession_overlap_matrix.tsv`。总体结论：SNP PLINK、indel PLINK、Qmatrix/RICE_RP FAM 的 B001-style IDs 具备较高直接对齐潜力；trait table 的 accession-like values 需要进一步判定字段含义和 ID mapping，不能直接假设已对齐。

## 11. chromosome naming 结果

FASTA/GFF3 使用 `NC_*` accession-style seqid。SNP VCF、SNP PLINK 和 indel PLINK 主要使用 numeric chromosome values，如 `1` 到 `12`。直接 join 会失败，必须在 Phase 4 前建立 chromosome naming mapping。当前发现 4 个 genotype source 存在 direct naming mismatch。

## 12. 主要风险

主要 high risk 包括 accession ID mismatch、trait/genotype overlap insufficient、unknown cannot be negative。另发现 2 个 raw weak evidence candidate，但尚未完成 provenance、coordinate build 和 checksum/manifest 补登记。完整风险见 `raw_data_risk_report.tsv`。

## 13. v0.1-mini 建议

v0.1-mini 建议优先使用 `core_v0.7.*` 做 SNP-only chr1 prototype；trait table 先只进入 accession mapping 审计，不作为 prediction target。v0.2-core 再纳入 `Nipponbare_indel.*`，形成 SNP+indel。详细建议见 `v0_1_mini_recommendation.md`。

## 14. 下一步

根据 inventory 结果，创建 Phase 4 prompt：确定 v0.1-mini 数据范围，并开始构建最小可运行 benchmark 输入表。
