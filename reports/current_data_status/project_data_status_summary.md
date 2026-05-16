# 项目当前数据状态总报告

## 当前已下载的 3K Rice 数据

当前 `data/raw/` 下共有 74 个文件，总大小约 4.26 GiB。已覆盖的数据类别包括：Oryzabase,Q-TARO,Qmatrix / population structure,SNP genotype,accession metadata,annotation,indel genotype,listing / metadata,phenotype / trait,pruned SNP,reference,Sanciangco / Dataverse。

主要 3K Rice backbone 资产包括 reference FASTA、GFF3 annotation、SNP genotype、indel genotype、pruned SNP、Qmatrix、3K phenotype XLSX、SNP-Seek SRA list、Genesys MCPD 和 NCBI RunInfo。

## 当前 weak evidence

当前已下载并登记 Oryzabase known/cloned trait gene list 与 Q-TARO QTL interval archive。v0.1 可以使用 Oryzabase + Q-TARO 做 `weak localization evidence` 候选。它们不能写成 `causal ground truth`，未覆盖的 variant/window 仍然是 unknown，不能当作 negative。

## accession mapping 状态

本地 accession mapping 来源已经比较齐全，Phase 4D 已构建 `accession_mapping_master.tsv` 草稿，Phase 4E 已形成 accession ID harmonization 口径说明。主 benchmark 只允许使用 A/B high-confidence phenotype mappings；C-level name-only candidates 只进入人工审查；D-level unmapped samples 不解释为 negative，也不进入 trait-conditioned training/evaluation。

当前 genotype union samples 为 3024。`3K_list_sra_ids.txt` 和 NCBI RunInfo 均覆盖 3024 / 3024 个 genotype samples，Genesys MCPD 覆盖 2706 / 3024。phenotype 侧当前 A=0、B=2269、C=12、D=743；可用于 trait mapping 的 high-confidence subset 为 2269 个样本。

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

当前缺失项中阻塞 v0.1 的是：冻结后的 high-confidence accession subset、正式 trait_value_table 和基于该 subset 的 benchmark split。

GWAS lead SNP、更多文献级 evidence、RAP/MSU/Gramene ID mapping、功能注释增强层、表达/多组学数据都不阻塞当前阶段。Dataverse GWAS 下载失败不阻塞当前阶段。

## manifest / checksum 状态

当前 raw 文件中已有 65 个文件登记 checksum，9 个文件仍缺 checksum/manifest 补登记。缺口主要来自新落地的 accession mapping 文件和 pruned SNP 文件。04C 只做统计，不修改 manifest；正式使用这些文件前必须补登记 checksum。

## 外部数据库路线

外部数据库应作为知识层，而不是替代 3K Rice genotype backbone。第一优先是 accession ID mapping files、funRiceGenes、RAP-DB gene annotation / mapping，以及继续整理已有 Oryzabase / Q-TARO。第二优先是 RiceVarMap / RiceVarMap2 variation annotation 和 MSU / Gramene / Ensembl ID mapping。第三优先是 MBKbase、Lin2020 PNAS 与 Sanciangco Dataverse metadata。

## 下一步

下一步最优先创建 Phase 5 prompt：基于 A/B high-confidence accession subset 构建 trait_value_table 草案，并在冻结 ID 口径后生成 Task 1 instances。v0.2 可以在 accession mapping 和 trait table 稳定后自跑 GWAS 生成 Tier 2 `weak localization evidence`。
