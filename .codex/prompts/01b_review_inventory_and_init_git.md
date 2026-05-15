# 01b_review_inventory_and_init_git.md

你现在要执行一个 Phase 1 后的修正任务：审阅 source_inventory，并初始化 / 修复 git 仓库状态。

本任务不是下载数据，不是处理数据，不是写 schema，不是写模型。  
本任务只做两件事：

1. 审阅 Phase 1 生成的 `manifest/source_inventory.tsv`。
2. 确认当前项目目录是 git 仓库，并提交 Phase 0 + Phase 1 当前成果。

---

## 0. 语言要求

所有说明性文档主体使用中文。

固定术语可以保留英文，例如：

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

---

## 1. 项目根目录要求

当前项目根目录应为：

```bash
/home/data2/projects/rice_benchmark
````

请先执行：

```bash
pwd
ls -la
```

确认当前目录包含以下文件或目录：

```text
AGENTS.md
README.md
configs/
docs/
manifest/
scripts/
src/
tests/
.codex/
```

如果当前目录不是 `/home/data2/projects/rice_benchmark`，请切换到该目录：

```bash
cd /home/data2/projects/rice_benchmark
```

不要在错误目录下初始化 git。

---

## 2. 本任务禁止事项

禁止做：

```text
不要下载 raw data
不要创建 data/raw/
不要执行 aws s3 cp
不要执行 aws s3 sync
不要执行 wget 下载数据文件
不要执行 curl 下载数据文件
不要执行 prefetch / fasterq-dump
不要解析 VCF/BCF/FASTA/GFF
不要实现 schema
不要实现 benchmark builder
不要实现 split
不要实现 evaluator
不要实现 baseline
不要实现 model
不要实现 Evo2 代码
不要生成 toy data
```

---

## 3. source_inventory 审阅任务

请读取：

```text
manifest/source_inventory.tsv
manifest/source_inventory.schema.tsv
configs/sources.yaml
docs/data_source_inventory.md
docs/data_download_risk_notes.md
```

然后创建：

```text
reports/source_inventory/source_inventory_review.md
reports/source_inventory/p0_source_review.tsv
```

---

## 4. reports/source_inventory/source_inventory_review.md 内容要求

该报告主体使用中文。

至少包含：

```text
1. 审阅目标
2. 当前 source_inventory 行数
3. 已覆盖的数据类别
4. P0 数据源覆盖情况
5. SNP genotype 数据源风险
6. indel genotype 数据源风险
7. accession metadata 对齐风险
8. trait table 对齐风险
9. reference build 一致性风险
10. weak evidence 泄漏风险
11. excluded_for_v1 数据源检查
12. Phase 2 下载前必须人工确认的问题
13. 是否允许进入 Phase 2 的建议
```

其中第 13 点不要直接写“完全允许下载”。
应该写成：

```text
可以进入 Phase 2 下载脚本准备，但 P0 数据源的 URL / access method / reference build / accession ID mapping 仍需在下载前逐项确认。
```

---

## 5. reports/source_inventory/p0_source_review.tsv 内容要求

创建 TSV 文件，字段包括：

```text
source_id
data_category
dataset_name
candidate_source_name
download_url_or_access_method
reference_build
expected_format
verification_status
risk_level
phase2_action
manual_check_required
review_notes
```

`phase2_action` 可选值：

```text
prepare_download_script
manual_verify_first
defer
exclude_from_v1
```

规则：

1. P0 且 `verification_status` 为 verified 或 partially_verified 的数据源，可以写 `prepare_download_script`，但如果仍有版本或 accession 风险，`manual_check_required` 必须为 yes。
2. P0 且 `verification_status` 为 needs_manual_review 的数据源，写 `manual_verify_first`。
3. `exclude_from_v1 = yes` 的数据源写 `exclude_from_v1`。
4. 风险高且来源不清楚的写 `defer`。

---

## 6. 运行已有校验脚本

执行：

```bash
python scripts/utils/validate_source_inventory.py manifest/source_inventory.tsv
python -m py_compile scripts/utils/validate_source_inventory.py
```

如果校验失败，只修复 manifest 格式问题，不要新增下载逻辑。

---

## 7. Git 初始化 / remote 设置

本项目远程仓库为：

```text
git@github.com:HNU-yd/rice_benchmark.git
```

请执行：

```bash
git status
```

如果返回：

```text
fatal: not a git repository
```

则在项目根目录执行：

```bash
git init
git branch -M main
```

然后检查 remote：

```bash
git remote -v
```

如果没有 origin，则执行：

```bash
git remote add origin git@github.com:HNU-yd/rice_benchmark.git
```

如果已有 origin，但不是：

```text
git@github.com:HNU-yd/rice_benchmark.git
```

不要覆盖。请在最终回复中报告风险。

---

## 8. .gitignore 检查

请确认 `.gitignore` 存在。

如果不存在，请创建 `.gitignore`，至少包含：

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.pytest_cache/
.mypy_cache/
.ruff_cache/
.ipynb_checkpoints/

# Environment
.env
.venv/
venv/
conda-meta/
*.egg-info/

# Data
data/raw/
data/interim/
data/processed/
data/external/
*.vcf
*.vcf.gz
*.bcf
*.bcf.csi
*.tbi
*.fasta
*.fa
*.fna
*.fastq
*.fq
*.gz
*.zip
*.tar
*.tar.gz
*.bam
*.bai
*.cram
*.crai
*.h5
*.hdf5
*.parquet

# Large model / embedding files
checkpoints/
models/
weights/
embeddings/
*.pt
*.pth
*.ckpt
*.safetensors
*.npy
*.npz

# Reports and logs
logs/
tmp/
temp/
*.log

# OS / editor
.DS_Store
Thumbs.db
.vscode/
.idea/
```

注意：

```text
.codex/prompts/ 可以提交，因为 prompt 是项目工程的一部分。
manifest/source_inventory.tsv 可以提交，因为这是数据源清单，不是 raw data。
reports/source_inventory/ 可以提交，因为这是审阅报告。
```

---

## 9. Git commit

完成审阅和 git 初始化后执行：

```bash
git status
git add AGENTS.md README.md .gitignore configs docs manifest reports/source_inventory scripts src tests .codex
git commit -m "bootstrap project and add 3K Rice source inventory"
```

如果 commit 失败，请报告原因，不要强行修改用户身份配置，除非 git 明确要求 `user.name` 和 `user.email`。

如果 git 要求配置身份，可设置本仓库局部配置：

```bash
git config user.name "HNU-yd"
git config user.email "HNU-yd@users.noreply.github.com"
```

然后重新 commit。

---

## 10. Git push

commit 成功后执行：

```bash
git push -u origin main
```

如果 push 成功，报告 push 状态。

如果 push 失败，不要改用 HTTPS，不要写入 token，不要反复尝试。
请报告：

```text
push 失败原因
当前 commit hash
git remote -v
git status
```

---

## 11. 最终检查命令

完成后请运行：

```bash
git status
git log --oneline -3
find reports/source_inventory -maxdepth 2 -type f | sort
```

---

## 12. 最终回复要求

完成后请用中文报告：

```text
1. 当前工作目录
2. source_inventory 审阅结果
3. P0 数据源进入 Phase 2 的建议
4. Created / updated files
5. Commands run
6. Validation result
7. Git init / remote / commit / push 状态
8. What was intentionally not implemented
9. Next step
```

Next step 应该是：

```text
在人工确认 p0_source_review.tsv 后，创建 02_download_raw_data.md，开始 Phase 2 raw data download、checksum 和 download_manifest。
```

现在开始执行 Phase 1b：source inventory review and git initialization。

