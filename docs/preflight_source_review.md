# Preflight Source Review

## 1. 已读取的 source inventory

Phase 2A 已读取：

- `manifest/source_inventory.tsv`
- `manifest/source_inventory.schema.tsv`
- `reports/source_inventory/p0_source_review.tsv`
- `reports/source_inventory/source_inventory_review.md`
- `configs/sources.yaml`
- `docs/data_acquisition_plan.md`

`source_inventory.tsv` 已修正 reference source 风险，并新增 `SRC_REF_IRGSP_FASTA_003` 作为 GCF_001433935.1 / IRGSP-1.0 的候选确认来源。

## 2. 当前 P0 source 状态

当前 P0 source 覆盖 accession metadata、SNP genotype、indel genotype、reference genome、trait table 和 weak evidence。

没有任何 P0 source 被标记为 fully ready。多数 P0 source 状态为 `partially_verified` 或 `needs_manual_review`，因此 Phase 2B 前仍需人工确认。

## 3. 可以进入 Phase 2B 的候选项

当前没有直接标记为 `phase2b_ready = yes` 的来源。

可进入 Phase 2B 下载脚本准备，但需要人工确认后再下载的候选包括：

- `SRC_3K_SNP_GENOTYPE_001`
- `SRC_3K_INDEL_GENOTYPE_002`
- `SRC_REF_IRGSP_FASTA_003`
- `SRC_TRAIT_TABLE_001`
- `SRC_WEAK_QTL_001`

## 4. 不能进入 Phase 2B 的候选项

当前不能直接进入 Phase 2B 下载的候选包括：

- `SRC_3K_INDEL_GENOTYPE_001`：exact indel bulk path 未确认。
- `SRC_TRAIT_TABLE_003`：直接数据文件 URL 未做下载前人工确认。
- `SRC_WEAK_KNOWN_GENES_001`：没有具体 export path。
- `SRC_WEAK_GWAS_001`：没有具体文件 URL，且 leakage 风险高。
- `SRC_EXCLUDED_PAV_SV_001`：明确 excluded_for_v1。

## 5. 需要人工确认的候选项

需要人工确认的问题已记录在 `reports/download_preflight/manual_confirmation_required.tsv`，包括：

- SNP-Seek offline / mirror validation。
- SNP genotype exact file list。
- indel genotype exact file path。
- reference genome GCF/GCA source choice。
- trait table accession overlap。
- weak evidence leakage control。
- QTL coordinate build。
- known gene database ID mapping。

## 6. reference source 修正建议

`SRC_REF_IRGSP_FASTA_001` 原本使用 GCA_001433935.1 页面，不应作为低风险直接下载入口。

Phase 2A 已将其风险说明改为：GCA 页面可能被移除或重定向，Phase 2B 下载前应优先检查 GCF_001433935.1 / IRGSP-1.0 assembly entry。

新增 `SRC_REF_IRGSP_FASTA_003` 作为候选确认来源，但仍需人工确认 exact FASTA package、checksum 和 chromosome naming。

## 7. indel genotype source 风险

indel genotype 仍是 Phase 2B 前的关键风险：

- SNP-Seek short indel 的 exact bulk path 未确认。
- AWS VCF prefix 需要 listing 后确认是否包含 indel 或 joint SNP+indel。
- 必须确认 ref/alt allele 表示和 indel normalization。
- 必须确认与 SNP genotype 的 accession ID 和 reference build 一致。

## 8. trait overlap 风险

trait table 下载前必须确认 accession overlap。

如果 trait table 与 SNP/indel genotype 的 accession overlap 不足，后续 v0.1-mini / v0.2-core / v1.0-full benchmark scope 必须降级或重新选择 trait。

trait table 只能用于构建 trait_state，不能用于 `phenotype prediction`。

## 9. weak evidence leakage 风险

weak evidence 下载和整理必须记录 provenance。

GWAS/QTL/known genes 只能作为 `weak localization evidence`，不能写成 `causal ground truth`。

对 literature-curated GWAS lead SNPs，当前建议 `defer`，直到建立人工文献筛选规则、panel overlap 检查和 leakage flag。

