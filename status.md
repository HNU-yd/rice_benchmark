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
