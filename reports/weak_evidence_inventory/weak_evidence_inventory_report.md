# Phase 3C Weak Evidence Inventory 报告

## 任务目标

本次任务只登记和检查已有 weak evidence raw files：Oryzabase known/cloned trait gene list 与 Q-TARO QTL interval archive。所有结果只用于判断后续是否可构建 `weak localization evidence`，不生成正式 `weak_evidence_table`，不定义 benchmark schema，不构建 split，不运行 model。

## 已检查文件

- Oryzabase：`data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv`
- Q-TARO：`data/raw/evidence/qtl/qtaro/qtaro_sjis.zip`
- Q-TARO UTF-8 中间文件：`data/interim/evidence/qtaro/qtaro_sjis.csv.utf8`

`data/raw/` 与 `data/interim/` 仍然由 `.gitignore` 排除，不进入 git。

## Q-TARO 检查结果

Q-TARO 可读取，原始 CSV 已从 SHIFT_JIS 转为 UTF-8。当前记录数为 1051，字段数为 32。

关键字段识别结果：

- QTL name：`QTL/Gene`
- trait / character：`Character`
- major category：`Major category`
- trait category：`Category of object character`
- chromosome：`Chr`
- genome start：`Genome start`，可解析为整数的行数 1051
- genome end：`Genome end`，可解析为整数的行数 1051
- reference：`Reference`

Q-TARO 当前定位为 Tier 4 QTL interval evidence。coordinate build 仍需后续确认，因此不能直接作为 `causal ground truth`。

## Oryzabase 检查结果

Oryzabase gene list 可读取，当前记录数为 22015，字段数为 18，HTML 检测结果为 `no`。

关键字段识别结果：

- gene symbol：`CGSNL Gene Symbol`
- RAP ID：`RAP ID`
- MSU ID：`MSU ID`
- chromosome：`Chromosome No.`
- trait class：`Trait Class`
- Trait Ontology：`Trait Ontology`

Oryzabase 当前定位为 Tier 1 known/cloned trait gene evidence。后续仍需把 RAP/MSU/gene symbol 映射到 IRGSP-1.0 reference coordinates。

## GWAS Lead SNP 状态

未发现本地 GWAS lead SNP 候选文件。

GWAS lead SNP 缺口不阻塞 v0.1-mini。v0.2-core 应在完成 3K phenotype、core SNP genotype、Qmatrix 和 accession mapping 对齐后自跑 GWAS。自计算 GWAS 仍然只是 `weak localization evidence`。

## Evidence Tier 小结

- Tier 1 known/cloned trait gene：Oryzabase，可进入后续候选 weak evidence 整理。
- Tier 4 QTL interval：Q-TARO，可进入后续候选 weak evidence 整理，但 coordinate build 必须确认。
- Tier 2 self-computed GWAS lead SNP：当前不存在，后续 v0.2-core 自跑。

## v0.1-mini 支持结论

v0.1-mini 可以使用 Tier 1 Oryzabase known genes 与 Tier 4 Q-TARO QTL intervals 作为候选 `weak localization evidence` 来源。GWAS lead SNP 后续自跑，不作为当前阻塞项。

## 风险与下一步

- `weak localization evidence` 不能写成 `causal ground truth`。
- `unknown != negative`：没有 evidence 覆盖的 SNP/indel 或 window 不等于 negative。
- 下一步需要确认 Oryzabase gene ID 到 reference coordinate 的映射，以及 Q-TARO interval 的 reference build / coordinate convention。
- 后续构建正式 evidence 表前，需要加入 provenance、trait specificity、coordinate build、evidence tier 和 leakage flag。
