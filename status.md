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
