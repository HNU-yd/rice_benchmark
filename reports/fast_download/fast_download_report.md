# Phase 2D 快速下载报告

执行日期：2026-05-16（Asia/Shanghai）。

## 1. 本次任务目标

本次任务的目标是在不继续过度 preflight 的前提下，快速列出 AWS / 42basepairs / SNP-Seek mirror 中可访问的 3K Rice 数据，并优先下载第一阶段 benchmark 需要的 raw data：reference FASTA、reference GFF3 / annotation、accession metadata、SNP genotype、indel genotype、trait / phenotype table，以及可直接获取的 weak evidence 文件。

本次任务仍严格遵守项目边界：主位数据限定为 3K Rice，变异限定为 SNP / indel，不下载 BAM / CRAM / FASTQ / SRA，不纳入 SV、PAV、CNV、pan-reference、多物种数据、模型权重或 Evo2 embedding，不实现 schema、model、evaluator 或 benchmark construction。

## 2. 成功 listing 的来源

成功完成 listing 的 AWS S3 来源如下：

| listing_id | path | 行数 | 输出文件 |
| --- | --- | ---: | --- |
| aws_3kricegenome_root | `s3://3kricegenome/` | 36 | `data/raw/listings/aws_3kricegenome_root.txt` |
| aws_3kricegenome_snpseek_dl | `s3://3kricegenome/snpseek-dl/` | 21 | `data/raw/listings/aws_3kricegenome_snpseek_dl.txt` |
| aws_3kricegenome_reduced | `s3://3kricegenome/reduced/` | 36 | `data/raw/listings/aws_3kricegenome_reduced.txt` |
| aws_3kricegenome_reduced_recursive | `s3://3kricegenome/reduced/ --recursive` | 36 | `data/raw/listings/aws_3kricegenome_reduced_recursive.txt` |
| aws_3kricegenome_snpseek_dl_recursive | `s3://3kricegenome/snpseek-dl/ --recursive` | 143 | `data/raw/listings/aws_3kricegenome_snpseek_dl_recursive.txt` |
| aws_3kricegenome_snpseek_dl_phenotype | `s3://3kricegenome/snpseek-dl/phenotype/` | 2 | `data/raw/listings/aws_3kricegenome_snpseek_dl_phenotype.txt` |
| aws_3kricegenome_snpseek_dl_core | `s3://3kricegenome/snpseek-dl/3krg-base-filt-core-v0.7/` | 17 | `data/raw/listings/aws_3kricegenome_snpseek_dl_core.txt` |

`s3://3kricegenome/VCF/` 本次未列出可用文件，已保留空 listing 文件用于记录。

## 3. AWS / 42basepairs / SNP-Seek mirror 可用性

AWS Open Data 3K Rice 是本次实际下载来源，root、`snpseek-dl/`、`reduced/`、phenotype 和 core SNP prefix 可访问。

42basepairs mirror 的 root 和 `reduced` 页面 HTTP 状态为 200，可作为网页核验或备用入口，但本次没有通过 42basepairs 下载 raw data。

SNP-Seek mirror `https://snpseekv3.duckdns.org/` 和 `https://brs-snpseek.duckdns.org/` 的首页 HTTP 状态为 200。本次没有从 mirror 导出数据库表，因为 accession metadata 的字段结构和 export schema 需要在 raw data inventory 阶段检查。

可用性记录见 `reports/fast_download/mirror_availability.tsv`。

## 4. 自动筛选出的下载候选数量

`reports/fast_download/auto_download_candidates.tsv` 共筛选出 55 个下载候选。

按候选类别统计：

| data_category | 候选数 |
| --- | ---: |
| reference | 1 |
| annotation | 1 |
| metadata | 1 |
| accession_metadata | 10 |
| snp_genotype | 36 |
| indel_genotype | 5 |
| trait_table | 1 |
| weak_evidence | 0 |

## 5. 实际下载文件数量

55 个下载候选全部下载成功，缺失候选数为 0。另保存 8 个 S3 listing 文件。`manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv` 当前共登记 63 个 `data/raw` 文件。

主要下载内容包括：

- `GCF_001433935.1_IRGSP-1.0_genomic.fna.gz`
- `GCF_001433935.1_IRGSP-1.0_genomic.gff.gz`
- `md5checksums.txt`
- `RICE_RP.tar.gz`
- `Qmatrix-k9-3kRG.csv`
- `3kRG_PhenotypeData_v20170411.xlsx`
- `NB_bialSNP_pseudo.vcf.gz` 和 `.tbi`
- `NB_bialSNP_pseudo_canonical_ALL.vcf.gz`
- `3K_coreSNP-v2.1.plink.tar.gz`
- `3k-core-v7-chr1.zip` 到 `3k-core-v7-chr12.zip`
- `core_v0.7.bed.gz`、`core_v0.7.bim.gz`、`core_v0.7.fam.gz`
- `Nipponbare_indel.bed.gz`、`Nipponbare_indel.bim.gz`、`Nipponbare_indel.fam.gz`
- 相关 README、license、download page、manifest 和 pruned PCA metadata 文件

完整文件清单见 `reports/fast_download/raw_file_list.txt`。

## 6. 按类别统计

| 类别 | 下载状态 | 文件数 | 字节数 | 说明 |
| --- | --- | ---: | ---: | --- |
| reference | 已下载 | 1 | 118932090 | IRGSP-1.0 RefSeq FASTA |
| annotation | 已下载 | 1 | 10328864 | IRGSP-1.0 RefSeq GFF3 |
| metadata / checksum | 已下载 | 1 | 12720 | NCBI md5checksums.txt |
| accession metadata | 已下载，待 inventory 解包检查 | 10 | 989931158 | 包含 `RICE_RP.tar.gz`、Qmatrix、download page、manifest、README |
| SNP genotype | 已下载 | 36 | 2389837030 | 包含 reduced VCF、canonical VCF、core SNP、PLINK、per-chromosome core zip |
| indel genotype | 已下载 | 5 | 250804901 | 包含 `Nipponbare_indel.*.gz` 和 indel README |
| trait table | 已下载 | 1 | 1135836 | `3kRG_PhenotypeData_v20170411.xlsx` |
| weak evidence | 未下载 | 0 | 0 | 未在 fast listing 中发现可直接纳入的 known gene / QTL / GWAS lead SNP 表 |
| listing metadata | 已保存 | 8 | 19263 | AWS listing 结果 |

## 7. 跳过的 BAM / CRAM / FASTQ 文件

本次已检查的 AWS listing 中未发现被候选筛选器纳入的 BAM / CRAM / FASTQ / SRA 文件。

筛选器另外跳过了 out-of-scope 的 CNV / LargeSV 文件，包括 `CNVnator_Q10_goodRD_noCN1-3.vcf.gz`、`CNVnator_Q10_goodRD_noCN1-3_regions.txt` 和 `LargeSV-README.txt`。这些文件不属于第一版 SNP / indel benchmark 范围。

跳过记录见 `reports/fast_download/skipped_large_raw_reads.tsv`。

## 8. 下载失败的文件

最终补跑后没有下载失败文件。`reports/fast_download/download_failures.tsv` 只保留表头。

执行过程中曾发现 non-recursive prefix listing 的 S3 key 需要补齐 prefix；已在 `scripts/download/select_download_candidates.py` 中修正，并补跑下载完成。

## 9. checksum 结果

`scripts/download/update_fast_download_manifest.py` 已对 63 个 `data/raw` 文件计算 sha256，并更新：

- `manifest/download_manifest.tsv`
- `manifest/checksum_table.tsv`
- `reports/fast_download/downloaded_files.tsv`
- `reports/fast_download/checksum_summary.tsv`

`python scripts/utils/validate_download_manifest.py manifest/download_manifest.tsv` 校验通过。

## 10. raw data 未进入 git 的确认

`git status --short --ignored` 显示 `data/` 处于 ignored 状态，未出现在待提交文件中。`data/raw/` 下 raw data 不会进入本次 commit。

## 11. 仍缺失的数据

仍缺失或需要后续 inventory/人工核验的数据包括：

- `RICE_RP.tar.gz` 中是否存在可直接作为主 accession metadata 的 accession_id 字段，需要解包审阅后确认。
- known trait genes / cloned genes：fast listing 中没有发现可直接下载的 3K Rice trait-specific 表。
- GWAS lead SNPs / significant SNPs：fast listing 中没有发现可直接使用的 3K Rice GWAS lead SNP 表。
- QTL intervals：本次未发现可直接下载并确认 coordinate build 的 QTL interval 表。

这些缺口不能用 `unknown == negative` 的方式处理，也不能把 weak evidence 写成 `causal ground truth`。

## 12. 下一步

下一步应创建 raw data inventory prompt，对已下载文件做 accession / SNP / indel / trait / reference build 对齐检查。

inventory 阶段应优先完成：

- 解包并检查 `RICE_RP.tar.gz` 的 accession metadata 字段。
- 检查 SNP 与 indel 文件的 accession overlap。
- 检查 `3kRG_PhenotypeData_v20170411.xlsx` 与 genotype accession 的可映射性。
- 检查 FASTA / GFF3 / SNP / indel 的 chromosome naming 和 reference build 是否一致。
- 建立不能作为 negative 的 unknown / unlabeled variants 记录规则。
