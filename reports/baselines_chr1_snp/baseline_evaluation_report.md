# Rice Benchmark: chr1 SNP Baseline Prototype

## 当前阶段定位

当前阶段是 `06A`：minimal evaluator and baseline prototype。

这一阶段的目标不是训练模型，也不是报告正式 benchmark 性能，而是完成三个前置任务：

1. 验证 chr1 SNP-only Task 1 的输入表、baseline 输出表和 evaluator ranking 流程是否可以跑通。
2. 用最低限度 baseline 检查 weak localization evidence 是否存在明显数据偏差。
3. 在进入 matched decoy、frozen split 和正式 evaluator 之前，提前识别可能污染评估结果的 shortcut。

因此，本阶段结果应被解释为 **baseline sanity check / bias audit**，而不是正式模型性能。

---

## 使用的输入数据

本阶段使用以下 chr1 SNP prototype 数据：

```text
data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv
data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
reports/trait_state_review/frozen_v0_1_traits.tsv
```

其中：

- `window_weak_signal_chr1_snp.tsv` 提供 window-level weak localization evidence。
- `variant_weak_label_chr1_snp.tsv` 提供 variant-level weak evidence label。
- `window_table_chr1_v0_1.tsv` 和 `variant_table_chr1_snp_v0_1.tsv` 提供 chr1 SNP prototype 的 ranking background。
- `frozen_v0_1_traits.tsv` 提供当前 prototype 使用的 trait 集合。

---

## 已实现的 baseline

### 1. `random_uniform`

在每个 trait 内使用固定 seed 生成随机分数并排序。

作用：

- 提供最低随机参照。
- 用于判断 top-k recall 和 enrichment 是否高于随机背景。
- 当前 seed 为 `20260516`，用于保证结果可复现。

---

### 2. `window_snp_density`

使用窗口内 SNP 数量作为排序分数。

window 层面：

```text
score = n_snp_in_window
```

variant 层面：

```text
score = max SNP density of overlapping windows
```

作用：

- 检查 weak evidence 是否只是偏向 SNP 密集区域。
- 如果该 baseline 表现很强，说明模型可能通过变异密度 shortcut 获得高分。

---

### 3. `genomic_position`

使用 window start 或 variant position 归一化后的基因组坐标作为排序分数。

作用：

- 检查 weak evidence 是否集中在 chr1 的某些坐标区域。
- 如果该 baseline 表现很强，说明当前 weak evidence 存在明显 position bias。
- 这是后续 matched decoy 和 split 设计中最需要处理的风险。

---

### 4. `shuffled_trait`

打乱 trait 与 weak signal 的对应关系。

作用：

- 做 trait-specific sanity check。
- 检查 weak evidence 是否仍然可以在错误 trait 映射下保持较高 ranking 表现。
- 该 baseline 只是 prototype sanity check，不是正式 negative control。

---

## Window-level 结果

| baseline | mean weak_evidence_recall_at_50 | mean enrichment_over_random_at_50 | mean evidence rank percentile |
|---|---:|---:|---:|
| `genomic_position` | 0.383341 | 6.631805 | 0.871528 |
| `random_uniform` | 0.050673 | 0.876633 | 0.423707 |
| `shuffled_trait` | 0.001157 | 0.020023 | 0.251350 |
| `window_snp_density` | 0.031001 | 0.536306 | 0.431134 |

---

## Variant-level 结果

| baseline | mean weak_evidence_recall_at_1000 | mean enrichment_over_random_at_1000 | mean evidence rank percentile |
|---|---:|---:|---:|
| `genomic_position` | 0.347243 | 14.746009 | 0.872366 |
| `random_uniform` | 0.067981 | 2.886881 | 0.545194 |
| `shuffled_trait` | 0.000000 | 0.000000 | 0.208984 |
| `window_snp_density` | 0.010691 | 0.453987 | 0.384265 |

---

## 结果分析

### 1. 最重要发现：`genomic_position` 明显强于其他 baseline

在 window 层面，`genomic_position` 的 mean weak evidence recall@50 为 `0.383341`，明显高于 `random_uniform` 的 `0.050673`。

在 variant 层面，`genomic_position` 的 mean weak evidence recall@1000 为 `0.347243`，也明显高于 `random_uniform` 的 `0.067981`。

更关键的是，`genomic_position` 在两个层面上的 mean evidence rank percentile 都约为 `0.87`：

```text
window-level:  0.871528
variant-level: 0.872366
```

这说明 weak evidence 在当前 chr1 prototype 中不是随机分布的，而是可能集中在较固定的基因组坐标区域。

因此，当前数据存在一个重要风险：

> 模型可能不需要真正理解 trait-conditioned perturbation signal，只需要学习 chr1 的坐标先验，就能获得较高 ranking 表现。

这不是模型能力，而是 evaluation shortcut。后续如果直接在这个 weak evidence 上报告正式 AUROC / AUPRC，会高估模型性能。

---

### 2. `window_snp_density` 没有成为强 baseline

`window_snp_density` 在 window 和 variant 两个层面都低于 random baseline：

```text
window-level recall@50:   0.031001
variant-level recall@1000: 0.010691
```

这说明当前 weak evidence 的主要偏差不太像是简单的 SNP 密度偏差。

换句话说，当前风险更像是 **genomic coordinate bias**，而不是单纯的 **SNP density bias**。

不过，这并不意味着 SNP density 可以忽略。后续 matched decoy 仍然应该控制 SNP density，否则正式 evaluator 可能在更大数据范围内重新暴露密度 shortcut。

---

### 3. `shuffled_trait` 接近 0，说明 trait mapping 仍然有一定约束作用

`shuffled_trait` 在 window 层面 recall@50 为 `0.001157`，variant 层面 recall@1000 为 `0`。

这说明打乱 trait 对应关系后，weak evidence ranking 基本失效。

这个结果是一个有利信号：

> 当前 weak evidence 并不是完全由 trait-independent 的全局坐标分布决定，trait_id 映射仍然影响结果。

但这个结论不能过度解释。因为 `shuffled_trait` 只是 prototype sanity check，它还不是严格的 negative control。正式实验仍需要 matched decoy 和 frozen split。

---

### 4. `unknown_unlabeled` 不能当成 true negative

当前 `unknown_unlabeled` 只表示 weak evidence 没有覆盖该 window 或 variant。

它不能被解释为：

```text
non-causal
true negative
no trait association
```

原因是 weak evidence 来源本身不完整。一个 window 或 variant 没有 weak evidence，并不代表它生物学上没有作用。

因此，本阶段只能做 ranking evaluation，不能直接构造 causal / non-causal 二分类任务。

---

## 为什么当前不能报告正式 AUROC / AUPRC

当前缺少两个正式 benchmark 必需组件：

### 1. Matched decoy

需要构造与 positive weak evidence 匹配的 decoy background。匹配因素至少应包括：

- chromosome / local genomic region
- window size
- SNP count / variant density
- distance to nearby evidence region
- callable / mappable region 状态
- trait coverage 状态

目标是让模型不能依赖明显 shortcut，例如坐标位置或 SNP 密度。

---

### 2. Frozen split

需要固定 train / validation / test 划分，并保证后续所有模型使用同一划分。

split 至少需要考虑：

- trait-level split
- individual-level split
- genomic-region-level split
- evidence-source-level leakage control

如果没有 frozen split，正式 evaluator 结果不可复现，也容易产生数据泄漏。

---

## 对 benchmark 设计的影响

基于本次 06A 结果，后续 benchmark 设计需要优先解决以下问题。

### 1. matched decoy 必须控制 genomic position

因为 `genomic_position` 是当前最强 baseline，所以 decoy 不能从全 chr1 随机抽取。

更合理的策略是：

```text
positive window / variant
→ 在相邻 genomic block 或同一 local bin 内采样 decoy
→ 控制 SNP density、window length、callable 状态等协变量
```

目标是让 genomic position baseline 在 matched decoy set 上下降到接近 random。

---

### 2. evaluator 需要保留 bias audit 指标

正式 evaluator 不应只输出模型指标，还应同步输出 baseline audit：

- random baseline
- SNP density baseline
- genomic position baseline
- shuffled trait sanity check
- decoy matching diagnostics

如果一个简单 heuristic 在 test set 上仍然很强，则对应模型结果需要谨慎解释。

---

### 3. 论文或报告中不能把 06A 写成正式结果

当前 06A 可以写成：

> We first constructed a minimal ranking evaluator and a set of random / heuristic baselines to audit weak evidence bias before formal benchmark evaluation.

不能写成：

> The model achieved strong performance on chr1 SNP localization.

因为本阶段没有模型，也没有正式 negative set。

---

## 当前 prototype 的限制

- 仅覆盖 chr1 SNP。
- 不包含 indel、SV 或其他染色体。
- weak evidence 不是 causal ground truth。
- 没有 matched decoy。
- 没有 frozen split。
- 没有正式 supervised evaluator。
- `shuffled_trait` 只是 sanity check，不是正式 negative control。
- variant-level `window_snp_density` 是从 overlapping windows 派生的粗略 heuristic。

---

## 下一步工程任务

建议后续按以下顺序推进。

### 06B: matched decoy prototype

目标：

- 为 window-level 和 variant-level weak evidence 构造 matched decoy。
- 控制 genomic position、SNP density、window length 等协变量。
- 重新运行 baseline，确认 `genomic_position` baseline 是否显著下降。

验收标准：

```text
genomic_position baseline should be close to random on matched decoy evaluation.
window_snp_density baseline should not dominate random.
```

---

### 06C: frozen split

目标：

- 固定 trait / individual / genomic region split。
- 避免同一 genomic region 或高度相邻 evidence 同时出现在 train 和 test。
- 输出可复现 split 文件。

建议输出：

```text
data/splits/v0_1/task1_window_split.tsv
data/splits/v0_1/task1_variant_split.tsv
reports/splits/v0_1/split_diagnostics.md
```

---

### 06D: formal evaluator

目标：

- 在 matched decoy + frozen split 基础上计算正式指标。
- 保留 ranking metrics，同时增加正式 binary metrics。

正式指标可以包括：

```text
AUROC
AUPRC
Recall@K
Precision@K
enrichment_over_random
evidence rank percentile
```

但 AUROC / AUPRC 只有在 matched decoy 完成后才可以作为主指标。

---

## 当前结论

本阶段已经完成 minimal evaluator 和 baseline prototype，并验证了 chr1 SNP weak evidence ranking 流程可以运行。

最重要的分析结论是：

> 当前 chr1 SNP weak evidence 存在明显 genomic position bias。`genomic_position` baseline 在 window-level 和 variant-level 都显著强于 random baseline。这说明后续正式 benchmark 必须引入 matched decoy 和 frozen split，否则模型可能通过坐标 shortcut 获得虚高性能。

因此，06A 的价值不是证明模型有效，而是提前暴露 benchmark 风险，并为后续 evaluator 设计提供约束。
