# 3K Rice SNP/indel Trait-conditioned Localization Benchmark

本仓库用于构建一个面向 3K Rice 的 `trait-conditioned SNP/indel localization` benchmark。核心任务是在给定 trait state 与 accession context 的条件下，对候选 SNP/indel loci、reference window 和 candidate regions 进行定位与打分；GWAS、QTL、known genes、LD blocks、credible intervals 和 trait annotations 只能作为 `weak localization evidence`，不能作为 `causal ground truth`。

## 当前范围

- 主位数据：3K Rice only。
- 变异范围：SNP 和 indel only。
- 主任务：Task 1，`trait-conditioned SNP/indel localization`。
- 补充任务：Task 2，`reference-conditioned candidate SNP/indel edit hypothesis generation`。
- Evidence 原则：`weak localization evidence` 不是 `causal ground truth`，并且 `unknown != negative`。

## 明确不做

- `phenotype prediction`。
- accession phenotype value prediction。
- `trait classification`。
- causal/non-causal strong supervised variant classification。
- SV、PAV 或 CNV benchmark construction。
- pan-reference、multi-reference 或 multi-species benchmark construction。
- genome foundation model pretraining。
- Phase 0 不实现 Evo2 相关代码。

## 计划流程

Phase 0: 仓库治理与项目约束
Phase 1: 3K Rice 数据源清单
Phase 2: 下载 raw data，计算 checksum，并完成 manifest registration
Phase 3: 建立 raw data inventory，并完成 accession/trait/variant compatibility audit
Phase 4: 确定 v0.1-mini / v0.2-core / v1.0-full benchmark scope
Phase 5: 设计 schema 并构建 benchmark table
Phase 6: 执行 data normalization 并构建 reference window
Phase 7: 构建 weak evidence 与 matched decoy
Phase 8: 生成 frozen splits
Phase 9: 实现 evaluator 与 baselines
Phase 10: 预计算 frozen Evo2 features
Phase 11: 进行 Task 1 model training and inference
Phase 12: 执行 ablation、negative controls 与 Task 2 supplementary demo

## 当前仓库状态

当前阶段：Matched decoy v0.5.5 chr1 SNP prototype pre-layer。

当前目标：在已完成的 v0.5.5 数据协议和 external knowledge annotation / evidence / mapping 层上，构建 chr1 SNP-only prototype 的 matched background candidate pool、matched decoy pair 和 diagnostics。不训练模型，不冻结 split，不构建正式 evaluator，不把 weak evidence、decoy、unknown/unlabeled 写成 causal ground truth / negative label。

当前产物包括 `reports/accession_mapping/accession_mapping_summary.md`、`reports/accession_mapping/accession_mapping_source_summary.tsv`、`reports/accession_mapping/genotype_mapping_coverage.tsv`、`reports/accession_mapping/phenotype_mapping_coverage.tsv`、`reports/accession_mapping/mapping_confidence_summary.tsv` 和 `reports/accession_mapping/manual_review_candidates_preview.tsv`。

Phase 4D 结论：genotype union 样本数为 3024，`3K_list_sra_ids.txt` 和 RunInfo 覆盖 3024 / 3024；Genesys MCPD 覆盖 2706 / 3024；phenotype A/B 级可用于 trait mapping 的样本数为 2269 / 3024。C 级 name match 和多重匹配必须人工审查。

Phase 4E 已形成 accession ID harmonization 口径说明：`docs/accession_id_harmonization.md`。主 benchmark 只使用 A/B 级 high-confidence genotype–phenotype mapping；C 级只进入人工审查，D 级不进入 trait-conditioned training/evaluation。未映射样本不作为 negative。

Phase 5A 已生成 trait_state prototype：high-confidence accession subset 为 2268 个样本，可用于 SNP-only trait prototype 的样本数为 2268，可用于 SNP+indel trait prototype 的样本数为 2268。当前识别到非 metadata trait 122 个，其中 continuous 0 个、categorical 99 个、binary 23 个；推荐进入 v0.1-mini 的 trait 为 34 个。报告位于 `reports/trait_state/trait_state_prototype_report.md`。

Phase 5B 已审查 34 个推荐 trait，全部找到 descriptor，冻结进入 v0.1-mini 的 trait 为 9 个：`SPKF`、`FLA_REPRO`、`CULT_CODE_REPRO`、`LLT_CODE`、`PEX_REPRO`、`LSEN`、`PTH`、`CUAN_REPRO` 和 `CUDI_CODE_REPRO`。冻结配置位于 `configs/v0_1_frozen_traits.yaml`，审查报告位于 `reports/trait_state_review/trait_descriptor_review_report.md`。

Phase 5C-prebuild 已生成 v0.1-mini chr1 SNP-only 输入骨架：chr1 SNP 数为 42466，chr1 window 数为 865，variant-window mapping 行数为 84886，chr1 weak evidence candidates 为 543，其中 42 个有 Q-TARO interval 坐标，501 个为无坐标 Oryzabase gene/trait 语义证据。报告位于 `reports/v0_1_mini/v0_1_mini_input_skeleton_report.md`。

Phase 5C 已构建 chr1 SNP-only minimal Task 1 instance prototype：frozen trait 数为 9，high-confidence accession 数为 2268，chr1 SNP 数为 42466，chr1 window 数为 865，Task 1 instance 数为 16265460。当前 weak evidence 覆盖 722 个 trait-window pair 和 32590 个 trait-variant pair；未覆盖的 window / variant 保留为 `unknown_unlabeled`，不作为 negative。报告位于 `reports/task1_chr1_snp/task1_chr1_snp_report.md`。

Phase 6A 已构建 evaluator / baseline prototype：baseline 包括 `random_uniform`、`window_snp_density`、`genomic_position` 和 `shuffled_trait`。window-level baseline score 行数为 31140，variant-level baseline score 行数为 1528776；评价报告位于 `reports/baselines_chr1_snp/baseline_evaluation_report.md`，校验报告位于 `reports/baselines_chr1_snp/baseline_validation.tsv`。

Phase 7A 已补充第一批外部水稻知识库：RAP-DB 下载 10 个文件，funRiceGenes 下载 8 个文件，MSU / RGAP 下载 7 个文件，失败或 skipped 记录数为 0。报告位于 `reports/external_knowledge/summary/external_knowledge_07a_report.md`，字段审查位于 `reports/external_knowledge/summary/external_knowledge_schema_preview.tsv`，集成计划位于 `reports/external_knowledge/summary/external_knowledge_integration_plan.tsv`。

Population covariate completion 已补齐 pruned v2.1 PCA / kinship 文件，并确认当前环境字段只有 phenotype `CROPYEAR`、passport origin / SUBTAXA 和测序 run metadata proxy。报告位于 `reports/current_data_status/population_covariate_download_report.md`。

Stratified residualization feasibility review 结论：严格 `subgroup x PC-bin x environment x batch x source` 硬分层不可行；当前可行主硬约束是 `trait_id`、`source_sheet` 和 broad subgroup，PC 只能作为连续距离或 kNN 约束，CROPYEAR/country/SUBTAXA/batch 只进入软约束、协变量、敏感性分析或 balance diagnostics。报告位于 `reports/current_data_status/stratified_residualization_feasibility_report.md`。

Design v0.5.5 data protocol alignment 已生成：

- full local tables：`data/interim/design_v055/metadata/`、`data/interim/design_v055/decoy/`、`data/interim/design_v055/negative_pairs/` 和 `data/interim/design_v055/qc_diagnostics/`。
- review tables：`reports/current_data_status/v055_trait_usability_table.tsv`、`v055_trait_preprocessing_table.tsv`、`v055_matching_field_availability_table.tsv`、`v055_covariate_field_availability_table.tsv`、`v055_negative_pair_candidate_pool_summary.tsv`、`v055_generated_table_schema.tsv` 和 `v055_data_processing_validation.tsv`。
- report：`reports/current_data_status/v055_data_processing_report.md`。
- script：`scripts/trait_state/build_design_v055_tables.py`。

本次处理结果：2268 个 high-confidence accession covariate rows，9 个 frozen traits 全部 usable for main，18804 条 non-missing frozen trait-state rows 均生成 L1 main hard mismatched trait-state pair；校验失败 0、警告 0。CROPYEAR 仍只有 741 / 2268 accession 有已知值，必须继续作为 weak environment proxy。

External knowledge v0.5.5 integration 已生成统一 annotation / evidence / gene ID mapping layer：

- full local tables：`data/interim/external_knowledge_v055/annotation/`、`data/interim/external_knowledge_v055/evidence/`、`data/interim/external_knowledge_v055/mapping/` 和 `data/interim/external_knowledge_v055/qc_diagnostics/`。
- report previews：`reports/external_knowledge_v055/`。
- scripts：`scripts/external_knowledge/build_gene_annotation_table.py`、`build_gene_id_mapping_table.py`、`build_known_gene_evidence_table.py`、`build_trait_gene_evidence_table.py`、`build_qtl_interval_evidence_table.py`、`build_evidence_coordinate_mapping_table.py`、`validate_external_knowledge_layer.py` 和 `run_build_external_knowledge_v055.sh`。
- report：`reports/external_knowledge_v055/external_knowledge_integration_report.md`。

本次处理结果：gene annotation 125082 行，gene ID mapping 154144 行，known gene evidence 80635 行，trait-gene evidence 80635 行，QTL interval evidence 1051 行，evidence coordinate mapping 81686 行，source manifest 13 行，validation 13 项检查全部 pass。可进入 frozen 9 traits 主评价候选池的 exact trait-gene evidence 为 4696 行；2391 行 ambiguous frozen-trait keyword matches 和其余 broader / missing trait evidence 均只进入 broader evidence pool 或 manual review。所有 evidence 的 `allowed_usage` 均限制为 evaluation / explanation / case study / development evidence candidate，不作为 training label。

Matched decoy v0.5.5 pre-layer 已生成 chr1 SNP-only matched background candidate pool：

- full local tables：`data/interim/matched_decoy_v055/objects/`、`candidate_pool/`、`pairs/` 和 `diagnostics/`。
- report previews：`reports/matched_decoy_v055/`。
- scripts：`scripts/matched_decoy/build_matched_decoy_objects_v055.py`、`build_detectability_research_bias_v055.py`、`build_matched_decoy_candidate_pool_v055.py`、`build_matched_decoy_pairs_v055.py`、`validate_matched_decoy_v055.py` 和 `run_build_matched_decoy_v055.sh`。
- report：`reports/matched_decoy_v055/matched_decoy_report.md`。

本次处理结果：matched decoy objects 114998 行，其中 33981 个进入 chr1 主 evaluation candidate pool；candidate pool 1019430 行；matched decoy pair 169905 行；diagnostics 61 行；detectability proxy 和 research-bias proxy 各 114998 行；validation 16 项检查全部 pass。主候选对象按类型为 variant 32590、window 722、gene 623、qtl_interval 46，所有主候选对象均有 candidate pool 和 5 个 matched background decoy。PEX_REPRO exact main-evaluation evidence 仍为 0；Q-TARO 只作为 region-level / interval-level evidence，不强行 gene mapping。

下一阶段：基于 matched decoy diagnostics 设计 frozen split，确保 gene / interval proximity blocking，并继续排除 manual review 和 broader evidence。

当前仍不包含 frozen split、Task 1 instance 重建、model implementation、formal AUROC / AUPRC、GWAS 或 Evo2 相关实现。外部数据库只作为 evidence / annotation / explanation layer；matched decoy 只作为 matched background，不是真阴性。`data/raw/` 和 `data/interim/` 已被 `.gitignore` 排除，不进入 git。

## 目录概览

- `AGENTS.md`：Codex 任务需要遵守的仓库级科研与工程规则。
- `configs/`：paths 和 source categories 的配置模板。
- `docs/`：项目范围、数据获取计划、benchmark 范围、Codex workflow 和审阅清单。
- `scripts/`：download、inspect 和 utility scripts。
- `src/ricebench/`：最小 Python package namespace。
- `tests/`：后续 tests 的占位目录。
- `.codex/prompts/`：仅保留目录占位；历史 prompt markdown 已清理，执行历史以 `status.md` 和 reports 为准。

## Codex Workflow 说明

每次 Codex 任务都应按小 PR 处理。任务完成时必须报告 goal、changed files、commands run、checks run、generated outputs、known limitations，以及 README/docs 是否已更新。新增或修改 Python 代码时，必须在同一任务中更新 README 或对应 docs。
