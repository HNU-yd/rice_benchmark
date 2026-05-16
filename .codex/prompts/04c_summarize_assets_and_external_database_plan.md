# 04c_summarize_assets_and_external_database_plan.md

你现在执行一个阶段性统计与外部数据库搜集规划任务。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

当前项目已经下载了多批数据，包括 3K Rice genotype、phenotype、reference、annotation、Qmatrix、Oryzabase、Q-TARO、Genesys MCPD、NCBI RunInfo、3K_list_sra_ids、pruned SNP 等。现在需要对服务器上的实际文件做一次完整统计，并准备后续搜集其他水稻数据库。

本任务目标：

1. 统计服务器上已经下载的数据。
2. 统计还缺哪些数据。
3. 判断缺失数据是否阻塞当前 benchmark。
4. 梳理 accession ID 对照表现状。
5. 梳理 genotype、phenotype、weak evidence、annotation 的现状。
6. 制定其他水稻数据库搜集计划。
7. 不构建正式 benchmark schema。
8. 不训练模型。
9. 不做 phenotype prediction。
10. 不下载大文件，除非只是极小的网页或 metadata 检查。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 主位数据：3K Rice accession-level SNP/indel genotype backbone
- 变异范围：SNP + indel
- 主任务：trait-conditioned SNP/indel localization
- Task 2 仅作为 supplementary / application demo
- 不做 phenotype prediction
- 不做 trait classification
- 不纳入 SV / PAV / CNV
- 不使用 pan-reference / multi-reference / 多物种 genotype benchmark
- 不重新预训练 genome foundation model
- weak evidence 只能作为 weak localization evidence
- GWAS / QTL / known gene 不能写成 causal ground truth
- unknown / unlabeled variants 不能默认作为 negative

允许扩展的是：

- 水稻知识库
- trait-gene evidence
- QTL evidence
- gene annotation
- functional annotation
- ontology
- external GWAS / association evidence
- candidate gene explanation layer

禁止把外部数据库直接混成 causal label。

---

## 2. 本任务允许做什么

允许读取：

```text
data/raw/
data/interim/
manifest/
reports/
configs/
````

允许创建：

```text
reports/current_data_status/
reports/external_database_plan/
```

允许创建脚本：

```text
scripts/audit/summarize_current_assets.py
scripts/audit/summarize_accession_mapping_sources.py
scripts/audit/summarize_external_database_candidates.py
scripts/audit/run_current_data_audit.sh
```

允许做轻量级网页状态检查：

```bash
curl -I <url>
```

禁止下载大文件。

---

## 3. 本任务禁止做什么

禁止：

```text
不要继续下载大文件
不要下载 FASTQ / BAM / CRAM / SRA
不要下载 SV / PAV / CNV / pan-genome 专用数据
不要实现正式 schema
不要构建 split
不要构建 evaluator
不要训练模型
不要写 Evo2 代码
不要做 phenotype prediction
不要做 trait classification
不要把 weak evidence 写成 causal ground truth
不要把 unknown 当 negative
不要提交 data/raw 或 data/interim
```

---

## 4. 当前数据统计

创建脚本：

```text
scripts/audit/summarize_current_assets.py
```

功能：

1. 扫描 `data/raw/` 下所有文件。
2. 按数据类别统计文件数和大小：

   * reference
   * annotation
   * SNP genotype
   * indel genotype
   * pruned SNP
   * phenotype / trait
   * accession metadata
   * Qmatrix / population structure
   * Oryzabase
   * Q-TARO
   * Sanciangco / Dataverse
   * listing / metadata
3. 读取 `manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv`。
4. 检查每个 raw 文件是否有 checksum。
5. 输出：

```text
reports/current_data_status/current_raw_file_summary.tsv
reports/current_data_status/current_data_category_summary.tsv
reports/current_data_status/current_manifest_checksum_status.tsv
```

字段建议：

`current_raw_file_summary.tsv`：

```text
file_path
file_name
file_size_bytes
file_size_mb
data_category_guess
format_guess
checksum_registered
notes
```

`current_data_category_summary.tsv`：

```text
data_category
n_files
total_size_bytes
total_size_gb
key_files
status
notes
```

---

## 5. accession ID 对照表现状统计

创建脚本：

```text
scripts/audit/summarize_accession_mapping_sources.py
```

重点检查以下文件是否存在：

```text
data/raw/accessions/snpseek/3K_list_sra_ids.txt
data/raw/accessions/genesys/genesys_3k_mcpd_passport.xlsx
data/raw/accessions/ncbi_prjeb6180/PRJEB6180_runinfo.csv
data/raw/variants/snp/core_v0.7.fam.gz
data/raw/variants/indel/Nipponbare_indel.fam.gz
data/raw/metadata/Qmatrix-k9-3kRG.csv
data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx
```

如果路径不同，请自动在 `data/raw/` 中搜索相似文件。

输出：

```text
reports/current_data_status/accession_mapping_source_status.tsv
reports/current_data_status/accession_mapping_priority_report.md
```

`accession_mapping_source_status.tsv` 字段：

```text
source_name
expected_file
found_file
exists
n_rows_or_records
key_columns
role_in_mapping
status
notes
```

`accession_mapping_priority_report.md` 必须说明：

1. 哪个文件是主桥梁。
2. 哪个文件补充 passport 信息。
3. 哪个文件补充 SRA / BioSample / Run 信息。
4. 当前是否可以开始构建 `accession_mapping_master.tsv`。
5. 哪些 ID 关系必须优先检查。

必须明确：

```text
3K_list_sra_ids.txt 是 genotype ID ↔ stock name ↔ SRA accession 的主桥梁。
Genesys MCPD 是 passport / IRGC / name 补充。
NCBI RunInfo 是 SRA / BioSample / Run 补充。
Qmatrix 和 PLINK fam 是 genotype sample ID 的主来源。
phenotype XLSX 是 trait_state 的来源，但不能当 phenotype prediction target。
```

---

## 6. 当前缺失数据评估

创建：

```text
reports/current_data_status/missing_data_priority.tsv
reports/current_data_status/missing_data_report.md
```

缺失数据至少包括：

```text
标准 accession ID master table
trait accession 与 genotype sample 的高置信 mapping
正式 trait_value_table
GWAS lead SNP / significant SNP
更多文献级 trait-specific evidence
RAP / MSU / Gramene ID mapping
功能注释增强层
表达 / 多组学增强数据
```

`missing_data_priority.tsv` 字段：

```text
missing_item
importance
blocks_v0_1
blocks_v0_2
can_be_generated_in_house
recommended_action
notes
```

判断规则：

```text
accession ID mapping：
  最高优先级，阻塞 trait-conditioned instances。

GWAS lead SNP：
  重要，但不阻塞 v0.1；可后续用 genotype + phenotype + Qmatrix 自跑。

RAP / MSU / Gramene ID mapping：
  重要，主要影响 gene explanation，不阻塞 v0.1 skeleton。

表达数据：
  增强层，不阻塞 v0.1 / v0.2。
```

---

## 7. 外部水稻数据库候选清单

创建：

```text
reports/external_database_plan/external_database_inventory.tsv
reports/external_database_plan/external_database_collection_plan.md
```

候选数据库至少包含：

### 7.1 RAP-DB

用途：

```text
IRGSP-1.0 gene annotation
RAP ID
gene function
curated genes
candidate gene explanation
RAP / MSU / RefSeq ID bridge
```

优先级：高。

### 7.2 RiceVarMap / RiceVarMap2

用途：

```text
外部 SNP / indel variation
allele frequency
variant annotation
external variant knowledge
candidate variant explanation
```

优先级：中高。

### 7.3 MBKbase-rice

用途：

```text
germplasm information
known alleles
phenotype
gene expression
multi-omics explanation
candidate gene evidence
```

优先级：中。

### 7.4 funRiceGenes

用途：

```text
functionally characterized rice genes
cloned gene evidence
gene family
literature evidence
candidate gene explanation
```

优先级：高。

### 7.5 Ensembl Plants / Gramene

用途：

```text
IRGSP-1.0 gene annotation
cross-reference
GO / ontology
gene ID mapping
```

优先级：中。

### 7.6 Rice Genome Annotation Project / MSU

用途：

```text
MSU gene model
MSU locus ID
RAP-MSU mapping
legacy literature ID support
```

优先级：中高。

### 7.7 Lin et al. 2020 PNAS

用途：

```text
hybrid rice yield / heterosis external evidence
heterotic loci
yield-related case study
external validation
```

优先级：中。

### 7.8 Sanciangco Harvard Dataverse

用途：

```text
external GWAS evidence
SNP/indel association results
historical trait GWAS
```

状态：当前下载失败，可暂时标记为 defer，不阻塞主流程。

---

## 8. external_database_inventory.tsv 字段

字段：

```text
database_name
url
data_type
main_use
priority
download_status
expected_files
expected_format
blocks_current_phase
risk
recommended_next_action
notes
```

下载状态可选：

```text
not_started
metadata_checked
downloaded
partially_downloaded
failed
defer
```

推荐行动可选：

```text
download_now
metadata_check_first
manual_browser_download
defer
skip_for_v1
```

必须注意：

```text
不要把 RiceVarMap / MBKbase 的 genotype 数据直接混入 3K backbone。
它们优先作为 external knowledge / annotation / evidence layer。
```

---

## 9. 外部数据库搜集策略报告

`external_database_collection_plan.md` 必须包含：

1. 为什么现在要搜集其他数据库。
2. 为什么不把主数据从 3K Rice 扩成多数据集。
3. 3K Rice genotype backbone 和外部 knowledge layer 的区别。
4. 每个数据库能补什么。
5. 哪些数据库优先下载。
6. 哪些数据库只做 metadata check。
7. 哪些数据库暂缓。
8. 哪些数据不能进入第一版。
9. 下一步下载顺序。

推荐结论：

```text
第一优先：
  accession ID mapping files
  funRiceGenes
  RAP-DB gene annotation / mapping
  Oryzabase / Q-TARO 已有，继续整理

第二优先：
  RiceVarMap / RiceVarMap2 variation annotation
  MSU / Gramene ID mapping

第三优先：
  MBKbase known allele / expression
  Lin2020 PNAS hybrid-yield external evidence

暂缓：
  Sanciangco Dataverse 大规模 GWAS 文件
  pan-genome / SV / CNV 数据
  multi-species 数据
```

---

## 10. 生成阶段性总报告

创建：

```text
reports/current_data_status/project_data_status_summary.md
```

主体中文，必须包含：

1. 当前已经下载了哪些 3K Rice 数据。
2. 当前已经下载了哪些 weak evidence。
3. accession mapping 的当前状态。
4. genotype 数据当前状态。
5. trait 数据当前状态。
6. weak evidence 当前状态。
7. 还缺哪些数据。
8. 哪些缺失数据阻塞当前阶段。
9. 哪些缺失数据不阻塞。
10. 下一步最优先做什么。
11. 外部数据库搜集路线。

结论必须明确：

```text
当前最优先事项是构建 accession_mapping_master.tsv。
Dataverse GWAS 下载失败不阻塞当前阶段。
v0.1 可以用 Oryzabase + Q-TARO 做 weak evidence。
v0.2 可以在 accession mapping 完成后自跑 GWAS 生成 Tier 2 weak evidence。
外部数据库应作为知识层，而不是替代 3K Rice genotype backbone。
```

---

## 11. 运行脚本

创建：

```text
scripts/audit/run_current_data_audit.sh
```

内容：

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/current_data_status reports/external_database_plan

python scripts/audit/summarize_current_assets.py
python scripts/audit/summarize_accession_mapping_sources.py
python scripts/audit/summarize_external_database_candidates.py
```

执行：

```bash
bash scripts/audit/run_current_data_audit.sh
```

然后执行：

```bash
find reports/current_data_status -maxdepth 1 -type f | sort
find reports/external_database_plan -maxdepth 1 -type f | sort
python -m py_compile scripts/audit/*.py
git status --short --ignored
```

---

## 12. Git 提交要求

注意：

```text
data/raw/ 不能提交
data/interim/ 不能提交
```

确认 `git status --short --ignored` 只显示 data 被忽略，不要 stage raw data。

提交：

```bash
git add reports/current_data_status reports/external_database_plan scripts/audit README.md docs configs manifest .gitignore
git commit -m "summarize current data assets and plan external databases"
git push
```

如果 README 或 docs 没有变化，可以不用强行修改。

---

## 13. 最终回复要求

完成后用中文报告：

```text
1. 当前工作目录
2. 当前 raw data 总文件数和总大小
3. 已下载的数据类别
4. accession mapping 文件是否齐全
5. genotype 数据是否齐全
6. phenotype / trait 数据是否齐全
7. weak evidence 是否齐全
8. 当前最阻塞的问题
9. Dataverse GWAS 是否还需要继续尝试
10. 其他数据库优先级
11. 生成的报告文件
12. Git commit / push 状态
13. raw/interim data 是否未进入 git
14. 下一步
```

下一步应该是：

```text
构建 accession_mapping_master.tsv；完成 genotype sample ID、SRA accession、Genesys passport、NCBI RunInfo 和 phenotype accession-like fields 的统一映射。
```

现在开始执行当前数据资产统计和外部数据库搜集规划。
