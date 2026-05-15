# 02b_confirm_p0_download_sources.md

你现在要执行 Phase 2B-0：确认 P0 数据源的 exact download sources。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

本任务不是全量下载 raw data。  
本任务的目标是把 Phase 2A 中仍需人工确认的 P0 数据源进一步核验到“可以下载”的程度。

具体目标：

1. 读取现有 source inventory、preflight source、download manifest 和人工确认清单。
2. 对 P0 数据源执行轻量级 exact file list / URL / S3 path 核验。
3. 不下载大文件，只确认文件是否存在、路径是否明确、版本是否可判断。
4. 更新 `manifest/preflight_verified_sources.tsv`。
5. 更新 `manifest/download_manifest.tsv` 中的 planned 记录。
6. 生成 `reports/download_preflight/p0_confirmed_download_sources.md`。
7. 生成 `reports/download_preflight/phase2c_download_candidates.tsv`。
8. 只有满足严格条件的来源才允许标记为 `phase2b_ready=yes`。
9. 本任务完成后，不执行真实大文件下载。

---

## 0. 语言要求

所有说明性文档主体使用中文。

固定术语、字段名、目录名、文件名、命令名可以保留英文，例如：

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
- preflight_verified_sources.tsv
- download_manifest.tsv
- checksum_table.tsv

文档风格必须是科研工程说明文，语气直接、清楚、可执行。

---

## 1. 项目最高约束

第一版严格限定为：

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
13. matched decoy 是后续必要组成部分，但本任务不构建 matched decoy。

---

## 2. 本任务允许做什么

允许创建或更新：

```text
manifest/preflight_verified_sources.tsv
manifest/download_manifest.tsv
manifest/checksum_table.tsv

reports/download_preflight/p0_confirmed_download_sources.md
reports/download_preflight/phase2c_download_candidates.tsv
reports/download_preflight/p0_exact_file_listing.tsv
reports/download_preflight/p0_unresolved_sources.tsv

docs/download_plan.md
docs/preflight_source_review.md
configs/sources.yaml
README.md
````

允许执行轻量级检查：

```bash
aws s3 ls <s3_path> --no-sign-request
curl -I <url>
wget --spider <url>
```

允许下载非常小的 listing / metadata 页面，但禁止下载大型 raw data 文件。

如果 `aws` CLI 不可用，不要安装，不要中断任务。
请记录为：

```text
aws CLI not available; S3 exact listing requires manual check or later environment setup
```

---

## 3. 本任务禁止做什么

禁止：

```text
不要下载 VCF / BCF / FASTA / GFF / BAM / CRAM / FASTQ / HDF5 / parquet 大文件
不要执行 aws s3 cp
不要执行 aws s3 sync
不要执行 curl -O
不要执行 wget 下载数据文件
不要执行 prefetch / fasterq-dump
不要解析 VCF/BCF/FASTA/GFF
不要创建 data/raw/
不要实现 schema
不要实现 benchmark builder
不要实现 split
不要实现 evaluator
不要实现 baseline
不要实现 model
不要实现 Evo2 代码
不要生成 toy data
不要把 raw data 加入 git
```

---

## 4. 读取已有文件

请读取：

```text
manifest/source_inventory.tsv
manifest/preflight_verified_sources.tsv
manifest/download_manifest.tsv
manifest/checksum_table.tsv
reports/source_inventory/p0_source_review.tsv
reports/download_preflight/manual_confirmation_required.tsv
reports/download_preflight/preflight_report.md
reports/download_preflight/aws_listing_summary.tsv
configs/sources.yaml
docs/download_plan.md
```

如果文件不存在，请报告缺失，不要凭空重建。

---

## 5. 本阶段判断标准

只有满足以下条件的数据源，才允许在 `manifest/preflight_verified_sources.tsv` 中标记：

```text
phase2b_ready = yes
recommended_action = download_in_phase2b
```

必须同时满足：

```text
1. 数据源属于 P0。
2. data_category 是 accession_metadata、snp_genotype、indel_genotype、reference_genome、trait_table 或 weak_evidence。
3. exact URL、exact S3 path、exact FTP path 或明确访问方法已经写入。
4. 文件类型与 expected_format 一致。
5. 没有明显违反 v1 范围，例如 SV/PAV/CNV/pan-genome/multi-reference。
6. reference_build 已知，或已明确写出需要后续坐标核验。
7. download_manifest.tsv 中已经有 planned 记录。
8. 风险没有被隐藏；即使 phase2b_ready=yes，也要保留风险说明。
```

以下情况不能写 yes：

```text
SNP-Seek 原入口只是 landing page，没有 exact file URL
mirror 页面存在但文件版本/checksum 不清楚
indel bulk path 没有明确文件
trait table 没有 accession ID 字段说明
weak evidence 只有数据库首页，没有具体文件或下载方式
reference source 是已知移除或跳转不明的 GCA 页面
包含 SV/PAV/CNV/pan-genome/multi-reference 的来源
```

---

## 6. 必须重点核验的 P0 数据源

请重点核验以下类别。

### 6.1 accession metadata

目标：找到可以下载或可访问的 accession metadata / sample information / variety metadata。

必须确认：

```text
是否有 accession_id / variety name / sample_id
是否可能与 SNP genotype 对齐
是否可能与 indel genotype 对齐
是否可能与 trait table 对齐
是否包含 subpopulation 或 geographic metadata
```

输出到：

```text
reports/download_preflight/p0_exact_file_listing.tsv
```

---

### 6.2 SNP genotype

目标：确认 3K Rice SNP genotype 的 exact file list 或 exact S3 path。

必须确认：

```text
是否是 accession-level genotype
是否是 SNP
是否是 3K Rice
是否能按 chromosome 下载
是否是 VCF/BCF/HDF5/PLINK 或其它格式
是否有 reference build 信息
```

如果只能确认 bucket 或目录，但不能确认具体文件，不能写 `phase2b_ready=yes`。

---

### 6.3 indel genotype

目标：确认 3K Rice indel genotype 的 exact file path。

这是本项目第一版的关键数据源，不能被 SNP 替代。

必须确认：

```text
是否是 accession-level indel genotype
是否与 SNP genotype 使用同一 accession 集合或可映射集合
是否有 ref / alt allele
是否包含 insertion / deletion
是否能用于后续 edit_operation_table
```

如果 indel 只有网页说明，没有明确 bulk file，不能写 `phase2b_ready=yes`。

---

### 6.4 reference genome

目标：确认 Nipponbare / IRGSP-1.0 reference genome FASTA 的 exact download source。

优先检查：

```text
GCF_001433935.1 / IRGSP-1.0 RefSeq assembly
RAP-DB IRGSP-1.0 download
NCBI Datasets GCF_001433935.1 landing page
```

必须避免直接依赖已被标记为 removed / redirected 的 GCA 页面。

必须确认：

```text
reference_build
FASTA 是否可下载
GFF3 / annotation 是否可下载
chromosome naming convention 是否需要后续检查
```

---

### 6.5 trait table

目标：确认 3K Rice trait / phenotype table 的来源。

注意：trait table 只用于构建 `trait_state`，不能作为 phenotype prediction target。

必须确认：

```text
是否能映射 accession
是否包含 trait name / trait value
是否可能存在多环境或重复测量
是否需要后续 trait cleaning
```

如果只有网页入口，没有文件或 API，不能写 `phase2b_ready=yes`。

---

### 6.6 weak evidence

目标：确认 known trait genes、GWAS、QTL 等 weak localization evidence 的可下载来源。

必须区分：

```text
known trait genes / cloned genes
GWAS lead SNPs / significant SNPs
QTL intervals
trait-gene annotation
```

必须在 notes 里写明：

```text
weak evidence != causal ground truth
该来源只用于 weak_evidence_table、evaluation、case study 或 explanation
```

如果只有数据库首页，没有具体文件或访问方式，不能写 `phase2b_ready=yes`。

---

## 7. reports/download_preflight/p0_exact_file_listing.tsv 要求

创建 TSV 文件。

字段：

```text
source_id
data_category
priority
candidate_source_name
checked_path_or_url
check_method
check_status
n_candidate_files
candidate_file_examples
expected_format
reference_build
phase2b_ready
manual_confirmation_required
notes
```

`check_status` 可选：

```text
exists
reachable_landing_page_only
listing_unavailable
aws_cli_unavailable
not_found
needs_manual_review
excluded_for_v1
```

`phase2b_ready` 可选：

```text
yes
no
needs_manual_confirmation
defer
exclude_from_v1
```

---

## 8. reports/download_preflight/phase2c_download_candidates.tsv 要求

创建 TSV 文件，只记录可以进入后续真实下载 prompt 的候选项。

字段：

```text
download_id
source_id
data_category
file_role
candidate_filename_or_pattern
download_url_or_access_method
access_method_type
expected_format
local_path
reference_build
phase2c_priority
download_mode
manual_confirmation_required
notes
```

`download_mode` 可选：

```text
single_file
chromosome_split
directory_listing_required
manual_download
defer
```

规则：

1. 只有 `phase2b_ready=yes` 或 `needs_manual_confirmation` 的 P0 source 可以进入。
2. `manual_confirmation_required=yes` 的项后续下载 prompt 仍必须默认 dry-run。
3. indel genotype 如果 exact path 不明确，不能进入真实下载候选，只能进入 unresolved。

---

## 9. reports/download_preflight/p0_unresolved_sources.tsv 要求

创建 TSV 文件，记录仍不能下载的数据源。

字段：

```text
source_id
data_category
priority
reason_unresolved
why_it_blocks_download
suggested_manual_action
notes
```

必须包含所有：

```text
phase2b_ready=no
phase2b_ready=defer
phase2b_ready=needs_manual_confirmation 但没有 exact file path
```

---

## 10. reports/download_preflight/p0_confirmed_download_sources.md 内容要求

主体中文。

至少包含：

```text
1. 本次核验目标
2. 核验输入文件
3. P0 source 总数
4. 已确认 exact download source 的数据源
5. 仍需人工确认的数据源
6. 不能下载的数据源
7. accession metadata 结果
8. SNP genotype 结果
9. indel genotype 结果
10. reference genome 结果
11. trait table 结果
12. weak evidence 结果
13. 是否允许进入 Phase 2C 下载的建议
```

第 13 点必须谨慎：

```text
只有 phase2c_download_candidates.tsv 中列出的候选项允许进入 Phase 2C。
仍 unresolved 的 P0 source 不允许下载。
```

---

## 11. 更新 manifest/preflight_verified_sources.tsv

根据本次核验结果更新该文件。

规则：

```text
不要把 landing page 当作 exact file source。
不要把 mirror 直接当作 verified。
不要把 SNP-Seek offline source 写成 yes。
不要把 indel source 写成 yes，除非 exact file path 明确。
不要把 weak evidence 写成 causal ground truth。
```

保留风险说明。

---

## 12. 更新 manifest/download_manifest.tsv

根据 `phase2c_download_candidates.tsv` 更新 planned 记录。

要求：

```text
所有记录 download_status 必须仍是 planned。
不能写 downloaded。
不能写虚假 checksum。
不能写虚假 file_size_bytes。
local_path 必须规划到 data/raw/ 下。
download_command 可以写 dry-run 计划命令，但不能实际执行。
```

---

## 13. 更新 configs/sources.yaml

更新各类 source 的状态。

建议状态：

```text
ready_for_phase2c_download
needs_manual_confirmation
unresolved
defer
excluded_for_v1
```

不要把未确认 exact file 的 source 写成 ready。

---

## 14. 更新 docs/download_plan.md

补充 Phase 2B-0 结果：

```text
哪些 source 已进入 phase2c_download_candidates.tsv。
哪些 source 仍 unresolved。
Phase 2C 下载只允许使用候选清单。
下载前仍要 dry-run。
下载后必须计算 sha256。
```

---

## 15. 更新 README.md

在当前状态中加入：

```text
当前阶段：Phase 2B-0 P0 download source confirmation。
当前目标：确认 P0 数据源 exact file list / URL / S3 path，不下载大文件。
下一阶段：Phase 2C confirmed raw data download and checksum。
```

---

## 16. 运行检查

运行：

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
```

不要运行任何 `--execute`。

可以尝试：

```bash
aws s3 ls s3://3kricegenome/ --no-sign-request
aws s3 ls s3://3kricegenome/snpseek-dl/ --no-sign-request
aws s3 ls s3://3kricegenome/VCF/ --no-sign-request
```

如果 `aws` 不可用，记录失败原因。

可以尝试：

```bash
curl -I https://snp-seek.irri.org/
curl -I https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_001433935.1/
```

只允许 header check，不允许下载内容。

---

## 17. Git 提交要求

完成后执行：

```bash
git status
git add README.md configs docs manifest reports/download_preflight scripts/download scripts/utils
git commit -m "confirm P0 raw data source paths"
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

## 18. 最终回复要求

完成后请用中文报告：

```text
1. 当前工作目录
2. Created / updated files
3. 是否发现 exact download source
4. 哪些 source 被标记为 phase2b_ready=yes
5. 哪些 source 仍 unresolved
6. phase2c_download_candidates 摘要
7. download_manifest planned 记录变化
8. AWS listing / HTTP header check 结果
9. Validation result
10. 下载脚本 dry-run 结果
11. Git commit / push 状态
12. What was intentionally not implemented
13. Phase 2C 前必须人工确认的问题
14. Next step
```

Next step 应该是：

```text
只对 phase2c_download_candidates.tsv 中已确认的候选项创建 02c_download_confirmed_raw_data.md，执行 dry-run 优先的 raw data 下载、checksum 计算和 download_manifest 更新。
```

现在开始执行 Phase 2B-0：P0 download source confirmation。

