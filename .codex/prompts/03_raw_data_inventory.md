# 03_raw_data_inventory.md

你现在执行 Phase 3：raw data inventory / 数据可用性审查。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

当前 raw data 已经通过快速下载落盘。现在不要继续下载，也不要写 benchmark schema、split、evaluator、model 或 Evo2。
本任务目标是：对 `data/raw/` 下已经下载的 3K Rice 数据进行系统 inventory，确认 reference、annotation、accession metadata、SNP genotype、indel genotype、trait table 是否能对齐，并给出 v0.1-mini / v0.2-core 的数据可用性建议。

---

## 0. 语言要求

所有说明性文档主体使用中文。

固定术语、字段名、目录名、文件名、命令名可以保留英文，例如：

- 3K Rice
- SNP / indel
- Task 1 / Task 2
- accession
- trait_state
- reference window
- weak localization evidence
- matched decoy
- phenotype prediction
- causal ground truth
- unknown != negative
- VCF
- PLINK
- FASTA
- GFF3
- FAM
- BIM
- BED
- XLSX

文档风格必须是科研工程说明文，直接、清楚、可执行。

---

## 1. 项目边界

第一版 benchmark 仍然严格限定为：

1. 主位数据只使用 3K Rice。
2. 变异范围只包含 SNP + indel。
3. Task 1 是 trait-conditioned SNP/indel localization。
4. Task 2 只是 supplementary / application demo。
5. 不做 phenotype prediction。
6. 不做 trait classification。
7. 不纳入 SV、PAV、CNV。
8. 不使用 pan-reference、multi-reference、多物种 benchmark。
9. 不重新预训练 genome foundation model。
10. weak evidence 只能作为 weak localization evidence。
11. GWAS/QTL/known gene 不能写成 causal ground truth。
12. unknown / unlabeled variants 不能默认作为 negative。

本任务只是 raw data inventory，不做训练、不做模型、不生成 benchmark 正式表。

---

## 2. 本任务允许做什么

允许读取和检查：

```text
data/raw/reference/
data/raw/annotation/
data/raw/accessions/
data/raw/variants/
data/raw/traits/
data/raw/metadata/
data/raw/listings/
manifest/download_manifest.tsv
manifest/checksum_table.tsv
reports/fast_download/raw_file_list.txt
reports/fast_download/downloaded_files.tsv
````

允许创建：

```text
reports/raw_data_inventory/
data/interim/inventory/
```

允许创建或更新脚本：

```text
scripts/inspect/inspect_raw_files.py
scripts/inspect/inspect_archives.py
scripts/inspect/inspect_reference.py
scripts/inspect/inspect_vcf_headers.py
scripts/inspect/inspect_plink_files.py
scripts/inspect/inspect_trait_table.py
scripts/inspect/inspect_accession_metadata.py
scripts/inspect/compare_accession_sets.py
scripts/inspect/run_raw_inventory.sh
```

允许解包小型 metadata / README / manifest / table 文件。
允许列出 `.tar.gz` / `.zip` 内容。
允许从压缩包中只抽取元数据文件、README、CSV、TSV、XLS/XLSX、FAM/BIM 小文件。
不要盲目解压大型 genotype 全量文件到 git 管理目录。

---

## 3. 本任务禁止做什么

禁止：

```text
不要继续下载 raw data
不要执行 aws s3 cp/sync
不要执行 wget/curl 下载新数据
不要执行 prefetch / fasterq-dump
不要写 benchmark schema
不要构建正式 accession_table / variant_table / genotype_table
不要构建 split
不要构建 evaluator
不要写 baseline
不要写 model
不要写 Evo2 代码
不要做 phenotype prediction
不要把 phenotype 当预测目标
不要把 unknown 当 negative
不要把 weak evidence 当 causal ground truth
不要把 data/raw/ 加入 git
```

---

## 4. 本任务核心目标

本阶段要回答以下问题：

```text
1. data/raw 中每个文件是什么？
2. reference FASTA 的 chromosome / contig 命名是什么？
3. GFF3 的 chromosome / seqid 命名是否与 FASTA 一致？
4. SNP genotype 文件的格式、染色体命名、sample/accession 数量是什么？
5. indel genotype 文件的格式、染色体命名、sample/accession 数量是什么？
6. SNP 与 indel 的 accession/sample overlap 有多大？
7. phenotype XLSX 中有哪些 sheet、字段、trait 数量、accession 字段？
8. phenotype accession 与 SNP/indel accession 能否对齐？
9. RICE_RP.tar.gz 中是否有可用 accession metadata？
10. Qmatrix / population metadata 能否与 genotype accession 对齐？
11. 哪些文件适合进入 v0.1-mini？
12. 哪些文件适合进入 v0.2-core？
13. 仍缺失哪些 weak evidence？
```

---

## 5. 输出目录

创建：

```text
reports/raw_data_inventory/
data/interim/inventory/
```

报告文件：

```text
reports/raw_data_inventory/raw_file_inventory.tsv
reports/raw_data_inventory/archive_contents.tsv
reports/raw_data_inventory/reference_inventory.tsv
reports/raw_data_inventory/gff3_inventory.tsv
reports/raw_data_inventory/snp_file_inventory.tsv
reports/raw_data_inventory/indel_file_inventory.tsv
reports/raw_data_inventory/plink_file_inventory.tsv
reports/raw_data_inventory/trait_table_inventory.tsv
reports/raw_data_inventory/accession_metadata_inventory.tsv
reports/raw_data_inventory/accession_overlap_matrix.tsv
reports/raw_data_inventory/chromosome_naming_report.tsv
reports/raw_data_inventory/raw_data_risk_report.tsv
reports/raw_data_inventory/v0_1_mini_recommendation.md
reports/raw_data_inventory/raw_data_inventory_report.md
```

中间文件：

```text
data/interim/inventory/reference_chromosomes.tsv
data/interim/inventory/gff3_seqids.tsv
data/interim/inventory/snp_samples.tsv
data/interim/inventory/indel_samples.tsv
data/interim/inventory/plink_samples.tsv
data/interim/inventory/trait_accessions.tsv
data/interim/inventory/metadata_accessions.tsv
data/interim/inventory/accession_set_summary.tsv
```

注意：`data/interim/` 不进入 git。
报告可以进入 git。

---

## 6. inspect_raw_files.py

创建：

```text
scripts/inspect/inspect_raw_files.py
```

功能：

1. 扫描 `data/raw/` 下所有文件。
2. 输出文件路径、大小、扩展名、推断类别、是否压缩、是否 archive。
3. 读取 `manifest/checksum_table.tsv`，检查每个 raw 文件是否有 sha256 记录。
4. 输出：

```text
reports/raw_data_inventory/raw_file_inventory.tsv
```

字段：

```text
file_id
local_path
relative_path
filename
file_size_bytes
file_size_mb
extension
inferred_category
is_compressed
is_archive
checksum_status
notes
```

---

## 7. inspect_archives.py

创建：

```text
scripts/inspect/inspect_archives.py
```

功能：

1. 对 `.tar.gz`、`.zip` 文件只列内容，不全量解压。
2. 输出 archive 内文件名、大小、可能类别。
3. 对 `RICE_RP.tar.gz` 重点检查是否包含 accession metadata、passport data、variety metadata、population metadata、README、CSV/TSV/XLS/XLSX。
4. 对 `3K_coreSNP-v2.1.plink.tar.gz` 和 `3k-core-v7-chr*.zip` 重点检查是否包含 `.bed/.bim/.fam` 或 VCF。
5. 输出：

```text
reports/raw_data_inventory/archive_contents.tsv
```

字段：

```text
archive_path
member_name
member_size_bytes
member_extension
inferred_member_category
extract_recommended
notes
```

规则：

```text
metadata / README / CSV / TSV / XLS / XLSX / FAM / BIM 小文件 extract_recommended=yes
大型 BED / VCF / genotype matrix extract_recommended=no
```

---

## 8. inspect_reference.py

创建：

```text
scripts/inspect/inspect_reference.py
```

功能：

1. 读取 `data/raw/reference/` 下 FASTA/FNA gz 文件。
2. 不需要完整解压到磁盘。
3. 统计每条 sequence 的 name、length。
4. 读取 GFF3 gz 文件，统计 seqid、feature type 数量、gene 数量。
5. 输出：

```text
reports/raw_data_inventory/reference_inventory.tsv
reports/raw_data_inventory/gff3_inventory.tsv
data/interim/inventory/reference_chromosomes.tsv
data/interim/inventory/gff3_seqids.tsv
```

FASTA 输出字段：

```text
source_file
seq_name
seq_length
is_primary_chromosome_guess
notes
```

GFF3 输出字段：

```text
source_file
seqid
n_features
n_gene
n_mRNA
n_exon
n_CDS
notes
```

---

## 9. inspect_vcf_headers.py

创建：

```text
scripts/inspect/inspect_vcf_headers.py
```

功能：

1. 检查 `data/raw/variants/` 下 `.vcf.gz` 文件。
2. 只读取 header 和前若干非 header 记录，不全量解析。
3. 如果 `bcftools` 可用，优先使用：

   * `bcftools view -h`
   * `bcftools query -l`
4. 如果 `bcftools` 不可用，用 Python gzip 读取 header 中 `#CHROM` 行提取 sample IDs。
5. 统计：

   * file path
   * VCF sample count
   * first 10 sample IDs
   * contig header
   * first observed chrom values
   * variant count estimate 如果能快速获得 index 信息，否则写 unknown
   * whether .tbi exists
6. 输出：

```text
reports/raw_data_inventory/snp_file_inventory.tsv
data/interim/inventory/snp_samples.tsv
```

字段：

```text
file_path
variant_type_guess
sample_count
first_samples
has_tbi
contig_header_count
first_observed_chroms
reference_build_guess
notes
```

`snp_samples.tsv` 字段：

```text
source_file
sample_id
sample_order
```

注意：

```text
不要全量读取巨大 VCF。
只做 header 和少量行检查。
```

---

## 10. inspect_plink_files.py

创建：

```text
scripts/inspect/inspect_plink_files.py
```

功能：

1. 检查 `.fam.gz`、`.bim.gz`、`.bed.gz` 或解包 archive 中的 PLINK 文件。
2. 对 `.fam.gz` 读取 sample IDs。
3. 对 `.bim.gz` 读取 variant 数量、染色体命名、variant ID 示例。
4. 对 `.bed.gz` 只记录大小和是否存在，不解析二进制。
5. 重点检查：

   * `core_v0.7.fam.gz`
   * `core_v0.7.bim.gz`
   * `Nipponbare_indel.fam.gz`
   * `Nipponbare_indel.bim.gz`
6. 输出：

```text
reports/raw_data_inventory/plink_file_inventory.tsv
data/interim/inventory/plink_samples.tsv
data/interim/inventory/indel_samples.tsv
```

字段：

```text
file_group
data_category_guess
fam_path
bim_path
bed_path
sample_count
variant_count
chrom_values
first_samples
first_variants
notes
```

如果判断是 indel PLINK，则把 sample 写入 `indel_samples.tsv`。
如果判断是 SNP PLINK，则把 sample 写入 `snp_samples.tsv` 或 `plink_samples.tsv`。

---

## 11. inspect_trait_table.py

创建：

```text
scripts/inspect/inspect_trait_table.py
```

功能：

1. 读取 `data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx`。
2. 优先使用 `openpyxl` 或 `pandas`。如果当前环境没有，允许用：

```bash
python -m pip install --user openpyxl
```

不要安装大型库。

3. 输出每个 sheet 的：

   * sheet name
   * n_rows
   * n_cols
   * column names
   * possible accession columns
   * possible trait columns
   * missing rate summary
4. 提取可能的 accession ID / variety name 列。
5. 输出：

```text
reports/raw_data_inventory/trait_table_inventory.tsv
data/interim/inventory/trait_accessions.tsv
```

字段：

```text
sheet_name
n_rows
n_cols
columns
candidate_accession_columns
candidate_trait_columns
n_candidate_accessions
notes
```

`trait_accessions.tsv` 字段：

```text
source_file
sheet_name
accession_candidate
accession_column
row_id
```

注意：
trait table 只用于后续构建 `trait_state`，不能写成 phenotype prediction target。

---

## 12. inspect_accession_metadata.py

创建：

```text
scripts/inspect/inspect_accession_metadata.py
```

功能：

1. 检查 accession metadata 相关文件：

   * `RICE_RP.tar.gz`
   * `Qmatrix-k9-3kRG.csv`
   * README / manifest / download page
2. 对 `RICE_RP.tar.gz`：

   * 先列内容。
   * 只抽取小型表格、README、CSV/TSV/XLS/XLSX。
   * 不抽取大型 genotype 文件。
   * 抽取到：

```text
data/interim/inventory/extracted_metadata/
```

3. 识别可能的 accession / variety / sample / IRIS / subpopulation 字段。
4. 输出：

```text
reports/raw_data_inventory/accession_metadata_inventory.tsv
data/interim/inventory/metadata_accessions.tsv
```

字段：

```text
source_file
extracted_file
n_rows
n_cols
columns
candidate_accession_columns
candidate_subpopulation_columns
candidate_country_columns
n_candidate_accessions
notes
```

---

## 13. compare_accession_sets.py

创建：

```text
scripts/inspect/compare_accession_sets.py
```

功能：

1. 读取以下 accession/sample set：

   * `data/interim/inventory/snp_samples.tsv`
   * `data/interim/inventory/indel_samples.tsv`
   * `data/interim/inventory/plink_samples.tsv`
   * `data/interim/inventory/trait_accessions.tsv`
   * `data/interim/inventory/metadata_accessions.tsv`
2. 进行标准化匹配尝试：

   * 原始 ID
   * 去空格
   * 大小写统一
   * 去特殊字符
   * 去前后缀版本号
3. 计算 pairwise overlap：

   * n_left
   * n_right
   * n_intersection_raw
   * n_intersection_normalized
   * jaccard_raw
   * jaccard_normalized
4. 输出：

```text
reports/raw_data_inventory/accession_overlap_matrix.tsv
data/interim/inventory/accession_set_summary.tsv
```

字段：

```text
left_set
right_set
n_left
n_right
n_intersection_raw
n_intersection_normalized
jaccard_raw
jaccard_normalized
example_matches
example_left_only
example_right_only
notes
```

---

## 14. chromosome_naming_report

创建脚本或在现有脚本中生成：

```text
reports/raw_data_inventory/chromosome_naming_report.tsv
```

比较：

```text
reference_chromosomes
gff3_seqids
snp_vcf_chroms
snp_plink_chroms
indel_plink_chroms
```

字段：

```text
source_type
source_file
chrom_values
n_chrom_values
n_matching_reference
n_not_matching_reference
example_not_matching
notes
```

目标是判断：

```text
FASTA / GFF3 / SNP / indel 是否能在同一 reference coordinate system 下对齐。
```

---

## 15. raw_data_risk_report.tsv

创建：

```text
reports/raw_data_inventory/raw_data_risk_report.tsv
```

字段：

```text
risk_id
risk_category
severity
affected_files
description
why_it_matters
recommended_action
blocking_next_phase
```

必须覆盖：

```text
accession ID mismatch
SNP / indel sample mismatch
trait / genotype overlap insufficient
reference build mismatch
chromosome naming mismatch
weak evidence missing
unknown cannot be negative
archive content unclear
large genotype file not fully inspected
```

---

## 16. v0_1_mini_recommendation.md

创建：

```text
reports/raw_data_inventory/v0_1_mini_recommendation.md
```

主体中文。

必须给出一个务实建议：

```text
v0.1-mini 应该优先使用哪些文件？
先用 VCF 还是 PLINK？
先用 SNP-only 还是 SNP+indel？
是否能马上纳入 trait table？
是否需要先做 accession mapping？
是否能先做 chr1 prototype？
哪些 trait 值得优先检查？
```

建议格式：

```text
推荐方案 A：最快跑通
推荐方案 B：更接近正式 benchmark
推荐方案 C：如果 trait accession 对齐失败
```

注意：
不能建议做 phenotype prediction。
不能把缺失 weak evidence 的 unknown 当 negative。

---

## 17. raw_data_inventory_report.md

创建：

```text
reports/raw_data_inventory/raw_data_inventory_report.md
```

主体中文。

必须包含：

```text
1. 本次 inventory 目标
2. 已检查的数据目录
3. raw 文件总数和总大小
4. reference FASTA 结果
5. GFF3 annotation 结果
6. SNP genotype 结果
7. indel genotype 结果
8. trait table 结果
9. accession metadata 结果
10. accession overlap 结果
11. chromosome naming 结果
12. 主要风险
13. v0.1-mini 建议
14. 下一步
```

下一步应是：

```text
根据 inventory 结果，创建 Phase 4 prompt：确定 v0.1-mini 数据范围，并开始构建最小可运行 benchmark 输入表。
```

---

## 18. run_raw_inventory.sh

创建：

```text
scripts/inspect/run_raw_inventory.sh
```

内容：

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/raw_data_inventory data/interim/inventory

python scripts/inspect/inspect_raw_files.py
python scripts/inspect/inspect_archives.py
python scripts/inspect/inspect_reference.py
python scripts/inspect/inspect_vcf_headers.py
python scripts/inspect/inspect_plink_files.py
python scripts/inspect/inspect_trait_table.py
python scripts/inspect/inspect_accession_metadata.py
python scripts/inspect/compare_accession_sets.py
```

如果某一步因为缺少 Python 包失败，应在报告中记录，并继续执行其它可执行检查。
可以在脚本中对非关键失败使用 `|| true`，但最终报告必须说明失败。

---

## 19. 运行命令

执行：

```bash
bash scripts/inspect/run_raw_inventory.sh
```

然后执行：

```bash
find reports/raw_data_inventory -maxdepth 1 -type f | sort
find data/interim/inventory -maxdepth 2 -type f | sort | head -200
du -sh data/raw data/interim/inventory reports/raw_data_inventory
python -m py_compile scripts/inspect/*.py
git status --short --ignored
```

---

## 20. Git 提交要求

注意：

```text
data/raw/ 不能提交。
data/interim/ 不能提交。
```

如果 `.gitignore` 还没有忽略 `data/interim/`，请修正 `.gitignore`。

执行：

```bash
git status --short --ignored
```

确认：

```text
!! data/
```

或至少确认 raw/interim 不会被提交。

然后提交：

```bash
git add README.md docs reports/raw_data_inventory scripts/inspect .gitignore
git commit -m "inspect downloaded 3K Rice raw data inventory"
git push
```

如果 `README.md` 或 docs 未更新，可以先更新当前阶段说明：

```text
当前阶段：Phase 3 raw data inventory。
目标：检查已下载 reference、SNP、indel、trait、metadata 的格式、accession overlap 和 reference build 一致性。
```

---

## 21. 最终回复要求

完成后用中文报告：

```text
1. 当前工作目录
2. raw 文件总数和总大小
3. reference FASTA 检查结果
4. GFF3 检查结果
5. SNP genotype 检查结果
6. indel genotype 检查结果
7. trait table 检查结果
8. accession metadata 检查结果
9. SNP / indel / trait / metadata accession overlap
10. chromosome naming 是否一致
11. v0.1-mini 推荐方案
12. 主要风险
13. Git commit / push 状态
14. 确认 raw/interim data 未进入 git
15. What was intentionally not implemented
16. Next step
```

Next step 应该是：

```text
根据 raw data inventory 结果，创建 Phase 4 prompt，确定 v0.1-mini 数据范围，并开始构建最小可运行 benchmark 输入表。
```

现在开始执行 Phase 3 raw data inventory。
