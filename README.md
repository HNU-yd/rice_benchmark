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

当前阶段：Phase 1 data source inventory。

当前目标：确认 3K Rice benchmark 所需数据源，不下载数据，不写 schema，不训练模型。

当前产物包括 `manifest/source_inventory.tsv`、`manifest/source_inventory.schema.tsv`、`docs/data_source_inventory.md` 和 `docs/data_download_risk_notes.md`。

下一阶段：Phase 2 raw data download, checksum, and manifest registration。

当前 Phase 1 不包含 raw data 下载、schema 实现、benchmark construction、model implementation 或 evaluator implementation。

## 目录概览

- `AGENTS.md`：Codex 任务需要遵守的仓库级科研与工程规则。
- `configs/`：paths 和 source categories 的配置模板。
- `docs/`：项目范围、数据获取计划、benchmark 范围、Codex workflow 和审阅清单。
- `scripts/`：后续 download、inspect 和 utility scripts 的占位目录。
- `src/ricebench/`：最小 Python package namespace。
- `tests/`：后续 tests 的占位目录。
- `.codex/prompts/`：分阶段 Codex prompt 文件。

## Codex Workflow 说明

每次 Codex 任务都应按小 PR 处理。任务完成时必须报告 goal、changed files、commands run、checks run、generated outputs、known limitations，以及 README/docs 是否已更新。新增或修改 Python 代码时，必须在同一任务中更新 README 或对应 docs。
