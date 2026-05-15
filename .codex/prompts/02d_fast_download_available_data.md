# 02d_fast_download_available_data.md

你现在执行快速数据下载任务。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

用户明确要求：不要再过度 preflight，不要只下载两个 reference 文件。现在要尽快把能公开拿到的 3K Rice benchmark 相关数据下载到本地。

本任务目标：

1. 快速列出 AWS / 42basepairs / SNP-Seek mirror 中可下载的 3K Rice 数据。
2. 优先下载 benchmark 第一阶段需要的数据：
   - accession metadata
   - SNP genotype
   - indel genotype
   - trait / phenotype table
   - reference FASTA
   - reference GFF3 / annotation
   - weak evidence / known gene / QTL / GWAS 可直接下载文件
3. 不下载 BAM / CRAM / FASTQ 等巨大原始测序文件。
4. 下载完成后补充 `download_manifest.tsv`、`checksum_table.tsv` 和下载报告。
5. 对下载失败的 source，自动尝试 mirror 或备用入口。
6. 不实现 schema、model、evaluator、Evo2。

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
- AWS S3
- 42basepairs
- SNP-Seek mirror
- download_manifest.tsv
- checksum_table.tsv

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

本任务只是下载数据，不做 benchmark schema 和模型。

---

## 2. 本任务允许下载什么

允许下载：

```text
reference FASTA
reference GFF3 / GTF
accession metadata / variety metadata / sample metadata
3K Rice SNP genotype 文件
3K Rice indel genotype 文件
3K Rice phenotype / trait 表
3K Rice diversity / population / subpopulation metadata
known trait gene 表
QTL interval 表
GWAS summary / GWAS lead SNP 表
README / license / data description / md5 / checksum 文件
````

优先下载格式：

```text
VCF / VCF.gz
BCF
HDF5 / H5
TSV / CSV / XLS / XLSX
FASTA / FNA / FA / FASTA.gz / FNA.gz
GFF / GFF3 / GTF
TXT / README / md5checksums.txt
```

---

## 3. 本任务禁止下载什么

禁止下载：

```text
BAM
CRAM
FASTQ
FQ
SRA
prefetch / fasterq-dump 结果
大规模 read-level raw sequencing data
pan-genome / SV / PAV / CNV 专用数据
多物种数据
模型权重
Evo2 embedding
```

如果 listing 中出现 BAM / CRAM / FASTQ，只记录路径，不下载。

---

## 4. 本任务优先数据源

优先尝试以下来源：

### 4.1 AWS Open Data 3K Rice

优先使用：

```bash
aws s3 ls s3://3kricegenome/ --no-sign-request
```

重点探索：

```bash
aws s3 ls s3://3kricegenome/ --no-sign-request
aws s3 ls s3://3kricegenome/snpseek-dl/ --no-sign-request
aws s3 ls s3://3kricegenome/VCF/ --no-sign-request
aws s3 ls s3://3kricegenome/reduced/ --no-sign-request
```

如果 aws CLI 不存在，优先尝试：

```bash
python -m pip install --user awscli
```

如果不能安装，则记录失败，转用 42basepairs 网页和可复制下载 URL。

### 4.2 42basepairs mirror

优先检查：

```text
https://42basepairs.com/browse/s3/3kricegenome
https://42basepairs.com/browse/s3/3kricegenome/reduced
https://42basepairs.com/download/s3/3kricegenome/3kRG_download.html
```

如果 AWS CLI 不可用，可以从 42basepairs 页面复制 download URL 或使用可访问的 https 链接下载。

### 4.3 SNP-Seek mirror

SNP-Seek 原站可能离线。优先尝试官方页面列出的 mirror：

```text
https://snpseekv3.duckdns.org
https://brs-snpseek.duckdns.org
```

重点寻找：

```text
Download
3K RG Phenotype
SNP dataset
indel dataset
variety information
accession metadata
```

如果 mirror 响应慢，不要反复卡住。记录状态，继续下载 AWS / 42basepairs 可用数据。

### 4.4 Reference / annotation

reference 继续使用已确认的：

```text
GCF_001433935.1 / IRGSP-1.0
```

下载：

```text
GCF_001433935.1_IRGSP-1.0_genomic.fna.gz
GCF_001433935.1_IRGSP-1.0_genomic.gff.gz
md5checksums.txt
```

---

## 5. 下载目录

创建：

```text
data/raw/
  reference/
  annotation/
  accessions/
  variants/
    snp/
    indel/
    mixed/
  traits/
  evidence/
  metadata/
  checksums/
  listings/
```

注意：`data/raw/` 已经在 `.gitignore` 中，不能提交 raw data。

---

## 6. 快速 listing

创建脚本：

```text
scripts/download/fast_list_available_sources.sh
```

功能：

1. 列出 AWS S3 可访问目录。
2. 把结果保存到：

```text
data/raw/listings/
reports/fast_download/
```

至少尝试：

```bash
aws s3 ls s3://3kricegenome/ --no-sign-request
aws s3 ls s3://3kricegenome/snpseek-dl/ --no-sign-request
aws s3 ls s3://3kricegenome/VCF/ --no-sign-request
aws s3 ls s3://3kricegenome/reduced/ --no-sign-request
aws s3 ls s3://3kricegenome/reduced/ --recursive --no-sign-request
aws s3 ls s3://3kricegenome/snpseek-dl/ --recursive --no-sign-request
```

如果 recursive listing 很大，只保存前 5000 行：

```bash
aws s3 ls ... | head -n 5000
```

不要 recursive 列 BAM / CRAM 目录。

---

## 7. 自动筛选候选文件

创建：

```text
scripts/download/select_download_candidates.py
```

输入：

```text
data/raw/listings/*.txt
```

输出：

```text
reports/fast_download/auto_download_candidates.tsv
reports/fast_download/skipped_large_raw_reads.tsv
reports/fast_download/unresolved_needed_data.tsv
```

筛选规则：

### 7.1 优先纳入

文件名或路径包含：

```text
phenotype
trait
variety
accession
sample
metadata
IRIS
3kRG
3K
SNP
snp
indel
InDel
vcf
hdf5
h5
core
filtered
base
pruned
gwas
QTL
gene
annotation
README
license
md5
checksum
```

文件扩展名包含：

```text
.vcf
.vcf.gz
.bcf
.h5
.hdf5
.tsv
.csv
.xls
.xlsx
.txt
.gz
.gff
.gff3
.gtf
.fna
.fa
.fasta
```

### 7.2 排除

路径或文件名包含：

```text
BAM
bam
CRAM
cram
FASTQ
fastq
fq
SRA
sra
```

以及扩展名：

```text
.bam
.cram
.fastq
.fq
.sra
```

### 7.3 输出字段

`auto_download_candidates.tsv` 字段：

```text
candidate_id
data_category
file_role
source
remote_path_or_url
access_method_type
expected_format
priority
local_path
reason_selected
notes
```

---

## 8. 快速下载脚本

创建：

```text
scripts/download/fast_download_selected_data.sh
```

功能：

1. 读取 `reports/fast_download/auto_download_candidates.tsv`。
2. 下载 P0 / P1 候选文件。
3. 默认 dry-run。
4. 显式 `--execute` 才下载。
5. 支持跳过已存在文件。
6. 支持 `.partial` 临时文件。
7. 下载失败继续下一个，不要整体中断。
8. 下载失败记录到：

```text
reports/fast_download/download_failures.tsv
```

命令：

```bash
bash scripts/download/fast_download_selected_data.sh
bash scripts/download/fast_download_selected_data.sh --execute
```

下载方式：

* S3 路径用：

```bash
aws s3 cp <s3_path> <local_path> --no-sign-request
```

* HTTPS URL 用：

```bash
curl -L --fail --retry 5 --retry-delay 10 -o <local_path>.partial <url>
mv <local_path>.partial <local_path>
```

注意：不要下载 BAM / CRAM / FASTQ。

---

## 9. 下载后 checksum

创建：

```text
scripts/download/update_fast_download_manifest.py
```

功能：

1. 扫描 `data/raw/` 下已下载文件。
2. 排除 BAM / CRAM / FASTQ。
3. 计算 sha256。
4. 更新：

```text
manifest/download_manifest.tsv
manifest/checksum_table.tsv
reports/fast_download/downloaded_files.tsv
reports/fast_download/checksum_summary.tsv
```

字段必须包括：

```text
download_id
source_id
data_category
file_role
original_filename
local_path
download_url_or_access_method
access_method_type
download_status
file_size_bytes
checksum_sha256
download_finished_at
source_version
reference_build
notes
```

如果某个文件无法确认 source_id，可以先写：

```text
source_id = auto_discovered
notes = source_id requires later curation
```

现在重点是先把数据拿到。

---

## 10. 快速下载报告

创建：

```text
reports/fast_download/fast_download_report.md
```

主体中文，包含：

```text
1. 本次任务目标
2. 成功 listing 的来源
3. AWS / 42basepairs / SNP-Seek mirror 可用性
4. 自动筛选出的下载候选数量
5. 实际下载文件数量
6. 按类别统计：
   - reference
   - annotation
   - accession metadata
   - SNP genotype
   - indel genotype
   - trait table
   - weak evidence
7. 跳过的 BAM / CRAM / FASTQ 文件
8. 下载失败的文件
9. checksum 结果
10. raw data 未进入 git 的确认
11. 仍缺失的数据
12. 下一步：raw data inventory
```

---

## 11. 实际执行要求

先执行 listing：

```bash
bash scripts/download/fast_list_available_sources.sh
```

再筛选：

```bash
python scripts/download/select_download_candidates.py
```

先 dry-run：

```bash
bash scripts/download/fast_download_selected_data.sh
```

如果 dry-run 候选没有 BAM / CRAM / FASTQ，也没有明显超大 read-level 文件，则执行：

```bash
bash scripts/download/fast_download_selected_data.sh --execute
```

下载后运行：

```bash
python scripts/download/update_fast_download_manifest.py
```

然后运行：

```bash
find data/raw -type f | sed 's#^\./##' | sort > reports/fast_download/raw_file_list.txt
du -sh data/raw/* > reports/fast_download/raw_data_size_summary.txt || true
git status
```

---

## 12. Git 提交要求

raw data 不能提交。

执行：

```bash
git status
```

如果显示 `data/raw/` 中有文件准备提交，必须停止并修正 `.gitignore`。

只提交脚本、manifest 和报告：

```bash
git add README.md docs manifest reports/fast_download scripts/download scripts/utils configs
git commit -m "fast download available 3K Rice benchmark data"
git push
```

不要提交 `data/raw/`。

---

## 13. 最终回复要求

完成后用中文报告：

```text
1. 当前工作目录
2. 成功 listing 的来源
3. 下载候选数量
4. 实际下载了哪些文件
5. 各类别是否已拿到：
   - reference
   - annotation
   - accession metadata
   - SNP genotype
   - indel genotype
   - trait table
   - weak evidence
6. 下载失败或仍缺失的数据
7. data/raw 总大小
8. checksum / manifest 更新状态
9. raw data 是否确认未进入 git
10. Git commit / push 状态
11. What was intentionally not implemented
12. Next step
```

Next step 应该是：

```text
创建 raw data inventory prompt，对已下载文件做 accession / SNP / indel / trait / reference build 对齐检查。
```

现在开始执行快速数据下载。
