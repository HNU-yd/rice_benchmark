# 项目范围

## 范围内

- 主位数据：3K Rice。
- 变异范围：SNP + indel。
- 主任务：`trait-conditioned SNP/indel localization`。
- 第二任务：`reference-conditioned candidate SNP/indel edit hypothesis generation`。

## 核心输出

- `variant-level score`。
- `window-level signal map`。
- candidate significant regions。
- fine SNP/indel loci。

## Evidence 原则

GWAS、QTL、known trait genes、LD blocks、credible intervals 和 trait-gene annotations 可以用于支持 localization，但只能作为 `weak localization evidence`。

这些 evidence 不能被编码为 `causal ground truth`。

Unknown 或 unlabeled variants 不能默认作为 negative labels。

## 明确不做

- `phenotype prediction`。
- `trait classification`。
- causal/non-causal strong supervised classification。
- SV/PAV/CNV。
- pan-reference。
- multi-reference。
- multi-species benchmark。
- genome model pretraining。
