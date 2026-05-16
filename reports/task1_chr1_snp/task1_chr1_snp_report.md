# chr1 SNP-only Minimal Task 1 Instance Report

## 本次任务目标

本阶段基于 frozen v0.1 traits、high-confidence accession subset、chr1 SNP variant/window tables 和 chr1 weak evidence audit，构建 chr1 SNP-only minimal Task 1 instance prototype。本阶段不训练模型，不构建 evaluator，不做 phenotype prediction。

## 输入数据

- frozen traits：`configs/v0_1_frozen_traits.yaml` 和 `reports/trait_state_review/frozen_v0_1_traits.tsv`。
- accession subset：`data/interim/trait_state/high_confidence_accessions.tsv`。
- chr1 SNP/window：`data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv` 和 `window_table_chr1_v0_1.tsv`。
- weak evidence：`data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv`。

## Frozen Trait 子集

`SPKF`、`FLA_REPRO`、`CULT_CODE_REPRO`、`LLT_CODE`、`PEX_REPRO`、`LSEN`、`PTH`、`CUAN_REPRO`、`CUDI_CODE_REPRO`。

## 样本与变异规模

- high-confidence accession 数：2268。
- chr1 SNP 数：42466。
- chr1 window 数：865。
- Task 1 instance 数：16265460。

## Weak Evidence 覆盖情况

- trait-window weak evidence pairs：722。
- trait-variant weak evidence pairs：32590。
- 有坐标 QTL candidates：42。
- 无坐标 gene/trait semantic candidates：501。

## Window Weak Signal 规则

窗口与带坐标 weak evidence interval overlap 时标记为 `regional_weak_evidence`，`window_weak_signal` 为 overlap evidence 数量。没有 overlap 的窗口标记为 `unknown_unlabeled`。

## Variant Weak Label 规则

variant 落入 Q-TARO interval 时标记为 `regional_weak_evidence`。当前 Oryzabase 证据没有可用坐标，只保留在 evidence audit 中，不直接标记 variant。

## 为什么没有 evidence 不等于 negative

没有 evidence 只表示当前 weak evidence 来源未覆盖该 window 或 variant，不能解释为 true negative。本 prototype 保留 `unknown_unlabeled`。

## 为什么这不是 phenotype prediction

`trait_state` 是条件输入，不是预测目标。本阶段没有预测 accession phenotype value，没有训练模型，也没有构建 evaluator。

## 当前 Prototype 的限制

- 仅覆盖 chr1 SNP，不包含 indel、其他染色体或 SV/PAV/CNV。
- Q-TARO coordinate build 仍标记为 uncertain。
- Oryzabase chr1 gene/trait evidence 当前缺少坐标，不能形成 variant/window overlap。
- allele1 / allele2 未验证为 reference / alternate allele。

## 下一步建议

如果 Task 1 instance prototype 合格，则构建 minimal evaluator 和 random / heuristic baseline prototype。

## 结论

这是 chr1 SNP-only minimal Task 1 instance prototype。它不是最终 benchmark。weak evidence 只是 weak localization evidence。unknown_unlabeled 不作为 negative。
