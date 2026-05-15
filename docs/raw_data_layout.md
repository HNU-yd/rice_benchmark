# Raw Data 目录规划

本文档只规划后续 raw data 目录结构。Phase 2A 不创建 `data/raw/`，不下载 raw data，不提交 raw data 文件。

## 规划结构

```text
data/raw/
  reference/
  variants/
    snp/
    indel/
    joint_vcf/
  accessions/
  traits/
  annotation/
  evidence/
  aws_listing/
```

## 目录用途

`data/raw/reference/` 用于存放后续确认并下载的 IRGSP-1.0 reference FASTA、FAI、dict 或相关 metadata。不得混入 derived windows 或 processed sequence tables。

`data/raw/variants/snp/` 用于存放 3K Rice SNP genotype raw files。不得放入 normalized benchmark tables。

`data/raw/variants/indel/` 用于存放 3K Rice indel genotype raw files。不得放入后续 schema 化的 `indel_table` 或 `edit_operation_table`。

`data/raw/variants/joint_vcf/` 用于存放同时包含 SNP + indel 的 joint VCF 或 accession-level VCF。使用前必须记录 source_id、reference build 和 accession layout。

`data/raw/accessions/` 用于存放 accession metadata、passport metadata、subpopulation 和 geography 相关 raw source。

`data/raw/traits/` 用于存放 trait / phenotype raw tables。该目录中的数据只能用于构建 trait_state，不能作为 `phenotype prediction` target。

`data/raw/annotation/` 用于存放 gene annotation、functional annotation、GO/pathway annotation raw files。不得在 raw 目录中写入 processed gene feature tables。

`data/raw/evidence/` 用于存放 GWAS、QTL、known genes、LD blocks、credible intervals 和 trait-gene annotation raw evidence。所有 evidence 只能作为 `weak localization evidence`。

`data/raw/aws_listing/` 用于存放后续 Phase 2B 生成的小型 AWS listing metadata。不得存放 VCF/BCF/BAM/CRAM 等 raw genotype 文件。

## 不允许放入 raw data 目录的内容

- benchmark schema tables。
- train/val/test splits。
- model outputs。
- evaluator outputs。
- normalized windows。
- generated matched decoy。
- 手工编辑过但未记录 provenance 的数据。

## Git 规则

`data/raw/` 及其子目录不进入 git。

只允许提交：

- `manifest/*.tsv`
- `manifest/*.schema.tsv`
- `reports/download_preflight/*.tsv`
- `reports/download_preflight/*.md`
- 下载脚本模板
- 文档

