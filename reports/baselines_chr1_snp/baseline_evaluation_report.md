# chr1 SNP Baseline Evaluation Report

## 本次任务目标

本阶段构建 minimal evaluator 和 random / heuristic baseline prototype，用于检查 chr1 SNP-only Task 1 weak localization evidence 的排序行为。本阶段不训练模型，不构建深度学习模型，不执行 GWAS，不做 phenotype prediction。

## 使用的输入数据

- `data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv`。
- `data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv`。
- `data/interim/v0_1_mini/window_table_chr1_v0_1.tsv`。
- `data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv`。
- `reports/trait_state_review/frozen_v0_1_traits.tsv`。

## Baseline 类型

- `random_uniform`：每个 trait 内固定 seed 随机分数，seed 为 20260516。
- `window_snp_density`：window 层面使用 `n_snp_in_window`，variant 层面继承 overlapping windows 中最大的 SNP density。
- `genomic_position`：用 window start 或 variant pos 除以 chr1 prototype length。
- `shuffled_trait`：将 trait-specific weak signal 映射到另一个 trait，仅作为 prototype sanity check，不是正式 negative control。

## Window-level 评价结果

下表为 baseline-level 摘要；均值只在对应指标非空的 trait 上计算，因此不把无 weak evidence 的 trait 强行计入 recall 或 enrichment。

| baseline | mean weak_evidence_recall_at_50 | mean enrichment_over_random_at_50 | mean evidence rank percentile |
|---|---:|---:|---:|
| `genomic_position` | 0.383341 | 6.631805 | 0.871528 |
| `random_uniform` | 0.050673 | 0.876633 | 0.423707 |
| `shuffled_trait` | 0.001157 | 0.020023 | 0.25135 |
| `window_snp_density` | 0.031001 | 0.536306 | 0.431134 |

## Variant-level 评价结果

下表为 baseline-level 摘要；均值只在对应指标非空的 trait 上计算，因此不把无 weak evidence 的 trait 强行计入 recall 或 enrichment。

| baseline | mean weak_evidence_recall_at_1000 | mean enrichment_over_random_at_1000 | mean evidence rank percentile |
|---|---:|---:|---:|
| `genomic_position` | 0.347243 | 14.746009 | 0.872366 |
| `random_uniform` | 0.067981 | 2.886881 | 0.545194 |
| `shuffled_trait` | 0 | 0 | 0.208984 |
| `window_snp_density` | 0.010691 | 0.453987 | 0.384265 |

## Random Baseline 表现

`random_uniform` 是固定 seed 的 ranking background；它用于给 top-k hit rate、weak evidence recall 和 enrichment_over_random 提供随机参照。

## SNP Density Heuristic 表现

`window_snp_density` 用于检查 weak evidence 是否集中在 SNP 密度较高的 window。它不是生物学模型，也不使用 accession phenotype value。

## Shuffled Trait Baseline 表现

`shuffled_trait` 保留 source trait 的 weak signal 分布，但打乱 trait_id 对应关系，用于检查 trait-specific weak evidence 是否主要来自坐标分布重叠。

## 为什么 unknown_unlabeled 不是 negative

`unknown_unlabeled` 只表示当前 weak evidence 来源没有覆盖该 window 或 variant，不能解释为 true negative，也不能用于构造 causal / non-causal 二分类标签。本阶段只把它作为 ranking background。

## 为什么本阶段不报告正式 AUROC / AUPRC

当前还没有 matched decoy，也没有 frozen split。因此 AUROC、AUPRC、accuracy、precision、F1 等正式二分类指标需要 matched decoy 后才能作为正式主指标。本阶段只报告 top-k ranking、weak evidence recall、evidence rank percentile 和 enrichment_over_random。

## 当前 Prototype 的限制

- 仅覆盖 chr1 SNP，不包含 indel 和其他染色体。
- weak evidence 不是 causal ground truth。
- 没有 matched decoy，因此不能解释为正式监督评测。
- `shuffled_trait` 使用 weak signal 分布做 sanity check，不能作为正式 negative control。
- variant 层面的 `window_snp_density` 是从 overlapping windows 派生的粗略 heuristic。

## 下一步建议

构建 matched decoy 和 frozen split，然后再进入正式 evaluator 指标。

## 结论

这是 evaluator / baseline prototype。正式主指标需要 matched decoy 和冻结 split 后再计算。
