# 02a_preflight_download_plan.md

你现在要执行 Phase 2A：raw data 下载前的 preflight 核验与下载脚本准备。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

本任务不是全量下载 raw data。  
本任务的目标是：

1. 根据 `manifest/source_inventory.tsv` 和 `reports/source_inventory/p0_source_review.tsv`，生成下载前核验报告。
2. 修正明显过时或风险过高的数据源记录，但不能凭空编造。
3. 建立 raw data 下载目录规划。
4. 建立 download_manifest 和 checksum_table 的表头与校验脚本。
5. 编写 Phase 2 下载脚本模板。
6. 只允许执行轻量级远程 listing / metadata 检查，不允许下载大文件。

---

## 0. 语言要求

所有说明性文档主体使用中文。

固定术语、表名、字段名、目录名、文件名、命令名可以保留英文，例如：

- 3K Rice
- SNP / indel
- Task 1 / Task 2
- trait-conditioned SNP/indel localization
- weak localization evidence
- matched decoy
- accession
- reference window
- phenotype prediction
- causal ground truth
- unknown != negative
- source_inventory.tsv
- download_manifest.tsv
- checksum_table.tsv

文档风格必须是科研工程说明文，不要写成宣传文案。

---

## 1. 项目最高约束

第一版严格限定为：

1. 主位数据只使用 3K Rice。
2. 变异范围只包含 SNP + indel。
3. Task 1 是 trait-conditioned SNP/indel localization。
4. Task 2 是 reference-conditioned candidate SNP/indel edit hypothesis generation，仅作为 supplementary / application demo。
5. 不做 phenotype prediction。
6. 不做 trait classification。
7. 不纳入 SV、PAV、CNV。
8. 不使用 pan-reference、multi-reference、多物种 benchmark。
9. 不重新预训练 genome foundation model。
10. weak evidence 只能作为 weak localization evidence。
11. GWAS/QTL/known gene 不能写成 causal ground truth。
12. unknown / unlabeled variants 不能默认作为 negative。
13. matched decoy 是后续必要组成部分，但本任务不构建 matched decoy。

---

## 2. 本任务允许做什么

允许创建或更新：

```text
manifest/download_manifest.tsv
manifest/download_manifest.schema.tsv
manifest/checksum_table.tsv
manifest/checksum_table.schema.tsv
manifest/preflight_verified_sources.tsv

docs/download_plan.md
docs/raw_data_layout.md
docs/preflight_source_review.md

reports/download_preflight/
reports/download_preflight/preflight_report.md
reports/download_preflight/aws_listing_summary.tsv
reports/download_preflight/manual_confirmation_required.tsv

scripts/download/
  download_raw_data.sh
  download_reference.sh
  download_3k_snp.sh
  download_3k_indel.sh
  download_traits.sh
  download_annotation.sh
  download_weak_evidence.sh
  README.md

scripts/utils/
  validate_download_manifest.py
  compute_checksum.py
  validate_preflight_sources.py
````

允许执行：

```bash
aws s3 ls s3://3kricegenome/ --no-sign-request
aws s3 ls s3://3kricegenome/snpseek-dl/ --no-sign-request
aws s3 ls s3://3kricegenome/VCF/ --no-sign-request
```

这些命令只允许做 listing，不允许 `cp` 或 `sync`。

如果没有安装 `aws`，不要安装，不要中断任务；只需要在报告中写明 `aws CLI not available`。

允许使用 `curl -I` 或 `wget --spider` 做 HTTP header 检查。

禁止使用 `curl -O`、`wget URL` 下载实际数据文件。

---

## 3. 本任务禁止做什么

禁止：

```text
不要下载 VCF / BCF / FASTA / GFF / BAM / CRAM / FASTQ / HDF5 / parquet 大文件
不要执行 aws s3 cp
不要执行 aws s3 sync
不要执行 wget 下载文件
不要执行 curl 下载文件内容
不要执行 prefetch / fasterq-dump
不要解析 VCF/BCF/FASTA/GFF
不要实现数据 schema
不要实现 benchmark builder
不要实现 split
不要实现 evaluator
不要实现 baseline
不要实现 model
不要实现 Evo2 代码
不要生成 toy data
不要把 raw data 加入 git
```

如果你发现脚本中有实际下载大文件的命令，请只写成注释或 dry-run 形式，不要执行。

---

## 4. 读取已有文件

请读取：

```text
manifest/source_inventory.tsv
manifest/source_inventory.schema.tsv
reports/source_inventory/p0_source_review.tsv
reports/source_inventory/source_inventory_review.md
configs/sources.yaml
docs/data_acquisition_plan.md
```

如果某些文件不存在，请报告缺失，不要凭空重建。

---

## 5. 修正 reference source 风险

请检查 `manifest/source_inventory.tsv` 中 reference genome 行。

当前需要重点检查：

```text
SRC_REF_IRGSP_FASTA_001
```

如果它使用的是：

```text
https://www.ncbi.nlm.nih.gov/datasets/genome/GCA_001433935.1/
```

请不要直接把它作为低风险下载入口。

请将其风险说明更新为：

```text
NCBI Datasets GCA_001433935.1 page may be removed or redirected; prefer checking GCF_001433935.1 / IRGSP-1.0 assembly entry before Phase 2B download.
```

并在 `manifest/preflight_verified_sources.tsv` 中把 reference source 标记为：

```text
phase2b_ready = needs_manual_confirmation
```

不要删除原始记录。
如果要新增候选 reference source，可以新增一行，例如：

```text
SRC_REF_IRGSP_FASTA_003
reference_genome
Nipponbare IRGSP-1.0 reference genome, RefSeq assembly
Oryza sativa
IRGSP-1.0
none
FASTA/GFF3
unknown
NCBI Assembly / NCBI Datasets GCF_001433935.1
https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001433935.1/
https
P0
Task1+Task2
window_table;reference_sequence;variant_coordinate_context
partially_verified
not_downloaded
medium
Need to pin exact downloadable FASTA package and checksum before download
no
Candidate replacement/confirmation source for IRGSP-1.0 reference genome
```

注意：新增行必须符合 `source_inventory.tsv` 的列格式。

---

## 6. manifest/preflight_verified_sources.tsv 要求

创建 `manifest/preflight_verified_sources.tsv`。

字段：

```text
source_id
data_category
priority
candidate_source_name
download_url_or_access_method
access_method_type
verification_status
risk_level
phase2b_ready
manual_confirmation_required
preflight_check_method
preflight_check_result
recommended_action
notes
```

`phase2b_ready` 可选值：

```text
yes
no
needs_manual_confirmation
defer
exclude_from_v1
```

`recommended_action` 可选值：

```text
download_in_phase2b
manual_verify_before_download
listing_only
defer
exclude_from_v1
```

规则：

1. P0 + partially_verified 的来源，如果 URL/path 明确，但仍有版本风险，写 `needs_manual_confirmation`。
2. P0 + needs_manual_review 的来源，写 `no` 或 `needs_manual_confirmation`。
3. excluded_for_v1 的来源，写 `exclude_from_v1`。
4. SNP-Seek 当前离线的来源，不能写 `yes`。
5. AWS bucket listing 成功的来源，可以写 `needs_manual_confirmation`，不能因为 listing 成功就写 fully verified。
6. indel source 如果没有明确 bulk path，不能写 `yes`。
7. weak evidence 文献来源如果没有具体文件 URL，不能写 `yes`。

---

## 7. manifest/download_manifest.tsv 要求

创建表头和占位记录，不登记已下载文件。

字段：

```text
download_id
source_id
data_category
file_role
original_filename
local_path
download_url_or_access_method
access_method_type
download_command
download_status
file_size_bytes
checksum_sha256
download_started_at
download_finished_at
source_version
reference_build
notes
```

本任务中所有 `download_status` 必须是：

```text
planned
```

不能写 `downloaded`。

`local_path` 必须指向后续规划目录，例如：

```text
data/raw/reference/
data/raw/variants/snp/
data/raw/variants/indel/
data/raw/traits/
data/raw/annotation/
data/raw/evidence/
```

但本任务不要创建这些 raw data 子目录，除非只是空目录规划写在文档里。
不允许创建或提交 raw data 文件。

---

## 8. manifest/checksum_table.tsv 要求

创建表头，不登记真实 checksum。

字段：

```text
file_id
download_id
source_id
local_path
checksum_algorithm
checksum_value
file_size_bytes
computed_at
verification_status
notes
```

本任务可以只写表头，或写 planned placeholder。
不要生成虚假 checksum。

---

## 9. schema 文件要求

创建：

```text
manifest/download_manifest.schema.tsv
manifest/checksum_table.schema.tsv
```

字段：

```text
column_name
required
allowed_values
description
example
```

其中：

```text
download_status allowed_values planned|downloading|downloaded|failed|skipped
checksum_algorithm allowed_values sha256
verification_status allowed_values planned|verified|failed|not_computed
```

---

## 10. docs/download_plan.md 内容要求

主体中文。

至少包含：

```text
1. Phase 2A 目标
2. 为什么不直接全量下载
3. Phase 2B 才允许下载的条件
4. P0 数据源下载优先级
5. SNP genotype 下载策略
6. indel genotype 下载策略
7. reference genome 下载策略
8. trait table 下载策略
9. weak evidence 下载策略
10. checksum 与 manifest 记录规则
11. raw data 不进 git 的规则
12. Phase 2B 下载前人工确认清单
```

必须明确：

```text
Phase 2A 只做 preflight，不下载大文件。
Phase 2B 才执行实际 raw data 下载。
所有下载文件必须先进入 download_manifest.tsv planned 记录。
下载完成后必须计算 sha256。
raw data 文件不进入 git。
```

---

## 11. docs/raw_data_layout.md 内容要求

主体中文。

写出后续 raw data 目录规划：

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

说明每类目录放什么，什么不能放，哪些文件不进入 git。

---

## 12. docs/preflight_source_review.md 内容要求

主体中文。

总结：

```text
1. 已读取的 source inventory
2. 当前 P0 source 状态
3. 可以进入 Phase 2B 的候选项
4. 不能进入 Phase 2B 的候选项
5. 需要人工确认的候选项
6. reference source 修正建议
7. indel genotype source 风险
8. trait overlap 风险
9. weak evidence leakage 风险
```

---

## 13. reports/download_preflight/preflight_report.md 内容要求

主体中文。

报告本次执行结果：

```text
1. 执行时间
2. 检查的文件
3. source_inventory 总行数
4. P0 source 数量
5. AWS listing 是否成功
6. HTTP header check 是否成功
7. 已生成的 manifest 文件
8. 未下载任何 raw data 的确认
9. Phase 2B 前必须人工确认的问题
```

如果 `aws s3 ls` 执行失败，要写清楚原因。

---

## 14. reports/download_preflight/aws_listing_summary.tsv 要求

如果 `aws s3 ls` 可用，请把 listing 摘要写入：

```text
reports/download_preflight/aws_listing_summary.tsv
```

字段：

```text
checked_path
status
n_lines_returned
example_entries
notes
```

不要保存超长 listing。
每个 path 最多保存 5 个 example entries。

如果 aws 不可用，也创建该文件，写：

```text
checked_path	status	n_lines_returned	example_entries	notes
s3://3kricegenome/	aws_cli_unavailable	0		aws CLI not available in current environment
```

---

## 15. reports/download_preflight/manual_confirmation_required.tsv 要求

创建 TSV。

字段：

```text
source_id
data_category
priority
issue
why_it_matters
manual_check
blocking_phase2b
notes
```

必须至少包含：

```text
SNP-Seek offline / mirror validation
SNP genotype exact file list
indel genotype exact file path
reference genome GCF/GCA source choice
trait table accession overlap
weak evidence leakage control
QTL coordinate build
known gene database ID mapping
```

---

## 16. 下载脚本模板要求

创建以下脚本，但不要执行实际下载：

```text
scripts/download/download_raw_data.sh
scripts/download/download_reference.sh
scripts/download/download_3k_snp.sh
scripts/download/download_3k_indel.sh
scripts/download/download_traits.sh
scripts/download/download_annotation.sh
scripts/download/download_weak_evidence.sh
```

脚本要求：

1. 每个脚本开头使用：

```bash
#!/usr/bin/env bash
set -euo pipefail
```

2. 每个脚本默认只显示 dry-run 信息，不能直接下载。

3. 必须支持显式参数：

```bash
--execute
```

只有用户后续明确传入 `--execute` 时，脚本才允许执行实际下载命令。

4. 如果没有 `--execute`，必须打印：

```text
DRY RUN ONLY. No files will be downloaded.
```

5. 每个脚本必须写明后续下载目标目录，但本任务不创建 raw data 文件。

6. 每个脚本中所有实际下载命令必须暂时注释，或包在 `if [[ "${EXECUTE}" == "1" ]]` 条件内。

7. 禁止在本次任务执行这些脚本的 `--execute` 模式。

---

## 17. scripts/download/README.md 要求

主体中文。

说明：

```text
这些脚本目前是 Phase 2A dry-run 下载模板。
默认不会下载任何文件。
只有后续 Phase 2B 人工确认 source 后，才能用 --execute 执行。
所有下载必须写入 download_manifest.tsv。
所有下载后文件必须计算 sha256。
raw data 不进入 git。
```

---

## 18. scripts/utils/validate_download_manifest.py 要求

只使用 Python 标准库。

功能：

```text
读取 manifest/download_manifest.tsv
检查必需列是否存在
检查 download_id 是否唯一
检查 source_id 是否非空
检查 download_status 是否属于 planned|downloading|downloaded|failed|skipped
检查 planned 记录不能有 checksum_sha256
检查 downloaded 记录必须有 file_size_bytes 和 checksum_sha256
检查 local_path 不能为空
```

运行方式：

```bash
python scripts/utils/validate_download_manifest.py manifest/download_manifest.tsv
```

---

## 19. scripts/utils/compute_checksum.py 要求

只使用 Python 标准库。

功能：

```text
输入一个文件路径
计算 sha256
打印 checksum 和 file size
```

运行方式：

```bash
python scripts/utils/compute_checksum.py <file_path>
```

如果文件不存在，返回非 0 exit code。
本任务不要对 raw data 运行该脚本，因为没有 raw data。

---

## 20. scripts/utils/validate_preflight_sources.py 要求

只使用 Python 标准库。

功能：

```text
读取 manifest/preflight_verified_sources.tsv
检查必需列是否存在
检查 phase2b_ready 是否属于 yes|no|needs_manual_confirmation|defer|exclude_from_v1
检查 recommended_action 是否属于 download_in_phase2b|manual_verify_before_download|listing_only|defer|exclude_from_v1
检查 SNP-Seek offline 来源不能 phase2b_ready=yes
检查 excluded_for_v1 来源必须 phase2b_ready=exclude_from_v1
检查 P0 source 至少有 accession_metadata、snp_genotype、indel_genotype、reference_genome、trait_table、weak_evidence
```

运行方式：

```bash
python scripts/utils/validate_preflight_sources.py manifest/preflight_verified_sources.tsv
```

---

## 21. 需要运行的命令

请运行：

```bash
python scripts/utils/validate_source_inventory.py manifest/source_inventory.tsv
python scripts/utils/validate_preflight_sources.py manifest/preflight_verified_sources.tsv
python scripts/utils/validate_download_manifest.py manifest/download_manifest.tsv
python -m py_compile scripts/utils/validate_download_manifest.py scripts/utils/compute_checksum.py scripts/utils/validate_preflight_sources.py
bash scripts/download/download_raw_data.sh
bash scripts/download/download_reference.sh
bash scripts/download/download_3k_snp.sh
bash scripts/download/download_3k_indel.sh
bash scripts/download/download_traits.sh
bash scripts/download/download_annotation.sh
bash scripts/download/download_weak_evidence.sh
git status
```

不要运行任何脚本的 `--execute` 模式。

可以尝试：

```bash
aws s3 ls s3://3kricegenome/ --no-sign-request
aws s3 ls s3://3kricegenome/snpseek-dl/ --no-sign-request
aws s3 ls s3://3kricegenome/VCF/ --no-sign-request
```

如果失败，只记录失败原因。

可以尝试：

```bash
curl -I https://snp-seek.irri.org/
curl -I https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001433935.1/
```

只允许 header check，不允许下载内容。

---

## 22. Git 提交要求

完成后执行：

```bash
git status
git add README.md configs docs manifest reports/download_preflight scripts/download scripts/utils
git commit -m "prepare raw data download preflight and manifests"
git push
```

如果 push 失败，不要改用 HTTPS，不要写 token，不要反复尝试。

请报告：

```text
push 失败原因
当前 commit hash
git remote -v
git status
```

---

## 23. 最终回复要求

完成后请用中文报告：

```text
1. 当前工作目录
2. Created / updated files
3. source_inventory 是否被修正
4. preflight_verified_sources 摘要
5. download_manifest planned 记录数量
6. AWS listing / HTTP header check 结果
7. Validation result
8. 下载脚本 dry-run 结果
9. Git commit / push 状态
10. What was intentionally not implemented
11. Phase 2B 前必须人工确认的问题
12. Next step
```

Next step 应该是：

```text
人工确认 manual_confirmation_required.tsv 和 preflight_verified_sources.tsv 后，创建 02b_download_confirmed_raw_data.md，执行经过确认的 raw data 下载、checksum 计算和 download_manifest 更新。
```

现在开始执行 Phase 2A：raw data download preflight。

