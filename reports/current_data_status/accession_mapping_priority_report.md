# Accession Mapping Source 优先级报告

## 当前结论

当前可以开始构建 `accession_mapping_master.tsv` 的第一版草稿，但不能直接进入正式 benchmark instance 构建。原因是 genotype 侧 B001-style sample IDs 已经来自 PLINK fam 与 Qmatrix，SRA / stock / passport 侧也有本地来源；但 B001、IRIS/GS accession、stock name、SRA accession、BioSample 和 phenotype `STOCK_ID` / `GS_ACCNO` 的高置信关系仍需要逐步核验。

## 主桥梁与补充来源

`3K_list_sra_ids.txt` 是 genotype ID / IRIS-style ID ↔ stock name ↔ SRA accession 的主桥梁。本地状态：present；records=3024。

Genesys MCPD 是 passport / IRGC / name 补充。本地状态：present；records=2761。

NCBI RunInfo 是 SRA / BioSample / Run 补充。本地状态：present；records=25529。

Qmatrix 和 PLINK fam 是 genotype sample ID 的主来源。本地状态：SNP fam present；records=3024；indel fam present；records=3023；Qmatrix present；records=3023。

phenotype XLSX 是 trait_state 的来源，但不能当 phenotype prediction target。本地状态：present；records=5203。

## 必须优先检查的 ID 关系

1. `core_v0.7.fam.gz` / `Nipponbare_indel.fam.gz` / `Qmatrix-k9-3kRG.csv` 之间的 B001-style sample ID 集合与顺序。
2. B001-style sample ID 到 `3K_list_sra_ids.txt` 中 IRIS/stock/SRA 字段的连接路径。
3. phenotype XLSX 中 `STOCK_ID`、`GS_ACCNO`、`NAME`、`Source_Accno` 与 SNP-Seek / Genesys / RunInfo 的关系。
4. `SRA Accession` 到 NCBI RunInfo 中 `Sample`、`BioSample`、`Run`、`Experiment` 的一对多关系。
5. Genesys MCPD 中 accession name、IRGC/passport 字段与 phenotype name/source accession 的同义词关系。

## 当前可执行动作

下一步应构建 `accession_mapping_master.tsv` 草稿，并为每一条映射记录保留 source、match rule、confidence、manual_review_required 和 conflict flag。高置信 mapping 完成前，不应生成正式 trait-conditioned benchmark instances。
