# Raw Data 下载计划与 Phase 2D 结果

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

## Phase 2B-0 核验结果

Phase 2B-0 对 P0 source 做了 exact file list / URL / S3 path 级核验。

已进入 `phase2c_download_candidates.tsv` 的候选项只有：

- `DL_REF_IRGSP_001`：`GCF_001433935.1_IRGSP-1.0_genomic.fna.gz`
- `DL_REF_IRGSP_GFF_001`：`GCF_001433935.1_IRGSP-1.0_genomic.gff.gz`

仍 unresolved 的 P0 source 包括 accession metadata、SNP genotype、indel genotype、trait table、known genes、QTL 和 GWAS weak evidence。

Phase 2C 下载只允许使用 `phase2c_download_candidates.tsv` 中列出的候选项。下载前仍要 dry-run。下载后必须计算 sha256 并更新 `checksum_table.tsv`。

## Phase 2D 快速下载结果

Phase 2D 按用户要求转为快速下载公开可访问数据，不再只停留在 reference 文件。实际执行范围仍限定为 3K Rice、SNP / indel、trait-conditioned SNP/indel localization 所需 raw data。

已完成：

- AWS Open Data 3K Rice root、`snpseek-dl/`、`reduced/`、phenotype 和 core SNP prefix listing。
- 55 个下载候选筛选，其中 SNP genotype 36 个、indel genotype 5 个、accession metadata 10 个、trait table 1 个、reference 1 个、annotation 1 个、metadata/checksum 1 个。
- 55 个候选文件全部下载成功。
- 8 个 AWS listing 文件保存到 `data/raw/listings/`。
- `manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv` 更新为 63 个 `data/raw` 文件的记录。
- 所有登记文件已计算 sha256。

未完成或必须后续核验：

- `RICE_RP.tar.gz` 需要在 raw data inventory 阶段解包检查 accession_id、sample_id、subpopulation、country/region 等字段。
- SNP、indel、trait table 的 accession overlap 尚未检查。
- FASTA / GFF3 / SNP / indel 的 chromosome naming 和 reference build 尚未做一致性审计。
- known gene、QTL、GWAS lead SNP 表未在 fast listing 中发现可直接下载且 provenance 足够清晰的文件。

本阶段仍不实现 schema、normalization、benchmark construction、evaluator、model 或 Evo2。

详细结果见 `reports/fast_download/fast_download_report.md`。

## Phase 3 inventory 后的下载使用建议

Phase 3 inventory 显示，当前已下载文件足以启动 v0.1-mini 的 genotype/reference prototype，但不能直接进入正式 benchmark table。

可优先使用：

- `core_v0.7.bed.gz`
- `core_v0.7.bim.gz`
- `core_v0.7.fam.gz`
- `GCF_001433935.1_IRGSP-1.0_genomic.fna.gz`
- `GCF_001433935.1_IRGSP-1.0_genomic.gff.gz`

进入 Phase 4 前必须先处理：

- numeric chromosome 到 RefSeq `NC_*` 的映射。
- trait table accession-like 字段到 genotype B001-style IDs 的映射。
- `unknown != negative` 的 unlabeled variant/window 处理规则。

详细建议见 `reports/raw_data_inventory/v0_1_mini_recommendation.md`。
