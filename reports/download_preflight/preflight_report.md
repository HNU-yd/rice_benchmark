# Phase 2A Preflight Report

## 1. 执行时间

本次执行时间：2026-05-16T01:15:22+08:00。

## 2. 检查的文件

本次读取和检查了以下文件：

- `manifest/source_inventory.tsv`
- `manifest/source_inventory.schema.tsv`
- `reports/source_inventory/p0_source_review.tsv`
- `reports/source_inventory/source_inventory_review.md`
- `configs/sources.yaml`
- `docs/data_acquisition_plan.md`

## 3. source_inventory 总行数

修正 reference source 后，`manifest/source_inventory.tsv` 包含 22 条数据源记录，不含表头。

## 4. P0 source 数量

当前 P0 source 数量为 11。新增的 `SRC_REF_IRGSP_FASTA_003` 是 P0 reference candidate，用于确认 GCF_001433935.1 / IRGSP-1.0 下载入口。

`manifest/preflight_verified_sources.tsv` 当前包含 12 条记录，其中包括 1 条 `exclude_from_v1` 边界记录。

## 5. AWS listing 是否成功

未成功执行 AWS listing。当前环境未检测到 `aws` CLI，因此未运行 `aws s3 ls`。

结果已记录在 `reports/download_preflight/aws_listing_summary.tsv`：

- `s3://3kricegenome/`：aws_cli_unavailable
- `s3://3kricegenome/snpseek-dl/`：aws_cli_unavailable
- `s3://3kricegenome/VCF/`：aws_cli_unavailable

## 6. HTTP header check 是否成功

已执行允许的 HTTP header check：

- `curl -I https://snp-seek.irri.org/`：HTTP 200。
- `curl -I https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001433935.1/`：HTTP 200。

这些结果只能说明 landing page 或 metadata page 可访问，不能证明 raw data 文件、导出接口、checksum 或版本已经确认。

## 7. 已生成的 manifest 文件

本次生成或更新：

- `manifest/preflight_verified_sources.tsv`
- `manifest/download_manifest.tsv`
- `manifest/download_manifest.schema.tsv`
- `manifest/checksum_table.tsv`
- `manifest/checksum_table.schema.tsv`
- `manifest/source_inventory.tsv`

## 8. 未下载任何 raw data 的确认

本次未下载 VCF、BCF、FASTA、GFF、BAM、CRAM、FASTQ、HDF5、parquet 或其他 raw data 文件。

本次未执行 `aws s3 cp`、`aws s3 sync`、`curl -O`、`wget URL`、`prefetch` 或 `fasterq-dump`。

本次未创建 `data/raw/` 目录，也未向 git 添加 raw data 文件。

## 9. Phase 2B 前必须人工确认的问题

Phase 2B 前必须确认：

- SNP-Seek offline / mirror validation。
- SNP genotype exact file list、release、checksum 和 accession list。
- indel genotype exact file path、ref/alt 表示和 accession-level genotype。
- reference genome GCF/GCA source choice、FASTA package、chromosome naming 和 checksum。
- trait table accession overlap、trait unit、重复测量和环境信息。
- weak evidence leakage control、QTL coordinate build 和 known gene database ID mapping。

这些事项已写入 `reports/download_preflight/manual_confirmation_required.tsv`。
