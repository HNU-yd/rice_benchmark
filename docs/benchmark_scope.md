# Benchmark 范围

benchmark 只能在 raw data inventory 确认 3K Rice 中实际可用的数据后构建。

Schema design 必须跟随真实可下载数据，不能基于理想化假设。

## Task 1

Task 1 input unit：trait_state + accession + reference_window。

Task 1 output：

- `variant-level score`。
- `window-level signal map`。
- candidate region。
- fine SNP/indel locus。

## Task 2

Task 2 仅作为 supplementary，并且 input 中必须隐藏 accession genotype。

Task 2 是 `reference-conditioned candidate SNP/indel edit hypothesis generation`。它不能变成主 benchmark，也不能变成 `phenotype prediction` 任务。

## 必须遵守的 Benchmark 原则

- `unknown != negative`。
- `weak localization evidence != causal ground truth`。
- 最终 benchmark 必须包含 `matched decoy`。
- Splits 必须固化为文件。

