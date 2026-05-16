# GWAS Lead SNP 状态

## 当前结论

当前没有可靠、可追溯、可直接纳入的 GWAS lead SNP raw file。本次 Phase 3C 不下载新的 GWAS 文件，也不从论文或网页中临时抽取 lead SNP。

本地 raw data 关键字扫描结果：未发现文件名包含 gwas/lead/significant/association/ricevarmap 的本地 raw 文件。

## 对 v0.1-mini 的影响

GWAS lead SNP 缺口不阻塞 v0.1-mini。v0.1-mini 可以先使用 Oryzabase known/cloned trait genes 和 Q-TARO QTL intervals 作为 `weak localization evidence` 候选来源。

## 后续处理

v0.2-core 应在完成 3K phenotype、core SNP genotype、Qmatrix 和 accession mapping 对齐后，自行计算 GWAS lead SNP 或 window-level signal map。自计算 GWAS 仍然只能作为 `weak localization evidence`，不能写成 `causal ground truth`。未被 GWAS/QTL/known genes 覆盖的 variant 或 window 仍然是 unknown，不能当作 negative。
