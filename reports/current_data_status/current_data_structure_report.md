# 当前数据结构报告

## 一、项目状态

当前仓库 `rice_benchmark` 是一个面向 3K Rice 的 `trait-conditioned SNP/indel localization` benchmark 构建仓库。当前可实际运行和审阅的数据面仍是 `v0.1 chr1 SNP-only prototype`，并已经额外完成了 v0.5.5 设计文档要求的数据协议对齐。

当前主线不是性状预测，也不是性状分类或因果/非因果二分类。当前所有 trait value / trait state 只作为模型条件信号或配对学习输入；GWAS、QTL、known genes、Oryzabase、Q-TARO 和外部知识库只能作为 `weak localization evidence`、annotation、解释层或后续评价证据，不能写成 `causal ground truth`。未被 evidence 覆盖的 variant/window 仍是 `unknown_unlabeled`，不能当作 negative label。

当前已经形成的主要结构是：

- raw source layer：`data/raw/`
- intermediate table layer：`data/interim/`
- review/report layer：`reports/`
- manifest/checksum layer：`manifest/`
- frozen config layer：`configs/`
- reproducible script layer：`scripts/`

其中 `data/raw/` 和 `data/interim/` 被 `.gitignore` 排除，不进入 git；可审阅、可协作的轻量结果放在 `reports/`、`manifest/`、`configs/` 和 `scripts/`。

## 二、物理目录结构

| 路径 | 作用 | 是否进 git | 当前状态 |
|---|---|---|---|
| `data/raw/` | 下载得到的原始数据、压缩包、原始表格、原始 annotation/evidence 文件 | 否 | 当前 audit 记录 103 个 raw files |
| `data/interim/` | 从 raw data 生成的中间表、prototype tables、protocol tables | 否 | 已包含 accession、trait、v0.1、Task 1、baseline 和 v0.5.5 protocol 层 |
| `reports/` | 审阅报告、验证表、状态摘要、轻量 review tables | 是 | 当前主要审阅入口 |
| `manifest/` | source inventory、download manifest、checksum table 及 schema | 是 | 登记下载文件与 checksum 状态 |
| `configs/` | frozen traits、v0.1-mini、Task 1、evaluator 等配置 | 是 | 当前冻结 v0.1 traits 和 chr1 SNP prototype 配置 |
| `scripts/` | 所有可复现处理脚本 | 是 | 每个已生成数据层都有命令行脚本 |
| `.codex/prompts/` | 历史 prompt 目录 | 是，仅保留目录 | 旧 prompt markdown 已清理，只保留 `.gitkeep` |

## 三、Raw Data 层

`data/raw/` 目前按来源和数据类型组织，不直接参与 git review。当前 raw category 摘要如下。

| raw 类别 | 文件数 | 总大小约 | 主要用途 | 当前边界 |
|---|---:|---:|---|---|
| accession metadata | 4 | 0.932 GB | accession ID mapping、RunInfo、Genesys passport、SNP-Seek SRA list | accession ID 只作 join key，不作模型 token |
| SNP genotype | 33 | 2.178 GB | SNP backbone、chr1 SNP prototype、后续全基因组 SNP 表 | 不构造 naive negative label |
| pruned SNP / PCA / kinship | 12 | 0.829 GB | Qmatrix、PC、kinship、协变量和诊断 | PC 只能作连续距离或 kNN，不作精确 strata |
| indel genotype | 5 | 0.234 GB | 后续 SNP+indel benchmark 扩展 | 尚未进入当前 Task 1 prototype |
| reference | 1 | 0.111 GB | IRGSP-1.0 reference window context | 坐标体系必须保持一致 |
| annotation | 4 | 0.013 GB | gene annotation、candidate gene explanation | 不是训练标签 |
| phenotype / trait | 1 | 0.001 GB | trait_state 构建 | 不是 phenotype prediction target |
| Qmatrix / population structure | 1 | 0.0001 GB | broad subgroup assignment | 用于 matching/diagnostics |
| Q-TARO | 1 | 0.0001 GB | QTL interval weak evidence | 不是 causal ground truth |
| Oryzabase | 1 | 0.011 GB | known/cloned gene weak evidence | 不是 causal ground truth |
| listing / metadata | 18 | 0.003 GB | AWS listing、README、checksum metadata | 只作数据审计 |
| external knowledge / other | 22 | 0.052 GB | funRiceGenes、RAP-DB、MSU/RGAP 等整合输入 | annotation/evidence/explanation only |
| Sanciangco / Dataverse | 2 | metadata only | GWAS dataset metadata | 大文件未进入 `data/raw/` |

当前环境协变量不完整。已有的环境 proxy 主要是 phenotype 表中的 `CROPYEAR`，以及 country、SUBTAXA、RunInfo/LibraryName 等来源或批次 proxy。项目不能声称已经完成完整环境校正，因为缺少统一的 site/location/season 表。

## 四、Manifest 层

Manifest 层负责回答“文件从哪里来、是否下载、是否登记 checksum、当前状态如何”。

核心文件：

- `manifest/source_inventory.tsv`
- `manifest/download_manifest.tsv`
- `manifest/checksum_table.tsv`
- `manifest/*.schema.tsv`
- `reports/current_data_status/current_raw_file_summary.tsv`
- `reports/current_data_status/current_data_category_summary.tsv`
- `reports/current_data_status/current_manifest_checksum_status.tsv`

当前 `current_raw_file_summary.tsv` 有 103 条 raw file audit 记录。Manifest 只说明文件状态和审计结果，不代表所有 raw 文件都已经可直接进入模型。

## 五、Interim 中间表层

### 5.1 Accession Mapping

该层解决 genotype sample、phenotype accession、SRA/RunInfo、Genesys passport、Qmatrix 之间的 ID 对齐。

| 表 | 数据行数 | 作用 |
|---|---:|---|
| `data/interim/accession_mapping/genotype_sample_master.tsv` | 3024 | genotype sample master list |
| `data/interim/accession_mapping/accession_mapping_master.tsv` | 3024 | unified accession mapping master |
| `data/interim/accession_mapping/phenotype_accession_candidates.tsv` | 14002 | phenotype accession candidates |
| `data/interim/accession_mapping/phenotype_to_genotype_candidate_matches.tsv` | 16178 | phenotype-genotype candidate matches |
| `data/interim/accession_mapping/manual_review_candidates.tsv` | 10204 | C-level 或 ambiguous review candidates |
| `data/interim/accession_mapping/unmatched_phenotype_accessions.tsv` | 559 | 无 high-confidence genotype mapping 的 phenotype accession |

当前主 benchmark 只使用 A/B high-confidence genotype-phenotype mapping。C 级候选必须人工审查；D 级或 unmatched samples 不解释为 negative，也不进入主 trait-conditioned training/evaluation。

### 5.2 Trait State

该层从 high-confidence accession 和 phenotype XLSX 中构建 trait table、trait value table 和 trait state table。

| 表 | 数据行数 | 作用 |
|---|---:|---|
| `data/interim/trait_state/high_confidence_accessions.tsv` | 2268 | A/B high-confidence accession subset |
| `data/interim/trait_state/trait_table_prototype.tsv` | 134 | trait metadata prototype |
| `data/interim/trait_state/trait_value_table_prototype.tsv` | 84295 | accession-trait value prototype |
| `data/interim/trait_state/trait_state_table_prototype.tsv` | 71630 | non-missing trait_state rows |
| `data/interim/trait_state_review/frozen_v0_1_trait_ids.txt` | 9 | frozen v0.1 trait IDs |

当前 frozen v0.1 traits 为：

`SPKF`、`FLA_REPRO`、`CULT_CODE_REPRO`、`LLT_CODE`、`PEX_REPRO`、`LSEN`、`PTH`、`CUAN_REPRO`、`CUDI_CODE_REPRO`。

这些 trait state 是模型条件信号，不是 phenotype prediction label。

### 5.3 v0.1-mini Chr1 SNP 输入骨架

该层是当前 Task 1 prototype 的 genome/window/variant 输入骨架，仅覆盖 chr1 SNP。

| 表 | 数据行数 | 作用 |
|---|---:|---|
| `data/interim/v0_1_mini/chromosome_map.tsv` | 12 | chromosome coordinate map |
| `data/interim/v0_1_mini/snp_table_chr1_v0_1.tsv` | 42466 | chr1 SNP table |
| `data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv` | 42466 | chr1 SNP variant table |
| `data/interim/v0_1_mini/window_table_chr1_v0_1.tsv` | 865 | chr1 reference windows |
| `data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv` | 84886 | variant-window overlapping mapping |
| `data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv` | 543 | chr1 weak evidence candidates |

当前仍是 chr1 SNP-only prototype。Whole-genome SNP+indel、matched decoy、frozen split 和 final locked evidence split 尚未完成。

### 5.4 Task 1 Chr1 SNP Prototype

该层把 frozen traits、high-confidence accessions、chr1 SNP、window 和 weak evidence 合成 Task 1 prototype。

| 表 | 数据行数 | 作用 |
|---|---:|---|
| `data/interim/task1_chr1_snp/task1_chr1_snp_instances.tsv` | 16265460 | accession-trait-window/variant prototype instances |
| `data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv` | 7785 | trait-window weak signal table |
| `data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv` | 382194 | trait-variant weak evidence table |
| `data/interim/task1_chr1_snp/task1_chr1_snp_instance_manifest.tsv` | 11 | instance generation manifest |

这里的 weak label / weak signal 只是 `weak localization evidence`。没有 evidence 的 row 是 `unknown_unlabeled`，不能作为 true negative。

### 5.5 Baseline Prototype

该层存放最小 evaluator / baseline prototype 的 score tables。

| 表 | 数据行数 | 作用 |
|---|---:|---|
| `data/interim/baselines_chr1_snp/window_baseline_scores.tsv` | 31140 | window-level baseline scores |
| `data/interim/baselines_chr1_snp/variant_baseline_scores.tsv` | 1528776 | variant-level baseline scores |

当前 baseline 包括 `random_uniform`、`window_snp_density`、`genomic_position` 和 `shuffled_trait`。这些只是 prototype sanity check，不是 final formal AUROC / AUPRC benchmark，因为 matched decoy 还没有构建。

### 5.6 Design v0.5.5 Protocol Layer

该层是根据 `/home/data2/projects/design` 中 v0.5.5 设计文档新固化的数据协议层，负责把协变量可用性、trait usability、trait preprocessing、matching field availability 和 negative pair protocol 明确成表。

| 表 | 数据行数 | 作用 |
|---|---:|---|
| `data/interim/design_v055/metadata/covariate_accession_table.tsv` | 2268 | accession-level covariate table |
| `data/interim/design_v055/metadata/trait_usability_table.tsv` | 9 | trait usability audit |
| `data/interim/design_v055/metadata/trait_preprocessing_table.tsv` | 9 | frozen preprocessing protocol |
| `data/interim/design_v055/decoy/matching_field_availability_table.tsv` | 12 | matching/detectability field availability |
| `data/interim/design_v055/negative_pairs/negative_pair_protocol_table.tsv` | 18804 | mismatched trait-state pair protocol |
| `data/interim/design_v055/negative_pairs/candidate_pool_size_table.tsv` | 18804 | row-level candidate pool diagnostics |
| `data/interim/design_v055/negative_pairs/balance_diagnostics_table.tsv` | 18804 | selected-pair balance diagnostics |
| `data/interim/design_v055/qc_diagnostics/negative_pair_candidate_pool_summary.tsv` | 9 | trait-level candidate pool summary |
| `data/interim/design_v055/qc_diagnostics/v055_data_processing_validation.tsv` | 6 | validation checks |
| `data/interim/design_v055/qc_diagnostics/v055_generated_table_schema.tsv` | 128 | generated table schema records |

v0.5.5 当前协议结论：

- 9 个 frozen traits 全部达到当前 main usability threshold。
- 2268 个 high-confidence accession 都有 Qmatrix 和 PC。
- 18804 条 non-missing frozen trait-state rows 全部生成 L1 main hard mismatched trait-state pair。
- L2、L3 和 no-pair 记录数均为 0。
- `CROPYEAR` known coverage 为 741 / 2268，只能作为 weak environment proxy。
- broad subgroup 可作为 hard constraint 或 balance field。
- PC1-PC5 只能作为连续距离，不做精确离散 strata。
- kinship 只用于 LMM / covariance baseline 或 sensitivity。
- exact LibraryName / Run 只用于 QC，不用于 trait residualization 或 hard matching。

注意：`negative_pair_protocol_table.tsv` 中的 negative 只表示训练中的 mismatched trait-state pair，不是 variant/window negative label。

## 六、Reports 审阅层

`reports/` 是当前主要审阅界面。关键报告分布如下。

| 报告区域 | 关键文件 |
|---|---|
| current data status | `project_data_status_summary.md`、`current_raw_file_summary.tsv`、`current_data_category_summary.tsv`、`population_covariate_download_report.md`、`stratified_residualization_feasibility_report.md`、`v055_data_processing_report.md`、`current_data_structure_report.md` |
| accession mapping | `accession_mapping_summary.md`、`mapping_confidence_summary.tsv`、`C_level_review_policy.md` |
| trait state | `trait_state_prototype_report.md`、`v0_1_trait_recommendation.tsv` |
| trait review | `trait_descriptor_review_report.md`、`frozen_v0_1_traits.tsv` |
| v0.1-mini | `v0_1_mini_input_skeleton_report.md`、`weak_evidence_mapping_summary.md` |
| Task 1 | `task1_chr1_snp_report.md`、`task1_chr1_snp_validation.tsv` |
| baselines | `baseline_evaluation_report.md`、`baseline_validation.tsv` |
| external knowledge | `external_knowledge_07a_report.md`、`external_knowledge_integration_plan.tsv` |

Full `data/interim/` 表不进 git，但都应能由 `scripts/` 重建；`reports/` 中的轻量表和报告用于 review。

## 七、当前数据流

当前数据流可以概括为：

1. 下载 source files 到 `data/raw/`，并登记到 `manifest/`。
2. 运行 inventory / audit 脚本，生成 raw file summary 和 source status。
3. 构建 accession mapping：统一 genotype sample、phenotype accession、RunInfo、Genesys、Qmatrix。
4. 构建 trait_state：从 high-confidence accession 和 phenotype XLSX 得到 trait table、trait value table、trait state table。
5. 冻结 v0.1 traits：从推荐 traits 中审查并冻结 9 个 trait。
6. 构建 v0.1-mini chr1 SNP skeleton：生成 chr1 SNP、window、variant-window mapping、weak evidence candidate。
7. 构建 Task 1 chr1 SNP prototype：生成 accession-trait-window/variant instances 和 weak signal tables。
8. 运行 baseline/evaluator prototype：生成 window / variant ranking scores 和 validation report。
9. 执行 v0.5.5 data protocol alignment：生成 covariate、trait usability、preprocessing、matching availability、negative pair 和 candidate pool diagnostics。

## 八、当前可用 Benchmark Surface

当前真正可用的数据面如下：

- accession scope：2268 个 A/B high-confidence accessions。
- trait scope：9 个 frozen v0.1 traits，全部来自 `Data < 2007`。
- variant/window scope：chr1 SNP-only prototype，42466 个 chr1 SNP，865 个 chr1 windows。
- Task 1 instance scope：16265460 行 prototype instances。
- weak evidence scope：Q-TARO 和 Oryzabase 已被尽可能映射到 chr1 weak evidence candidates。
- covariate scope：broad subgroup 和 PC 对 high-confidence accessions 完整可用；CROPYEAR 只部分可用。
- protocol scope：v0.5.5 的 trait usability、trait preprocessing、matching field availability 和 negative pair protocol 已固化。

当前结构还不是最终 full benchmark。尚缺的关键层包括：

- whole-genome SNP+indel tables。
- matched decoy tables。
- accession-disjoint / region-holdout / trait-disjoint / evidence splits。
- final locked evidence split。
- source-disjoint 或 temporal evidence split。
- detectability bias table。
- research bias matching table。
- model output schema，包括 accession-level intermediate scores 和 trait-level localization maps。

## 九、结果分析

当前数据结构已经从“原始下载和 prototype 构建”推进到了“可审计的数据协议层”。最重要的进展是 v0.5.5 设计要求中关于协变量、分层、防混杂和 negative pairing 的规则已经被物化为表，而不是只停留在说明文档中。

从可训练性看，当前 9 个 frozen traits 的样本量和 broad subgroup 分布可以支撑主 benchmark prototype。`trait x subgroup` 层大小稳定，L1 mismatched trait-state candidate pool 对所有 18804 条 non-missing frozen trait-state rows 都足够，说明主配对训练的候选池不会因为 subgroup 硬约束而碎裂。

从防混杂看，当前结构明确避免了过细硬分层。PC 没有被离散成精确 strata，CROPYEAR/country/SUBTAXA/batch 没有被强行作为全局 hard constraints。这个选择符合 v0.5.5 设计文档：先调查覆盖率、层大小和候选池，再决定字段角色。

从 benchmark 完整性看，当前仍处于 chr1 SNP-only prototype。它已经足够用于流程验证、schema 审阅、baseline sanity check 和设计协议落地，但还不能支撑最终论文式 full benchmark 结论。

## 十、风险解释

1. `CROPYEAR` 覆盖弱，且不是完整环境信息。它不能替代 site、location、season 或 field trial metadata。
2. exact `LibraryName` / Run 过细，不能用于 trait residualization 或 hard negative matching，只能作为测序 QC metadata。
3. 当前 weak evidence 主要来自 Q-TARO / Oryzabase / external knowledge，证据层仍不完整，不能写成完整真值。
4. 当前 chr1 SNP-only scope 不能代表全基因组 SNP+indel benchmark 的最终难度和偏差。
5. Baseline prototype 没有 matched decoy，因此不能报告正式 AUROC / AUPRC。
6. Detectability 和 research-bias matching 字段仍缺失或只是 partial proxy，后续 decoy 构建时必须显式记录不可用字段。
7. `negative_pairs/` 目录名和字段名可能引起误解，必须持续说明这里的 negative 是 mismatched trait-state pair，不是 locus negative。

## 十一、下一步工程任务

1. 把 RAP-DB、funRiceGenes、MSU/RGAP、Oryzabase 和 Q-TARO 整合成统一 gene annotation / known-gene evidence / gene ID mapping layer。
2. 构建 matched decoy 表，并同步生成 `matching_field_availability_table`、detectability proxy、research-bias proxy 和 decoy validation。
3. 冻结 accession-disjoint、region-holdout、trait-disjoint、evidence split 和 source-disjoint / temporal split。
4. 从 chr1 SNP-only prototype 扩展到 whole-genome SNP+indel 输入表，但必须先完成 sample order、coordinate build、indel representation 和 schema 校验。
5. 定义并固化模型输出目录结构：`outputs/accession_level/`、`outputs/trait_level/`、`outputs/candidate_regions/`、`outputs/priority_snp_indel/`。
6. 在 matched decoy 完成后，再升级 evaluator，避免在 unknown/unlabeled 背景上报告误导性的 formal AUROC / AUPRC。
