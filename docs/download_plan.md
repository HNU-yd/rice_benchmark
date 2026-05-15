# Raw Data 下载计划

## 1. Phase 2A 目标

Phase 2A 的目标是完成 raw data 下载前的 preflight 准备：复核 P0 source、建立 `download_manifest.tsv` 和 `checksum_table.tsv` 的表头与校验脚本、编写 dry-run 下载脚本模板，并记录 Phase 2B 前必须人工确认的问题。

Phase 2A 只做 preflight，不下载大文件。

## 2. 为什么不直接全量下载

3K Rice raw data 可能包含 VCF、BAM、CRAM、FASTA、GFF、HDF5 或压缩归档，文件体量大且来源版本复杂。直接全量下载会带来以下风险：

- SNP genotype、indel genotype、accession metadata 和 trait table 可能无法对齐。
- reference genome 可能存在 GCF/GCA、RAP、MSU 或其他 build 选择差异。
- mirror 文件可能缺少可复现 checksum 或 source version。
- raw data 可能被误提交到 git。
- weak evidence 可能产生 evidence leakage，或被误写成 `causal ground truth`。

## 3. Phase 2B 才允许下载的条件

Phase 2B 才执行实际 raw data 下载。进入 Phase 2B 前必须满足：

- `manual_confirmation_required.tsv` 已人工审阅。
- `preflight_verified_sources.tsv` 中目标 source 已确认可进入 Phase 2B。
- 每个下载文件已经在 `download_manifest.tsv` 中有 `planned` 记录。
- 下载目标路径、source version、reference build、file role 和访问方法已确认。
- `.gitignore` 已排除 `data/raw/`、大文件和压缩归档。

## 4. P0 数据源下载优先级

建议优先级：

1. Reference genome：先固定 IRGSP-1.0 FASTA 和 chromosome naming。
2. Accession metadata：建立 accession ID mapping 的主表来源。
3. SNP genotype：确认 source release、file list 和 accession list。
4. indel genotype：确认 exact source、ref/alt 表示和 accession-level genotype。
5. trait table：确认 accession overlap，并只用于构建 trait_state。
6. weak evidence：先建立 provenance 和 leakage control，再下载或人工整理。

## 5. SNP genotype 下载策略

SNP genotype 下载前必须先执行 listing 或网页 metadata 检查，确认：

- exact file list。
- source release。
- chromosome partitioning。
- accession list。
- expected format。
- file size 和 checksum 记录方式。

Phase 2B 下载前，`SRC_3K_SNP_GENOTYPE_001` 仍需人工确认。AWS listing 成功也不能直接等同于 fully verified。

## 6. indel genotype 下载策略

indel genotype 是第一版必要数据源，不能只做 SNP。

下载前必须确认：

- exact indel bulk path。
- 是否为 accession-level genotype。
- 是否与 SNP genotype 使用同一 reference build 和 accession ID。
- insertion / deletion 的 ref / alt allele 表示。
- 是否适合后续 `edit_operation_table` 和 Task 2 hidden genotype evaluation。

如果 exact bulk path 未确认，不能进入自动下载。

## 7. reference genome 下载策略

Phase 2A 已保留 `SRC_REF_IRGSP_FASTA_001`，但不再把 GCA page 当作低风险直接下载入口。

建议 Phase 2B 前优先人工确认 `SRC_REF_IRGSP_FASTA_003`：

- NCBI Assembly / NCBI Datasets GCF_001433935.1。
- IRGSP-1.0。
- FASTA package。
- chromosome naming。
- checksum。
- 是否同时需要 GFF3 或只下载 FASTA。

## 8. trait table 下载策略

trait / phenotype table 只能用于构建 trait_state，不能用于 `phenotype prediction`。

下载前必须确认：

- accession ID 是否能映射到 genotype accession。
- 每个 trait 的可用 accession 数。
- trait unit、重复测量和环境信息。
- high/low 或 case/control 分组是否可行。
- source version 和 checksum。

## 9. weak evidence 下载策略

weak evidence 只能作为 `weak localization evidence`，不能作为 `causal ground truth`。

下载或整理前必须确认：

- evidence 是否 trait-specific。
- coordinate build。
- evidence 类型是 SNP-level、gene-level、interval-level 还是 annotation-level。
- publication、database 和 panel provenance。
- 是否存在与 evaluation target 的 leakage 风险。

没有具体 URL 或 provenance 规则的 literature evidence 应 defer。

## 10. checksum 与 manifest 记录规则

所有下载文件必须先进入 `download_manifest.tsv` 的 `planned` 记录。

下载完成后必须计算 sha256，并把结果写入 `checksum_table.tsv`。

`download_manifest.tsv` 中只有真实下载完成并通过 checksum 记录的文件才能从 `planned` 更新为 `downloaded`。

不得编造 file size、checksum 或 source version。

## 11. raw data 不进 git 的规则

raw data 文件不进入 git。

以下路径和文件类型必须被 `.gitignore` 排除：

- `data/raw/`
- `data/interim/`
- `data/processed/`
- VCF/BCF/FASTA/GFF/BAM/CRAM/FASTQ/HDF5/parquet。
- 压缩归档和大模型/embedding 文件。

允许提交 manifest、schema、preflight 报告和下载脚本模板。

## 12. Phase 2B 下载前人工确认清单

Phase 2B 前必须人工确认：

- SNP-Seek offline / mirror validation。
- SNP genotype exact file list。
- indel genotype exact file path。
- reference genome GCF/GCA source choice。
- trait table accession overlap。
- weak evidence leakage control。
- QTL coordinate build。
- known gene database ID mapping。

