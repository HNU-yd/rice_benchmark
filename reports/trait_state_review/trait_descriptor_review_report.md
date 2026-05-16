# Trait Descriptor Review Report

## 本次任务目标

本阶段审查 Phase 5A 推荐的 34 个编码型 trait，核对 descriptor、编码含义、类别分布和 weak evidence 关键词匹配，并冻结一个小规模 v0.1-mini trait 子集。本阶段不构建 Task 1 instances，不训练模型，不做 phenotype prediction。

## 为什么不能直接使用 34 个推荐 trait

Phase 5A 的推荐主要基于样本覆盖度。34 个 trait 全部是 categorical / binary 编码字段，编码值不是连续生物量。如果不审查 descriptor 和 code meaning，容易把数值编码误读为表型强度，或把极度不平衡类别纳入主流程。

## Phenotype 字段为什么主要是 categorical / binary

3K phenotype XLSX 中的 `Data < 2007` 主要采用描述符代码记录形态、颜色、结构和生育相关表型。代码例如颜色等级、形态类别或有序评分，适合构建 trait_state 条件输入，但不能直接作为连续 phenotype prediction target。

## Descriptor 审查结果

- 审查 trait 数量：34。
- 找到 descriptor 的 trait 数量：34。
- 冻结进入 v0.1-mini 的 trait 数量：9。
- 保留为 sensitivity-only 的 trait 数量：16。
- 暂缓或排除的 trait 数量：9。

## 类别分布审查结果

- 最大类别比例 > 0.9 的 trait 数量：7。
- 类别数 > 10 的 trait 数量：1。
极度不平衡或类别过多的 trait 默认不进入 v0.1-mini 主流程。

## Weak Evidence 关键词匹配结果

- 有 Oryzabase / Q-TARO 关键词级匹配的 trait 数量：34。
这些匹配只表示 weak localization evidence 语义联系，不能写成 causal ground truth。

## 冻结的 v0.1 Trait 子集

`data_lt_2007__spkf`、`data_lt_2007__fla_repro`、`data_lt_2007__cult_code_repro`、`data_lt_2007__llt_code`、`data_lt_2007__pex_repro`、`data_lt_2007__lsen`、`data_lt_2007__pth`、`data_lt_2007__cuan_repro`、`data_lt_2007__cudi_code_repro`。

## 暂缓或排除的 trait

`data_lt_2007__blpub_veg`、`data_lt_2007__cust_repro`、`data_lt_2007__endo`、`data_lt_2007__ligco_rev_veg`、`data_lt_2007__ligsh`、`data_lt_2007__lpco_rev_post`、`data_lt_2007__noco_rev`、`data_lt_2007__pa_repro`、`data_lt_2007__second_br_repro`。

## 对后续 Task 1 Instances 的影响

后续 chr1 SNP-only minimal Task 1 instances 只应使用 `configs/v0_1_frozen_traits.yaml` 中的 frozen traits。sensitivity-only trait 可用于附录或消融，但不进入主流程。

## 为什么这不是 phenotype prediction

`trait_state` 是模型条件输入，用于构造 trait-conditioned localization query。本阶段没有预测 accession phenotype value，没有训练模型，没有构建 split，也没有构建 evaluator。

## AGENTS.md 未提交改动处理

`AGENTS.md` 当前新增规则为：每次执行 prompt 后更新 `status.md`。这是工作流规则，本阶段会随提交纳入，并已更新 `status.md`。

## 主要风险

- 冻结 traits 仍然是编码型状态，不能当作连续生物量。
- weak evidence 只做关键词级弱语义匹配，不能替代人工证据审查。
- 类别含义来自 phenotype XLSX dictionary，后续论文方法中应保留原始 code meaning。

## 下一步建议

如果 frozen v0.1 trait 子集质量可以接受，则构建 chr1 SNP-only minimal Task 1 instances。

## 结论

v0.1-mini 只使用冻结的 trait 子集。trait_state 是条件输入，不是预测目标。编码含义不清楚的 trait 不进入主流程。
