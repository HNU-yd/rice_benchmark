# 项目执行状态

## 2026-05-16 Phase 5A trait_state prototype

- 执行 prompt：`.codex/prompts/05a_build_trait_state_prototype.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段基于 A/B high-confidence accession mapping 构建 trait_state prototype。
- high-confidence accession subset 样本数：2268。
- 可用于 SNP-only trait prototype 的样本数：2268。
- 可用于 SNP+indel trait prototype 的样本数：2268。
- 识别到非 metadata trait 122 个，其中 continuous 0 个、categorical 99 个、binary 23 个。
- 推荐进入 v0.1-mini 的 trait 数：34。
- 生成报告：`reports/trait_state/trait_state_prototype_report.md`。
- 生成脚本：`scripts/trait_state/build_trait_state_prototype.py`。
- 生成配置：`configs/trait_state_v0_1.yaml`。
- `data/interim/trait_state/` 已生成本地 prototype tables，但不进入 git。
- 本阶段没有构建正式 benchmark schema，没有构建 split，没有训练模型，没有执行 phenotype prediction。

## 2026-05-16 Phase 5B trait descriptor review and frozen v0.1 traits

- 执行 prompt：`.codex/prompts/05b_review_trait_descriptors_and_freeze_v0_1_traits.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段审查 Phase 5A 推荐的 34 个 trait。
- 找到 descriptor 的 trait 数：34。
- weak evidence 关键词级匹配的 trait 数：34；这些匹配只作为 weak localization evidence 语义线索，不是 causal ground truth。
- 冻结进入 v0.1-mini 的 trait 数：9。
- 冻结 trait：`SPKF`、`FLA_REPRO`、`CULT_CODE_REPRO`、`LLT_CODE`、`PEX_REPRO`、`LSEN`、`PTH`、`CUAN_REPRO`、`CUDI_CODE_REPRO`。
- sensitivity-only trait 数：16。
- 暂缓或排除 trait 数：9。
- 生成报告：`reports/trait_state_review/trait_descriptor_review_report.md`。
- 生成配置：`configs/v0_1_frozen_traits.yaml`。
- `data/interim/trait_state_review/` 已生成本地 frozen trait id 文件，但不进入 git。
- 本阶段没有构建 Task 1 instances，没有构建 split，没有训练模型，没有执行 phenotype prediction。

## 2026-05-16 Phase 5C-prebuild v0.1-mini chr1 SNP input skeleton

- 执行 prompt：`.codex/prompts/05c_prebuild_v0_1_chr1_inputs.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段只构建 05C 的前置输入表，不构建 Task 1 instances。
- chr1 SNP 数：42466。
- chr1 window 数：865。
- variant-window mapping 行数：84886。
- chr1 weak evidence candidates 数：543。
- weak evidence 有坐标数量：42，来源为 Q-TARO interval，`coordinate_build_uncertain=true`。
- weak evidence 无坐标数量：501，来源为 Oryzabase chr1 gene/trait semantic evidence。
- 生成报告：`reports/v0_1_mini/v0_1_mini_input_skeleton_report.md`。
- 生成脚本目录：`scripts/build_v0_1/`。
- 生成配置：`configs/v0_1_mini.yaml`。
- `data/interim/v0_1_mini/` 已生成本地前置输入表，但不进入 git。
- 05C 所需输入表已补齐，可以重新执行 `.codex/prompts/05c_build_chr1_snp_task1_instances.md`。
- 本阶段没有训练模型，没有构建 evaluator，没有执行 phenotype prediction，没有把 weak evidence 写成 causal ground truth。

## 2026-05-16 Phase 5C chr1 SNP-only minimal Task 1 instances

- 执行 prompt：`.codex/prompts/05c_build_chr1_snp_task1_instances.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段基于 frozen v0.1 traits、high-confidence accession subset、chr1 SNP variant/window tables 和 chr1 weak evidence audit 构建 minimal Task 1 instance prototype。
- frozen trait 数：9。
- high-confidence accession 数：2268。
- chr1 SNP 数：42466。
- chr1 window 数：865。
- Task 1 instance 数：16265460。
- weak evidence 覆盖：722 个 trait-window pair，32590 个 trait-variant pair。
- `unknown_unlabeled` 已保留：instance 表中 14763798 行，window weak signal 表中 7063 行，variant weak label 表中 349604 行。
- 校验结果：`reports/task1_chr1_snp/task1_chr1_snp_validation.tsv` 中 10 项检查全部 `pass`，`validation_failed=0`。
- 生成报告：`reports/task1_chr1_snp/task1_chr1_snp_report.md`、`reports/task1_chr1_snp/task1_chr1_snp_instance_summary.tsv`、`reports/task1_chr1_snp/task1_chr1_snp_trait_summary.tsv`、`reports/task1_chr1_snp/task1_chr1_snp_window_signal_summary.tsv`、`reports/task1_chr1_snp/task1_chr1_snp_validation.tsv`。
- 生成脚本目录：`scripts/task1/`。
- 生成配置：`configs/task1_chr1_snp_v0_1.yaml`。
- `data/interim/task1_chr1_snp/` 已生成本地 instance、manifest、window signal 和 variant weak label 表，但不进入 git。
- 本阶段没有训练模型，没有构建 evaluator，没有构建 baseline，没有执行 GWAS，没有执行 phenotype prediction，没有把 trait_state 当 prediction label，没有把 weak evidence 写成 causal ground truth，也没有把 unknown/unlabeled 标记为 negative。

## 2026-05-16 Phase 6A minimal evaluator and baseline prototype

- 执行 prompt：`.codex/prompts/06a_minimal_evaluator_and_baseline_prototype.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段基于 chr1 SNP-only Task 1 window/variant weak signal tables 构建 minimal evaluator 和 baseline prototype。
- baseline 类型：`random_uniform`、`window_snp_density`、`genomic_position`、`shuffled_trait`。
- window-level baseline score 行数：31140。
- variant-level baseline score 行数：1528776。
- window-level 指标行数：36；variant-level 指标行数：36。
- top-k hit 明细：window 144 行，variant 144 行。
- window-level 摘要：`genomic_position` 在 mean weak_evidence_recall_at_50 上最高，为 0.383341；`random_uniform` 为 0.050673；`window_snp_density` 为 0.031001；`shuffled_trait` 为 0.001157。
- variant-level 摘要：`genomic_position` 在 mean weak_evidence_recall_at_1000 上最高，为 0.347243；`random_uniform` 为 0.067981；`window_snp_density` 为 0.010691；`shuffled_trait` 为 0。
- 校验结果：`reports/baselines_chr1_snp/baseline_validation.tsv` 中 10 项检查全部 `pass`，`validation_failed=0`。
- 生成报告：`reports/baselines_chr1_snp/baseline_evaluation_report.md`、`reports/baselines_chr1_snp/window_baseline_metrics.tsv`、`reports/baselines_chr1_snp/variant_baseline_metrics.tsv`、`reports/baselines_chr1_snp/topk_window_hits.tsv`、`reports/baselines_chr1_snp/topk_variant_hits.tsv`、`reports/baselines_chr1_snp/baseline_validation.tsv`。
- 生成脚本目录：`scripts/baselines/` 和 `scripts/eval/`。
- 生成配置：`configs/evaluator_chr1_snp_v0_1.yaml`。
- `data/interim/baselines_chr1_snp/` 已生成本地 score tables，但不进入 git。
- 本阶段没有训练模型，没有构建深度学习模型，没有执行 GWAS，没有构建 matched decoy，没有执行 phenotype prediction，没有把 weak evidence 写成 causal ground truth，没有把 unknown_unlabeled 当作 negative，也没有输出正式 AUROC / AUPRC。

## 2026-05-16 Phase 7A external rice knowledge collection

- 执行 prompt：`.codex/prompts/07a_collect_rapdb_funricegenes_msu.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段补充 RAP-DB、funRiceGenes 和 MSU / Rice Genome Annotation Project 第一批外部水稻知识库。
- RAP-DB 下载结果：10 个文件 downloaded，0 个 failed，0 个 skipped。
- funRiceGenes 下载结果：8 个文件 downloaded，0 个 failed，0 个 skipped。
- MSU / RGAP 下载结果：7 个文件 downloaded，0 个 failed，0 个 skipped。
- raw external knowledge 文件总数：25。
- 字段审查记录数：25。
- integration plan 记录数：25。
- 失败或需要人工下载记录数：0。
- 可进入 annotation layer 的关键文件包括 RAP-DB representative annotation / GTF、MSU RGAP all_models GFF3、functional annotation 和 locus brief info。
- 可进入 known gene evidence layer 的关键文件包括 funRiceGenes `geneInfo.table.txt`、RAP-DB `curated_genes.json` 和 `agri_genes.json`。
- 可进入 gene ID mapping layer 的关键文件包括 RAP-DB `RAP-MSU_2026-02-05.txt.gz` 和 funRiceGenes `famInfo.table.txt`。
- 更新 manifest：`manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv` 已登记 07A 下载文件与 sha256。
- 生成报告：`reports/external_knowledge/summary/external_knowledge_07a_report.md`、`external_knowledge_file_inventory.tsv`、`external_knowledge_download_failures.tsv`、`external_knowledge_schema_preview.tsv`、`external_knowledge_integration_plan.tsv`。
- 生成脚本目录：`scripts/external_knowledge/`。
- `data/raw/external_knowledge/` 已生成本地下载文件，但不进入 git。
- 本阶段没有训练模型，没有构建 Task 1 instances，没有构建 matched decoy，没有执行 GWAS，没有执行 phenotype prediction，没有把 known gene / QTL / annotation 写成 causal ground truth，也没有把没有 evidence 的区域当作 negative。

## 2026-05-16 Population covariate completion download

- 执行用户请求：补齐亚群、PC / kinship、来源批次和环境因素相关数据。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段新增下载 4 个 3K Rice pruned v2.1 PCA / kinship 文件：
  - `data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.eigenvec`
  - `data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.eigenval`
  - `data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.log`
  - `data/raw/variants/snp/pruned_v2.1/kinship/result.cXX.txt.bz2`
- 样本级 PCA 验证：3024 个样本加 header，14 列，PC1-PC12；样本顺序与 `pruned_v2.1.fam` 和 `core_v0.7.fam.gz` 一致。
- kinship 验证：`result.cXX.txt.bz2` 通过 bzip2 校验，解压后为 3024 行 x 3024 列。
- 已有相关数据确认：Qmatrix 3023 样本，RunInfo 25529 条测序 run 记录，Genesys MCPD passport 和 3K phenotype XLSX 均已在本地。
- AWS phenotype listing 中未发现独立 environment / site / season covariate 文件；当前环境相关字段仅能使用 phenotype `CROPYEAR`、passport origin / SUBTAXA / COLLSRC 和测序 run metadata 作为 proxy。
- 更新 manifest：`manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv` 已登记 4 个新增下载文件与 sha256。
- 生成报告：`reports/current_data_status/population_covariate_download_report.md`。
- 重新生成当前 raw 资产汇总：`reports/current_data_status/current_raw_file_summary.tsv`、`current_data_category_summary.tsv` 和 `current_manifest_checksum_status.tsv`，当前 raw 文件数为 103。
- 本阶段无下载失败文件，无需用户手工上传。
- 本阶段没有训练模型，没有构建 Task 1 instances，没有执行 GWAS，没有执行 phenotype prediction，没有把 covariate、weak evidence 或 unknown_unlabeled 写成 causal ground truth / negative label。

## 2026-05-16 Stratified residualization feasibility review

- 执行用户请求：评估 `subgroup x PC/kinship x 来源批次 x 环境` 残差化 / 分层标准化和同层负配对方案是否会因层过细而无法训练或评价。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 使用数据：9 个 v0.1 frozen traits，18804 条 frozen trait non-missing value rows，2096 个至少有一个 frozen trait 非缺失的 accession。
- 结论：严格硬分层不可行；`trait x subgroup` 可行，但叠加 `CROPYEAR`、country、SUBTAXA、exact library batch 后大量层变成 singleton 或小层。
- 关键统计：
  - `trait x subgroup`：81 个层，median size 193，层大小小于 20 的数量为 0。
  - `trait x subgroup x CROPYEAR`：1054 个层，median size 3，层大小小于 20 的数量为 928。
  - `trait x subgroup x country`：1958 个层，median size 2，层大小小于 20 的数量为 1707。
  - `trait x subgroup x CROPYEAR x country`：4055 个层，median size 1，层大小小于 20 的数量为 3841。
- `CROPYEAR` 覆盖弱：frozen trait rows 中只有 5257 / 18804 有已知年份，约 28.0%。
- PC 不能离散成精确 strata；PC1-PC5 四位小数分层几乎全是 singleton，应作为连续协变量或 kNN 距离约束。
- exact `library_names` 批次字段在 2096 个 accession 中 2096 个唯一，不能作为硬匹配批次层。
- 建议：硬约束保留 `trait_id`、`source_sheet` 和 broad subgroup；PC / kinship 用连续协变量或 nearest-neighbor；`CROPYEAR`、country、SUBTAXA、batch 用作软约束、协变量或 balance diagnostics。
- 生成报告：`reports/current_data_status/stratified_residualization_feasibility_report.md`。
- 本阶段没有修改 raw data，没有训练模型，没有构建新 labels，没有执行 phenotype prediction，没有把 unknown_unlabeled 当作 negative。

## 2026-05-17 Design v0.5.5 data protocol alignment

- 执行用户请求：根据 `/home/data2/projects/design` 中 v0.5.5 benchmark / method / constraints 文档处理 `rice_benchmark` 当前数据，并清理旧 prompt markdown。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 新增可复现脚本：`scripts/trait_state/build_design_v055_tables.py`。
- 执行命令：`python scripts/trait_state/build_design_v055_tables.py`。
- 读取数据：9 个 v0.1 frozen traits、2268 个 A/B high-confidence accession、Qmatrix broad subgroup、pruned v2.1 PC1-PC12、kinship 文件存在性、phenotype `CROPYEAR`、country / Genesys SUBTAXA / sequencing LibraryName proxy。
- 生成 full local tables：
  - `data/interim/design_v055/metadata/covariate_accession_table.tsv`
  - `data/interim/design_v055/metadata/trait_usability_table.tsv`
  - `data/interim/design_v055/metadata/trait_preprocessing_table.tsv`
  - `data/interim/design_v055/decoy/matching_field_availability_table.tsv`
  - `data/interim/design_v055/negative_pairs/negative_pair_protocol_table.tsv`
  - `data/interim/design_v055/negative_pairs/candidate_pool_size_table.tsv`
  - `data/interim/design_v055/negative_pairs/balance_diagnostics_table.tsv`
  - `data/interim/design_v055/qc_diagnostics/negative_pair_candidate_pool_summary.tsv`
  - `data/interim/design_v055/qc_diagnostics/v055_data_processing_validation.tsv`
  - `data/interim/design_v055/qc_diagnostics/v055_generated_table_schema.tsv`
- 生成 review reports / tables：
  - `reports/current_data_status/v055_data_processing_report.md`
  - `reports/current_data_status/v055_trait_usability_table.tsv`
  - `reports/current_data_status/v055_trait_preprocessing_table.tsv`
  - `reports/current_data_status/v055_matching_field_availability_table.tsv`
  - `reports/current_data_status/v055_covariate_field_availability_table.tsv`
  - `reports/current_data_status/v055_negative_pair_candidate_pool_summary.tsv`
  - `reports/current_data_status/v055_data_processing_validation.tsv`
  - `reports/current_data_status/v055_generated_table_schema.tsv`
- 处理结果：covariate accession rows 为 2268；frozen trait non-missing rows 为 18804；9 个 frozen traits 全部达到当前 main usability thresholds。
- 负配对协议结果：18804 条 non-missing frozen trait-state rows 均生成 `L1_main_hard_negative` mismatched trait-state pair；L2、L3 和 no-pair 记录数均为 0。这里的 negative 只表示训练中的 mismatched trait-state pair，不是 variant/window negative label。
- 候选池结果：各 trait 的 median L1 candidate pool size 为 108-235，所有行 L1 candidate pool size 均不低于 20。
- 协变量结论：Qmatrix 和 PC 覆盖 2268 / 2268；CROPYEAR known coverage 为 741 / 2268；CROPYEAR 继续作为 weak environment proxy，缺失值保留为 `unknown_env`，不能视为相同环境。
- matching field availability 结论：broad subgroup 可作为硬约束或 balance field；PC1-PC5 只能作为连续距离，不做精确 strata；kinship 只用于 LMM / covariance baseline 或 sensitivity；exact LibraryName 只用于 QC。
- 校验结果：`reports/current_data_status/v055_data_processing_validation.tsv` 中 6 项检查全部 `pass`，`validation_failed=0`，`validation_warn=0`。
- 清理旧 prompt markdown：删除 `.codex/prompts/*.md`，保留 `.codex/prompts/.gitkeep`。历史执行记录以 `status.md` 和 reports 为准。
- 本阶段没有修改 raw data，没有训练模型，没有构建 matched decoy，没有构建 frozen split，没有执行 GWAS / Evo2，没有执行 phenotype prediction，没有把 weak evidence 写成 causal ground truth，也没有把 unknown_unlabeled 当作 negative。

## 2026-05-17 Current data structure Chinese report

- 执行用户请求：说明当前数据结构，并写一份中文报告。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 生成报告：`reports/current_data_status/current_data_structure_report.md`。
- 报告内容覆盖：
  - 项目当前状态和科研边界。
  - `data/raw/`、`data/interim/`、`reports/`、`manifest/`、`configs/` 和 `scripts/` 的职责。
  - raw data category、manifest layer、accession mapping、trait state、v0.1-mini chr1 SNP、Task 1 prototype、baseline prototype 和 design v0.5.5 protocol layer。
  - 当前可用 benchmark surface：2268 个 A/B high-confidence accessions、9 个 frozen v0.1 traits、42466 个 chr1 SNP、865 个 chr1 windows、16265460 条 Task 1 prototype instances。
  - v0.5.5 协议层结果：18804 条 mismatched trait-state pair、9 个 traits 全部 usable for main、CROPYEAR 仍为 weak environment proxy。
- 结果分析、风险解释和下一步工程任务。
- 本阶段没有修改 raw data，没有新增模型或训练流程，没有构建新 labels，没有执行 phenotype prediction，没有把 weak evidence 写成 causal ground truth，也没有把 unknown_unlabeled 当作 negative。

## 2026-05-17 Phase 08A external knowledge v0.5.5 integration

- 执行 prompt：`.codex/prompts/08a_integrate_external_knowledge_v055.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段整合 RAP-DB、funRiceGenes、MSU / RGAP、Oryzabase、Q-TARO 和 reference annotation files，构建统一 annotation / evidence / gene ID mapping layer。
- 新增可复现脚本目录：`scripts/external_knowledge/`。
- 执行命令：`bash scripts/external_knowledge/run_build_external_knowledge_v055.sh` 和 `python -m py_compile scripts/external_knowledge/*.py`。
- 生成 full local tables：
  - `data/interim/external_knowledge_v055/annotation/gene_annotation_table.tsv`
  - `data/interim/external_knowledge_v055/mapping/gene_id_mapping_table.tsv`
  - `data/interim/external_knowledge_v055/evidence/known_gene_evidence_table.tsv`
  - `data/interim/external_knowledge_v055/evidence/trait_gene_evidence_table.tsv`
  - `data/interim/external_knowledge_v055/evidence/qtl_interval_evidence_table.tsv`
  - `data/interim/external_knowledge_v055/evidence/evidence_coordinate_mapping_table.tsv`
  - `data/interim/external_knowledge_v055/evidence/evidence_source_manifest.tsv`
  - `data/interim/external_knowledge_v055/qc_diagnostics/external_knowledge_manual_review_table.tsv`
  - `data/interim/external_knowledge_v055/qc_diagnostics/external_knowledge_validation.tsv`
- 生成 tracked report previews / summaries：
  - `reports/external_knowledge_v055/external_knowledge_integration_report.md`
  - `reports/external_knowledge_v055/external_knowledge_validation.tsv`
  - `reports/external_knowledge_v055/evidence_source_manifest.tsv`
  - `reports/external_knowledge_v055/*.preview.tsv`
- 表规模：gene annotation 125082 行，gene ID mapping 154144 行，known gene evidence 80635 行，trait-gene evidence 80635 行，QTL interval evidence 1051 行，evidence coordinate mapping 81686 行，source manifest 13 行，manual review 95848 行。
- gene ID mapping 成功率：funRiceGenes `famInfo` 1.0000，funRiceGenes `geneInfo` 1.0000，Oryzabase 0.9171，RAP-DB 0.8403，Q-TARO 0.0000。Q-TARO 的 mixed QTL/gene 字段保留为 interval-level weak localization evidence 或 manual review，不强行一对一 gene mapping。
- frozen 9 traits candidate pool：4696 条 exact trait-gene evidence 可进入主评价候选池；2391 条 ambiguous frozen-trait keyword matches 需要 manual review；其余 broader / missing trait evidence 不进入主评价候选池。
- evidence 层级：gene-level evidence/reference 80635 行，interval-level QTL evidence 1051 行，variant-level evidence 0 行。
- 坐标映射状态：`mapped_high_confidence` 73776 行，`gene_level_only` 6859 行，`region_level_only` 1033 行，`unmapped` 18 行。
- 校验结果：`reports/external_knowledge_v055/external_knowledge_validation.tsv` 中 13 项检查全部 `pass`，`validation_failed=0`。
- 校验覆盖：annotation 坐标有效性、mapping confidence、无 `training_label` usage、QTL 不作为 causal label、source manifest checksum、ambiguous mapping 进入 manual review、coordinate mapping 降级策略、主键唯一性。
- 当前限制：部分 source 坐标版本仍不一致，trait name normalization 仍有模糊映射，QTL interval 可能过宽，部分 source license / terms 需要继续确认，Q-TARO gene 字段不能可靠映射到统一 gene ID。
- 本阶段没有修改 raw data，没有训练模型，没有构建 matched decoy，没有冻结 split，没有扩展 whole-genome SNP+indel，没有引入 SV / PAV / pan-reference，没有报告正式 AUROC / AUPRC，没有把任何 evidence 写成 training label 或 causal ground truth。

## 2026-05-17 Phase 08B matched decoy v0.5.5 pre-layer

- 执行 prompt：`.codex/prompts/08B_build_matched_decoy_v055.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 本阶段基于 external knowledge v0.5.5 层和 chr1 SNP-only prototype，构建 matched decoy object、candidate pool、pair 和 diagnostics 前置层。
- 新增可复现脚本目录：`scripts/matched_decoy/`。
- 执行命令：
  - `python scripts/matched_decoy/build_matched_decoy_objects_v055.py`
  - `python scripts/matched_decoy/build_detectability_research_bias_v055.py`
  - `python scripts/matched_decoy/build_matched_decoy_candidate_pool_v055.py`
  - `python scripts/matched_decoy/build_matched_decoy_pairs_v055.py`
  - `python scripts/matched_decoy/validate_matched_decoy_v055.py`
  - `python -m py_compile scripts/matched_decoy/*.py`
- 生成 full local tables：
  - `data/interim/matched_decoy_v055/objects/matched_decoy_object_table.tsv`
  - `data/interim/matched_decoy_v055/candidate_pool/matched_decoy_candidate_pool.tsv`
  - `data/interim/matched_decoy_v055/pairs/matched_decoy_pair_table.tsv`
  - `data/interim/matched_decoy_v055/diagnostics/decoy_matching_diagnostics.tsv`
  - `data/interim/matched_decoy_v055/diagnostics/matching_field_availability_v055.tsv`
  - `data/interim/matched_decoy_v055/diagnostics/detectability_bias_table_v055.tsv`
  - `data/interim/matched_decoy_v055/diagnostics/research_bias_table_v055.tsv`
  - `data/interim/matched_decoy_v055/diagnostics/decoy_validation.tsv`
- 生成 tracked report previews / summaries：
  - `reports/matched_decoy_v055/matched_decoy_report.md`
  - `reports/matched_decoy_v055/decoy_validation.tsv`
  - `reports/matched_decoy_v055/decoy_matching_diagnostics.tsv`
  - `reports/matched_decoy_v055/matching_field_availability_v055.tsv`
  - `reports/matched_decoy_v055/*.preview.tsv`
- 表规模：matched decoy objects 114998 行，candidate pool 1019430 行，matched decoy pairs 169905 行，diagnostics 61 行，matching field availability 15 行，detectability proxy 114998 行，research-bias proxy 114998 行，validation 16 行。
- 主评价候选对象数：33981，其中 variant 32590、window 722、gene 623、qtl_interval 46。
- broader evidence objects excluded from main evaluation：74248；manual-review-required objects excluded from main evaluation：2611。
- candidate pool 覆盖率：gene、qtl_interval、variant 和 window 主候选对象均为 100%，每个主候选对象保留 30 个 matched background candidate。
- matched pair 覆盖率：gene、qtl_interval、variant 和 window 主候选对象均为 100%，每个主候选对象保留 5 个 matched background decoy。
- PEX_REPRO exact main-evaluation evidence object 数仍为 0，没有强行补标签。
- Q-TARO 生成 1051 个 qtl_interval objects，其中 46 个 chr1 exact trait-mapped interval objects 可进入当前 prototype candidate pool；Q-TARO 没有被强行映射为 high-confidence gene evidence。
- 匹配字段：coordinate、position_bin、gene_density、variant_density、annotation_richness、evidence_source_coverage、database_detectability、interval_length、research_bias 和 chr1_snp_coverage。
- 不可用字段：MAF、LD、missingness、mappability 和 recombination_rate；这些字段只在 diagnostics 中标记 unavailable，没有声称已经控制。
- detectability proxy：chr1 SNP coverage、window coverage、variant coverage 和 database detectability proxy。
- research-bias proxy：annotation record count、external knowledge hit count、database source count、trait evidence count 和 known-gene proximity proxy。
- 校验结果：`reports/matched_decoy_v055/decoy_validation.tsv` 中 16 项检查全部 `pass`，`validation_failed=0`。
- 校验覆盖：输出非空、object_id 唯一、主候选仅 exact frozen trait mapping、PEX_REPRO 不强行补 evidence、Q-TARO 不强行 gene mapping、broader/manual review 不进主候选、decoy 不写成 true negative、allowed_usage 不含 training_label、主键唯一性。
- 当前限制：candidate pool 是 bounded prototype，不是全基因组枚举；detectability 和 research bias 只是 proxy；当前没有 MAF / LD / mappability / recombination map / full callability；Q-TARO 坐标未 liftover。
- 本阶段没有修改 raw data，没有训练模型，没有冻结 split，没有构建正式 evaluator，没有扩展 whole-genome SNP+indel，没有引入 SV / PAV / pan-reference，没有报告正式 AUROC / AUPRC，没有把 evidence 当 causal ground truth，没有把 decoy 或 unknown_unlabeled 当 true negative。

## 2026-05-17 Phase 08C frozen split v0.5.5 chr1 SNP prototype

- 执行 prompt：`.codex/prompts/08C_freeze_chr1_snp_split_v055.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 08B 已 commit / push，当前输入 commit hash：`767f3e4`。
- 本阶段基于 08B matched decoy 前置层和 chr1 SNP-only prototype，构建 leakage-aware prototype split。
- 新增可复现脚本目录：`scripts/frozen_split/`。
- 执行命令：
  - `bash scripts/frozen_split/run_freeze_chr1_snp_split_v055.sh`
  - `python -m py_compile scripts/frozen_split/*.py`
- 生成 full local tables：
  - `data/interim/frozen_split_v055/units/split_unit_table.tsv`
  - `data/interim/frozen_split_v055/blocks/split_block_table.tsv`
  - `data/interim/frozen_split_v055/assignments/frozen_split_assignment.tsv`
  - `data/interim/frozen_split_v055/diagnostics/split_balance_diagnostics.tsv`
  - `data/interim/frozen_split_v055/diagnostics/split_leakage_check.tsv`
  - `data/interim/frozen_split_v055/diagnostics/split_validation.tsv`
  - `data/interim/frozen_split_v055/diagnostics/split_manifest.tsv`
- 生成 tracked report previews / summaries：
  - `reports/frozen_split_v055/frozen_split_report.md`
  - `reports/frozen_split_v055/split_balance_diagnostics.tsv`
  - `reports/frozen_split_v055/split_leakage_check.tsv`
  - `reports/frozen_split_v055/split_validation.tsv`
  - `reports/frozen_split_v055/split_manifest.tsv`
  - `reports/frozen_split_v055/*.preview.tsv`
- split unit 表规模：288045 行，其中 accession 2268、trait 9、region 865、evidence_object 114998、decoy_pair 169905。
- split block 表规模：117571 行，其中 accession_block 2268、trait_block 9、window_neighborhood_block 9、mixed_evidence_block 9、qtl_region_block 4、interval_overlap_block 4、gene_block 270、decoy_set_block 33981、manual_review_exclusion_block 2611、broader_evidence_exclusion_block 74248、excluded_no_exact_trait_mapping_block 4158。
- accession split：train 1606、dev 336、test 326；使用 broad_subgroup-stratified deterministic hash，random_seed 为 5508，并输出 PC1-PC5 balance summary。
- evidence object split：dev 22661、prototype_locked 2165、source_disjoint_or_temporal 9155、excluded_broader_evidence 74248、excluded_no_exact_trait_mapping 4158、excluded_manual_review 2611。
- block rule：非 QTL evidence / gene / window / variant 及其 decoy pair 使用 5 Mb mixed evidence proximity block；QTL interval 使用 overlap / nearby component，max gap 为 1 Mb；decoy pair 跟随 evidence object split。
- `prototype_locked_not_final=true` 写入所有 assignment；assignment 表不含 `final_locked`。
- PEX_REPRO main evidence rows after split 为 0，没有强行补 evidence。
- manual review 和 broader evidence 主评价 split 数量均为 0。
- decoy pair 和 evidence object split mismatch 为 0。
- leakage check：9 项全部 pass，blocking leakage 为 0。
- split validation：12 项全部 pass，validation_failed=0。
- 当前限制：仍是 chr1 SNP-only prototype，不是 final full benchmark split；region blocking 使用 coarse 5 Mb proximity bin；QTL source coordinates 未 liftover；MAF、LD、mappability、recombination rate 和 full callability 不可用。
- 本阶段没有修改 raw data，没有训练模型，没有构建正式 evaluator，没有报告 AUROC / AUPRC，没有扩展 whole-genome SNP+indel，没有引入 SV / PAV / pan-reference，没有把 evidence 当训练 label，没有把 matched decoy 或 unknown_unlabeled 当 true negative。

## 2026-05-17 Phase 09A split-aware evaluator scaffold v0.5.5

- 执行 prompt：`.codex/prompts/09A_build_split_aware_evaluator_scaffold_v055.md`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 08C 已 commit / push，当前输入 commit hash：`b8b5794`。
- 本阶段基于 08B matched decoy 层和 08C frozen split 层，构建 chr1 SNP-only prototype 的 split-aware evaluator scaffold。
- 新增可复现脚本目录：`scripts/evaluator_scaffold/`。
- 执行命令：
  - `bash scripts/evaluator_scaffold/run_build_evaluator_scaffold_v055.sh`
  - `python -m py_compile scripts/evaluator_scaffold/*.py`
- 生成 full local tables：
  - `data/interim/evaluator_scaffold_v055/inputs/evaluator_object_input_table.tsv`
  - `data/interim/evaluator_scaffold_v055/inputs/evaluator_decoy_input_table.tsv`
  - `data/interim/evaluator_scaffold_v055/outputs_schema/evaluator_score_input_schema.tsv`
  - `data/interim/evaluator_scaffold_v055/outputs_schema/evaluator_output_schema.tsv`
  - `data/interim/evaluator_scaffold_v055/tasks/evaluator_task_manifest.tsv`
  - `data/interim/evaluator_scaffold_v055/dry_run/baseline_score_dry_run_input.tsv`
  - `data/interim/evaluator_scaffold_v055/dry_run/evaluator_dry_run_join_check.tsv`
  - `data/interim/evaluator_scaffold_v055/diagnostics/evaluator_leakage_guard.tsv`
  - `data/interim/evaluator_scaffold_v055/diagnostics/evaluator_scaffold_validation.tsv`
  - `data/interim/evaluator_scaffold_v055/diagnostics/baseline_score_dry_run_join_summary.tsv`
- 生成 tracked report previews / summaries：
  - `reports/evaluator_scaffold_v055/evaluator_scaffold_report.md`
  - `reports/evaluator_scaffold_v055/evaluator_score_input_schema.tsv`
  - `reports/evaluator_scaffold_v055/evaluator_output_schema.tsv`
  - `reports/evaluator_scaffold_v055/evaluator_task_manifest.tsv`
  - `reports/evaluator_scaffold_v055/evaluator_dry_run_join_check.tsv`
  - `reports/evaluator_scaffold_v055/evaluator_leakage_guard.tsv`
  - `reports/evaluator_scaffold_v055/evaluator_scaffold_validation.tsv`
  - `reports/evaluator_scaffold_v055/baseline_score_dry_run_join_summary.tsv`
  - `reports/evaluator_scaffold_v055/*.preview.tsv`
- 表规模：evaluator object input 33981 行，evaluator decoy input 169905 行，score input schema 16 行，future output schema 17 行，task manifest 84 行，baseline score dry-run input 1559916 行，join check 7 行，leakage guard 10 行，validation 8 行。
- evaluator object 类型：variant 32590、window 722、gene 623、qtl_interval 46。
- evaluator object split：dev 22661、source_disjoint_or_temporal 9155、prototype_locked 2165。
- baseline dry-run join 覆盖：window 5560 / 31140，variant 131036 / 1528776，总体 136596 / 1559916。该 dry-run 只验证 baseline score 与 evaluator object / matched background decoy 的 schema 对齐和 join 可行性，不生成正式指标。
- decoy pair 跟随 evidence object split：169905 / 169905，通过率 100%。
- manual review 和 broader evidence 在 evaluator object input 中均为 0。
- score schema 中 `accession_id` 为 optional index only，不是必需评分字段，不能直接进入正式 evidence evaluation。
- `prototype_locked_not_final=true` 保留在 evaluator object input；没有使用 `final_locked` 作为字段名、split 值或 role 值。
- leakage guard 10 项全部 pass，blocking issue 为 0。
- scaffold validation 8 项全部 pass，validation_failed=0。
- 当前限制：仍是 chr1 SNP-only prototype scaffold；只定义输入、schema、任务 manifest、dry-run join 和 leakage guard；gene / QTL region score source 只在 schema 层定义，当前没有对应 score table；baseline score 只用于 dry-run，不形成正式主结果。
- 本阶段没有修改 raw data，没有训练模型，没有构建正式 evaluator，没有报告正式 AUROC / AUPRC，没有扩展 whole-genome SNP+indel，没有引入 SV / PAV / pan-reference，没有把 evidence 当训练 label，没有把 matched decoy 或 unknown_unlabeled 当 true negative。

## 2026-05-17 Phase 09B matched-ranking dry-run v0.5.5

- 执行 prompt：`.codex/prompts/09B_run_matched_ranking_dry_run_v055`。
- 当前工作目录：`/home/data2/projects/rice_benchmark`。
- 09A 已 commit / push，当前输入 commit hash：`e1639ac`。
- 本阶段基于 09A split-aware evaluator scaffold 和现有 chr1 SNP baseline score 表，执行 matched-ranking dry-run / evaluator adapter smoke test。
- 新增可复现脚本目录：`scripts/evaluator_dry_run/`。
- 执行命令：
  - `bash scripts/evaluator_dry_run/run_matched_ranking_dry_run_v055.sh`
  - `python -m py_compile scripts/evaluator_dry_run/*.py`
- 生成 full local tables：
  - `data/interim/evaluator_dry_run_v055/adapter/object_score_adapter_table.tsv`
  - `data/interim/evaluator_dry_run_v055/matched_sets/dry_run_matched_set_score_table.tsv`
  - `data/interim/evaluator_dry_run_v055/ranks/dry_run_rank_position_table.tsv`
  - `data/interim/evaluator_dry_run_v055/coverage/dry_run_score_coverage_table.tsv`
  - `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_missing_score_diagnostics.tsv`
  - `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_evaluator_adapter_contract.tsv`
  - `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_leakage_guard.tsv`
  - `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_validation.tsv`
- 生成 tracked report previews / summaries：
  - `reports/evaluator_dry_run_v055/matched_ranking_dry_run_report.md`
  - `reports/evaluator_dry_run_v055/object_score_adapter_table.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_score_coverage_table.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_evaluator_adapter_contract.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_leakage_guard.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_validation.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_matched_set_score_table.preview.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_rank_position_table.preview.tsv`
  - `reports/evaluator_dry_run_v055/dry_run_missing_score_diagnostics.preview.tsv`
- 表规模：object score adapter 4 行，dry-run matched set score 679620 行，dry-run rank position 135924 行，score coverage 188 行，missing-score diagnostics 1 行，adapter contract 7 行，leakage guard 10 行，validation 11 行。
- 使用 baseline score：`random_uniform`、`window_snp_density`、`genomic_position` 和 `shuffled_trait`，在 dry-run 输出中记录为 `baseline:<baseline_name>`。
- adapter 规则：
  - variant：`ADAPT_VARIANT_EXACT_V1`，exact variant-level score。
  - window：`ADAPT_WINDOW_EXACT_V1`，exact window-level score。
  - gene：`ADAPT_GENE_WINDOW_MEAN_V1`，overlapping-window mean，仅 dry-run diagnostic。
  - qtl_interval：`ADAPT_QTL_INTERVAL_WINDOW_MEAN_V1`，overlapping-window mean，仅 dry-run diagnostic。
- rank diagnostic 行数：variant 130360、window 2888、gene 2492、qtl_interval 184。
- split-level rank diagnostic 行数：dev 90644、prototype_locked 8660、source_disjoint_or_temporal 36620。
- 可 rank object/source rows：135924 / 135924；因缺失 score 不能 rank 的 object/source rows：0。
- score coverage：dev、prototype_locked 和 source_disjoint_or_temporal 的 rankable coverage 与 all-decoy score coverage 均为 1.0。
- manual review / broader evidence 进入 matched-ranking 的数量为 0。
- decoy rows 写成 true negative 的数量为 0；`uses_true_negative=false` 且 `decoy_semantics=matched_background`。
- unknown / unlabeled 写成 negative 的数量为 0；`uses_unknown_as_negative=false`。
- `accession_id` 没有作为 09B score input/output 字段。
- validation 11 项全部 pass，blocking issue 为 0；leakage guard 10 项全部 pass。
- 当前限制：仍是 chr1 SNP-only dry-run；rank / percentile / top1 / top5 字段只作为流程诊断，不是正式 top-k hit rate；gene / qtl_interval 的 adapter 聚合规则尚未 formalize；没有跨 trait / split / object_type 的正式 metric 聚合。
- 本阶段没有修改 raw data，没有训练模型，没有构建正式 evaluator，没有报告正式 AUROC / AUPRC，没有构建 final locked evaluation，没有扩展 whole-genome SNP+indel，没有引入 SV / PAV / pan-reference，没有把 evidence 当训练 label，没有把 matched decoy 或 unknown_unlabeled 当 true negative。
