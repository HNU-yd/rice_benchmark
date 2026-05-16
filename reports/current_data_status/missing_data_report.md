# 缺失数据优先级报告

## 阻塞项

当前阻塞 v0.1 的缺失项是：标准 accession ID master table,trait accession 与 genotype sample 的高置信 mapping,正式 trait_value_table。

其中最优先的是 `accession_mapping_master.tsv` 与 trait accession 到 genotype sample 的高置信 mapping。没有这一步，trait-conditioned SNP/indel localization 的 accession context 不能可靠构建。

## 非阻塞项

不阻塞 v0.1 的缺失项包括：GWAS lead SNP / significant SNP,更多文献级 trait-specific evidence,RAP / MSU / Gramene ID mapping,功能注释增强层,表达 / 多组学增强数据,Sanciangco / Dataverse GWAS raw result files,新增 accession / pruned SNP raw files 的 checksum 与 manifest 补登记。

GWAS lead SNP / significant SNP 重要，但可以在 accession mapping 完成后用 3K phenotype、core SNP genotype 和 Qmatrix 自跑，作为 Tier 2 `weak localization evidence`。RAP / MSU / Gramene ID mapping 和功能注释主要影响解释层，不阻塞 v0.1 skeleton。表达和多组学数据属于增强层，应暂缓。

## 当前策略

先做 accession mapping，再做 trait_state 和最小 benchmark 输入表。不要因为 Dataverse GWAS 下载失败而阻塞当前阶段，也不要把 Oryzabase、Q-TARO 或后续自跑 GWAS 写成 `causal ground truth`。
