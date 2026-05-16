# Trait State Prototype Report

## 本次任务目标

本阶段基于 A/B high-confidence accession mapping 构建 trait_state prototype，冻结可复查的 accession subset，并从 `3kRG_PhenotypeData_v20170411.xlsx` 抽取 trait 值。该阶段不做 phenotype prediction，不训练模型，不构建正式 benchmark schema，也不纳入 C/D 级 accession mapping 样本。

## High-confidence Accession Subset

- high-confidence accession subset 样本数：2268。
- 可用于 SNP-only trait prototype 的样本数：2268。
- 可用于 SNP+indel trait prototype 的样本数：2268。
- phenotype row 缺失或无法回取的 high-confidence 样本数：0。

## Phenotype Sheet 情况

- `Phenotype Data`：high-confidence rows = 23，rows = 2267，cols = 53。
- `Data < 2007`：high-confidence rows = 2096，rows = 2115，cols = 40。
- `Data > 2007`：high-confidence rows = 149，rows = 153，cols = 41。

## Trait 识别结果

- 识别到的非 metadata trait 总数：122。
- 连续性状数量：0。
- 分类性状数量：99。
- 二分类性状数量：23。
- ID / metadata 字段数量：12。

## 推荐 v0.1 Trait 子集

推荐进入 v0.1-mini 的 trait 数：34。

`data_lt_2007__blco_rev_veg`、`data_lt_2007__cco_rev_veg`、`data_lt_2007__ligco_rev_veg`、`data_lt_2007__apco_rev_repro`、`data_lt_2007__auco_rev_veg`、`data_lt_2007__blpub_veg`、`data_lt_2007__blsco_rev_veg`、`data_lt_2007__inco_rev_repro`、`data_lt_2007__pex_repro`、`data_lt_2007__cuan_repro`、`data_lt_2007__cust_repro`、`data_lt_2007__lpco_rev_post`、`data_lt_2007__spkf`、`data_lt_2007__cudi_code_repro`、`data_lt_2007__lsen`、`data_lt_2007__pty`、`data_lt_2007__fla_repro`、`data_lt_2007__pth`、`data_lt_2007__scco_rev`、`data_lt_2007__endo`、`data_lt_2007__sllt_code`、`data_lt_2007__cuno_code_repro`、`data_lt_2007__llt_code`、`data_lt_2007__cult_code_repro`、`data_lt_2007__sdht_code`、`data_lt_2007__plt_code_post`、`data_lt_2007__slco_rev`、`data_lt_2007__la`、`data_lt_2007__lppub`、`data_lt_2007__pa_repro`、`data_lt_2007__ligsh`、`data_lt_2007__psh`、`data_lt_2007__second_br_repro`、`data_lt_2007__noco_rev`。

完整推荐表见 `reports/trait_state/v0_1_trait_recommendation.tsv`。

## Trait_state 构建规则

- continuous trait：`normalized_value = (value - mean) / std`；按 bottom 30%、middle 40%、top 30% 分为 `low`、`mid`、`high`。
- categorical trait：`trait_state` 使用 normalized category string。
- binary trait：`trait_state` 使用 `class_0` / `class_1`。
- 缺失 trait 值不生成 trait_state 行。

## 为什么这不是 phenotype prediction

`trait_state` 是模型条件扰动信号，不是 prediction label。本阶段没有构建 phenotype prediction head，没有训练模型，没有把 accession phenotype value 作为待预测目标，也没有生成 train/val/test split。

## C/D 级样本为什么不进入 trait_state

C 级样本只有名称级候选匹配，存在 false genotype-trait pairing 风险；D 级样本缺少可用 phenotype mapping，不能解释为 negative。为保持 benchmark 可审计性，本阶段只使用 A/B accession mapping 样本。

## 主要风险

- 3K phenotype 字段大量为编码型 trait，部分 numeric summary 只反映编码值本身，不应解释为生物连续量。
- 不同 sheet 中同名 trait 的测量时期和编码体系可能不同，当前 prototype 保留 `source_sheet` 维度，不做跨 sheet 合并。
- v0.1-mini trait 子集仍需人工审查 trait descriptor、缺失模式和类别含义。

## 下一步建议

如果 v0.1 trait 子集足够，则构建 chr1 SNP-only minimal Task 1 instances；否则先人工审查 trait 字段和 accession mapping。

## 结论

本阶段只生成 prototype，不是最终 benchmark 表。只有 A/B accession mapping 样本进入 trait_state prototype。trait_state 是条件输入，不是预测目标。
