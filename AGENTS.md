# AGENTS.md

## 项目角色

本仓库用于构建 `3K Rice SNP/indel trait-conditioned localization benchmark`。

该 benchmark 的目标是支持可复现的构建、评估和审阅流程，核心场景是在 3K Rice 数据上完成 `trait-conditioned SNP/indel localization`。

## 硬性科研边界

本项目第一版必须遵守以下边界：

- 主 benchmark 只使用 3K Rice。
- 第一版只支持 SNP 和 indel。
- Task 1 是 `trait-conditioned SNP/indel localization`。
- Task 2 只能作为 supplementary / application demo。
- 本项目不能变成 `phenotype prediction`。
- 本项目不能变成 `trait classification`。
- 本项目不能把 `weak localization evidence` 写成 `causal ground truth`。
- 本项目不能把 unknown variants 当作 true negatives。
- 第一版不能引入 SV、PAV、CNV、pan-reference、multi-reference、multi-species 或 pretraining 范围。

GWAS、QTL、known trait genes、LD blocks、credible intervals 和 trait-gene annotations 只能作为 `weak localization evidence`。这些 evidence 不能被表示为 `causal ground truth`。

## 工程规则

- Raw data 绝不能被覆盖。
- 所有下载文件必须登记到 manifest files。
- 每个脚本必须有清楚的 input、output 和 usage example。
- 所有 data-processing logic 必须能从命令行复现。
- 每个生成的 benchmark table 都必须有已记录的 schema。
- 所有 train/val/test splits 必须固化为文件。
- 训练代码中禁止动态随机切分 split。
- 所有 models 和 baselines 必须输出标准化 output tables。
- 新增或修改 Python 代码时，必须同步更新 README 或对应 docs。

## GitHub 同步规则

- 为便于网页端审阅和协作，本仓库的 GitHub 目标仓库是 `HNU-yd/rice_benchmark`：<https://github.com/HNU-yd/rice_benchmark>。
- 需要同步到网页端时，应将本地 git 仓库 push 到该 GitHub 仓库。
- Push 前必须检查 changed files，确认没有包含 raw data、大文件、中间数据、私有路径、token、password 或其他敏感信息。
- Push 前必须确认 README/docs 已按本仓库规则更新，且当前改动没有扩大科研范围。
- 不得为了 push 而覆盖或回滚用户未要求修改的本地文件。

## Codex 行为规则

- 不要扩大科研范围。
- 不要静默新增任务。
- 不要引入 `phenotype prediction heads`。
- 不要实现未被请求的模块。
- 不要假设 missing data 是 negative labels。
- 不要把 GWAS、QTL 或 known genes 当作 `causal ground truth`。
- 在修改多个文件前，先检查仓库结构。
- 任务完成后，必须总结 changed files 和 remaining risks。
