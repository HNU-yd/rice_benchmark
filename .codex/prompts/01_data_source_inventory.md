# 01_data_source_inventory.md

你现在要执行 Phase 1：建立 3K Rice 数据源清单。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

本次任务的目标不是下载数据，也不是处理数据，而是先明确第一版 benchmark 需要哪些 3K Rice 数据源、每类数据可能从哪里获取、下载风险是什么、后续会用于哪些 benchmark 表和任务。

---

## 1. 项目最高约束

本项目第一版严格限定为：

1. 主位数据只使用 3K Rice。
2. 变异范围只包含 SNP + indel。
3. 主任务是 Task 1：trait-conditioned SNP/indel localization。
4. Task 2：reference-conditioned candidate SNP/indel edit hypothesis generation 仅作为 supplementary / application demo。
5. 不做 phenotype prediction。
6. 不预测 accession phenotype value。
7. 不做 trait classification。
8. 不纳入 SV、PAV、CNV。
9. 不使用 pan-reference、multi-reference、五参考 anchor block、branch chunk、path state。
10. 不引入多物种 benchmark。
11. 不重新预训练 genome foundation model。
12. 后续可以使用 frozen Evo2 encoder，但本 prompt 不实现 Evo2 代码。
13. GWAS、QTL、known trait gene、LD block、credible interval、trait-gene annotation 只能作为 weak localization evidence。
14. weak evidence 不能写成 causal ground truth。
15. unknown / unlabeled variants 不能默认作为 negative。
16. matched decoy 是后续 benchmark 的必要组成部分，但本 prompt 不构建 decoy。
17. 所有 split 后续必须固化为文件，不能在训练时动态重切。
18. 所有模型和 baseline 后续必须输出统一格式的 score table。

---

## 2. 本次任务范围

你只需要完成 Phase 1：3K Rice data source inventory。

允许做：

```text
创建 manifest/source_inventory.tsv
创建 manifest/source_inventory.schema.tsv
创建 docs/data_source_inventory.md
创建 docs/data_download_risk_notes.md
更新 docs/data_acquisition_plan.md
更新 configs/sources.yaml
更新 README.md 中的当前阶段说明
创建 scripts/utils/validate_source_inventory.py
运行 source inventory 的轻量校验
执行 git status / git add / git commit / git push
````

禁止做：

```text
不要下载任何 raw data
不要下载 VCF / BCF / FASTA / GFF / BAM / CRAM / FASTQ / HDF5 / parquet 大文件
不要执行 aws s3 cp
不要执行 aws s3 sync
不要执行 wget 下载数据文件
不要执行 curl 下载数据文件
不要执行 prefetch / fasterq-dump
不要写 VCF/BCF/FASTA/GFF 解析代码
不要实现 schema
不要实现 benchmark builder
不要实现 split
不要实现 evaluator
不要实现 baseline
不要实现 model
不要实现 Evo2 相关代码
不要生成 toy data
不要创建 data/raw/
不要把任何 raw data 加入 git
```

如果需要联网核验网页，只允许访问轻量 HTML / metadata 页面。
禁止下载实际数据文件。
如果当前环境不能联网，不要编造 URL，应该把对应字段标记为 `needs_manual_review`。

---

## 3. 本阶段核心原则

Phase 1 的核心原则是：

```text
先确认 3K Rice 有什么，再决定 benchmark 怎么落表。
```

因此：

1. 不要根据理想设计直接假设数据格式。
2. 不要跳过 source inventory。
3. 不要把 3K Rice 之外的数据当成第一版主证据。
4. 如果某个数据源包含 SV、PAV、CNV、pan-genome 或 multi-reference 内容，只能在 notes 中标记为 excluded_for_v1 或 not_primary_for_v1，不能纳入第一版主 benchmark。
5. trait / phenotype table 的用途只能是构建 trait_state，不是用于 phenotype prediction。
6. GWAS/QTL/known gene 的用途只能是 weak localization evidence，不是 causal ground truth。
7. indel genotype 是第一版必要数据源，不能只做 SNP。

---

## 4. 需要创建的目录和文件

如果不存在，请创建：

```text
manifest/
reports/
reports/source_inventory/
scripts/utils/
```

需要创建或更新：

```text
manifest/source_inventory.tsv
manifest/source_inventory.schema.tsv
docs/data_source_inventory.md
docs/data_download_risk_notes.md
docs/data_acquisition_plan.md
configs/sources.yaml
README.md
scripts/utils/validate_source_inventory.py
```

不要删除已有文件。
如果文件已经存在，请在不破坏已有内容的前提下补充或更新。

---

## 5. manifest/source_inventory.tsv 字段要求

创建 `manifest/source_inventory.tsv`，必须使用 TSV 格式。

字段必须包括：

```text
source_id
data_category
dataset_name
species
reference_build
variant_type
expected_format
expected_size
candidate_source_name
download_url_or_access_method
access_method_type
priority
required_for_task
used_for_table
verification_status
download_status
risk_level
risk_notes
exclude_from_v1
notes
```

字段含义：

```text
source_id:
  数据源唯一 ID，例如 SRC_3K_ACCESSION_METADATA_001。

data_category:
  数据类别，例如 accession_metadata、snp_genotype、indel_genotype、reference_genome、gene_annotation、trait_table、weak_evidence。

dataset_name:
  数据集名称。

species:
  固定为 Oryza sativa 或 rice，除非该行是工具性数据源。

reference_build:
  参考基因组版本，例如 Nipponbare / IRGSP-1.0。未知则写 unknown。

variant_type:
  SNP、indel、SNP+indel、none、mixed、not_applicable。

expected_format:
  预期格式，例如 VCF、BCF、FASTA、GFF3、TSV、CSV、HDF5、HTML/database、unknown。

expected_size:
  预期大小，未知写 unknown。不要编造具体数字。

candidate_source_name:
  候选来源名称，例如 AWS Open Data Registry、SNP-Seek mirror、RAP-DB、NCBI Assembly、literature supplementary。

download_url_or_access_method:
  URL、S3 path、网页入口或访问方法。不能确认时写 to_be_verified。

access_method_type:
  s3、https、ftp、database、manual、paper_supplement、unknown。

priority:
  P0、P1、P2。
  P0 = 第一版必须确认；
  P1 = 第一版重要但可后补；
  P2 = case study / annotation / supplementary 可后补。

required_for_task:
  Task1、Task2、Task1+Task2、evaluation、explanation、manifest_only。

used_for_table:
  后续可能进入的 benchmark 表，例如 accession_table、variant_table、genotype_table、trait_value_table、weak_evidence_table、window_table、candidate_gene_ranking_table。

verification_status:
  verified、partially_verified、needs_manual_review、unavailable、excluded_for_v1。

download_status:
  not_downloaded。Phase 1 不能改成 downloaded。

risk_level:
  low、medium、high。

risk_notes:
  说明风险，例如 SNP-Seek offline、URL mirror needs verification、accession ID mismatch risk、reference build mismatch risk、large file risk。

exclude_from_v1:
  yes / no。
  如果是 SV/PAV/CNV、pan-genome、multi-reference、多物种，必须写 yes。

notes:
  简要说明。
```

---

## 6. source_inventory 必须覆盖的数据类别

`manifest/source_inventory.tsv` 至少要覆盖以下 7 大类。

### 6.1 3K Rice accession metadata

必须至少登记 1 个候选来源。

用途：

```text
accession_table
accession ID mapping
subpopulation
country / region
sample quality
split construction
```

必须检查或备注：

```text
是否包含 accession_id / variety name / sample_id
是否能和 SNP genotype 对齐
是否能和 indel genotype 对齐
是否能和 trait table 对齐
是否包含 subpopulation / geographic metadata
```

priority: P0
required_for_task: Task1+Task2

---

### 6.2 3K Rice SNP genotype data

必须至少登记 1 个候选来源。

用途：

```text
variant_table
snp_table
genotype_table
MAF 统计
missing rate 统计
LD 统计
SNP-only benchmark
SNP+indel joint benchmark
```

必须检查或备注：

```text
是否是 accession-level genotype
是否基于 Nipponbare / IRGSP-1.0 或可映射坐标
是否是全基因组 SNP
是否包含 genotype matrix
是否可按 chromosome 分块
是否与 accession metadata 对齐
```

priority: P0
required_for_task: Task1

---

### 6.3 3K Rice indel genotype data

必须至少登记 1 个候选来源。

用途：

```text
variant_table
indel_table
genotype_table
indel-only benchmark
SNP+indel joint benchmark
Task 2 hidden genotype evaluation
Evo2 ref-alt delta precompute
```

必须检查或备注：

```text
是否是 accession-level indel genotype
是否与 SNP genotype 使用同一 reference build
是否与 SNP genotype 使用同一 accession ID
是否包含 insertion / deletion 的 ref / alt allele
是否可用于后续 edit_operation_table
```

priority: P0
required_for_task: Task1+Task2

---

### 6.4 Nipponbare / IRGSP reference genome FASTA

必须至少登记 1 个候选来源。

用途：

```text
window_table
reference_window sequence extraction
variant coordinate context
Evo2 window embedding
Evo2 ref-alt delta embedding
Task 2 reference-conditioned edit generation
```

必须检查或备注：

```text
reference build
chromosome naming convention
是否有 FASTA
是否有 FAI 或可 samtools faidx
是否和 SNP/indel 坐标一致
```

priority: P0
required_for_task: Task1+Task2

---

### 6.5 gene annotation / functional annotation

必须至少登记 1 个候选来源。

用途：

```text
gene density
distance_to_nearest_gene
nearest known gene baseline
matched decoy matching features
candidate_gene_ranking_table
case study explanation
```

必须检查或备注：

```text
是否与 reference build 一致
是否有 gene coordinate
是否有 gene_id / gene_name
是否有 functional annotation
是否有 GO / pathway annotation
```

priority: P1
required_for_task: explanation

---

### 6.6 trait / phenotype tables

必须至少登记 1 个候选来源。

注意：这里的 trait / phenotype table 只能用于构建 trait_state，不能用于 phenotype prediction。

用途：

```text
trait_table
trait_value_table
trait_id
trait_value_norm
trait_group
trait_state
trait_direction
```

必须检查或备注：

```text
是否能映射 accession
每个 trait 的可用 accession 数
trait 类型：continuous / binary / categorical
是否有单位
是否有重复测量
是否有环境信息
是否适合 high/low 或 case/control 分组
```

priority: P0
required_for_task: Task1+Task2

---

### 6.7 weak localization evidence

必须至少登记以下候选类型：

```text
known trait genes / cloned genes
GWAS lead SNPs / significant SNPs
QTL intervals
LD blocks / credible intervals if available
trait-gene annotation / pathway evidence
```

用途：

```text
weak_evidence_table
target_signal_table
window-level soft signal
variant-level weak evidence
evaluation
case study
candidate_gene_ranking_table
```

必须检查或备注：

```text
证据是否 trait-specific
是否有 coordinate
coordinate 是否与 reference build 一致
是否是 SNP-level、gene-level、interval-level 还是 annotation-level evidence
是否有来源文献或数据库
是否可能存在 evidence leakage
```

priority:

* known trait genes / GWAS / QTL: P0 或 P1
* pathway / functional annotation: P1 或 P2

required_for_task: evaluation / explanation

---

## 7. 建议优先核验的候选来源

你可以优先核验以下候选来源，但不能盲目信任，必须在 `verification_status` 和 `risk_notes` 中说明当前状态。

候选来源包括：

```text
AWS Open Data Registry: 3000 Rice Genomes Project
AWS / S3 3kricegenome public dataset
42basepairs 3K Rice / SNP-Seek mirror download page
SNP-Seek / IRRI 页面
RAP-DB IRGSP-1.0 genome and annotation download
NCBI Assembly IRGSP-1.0
Rice SNP-Seek literature and update papers
Q-TARO / Gramene / RAP-DB / Oryzabase / QTARO 等可能的 rice trait gene 或 QTL 证据来源
```

如果某个来源当前不可访问，例如 SNP-Seek hosted page offline，应标记：

```text
verification_status = unavailable 或 partially_verified
risk_level = high
risk_notes = hosted page offline; mirror or alternative source required
```

如果某个来源是 mirror，应标记：

```text
verification_status = partially_verified
risk_level = medium
risk_notes = mirror source requires checksum/version validation against original source
```

如果某个来源包含 pan-genome、SV、PAV、CNV 或 multi-reference 内容，应标记：

```text
exclude_from_v1 = yes
notes = contains content outside v1 benchmark scope
```

---

## 8. manifest/source_inventory.schema.tsv 要求

创建 `manifest/source_inventory.schema.tsv`，字段包括：

```text
column_name
required
allowed_values
description
example
```

其中：

```text
source_id required yes
data_category required yes
priority allowed_values P0|P1|P2
verification_status allowed_values verified|partially_verified|needs_manual_review|unavailable|excluded_for_v1
download_status allowed_values not_downloaded
risk_level allowed_values low|medium|high
exclude_from_v1 allowed_values yes|no
```

---

## 9. docs/data_source_inventory.md 内容要求

创建 `docs/data_source_inventory.md`。

主体中文，至少包含：

```text
1. Phase 1 目标
2. 为什么必须先做 source inventory
3. 7 类必需数据源
4. P0 / P1 / P2 优先级定义
5. 每类数据后续用于哪些 benchmark 表
6. 当前已登记候选来源摘要
7. 当前最大风险
8. Phase 2 下载前必须人工确认的问题
```

必须强调：

```text
本阶段不下载数据。
本阶段不设计最终 schema。
本阶段不根据理想情况假设数据格式。
后续 schema 必须服从真实下载数据。
```

---

## 10. docs/data_download_risk_notes.md 内容要求

创建 `docs/data_download_risk_notes.md`。

至少包含以下风险类别：

```text
1. accession ID 不一致风险
2. SNP 与 indel 来源版本不一致风险
3. reference build 不一致风险
4. SNP-Seek 原始入口不可用或临时离线风险
5. mirror 数据源版本和 checksum 风险
6. trait table 与 genotype accession overlap 不足风险
7. GWAS/QTL/known gene evidence 泄漏风险
8. weak evidence 被误写成 causal ground truth 的风险
9. 大文件下载和断点续传风险
10. raw data 被误提交到 git 的风险
```

每一类风险给出：

```text
risk
why_it_matters
how_to_check_later
mitigation
```

---

## 11. 更新 docs/data_acquisition_plan.md

如果该文件存在，请补充 Phase 1 的结果引用：

```text
Phase 1 只产生 source_inventory.tsv，不下载数据。
Phase 2 只有在 source_inventory.tsv 人工审阅后才能开始。
下载脚本必须使用 source_inventory.tsv 中经过确认的数据源。
所有下载文件必须进入 manifest/download_manifest.tsv 和 checksum_table.tsv。
```

不要写具体下载命令。

---

## 12. 更新 configs/sources.yaml

根据 `manifest/source_inventory.tsv` 更新 `configs/sources.yaml`。

要求：

1. 保留中文 notes。
2. 不填虚假 URL。
3. 对不能确认的来源写 `to_be_verified`。
4. 所有 source 的 `download_status` 必须是 `not_downloaded`。
5. 标记 P0 数据源。

建议结构：

```yaml
sources:
  accession_metadata:
    priority: P0
    required: true
    status: "to_be_verified"
    candidate_sources: []
    notes: "用于 accession_table、ID mapping 和 split。"

  snp_genotype:
    priority: P0
    required: true
    status: "to_be_verified"
    candidate_sources: []
    notes: "用于 SNP variant_table、snp_table 和 genotype_table。"

  indel_genotype:
    priority: P0
    required: true
    status: "to_be_verified"
    candidate_sources: []
    notes: "用于 indel_table、joint SNP+indel benchmark 和 Task 2 hidden genotype evaluation。"
```

可以根据 source_inventory 实际结果扩展。

---

## 13. 更新 README.md

在 README.md 的当前状态中加入：

```text
当前阶段：Phase 1 data source inventory。
当前目标：确认 3K Rice benchmark 所需数据源，不下载数据，不写 schema，不训练模型。
下一阶段：Phase 2 raw data download, checksum, and manifest registration。
```

如果 README.md 还没有 pipeline，请补充：

```text
Phase 0: repository governance and project constraints
Phase 1: 3K Rice data source inventory
Phase 2: raw data download, checksum, and manifest registration
Phase 3: raw data inventory and accession/trait/variant compatibility audit
Phase 4: decide v0.1-mini / v0.2-core / v1.0-full benchmark scope
Phase 5: schema and benchmark table construction
Phase 6: data normalization and window construction
Phase 7: weak evidence and matched decoy construction
Phase 8: frozen split generation
Phase 9: evaluator and baseline implementation
Phase 10: frozen Evo2 feature precomputation
Phase 11: Task 1 model training and inference
Phase 12: ablation, negative controls, and Task 2 supplementary demo
```

---

## 14. 创建 scripts/utils/validate_source_inventory.py

创建一个轻量校验脚本，只检查 inventory 文件格式，不处理真实数据。

脚本功能：

```text
读取 manifest/source_inventory.tsv
检查必需列是否存在
检查 source_id 是否唯一
检查 priority 是否属于 P0/P1/P2
检查 verification_status 是否属于允许值
检查 download_status 是否全部为 not_downloaded
检查 risk_level 是否属于 low/medium/high
检查 exclude_from_v1 是否属于 yes/no
检查是否至少覆盖 7 类必需 data_category
检查是否存在 P0 的 SNP genotype、indel genotype、reference genome、trait table、accession metadata
```

运行方式：

```bash
python scripts/utils/validate_source_inventory.py manifest/source_inventory.tsv
```

输出：

```text
[OK] source inventory validation passed
```

或打印错误并返回非 0 exit code。

不要引入 pandas。
只使用 Python 标准库，例如 csv、sys、pathlib。

---

## 15. 需要运行的检查命令

完成后请运行：

```bash
python scripts/utils/validate_source_inventory.py manifest/source_inventory.tsv
git status
find . -maxdepth 4 -type f | sort
```

不要运行任何下载命令。

---

## 16. Git 提交要求

本项目远程仓库为：

```text
git@github.com:HNU-yd/rice_benchmark.git
```

完成本任务后：

```bash
git status
git add README.md configs/sources.yaml docs/data_acquisition_plan.md docs/data_source_inventory.md docs/data_download_risk_notes.md manifest/source_inventory.tsv manifest/source_inventory.schema.tsv scripts/utils/validate_source_inventory.py
git commit -m "add 3K Rice data source inventory"
git push
```

如果 push 失败，不要写入 token，不要改用 HTTPS，不要反复尝试。
只需要在最终回复中说明失败原因、当前 commit hash 和 `git status`。

---

## 17. 最终回复要求

完成后，请用中文报告：

```text
1. Created / updated files
2. Source inventory summary
3. P0 数据源是否都已登记
4. Commands run
5. Validation result
6. Git commit / push 状态
7. What was intentionally not implemented
8. Risks or next steps
```

其中 next step 应该是：

```text
人工审阅 source_inventory.tsv，然后创建 02_download_raw_data.md，用经过确认的数据源下载 raw data、记录 checksum 和 download_manifest。
```

现在开始执行 Phase 1 data source inventory。

