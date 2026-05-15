# Data Download Risk Notes

本文档记录 Phase 1 识别出的下载与使用风险。Phase 2 只能在 `source_inventory.tsv` 经人工审阅后开始。

## 1. accession ID 不一致风险

- risk：accession metadata、SNP genotype、indel genotype 和 trait table 使用不同 ID、别名或样本命名。
- why_it_matters：ID 不一致会导致 genotype 与 trait_state 错配，直接破坏 Task 1 和 Task 2 的输入定义。
- how_to_check_later：下载后建立 accession ID crosswalk，比较 accession_id、sample_id、variety name、IRGC/IRIS 编号和缺失率。
- mitigation：在 schema 设计前冻结 `accession_table` 和 ID mapping 表；不允许训练代码动态猜测 ID 对齐。

## 2. SNP 与 indel 来源版本不一致风险

- risk：SNP genotype 和 indel genotype 可能来自不同 SNP-Seek release、不同 pipeline 或不同 S3 目录版本。
- why_it_matters：版本不一致会导致 variant coordinate、accession coverage 和 genotype missingness 不可比较。
- how_to_check_later：对每个 genotype source 记录 release、file name、checksum、sample list、variant count 和 reference build。
- mitigation：优先选择同一 release / 同一 accession set 的 SNP 和 indel；无法一致时必须在 benchmark scope 中降级或拆分版本。

## 3. reference build 不一致风险

- risk：候选来源可能使用 Nipponbare / IRGSP-1.0、MSU v7、RAP build 或旧 IRGSP build。
- why_it_matters：坐标不一致会影响 reference_window、gene annotation、QTL intervals 和 GWAS lead SNPs。
- how_to_check_later：核对 FASTA header、chromosome naming、assembly accession、annotation release 和 variant coordinate convention。
- mitigation：Phase 2 后冻结唯一主 reference build；所有非主 build evidence 必须记录 remapping 或 excluded 状态。

## 4. SNP-Seek 原始入口不可用或临时离线风险

- risk：SNP-Seek 原始入口当前显示临时离线，并提示使用 mirror。
- why_it_matters：原始入口不可用会影响数据导出、版本追踪、ID mapping 和 phenotype/passport 表获取。
- how_to_check_later：定期检查原始入口和 mirror，记录访问时间、页面状态、导出功能和失败原因。
- mitigation：将 mirror 标记为 `partially_verified`；下载前必须找到可复现访问方法并记录 checksum。

## 5. mirror 数据源版本和 checksum 风险

- risk：42basepairs、SNP-Seek mirror 或其他 mirror 可能与原始 S3/SNP-Seek 文件版本不同。
- why_it_matters：如果 mirror 版本不可追踪，后续 benchmark 无法复现。
- how_to_check_later：比对 file name、file size、last modified time、checksum 和来源文档。
- mitigation：只在 `download_manifest.tsv` 中记录经过 checksum 验证的 mirror 文件；未验证 mirror 不作为最终 source。

## 6. trait table 与 genotype accession overlap 不足风险

- risk：trait / phenotype tables 的 accession overlap 可能不足，或某些 trait 可用 accession 数过低。
- why_it_matters：Task 1 的 trait_state 需要足够 accession 覆盖；overlap 不足会限制 benchmark 范围。
- how_to_check_later：统计每个 trait 的可用 accession 数、与 SNP/indel genotype 的交集、缺失率、环境信息和重复测量。
- mitigation：Phase 4 再决定 v0.1-mini / v0.2-core / v1.0-full 范围；不在 Phase 1 预设 trait schema。

## 7. GWAS/QTL/known gene evidence 泄漏风险

- risk：weak evidence 可能来自与 benchmark trait 或 accession panel 高度重叠的研究。
- why_it_matters：如果证据来源和 evaluation target 没有隔离，模型可能学习到泄漏标签。
- how_to_check_later：为每条 evidence 记录 publication、trait、panel、sample size、method、coordinate build 和是否与目标 trait 重叠。
- mitigation：后续构建 `weak_evidence_table` 时加入 provenance 和 leakage flag；评估设计中保留 negative controls。

## 8. weak evidence 被误写成 causal ground truth 的风险

- risk：known genes、GWAS lead SNPs、QTL intervals、LD blocks 被当作强监督 causal/non-causal 标签。
- why_it_matters：这会违反项目最高约束，并把 localization benchmark 错写成 causal classification。
- how_to_check_later：审阅 schema、文档、builder 和 evaluator，检查是否出现 causal positive/negative label 语义。
- mitigation：所有 evidence 字段使用 weak、support、signal、provenance 等命名；明确 `unknown != negative`。

## 9. 大文件下载和断点续传风险

- risk：3K Rice VCF/BAM/CRAM/FASTQ 相关文件体量很大，下载可能中断或产生不完整文件。
- why_it_matters：不完整 raw data 会污染后续 inventory、checksum 和 schema 构建。
- how_to_check_later：Phase 2 记录 file size、checksum、download time、download command、retry count 和临时文件状态。
- mitigation：下载脚本必须写 manifest 和 checksum；raw data 不覆盖已有文件；失败下载保留明确状态。

## 10. raw data 被误提交到 git 的风险

- risk：raw data、interim data、大型 archive 或私有路径被误加入 git。
- why_it_matters：会造成仓库膨胀、权限风险和数据治理问题。
- how_to_check_later：push 前检查 `git status`、文件大小、路径模式和 manifest。
- mitigation：Phase 2 前补充 `.gitignore`；raw data 只能存放在 `data/raw/` 并由 manifest 管理，不纳入 git。

