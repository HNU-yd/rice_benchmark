# P0 Download Source 确认报告

## 1. 本次核验目标

本次执行 Phase 2B-0，目标是对 Phase 2A 中仍需人工确认的 P0 数据源做轻量级 exact file list / URL / S3 path 核验，并决定哪些来源可以进入 Phase 2C 下载候选清单。

本次不下载 VCF、BCF、FASTA、GFF、BAM、CRAM、FASTQ、HDF5、parquet 或其他 raw data 文件。

## 2. 核验输入文件

本次读取：

- `manifest/source_inventory.tsv`
- `manifest/preflight_verified_sources.tsv`
- `manifest/download_manifest.tsv`
- `manifest/checksum_table.tsv`
- `reports/source_inventory/p0_source_review.tsv`
- `reports/download_preflight/manual_confirmation_required.tsv`
- `reports/download_preflight/preflight_report.md`
- `reports/download_preflight/aws_listing_summary.tsv`
- `configs/sources.yaml`
- `docs/download_plan.md`

## 3. P0 source 总数

当前 `manifest/preflight_verified_sources.tsv` 中 P0 source 共 11 条。

其中只有 1 个 source 被标记为 `phase2b_ready=yes`：`SRC_REF_IRGSP_FASTA_003`。

## 4. 已确认 exact download source 的数据源

已确认 exact download source 的数据源：

- `SRC_REF_IRGSP_FASTA_003`：NCBI RefSeq assembly `GCF_001433935.1_IRGSP-1.0`。

HEAD 检查确认以下 exact URL 返回 HTTP 200：

- `GCF_001433935.1_IRGSP-1.0_genomic.fna.gz`
- `GCF_001433935.1_IRGSP-1.0_genomic.gff.gz`
- `md5checksums.txt`

这些文件已进入 `phase2c_download_candidates.tsv`，但 Phase 2C 仍必须先 dry-run，再下载，并在下载后计算 sha256。

## 5. 仍需人工确认的数据源

仍需人工确认的数据源包括：

- `SRC_3K_SNP_GENOTYPE_001`
- `SRC_3K_INDEL_GENOTYPE_002`

这两项目前只有 S3 prefix，且当前环境没有 `aws` CLI，不能生成 exact file list。

## 6. 不能下载的数据源

当前不能下载的数据源包括：

- `SRC_3K_ACCESSION_METADATA_001`
- `SRC_3K_INDEL_GENOTYPE_001`
- `SRC_TRAIT_TABLE_001`
- `SRC_TRAIT_TABLE_003`
- `SRC_WEAK_KNOWN_GENES_001`
- `SRC_WEAK_QTL_001`
- `SRC_WEAK_GWAS_001`

主要原因是只有 landing page、HTTP 403、缺少 exact export path、缺少 accession field 说明，或存在 weak evidence leakage 风险。

## 7. accession metadata 结果

`https://snp-seek.irri.org/` 返回 HTTP 200，但这只是 landing page。

本次没有确认 exact accession metadata export URL，也没有确认 accession_id、variety name、sample_id、subpopulation 或 geographic metadata 字段。因此 accession metadata 不能进入 Phase 2C 下载。

## 8. SNP genotype 结果

`SRC_3K_SNP_GENOTYPE_001` 仍只有 S3 prefix：`s3://3kricegenome/snpseek-dl/3krg-base-filt-core-v0.7/`。

当前环境没有 `aws` CLI，无法执行 exact listing。该 source 不能标记为 `phase2b_ready=yes`。

## 9. indel genotype 结果

indel genotype 仍未确认 exact file path。

`SRC_3K_INDEL_GENOTYPE_001` 只有 SNP-Seek landing page。`SRC_3K_INDEL_GENOTYPE_002` 只有 S3 VCF prefix，且当前环境无法 listing。

indel 是 v1 必需数据源，不能用 SNP 替代。Phase 2C 前必须确认 exact indel/joint VCF file names、accession layout、ref/alt allele 和 insertion/deletion 表示。

## 10. reference genome 结果

reference genome 是本次唯一确认到 exact source 的 P0 类别。

`SRC_REF_IRGSP_FASTA_003` 指向 NCBI FTP exact directory：

`https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/433/935/GCF_001433935.1_IRGSP-1.0/`

可进入 Phase 2C 的候选为 FASTA 和 GFF3。`SRC_REF_IRGSP_FASTA_001` 的 GCA landing page 继续保留，但不作为下载候选。

## 11. trait table 结果

`SRC_TRAIT_TABLE_001` 只有 SNP-Seek landing page。

`SRC_TRAIT_TABLE_003` 的 XLSX URL 在 HEAD 检查中返回 HTTP 403 Forbidden，并且 accession ID 字段、source version、checksum 和 accession overlap 都未确认。

trait table 只能用于构建 trait_state，不能作为 `phenotype prediction` target。当前 trait table 不进入 Phase 2C 下载候选。

## 12. weak evidence 结果

weak evidence 仍未确认 exact download source。

Q-TARO 页面返回 HTTP 200，但只是 metadata page，不是 exact QTL export。known genes 和 GWAS evidence 缺少具体文件 URL 或访问方法。

所有 weak evidence 只能作为 `weak localization evidence`，不能写成 `causal ground truth`。GWAS lead SNPs 当前建议 defer，直到建立人工文献筛选规则和 leakage control。

## 13. 是否允许进入 Phase 2C 下载的建议

只有 `phase2c_download_candidates.tsv` 中列出的候选项允许进入 Phase 2C。

仍 unresolved 的 P0 source 不允许下载。

Phase 2C 应只针对 `SRC_REF_IRGSP_FASTA_003` 的 FASTA/GFF3 候选创建 dry-run 优先的下载 prompt。SNP、indel、trait 和 weak evidence 必须继续人工确认 exact source。
