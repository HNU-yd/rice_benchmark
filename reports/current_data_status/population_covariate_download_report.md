# Population Covariate Download Report

## Scope

本次补齐用户要求的亚群、PC / kinship、来源批次和环境因素相关数据。没有扩大 benchmark 边界；这些数据只能作为 accession metadata、population covariate、batch covariate 或后续自跑 GWAS 的协变量候选，不构成 phenotype prediction target，也不构成 causal ground truth。

## Downloaded Files

| role | local path | size bytes | sha256 | validation |
|---|---|---:|---|---|
| sample-level PCA scores | `data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.eigenvec` | 483387 | `cb8c25bc86bad4d051cd393a12a79b3d9160dd7816f38253ce23bac88935370a` | 3024 samples + header, 14 columns |
| PCA eigenvalues | `data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.eigenval` | 95 | `41406643e6b0ace4f30e9116afce9037538d1a06145577770abc9065a5a5c014` | 12 eigenvalues |
| PCA run log | `data/raw/variants/snp/pruned_v2.1/pca/pca_pruned_v2.1.log` | 1192 | `b2cce29cf65519c95c9cf79489846f2c881cac3250957d1c5185d306112dd5d9` | PLINK log says 3024 people and 1011601 variants |
| kinship matrix | `data/raw/variants/snp/pruned_v2.1/kinship/result.cXX.txt.bz2` | 46533413 | `4f2eece1feb71b1022ee9d79d9a9b79580272d2e59aa7ff725212bed82c44e1b` | bzip2 valid; 3024 rows x 3024 columns |

## Already Available Inputs

| category | local path | current status |
|---|---|---|
| Qmatrix / subgroup proportions | `data/raw/metadata/Qmatrix-k9-3kRG.csv` | present; 3023 samples, K=9 columns |
| accession to SRA bridge | `data/raw/accessions/snpseek/3K_list_sra_ids.txt` | present; 3024 rows |
| sequencing run / batch metadata | `data/raw/accessions/ncbi_prjeb6180/PRJEB6180_runinfo.csv` | present; Run, Experiment, BioSample, LibraryName, Platform and CenterName fields |
| passport / origin metadata | `data/raw/accessions/genesys/genesys_3k_mcpd_passport.xlsx` | present; ORIGCTY, SUBTAXA and COLLSRC mostly populated |
| phenotype / trait source | `data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx` | present; has CROPYEAR but not a full environment/site covariate table |

## Validation Summary

- PCA sample order matches `data/raw/variants/snp/pruned_v2.1/pruned_v2.1.fam` exactly.
- PCA sample order also matches `data/raw/variants/snp/core_v0.7.fam.gz` exactly.
- Qmatrix has 3023 samples; one PCA/FAM sample is not present in Qmatrix.
- Kinship matrix is usable as a compressed GEMMA relatedness matrix after decompression.
- The public S3 phenotype prefix contains only `3kRG_PhenotypeData_v20170411.xlsx`; no separate environment/site/season covariate file was found in the local AWS listing.

## Manual Download Status

No file failed to download in this step. No user-side manual upload is required for the four missing PC / kinship files.

Fallback URLs if re-download is needed:

- `https://3kricegenome.s3.amazonaws.com/snpseek-dl/3k-pruned-v2.1/pruned_v2.1.pca/pca_pruned_v2.1.eigenvec`
- `https://3kricegenome.s3.amazonaws.com/snpseek-dl/3k-pruned-v2.1/pruned_v2.1.pca/pca_pruned_v2.1.eigenval`
- `https://3kricegenome.s3.amazonaws.com/snpseek-dl/3k-pruned-v2.1/pruned_v2.1.pca/pca_pruned_v2.1.log`
- `https://3kricegenome.s3.amazonaws.com/snpseek-dl/3k-pruned-v2.1/pruned_v2.1.kinship/result.cXX.txt.bz2`

## Remaining Risk

环境因素仍然不完整。当前可用的是 `CROPYEAR`、country / passport origin、SUBTAXA 和 sequencing run metadata；这些字段不能等同于严格的 field trial environment。若后续模型需要环境协变量，应先设计单独的 covariate schema，并把 `CROPYEAR` 与 passport/source fields 标记为 weak proxy。
