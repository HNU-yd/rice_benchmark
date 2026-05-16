# Accession Mapping Summary

## 本次任务目标

本次任务只构建 `accession_mapping_master.tsv` 草稿，用于梳理 genotype sample ID、3K_list_sra_ids、NCBI RunInfo、Genesys MCPD 和 phenotype accession-like fields 的关系。该表不是正式 `accession_table`，不生成 `trait_value_table`，不训练模型，不做 `phenotype prediction`。

## 输入文件

- core SNP FAM：`data/raw/variants/snp/core_v0.7.fam.gz`
- indel FAM：`data/raw/variants/indel/Nipponbare_indel.fam.gz`
- pruned SNP FAM：`data/raw/variants/snp/pruned_v2.1/pruned_v2.1.fam`
- Qmatrix：`data/raw/metadata/Qmatrix-k9-3kRG.csv`
- 3K_list_sra_ids：`data/raw/accessions/snpseek/3K_list_sra_ids.txt`
- NCBI RunInfo：`data/raw/accessions/ncbi_prjeb6180/PRJEB6180_runinfo.csv`
- Genesys MCPD：`data/raw/accessions/genesys/genesys_3k_mcpd_passport.xlsx`
- phenotype XLSX：`data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx`

## Genotype 样本覆盖

genotype union 样本数为 3024。core SNP 样本数 3024，indel 样本数 3023，pruned SNP 样本数 3024，Qmatrix 样本数 3023。core SNP 与 indel 交集为 3023，core SNP 与 Qmatrix 交集为 3023，core SNP 与 pruned SNP 交集为 3024。

## 3K_list_sra_ids 匹配

`genotype_sample_id` 精确匹配 `3K_DNA_IRIS_UNIQUE_ID` 的样本数为 3024 / 3024。该文件是 B001 / CX / IRIS ID 到 stock name 与 SRA accession 的主桥梁。

## RunInfo 匹配

通过 `SRA Accession` ↔ RunInfo `Sample` 匹配到 RunInfo 的 genotype 样本数为 3024 / 3024。一个 SRA Sample 可以对应多个 Run，已在 master 中用分号合并 `run_accessions`、`experiment_accessions`、`biosample_ids` 和 `library_names`。

## Genesys MCPD 匹配

Genesys MCPD 匹配到 2706 / 3024 个 genotype 样本。优先使用 IRGC ID 精确匹配，其次才使用 normalized stock name；名称匹配或国家字段冲突进入人工审查。

## Phenotype 匹配

phenotype accession-like candidate 数为 14002，候选匹配记录数为 16178。有任意 phenotype 匹配的 genotype 样本数为 2281 / 3024，其中 A/B 级可用于 trait mapping 的样本数为 2269 / 3024。

## 置信度统计

genotype mapping：A=3024，B=0，C=0，D=0。

phenotype mapping：A=0，B=2269，C=12，D=743。

## 可用于 trait mapping 的样本数

当前 `usable_for_trait_mapping=true` 的样本数为 2269。只有 A/B 级 phenotype mapping 可以进入正式 trait_value_table。C 级 name match 只能人工复核，不能直接训练。

## 不能用于 trait mapping 的原因

不能直接用于 trait mapping 的主要原因包括：没有 phenotype accession-like 匹配、只有 normalized stock name 匹配、同一 phenotype 行或同一 genotype 样本存在多重匹配、IRGC 一致但名称不一致、Genesys 与 3K_list country 字段冲突。

## 是否可以进入正式 trait_value_table 构建

当前只能在 A/B 级 phenotype mapping 样本上试做小范围 trait_state prototype。正式 `trait_value_table` 仍需先审查 `manual_review_candidates.tsv`，确认重复 phenotype 记录的聚合策略，并冻结 `accession_mapping_master.tsv` 的高置信子集。

## 下一步建议

优先人工审查 `manual_review_candidates.tsv` 中的 C 级名称匹配和多重匹配；然后生成 high-confidence accession mapping 子集。若 A/B 级 phenotype mapping 覆盖足够，再构建 trait_state 和最小 Task 1 instances；若不足，先补充 accession ID mapping。
