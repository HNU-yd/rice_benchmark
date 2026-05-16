# Accession ID Harmonization 说明

## 背景

本项目的第一版 benchmark 以 3K Rice accession-level SNP/indel genotype backbone 为主位数据。实际数据来自多个系统：genotype / PLINK / Qmatrix、phenotype XLSX、`3K_list_sra_ids.txt`、NCBI RunInfo、Genesys MCPD passport，以及 SRA / BioSample / Run metadata。不同系统服务于不同环节，因此使用的 ID 体系并不相同，不能假设存在一个可以直接跨表 join 的单一 accession 字段。

genotype 端通常使用 B001、CX、IRIS_313 等 3K DNA/IRIS ID。phenotype 端使用 `STOCK_ID`、`GS_ACCNO`、`NAME`、`Source_Accno` 等 accession-like 字段。SRA 元数据使用 ERS、ERR、BioSample 和 Run 等测序层 ID。Genesys MCPD 使用 `ACCENUMB`、`ACCENAME`、country、passport 和 DOI 等种质资源字段。因此，phenotype 表与 genotype FAM/Qmatrix 的直接 overlap 为 0 或较低，是多源数据整合中的预期问题，而不是单一文件损坏。

本项目将该问题作为 accession ID harmonization 处理：通过多源证据链建立高置信 genotype–phenotype 对照，并只把高置信子集用于 trait-conditioned benchmark。

## 为什么会不匹配

1. genotype ID 和 phenotype ID 属于不同数据系统。PLINK FAM 和 Qmatrix 记录的是 genotype sample ID，phenotype XLSX 记录的是材料、stock 或 source accession。
2. 一个水稻材料可能存在多个名称、别名、IRGC 编号、stock 编号和不同数据库中的规范写法。
3. SRA / Run / BioSample 是测序元数据层，用于追踪测序样本与 run，不等同于 phenotype accession。
4. Genesys MCPD 是 passport 补充来源，覆盖约 2700 个 accession，不覆盖完整 3024 个 genotype 样本。
5. phenotype 表不是所有 genotype accession 都有 trait 记录，因此存在真实的 unmapped genotype samples。
6. 名称匹配容易产生假阳性，尤其在别名、衍生系、近等基因系和重复 stock 存在时，不能直接作为正式映射。

## 使用的数据源

`core_v0.7.fam.gz`：SNP genotype sample ID 来源。

`Nipponbare_indel.fam.gz`：indel genotype sample ID 来源。

`pruned_v2.1.fam`：pruned SNP sample ID 来源，用于补充 sample ID 覆盖和后续 QC / GWAS 辅助。

`Qmatrix-k9-3kRG.csv`：群体结构和 sample ID 辅助来源，可作为后续自跑 GWAS covariate 候选。

`3K_list_sra_ids.txt`：3K DNA/IRIS ID、stock name、country 和 SRA accession 的主桥梁。

`PRJEB6180_runinfo.csv`：SRA accession 到 Run、Experiment、BioSample 和 LibraryName 的补充桥梁。

Genesys MCPD：IRGC、passport、accession name、country、subtaxa、DOI 和 URL 的补充来源。

`3kRG_PhenotypeData_v20170411.xlsx`：trait_state 的原始 phenotype 来源，不作为 `phenotype prediction` target。

## ID 对齐链路

当前对齐链路为：

```text
genotype sample ID
-> 3K DNA/IRIS ID
-> stock name / SRA accession
-> NCBI RunInfo / BioSample / Run
-> Genesys passport / IRGC / accession name
-> phenotype STOCK_ID / GS_ACCNO / NAME / Source_Accno
```

这是一条多证据链，不是单字段匹配。每条候选映射都需要保留 source、match rule、confidence 和 manual review flag。只有硬 ID 或多源一致证据支持的映射，才可以进入后续 trait_state / trait_value_table prototype。

## 置信度分级

A 级：phenotype 表中直接出现 genotype sample ID 或 3K DNA/IRIS ID 的精确匹配。

B 级：通过 SRA accession、IRGC、GS_ACCNO、Source_Accno 或多源 ID 证据链建立的高置信匹配。

C 级：仅通过 normalized stock name 或材料名称相似建立的候选匹配，缺乏硬 ID 支撑。

D 级：没有可用 phenotype mapping。

主 benchmark 只使用 A/B 级。C 级只进入人工审查，不进入主分析。D 级不进入 trait-conditioned training/evaluation。

## 当前映射结果

当前 genotype union 样本数为 3024，其中 core SNP 样本数为 3024，indel 样本数为 3023，pruned SNP 样本数为 3024，Qmatrix 样本数为 3023。

3024 个 genotype 样本中：

- 3024 个可以匹配到 `3K_list_sra_ids.txt`。
- 3024 个可以匹配到 NCBI RunInfo。
- 2706 个可以匹配到 Genesys MCPD。
- 2269 个具有 A/B 级 phenotype mapping。
- 12 个只有 C 级名称候选匹配。
- 743 个没有 phenotype mapping。

因此，2269 个 A/B 级样本将作为 trait-conditioned prototype 的 high-confidence accession subset。C 级和 D 级不进入主 benchmark。

## C 级样本处理原则

C 级只表示名称级候选匹配。由于水稻材料存在别名、衍生系、近等基因系、重复 stock 和命名变体，仅靠名称相似可能产生错误 genotype–phenotype 配对。因此 C 级样本默认不进入主 benchmark。

只有在人工复核中发现 IRGC、GS_ACCNO、Source_Accno、SRA accession、BioSample 或其他硬 ID 证据时，C 级样本才可以升级。升级后的样本必须标记为 `manual_reviewed`，并保留审查记录、证据字段、决策人、日期和版本。

## C 级人工审查标准

人工审查至少检查：

1. 是否存在 IRGC 编号精确一致。
2. 是否存在 GS_ACCNO 或 Source_Accno 精确一致。
3. 材料名称是否唯一匹配。
4. 是否存在多个候选 genotype。
5. 国家来源是否一致。
6. 是否存在衍生系、近等基因系或命名变体风险。
7. Genesys passport 与 3K stock name 是否冲突。

人工决策只能使用以下值：

```text
accept_as_B_manual
keep_as_C_excluded
reject_as_D
needs_more_evidence
```

默认策略是：除非有硬 ID 证据，否则 C 级不升级。

## 为什么排除未映射样本

743 个 D 级样本不是数据错误，而是当前 phenotype 数据源中没有可高置信映射的 trait 记录。这些样本仍可用于 genotype-only 统计、MAF/LD 估计或自监督 genotype representation。但它们不能用于 trait-conditioned training/evaluation，因为缺少可靠 trait_state。

未映射样本也不能作为 negative。`unknown != negative` 是本 benchmark 的基本原则。

## 审稿风险与防御

问题 1：为什么不是 3024 个样本都用于 trait-conditioned benchmark？

回答：只有 2269 个样本具有高置信 genotype–phenotype 映射。为避免错误配对，主分析只使用 A/B 级 high-confidence subset。

问题 2：排除样本是否造成偏差？

回答：后续将报告 included / excluded accession 的群体结构、国家来源和 genotype 可用性分布，并在固定 high-confidence subset 上构建 split。

问题 3：为什么 C 级不用？

回答：C 级仅由名称匹配产生，缺乏硬 ID 证据。为避免 false match，主分析排除 C 级样本。

问题 4：未映射样本是否作为 negative？

回答：不会。未映射或无 trait 的样本不作为 negative，也不进入 trait-conditioned 分析。

## 对后续 benchmark 的影响

1. high-confidence accession subset 将被冻结。
2. `trait_value_table` 只从 A/B 级样本构建。
3. split 只能在 high-confidence subset 内生成。
4. C 级样本如果人工升级，必须版本化记录。
5. D 级样本不参与 trait-conditioned training/evaluation。
6. unknown / unmapped 不等于 negative。
