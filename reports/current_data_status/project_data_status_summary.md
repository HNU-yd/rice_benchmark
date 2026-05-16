# 项目当前数据状态总报告

## 当前已下载的 3K Rice 数据

当前 `data/raw/` 下共有 74 个文件，总大小约 4.26 GiB。已覆盖的数据类别包括：Oryzabase,Q-TARO,Qmatrix / population structure,SNP genotype,accession metadata,annotation,indel genotype,listing / metadata,phenotype / trait,pruned SNP,reference,Sanciangco / Dataverse。

主要 3K Rice backbone 资产包括 reference FASTA、GFF3 annotation、SNP genotype、indel genotype、pruned SNP、Qmatrix、3K phenotype XLSX、SNP-Seek SRA list、Genesys MCPD 和 NCBI RunInfo。

## 当前 weak evidence

当前已下载并登记 Oryzabase known/cloned trait gene list 与 Q-TARO QTL interval archive。v0.1 可以使用 Oryzabase + Q-TARO 做 `weak localization evidence` 候选。它们不能写成 `causal ground truth`，未覆盖的 variant/window 仍然是 unknown，不能当作 negative。

## accession mapping 状态

本地 accession mapping 来源已经比较齐全，但高置信 master table 尚未构建。`3K_list_sra_ids.txt`、Genesys MCPD、NCBI RunInfo、PLINK fam、Qmatrix 和 phenotype XLSX 均已存在。当前最优先事项是构建 `accession_mapping_master.tsv`。

关键来源状态：

- SNP-Seek 3K_list_sra_ids：present
- Genesys MCPD：present
- NCBI RunInfo：present
- SNP PLINK fam：present
- indel PLINK fam：present
- Qmatrix：present
- phenotype XLSX：present

## genotype 数据状态

SNP genotype 和 indel genotype backbone 已在本地。SNP `core_v0.7.*` 与 indel `Nipponbare_indel.*` 可以作为 v0.1/v0.2 的主要候选，但仍需验证 sample set、sample order、chromosome naming 和 coordinate mapping。pruned SNP / LD-pruned PLINK 资产可作为后续 GWAS 或 QC 辅助。

## trait 数据状态

3K phenotype XLSX 已在本地，后续只能用于构建 `trait_state` 和 trait-conditioned query，不做 `phenotype prediction`，不做 trait classification。trait accession 到 genotype sample 的 mapping 完成前，不应生成正式 benchmark instances。

## 当前缺失数据

当前缺失项中阻塞 v0.1 的是：标准 accession ID master table,trait accession 与 genotype sample 的高置信 mapping,正式 trait_value_table。

GWAS lead SNP、更多文献级 evidence、RAP/MSU/Gramene ID mapping、功能注释增强层、表达/多组学数据都不阻塞当前阶段。Dataverse GWAS 下载失败不阻塞当前阶段。

## manifest / checksum 状态

当前 raw 文件中已有 65 个文件登记 checksum，9 个文件仍缺 checksum/manifest 补登记。缺口主要来自新落地的 accession mapping 文件和 pruned SNP 文件。04C 只做统计，不修改 manifest；正式使用这些文件前必须补登记 checksum。

## 外部数据库路线

外部数据库应作为知识层，而不是替代 3K Rice genotype backbone。第一优先是 accession ID mapping files、funRiceGenes、RAP-DB gene annotation / mapping，以及继续整理已有 Oryzabase / Q-TARO。第二优先是 RiceVarMap / RiceVarMap2 variation annotation 和 MSU / Gramene / Ensembl ID mapping。第三优先是 MBKbase、Lin2020 PNAS 与 Sanciangco Dataverse metadata。

## 下一步

下一步最优先创建 Phase 4D / Phase 5 prompt：构建 `accession_mapping_master.tsv` 草稿，固定 ID 字段、source、match rule、confidence 和 manual review flag。v0.2 可以在 accession mapping 完成后自跑 GWAS 生成 Tier 2 `weak localization evidence`。
