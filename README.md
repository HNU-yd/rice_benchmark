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

当前阶段：Phase 4C current data status audit and external database collection plan。

当前目标：统计服务器上已经落地的 3K Rice raw data、accession mapping sources、weak evidence 和 Dataverse metadata，明确缺失数据优先级，并制定外部水稻数据库搜集路线。不写正式 benchmark schema，不构建 split，不训练模型，不做 `phenotype prediction`。

当前产物包括 `reports/current_data_status/project_data_status_summary.md`、`reports/current_data_status/current_data_category_summary.tsv`、`reports/current_data_status/accession_mapping_source_status.tsv`、`reports/current_data_status/missing_data_priority.tsv`、`reports/external_database_plan/external_database_inventory.tsv` 和 `reports/external_database_plan/external_database_collection_plan.md`。

Phase 4C 结论：当前 `data/raw/` 有 74 个文件，总大小约 4.26 GiB；accession mapping 的源文件已基本齐全，但 `accession_mapping_master.tsv` 尚未构建，是当前最优先事项。Dataverse GWAS 下载失败不阻塞当前阶段。外部数据库只作为 knowledge layer，不替代 3K Rice genotype backbone。

下一阶段：构建 `accession_mapping_master.tsv` 草稿，并固定 source、match rule、confidence 和 manual review flag。

当前 Phase 4C 不包含 schema 实现、benchmark construction、split、model implementation、evaluator implementation 或 Evo2 相关实现。`data/raw/` 和 `data/interim/` 已被 `.gitignore` 排除，不进入 git。

## 目录概览

- `AGENTS.md`：Codex 任务需要遵守的仓库级科研与工程规则。
- `configs/`：paths 和 source categories 的配置模板。
- `docs/`：项目范围、数据获取计划、benchmark 范围、Codex workflow 和审阅清单。
- `scripts/`：download、inspect 和 utility scripts。
- `src/ricebench/`：最小 Python package namespace。
- `tests/`：后续 tests 的占位目录。
- `.codex/prompts/`：分阶段 Codex prompt 文件。

## Codex Workflow 说明

每次 Codex 任务都应按小 PR 处理。任务完成时必须报告 goal、changed files、commands run、checks run、generated outputs、known limitations，以及 README/docs 是否已更新。新增或修改 Python 代码时，必须在同一任务中更新 README 或对应 docs。
