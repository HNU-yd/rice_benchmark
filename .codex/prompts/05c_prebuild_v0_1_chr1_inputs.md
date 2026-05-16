# 05c_prebuild_v0_1_chr1_inputs.md

你现在执行 Phase 5C 前置任务：构建 v0.1-mini chr1 SNP-only 输入骨架。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

上一轮 05C 停止执行，原因是以下必需输入表不存在：

- `data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv`
- `data/interim/v0_1_mini/snp_table_chr1_v0_1.tsv`
- `data/interim/v0_1_mini/window_table_chr1_v0_1.tsv`
- `data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv`
- `data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv`
- `reports/v0_1_mini/weak_evidence_chr1_audit.tsv`

本任务目标是补齐这些前置输入表。
本任务不构建 Task 1 instances，不训练模型，不构建 evaluator，不做 phenotype prediction。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 主位数据：3K Rice accession-level SNP/indel genotype backbone
- v0.1-mini：chr1 SNP-only prototype
- 主任务：trait-conditioned SNP/indel localization
- trait_state 是条件输入，不是预测目标
- weak evidence 只能作为 weak localization evidence
- Oryzabase / Q-TARO 不能写成 causal ground truth
- unknown / unlabeled variants 不能默认作为 negative

本任务只构建 chr1 SNP-only 的 variant / window / weak evidence audit 输入骨架。

---

## 2. 输入文件

请自动查找并读取：

```text
data/raw/variants/snp/core_v0.7.bim.gz
data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz
data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz

reports/raw_data_inventory/reference_inventory.tsv
reports/raw_data_inventory/gff3_inventory.tsv

reports/weak_evidence_inventory/oryzabase_inventory.tsv
reports/weak_evidence_inventory/oryzabase_columns.tsv
reports/weak_evidence_inventory/qtaro_inventory.tsv
reports/weak_evidence_inventory/qtaro_columns.tsv

reports/trait_state_review/frozen_v0_1_traits.tsv
configs/v0_1_frozen_traits.yaml
````

如果某个文件路径不同，请在 `data/raw/`、`reports/`、`configs/` 中搜索相似文件。

如果 `reports/raw_data_inventory/reference_inventory.tsv` 缺失，可以直接从 FASTA header 读取 chromosome 长度。

如果 weak evidence inventory 缺失，不要重跑下载；只报告缺失，并生成空 weak evidence audit 表。

---

## 3. 允许创建

创建：

```text
data/interim/v0_1_mini/
reports/v0_1_mini/
scripts/build_v0_1/
configs/v0_1_mini.yaml
```

允许创建脚本：

```text
scripts/build_v0_1/build_chromosome_map.py
scripts/build_v0_1/build_chr1_snp_variant_tables.py
scripts/build_v0_1/build_chr1_window_tables.py
scripts/build_v0_1/build_chr1_weak_evidence_audit.py
scripts/build_v0_1/run_build_v0_1_mini.sh
```

注意：

```text
data/interim/ 不进入 git。
reports/v0_1_mini/、scripts/build_v0_1/、configs/v0_1_mini.yaml 可以进入 git。
```

---

## 4. 禁止事项

禁止：

```text
不要构建 Task 1 instances
不要训练模型
不要构建 evaluator
不要构建 baseline
不要跑 GWAS
不要做 phenotype prediction
不要做 trait classification
不要把 weak evidence 写成 causal ground truth
不要把 unknown 标记为 negative
不要提交 data/raw 或 data/interim
```

---

## 5. 创建 configs/v0_1_mini.yaml

创建：

```text
configs/v0_1_mini.yaml
```

内容包括：

```yaml
version: v0.1-mini

scope:
  species: "Oryza sativa"
  primary_dataset: "3K Rice"
  chromosome_scope: ["1"]
  variant_scope: "SNP-only"
  reference_build: "IRGSP-1.0 / GCF_001433935.1"
  task: "trait-conditioned SNP/indel localization"
  prototype: true

inputs:
  snp_bim: "data/raw/variants/snp/core_v0.7.bim.gz"
  reference_fasta: "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz"
  reference_gff3: "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz"
  frozen_traits: "configs/v0_1_frozen_traits.yaml"

window:
  chromosome: "1"
  refseq_chrom: "NC_029256.1"
  window_size: 100000
  stride: 50000

rules:
  weak_evidence_not_causal_ground_truth: true
  unknown_not_negative: true
  no_phenotype_prediction: true
```

---

## 6. chromosome map

创建：

```text
scripts/build_v0_1/build_chromosome_map.py
```

输出：

```text
data/interim/v0_1_mini/chromosome_map.tsv
reports/v0_1_mini/chromosome_map_report.tsv
```

固定映射：

```text
1  -> NC_029256.1
2  -> NC_029257.1
3  -> NC_029258.1
4  -> NC_029259.1
5  -> NC_029260.1
6  -> NC_029261.1
7  -> NC_029262.1
8  -> NC_029263.1
9  -> NC_029264.1
10 -> NC_029265.1
11 -> NC_029266.1
12 -> NC_029267.1
```

输出字段：

```text
numeric_chrom
refseq_chrom
reference_build
mapping_confidence
notes
```

---

## 7. chr1 SNP variant tables

创建：

```text
scripts/build_v0_1/build_chr1_snp_variant_tables.py
```

读取：

```text
data/raw/variants/snp/core_v0.7.bim.gz
data/interim/v0_1_mini/chromosome_map.tsv
```

只保留：

```text
chrom = 1
```

输出：

```text
data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
data/interim/v0_1_mini/snp_table_chr1_v0_1.tsv
reports/v0_1_mini/variant_table_chr1_summary.tsv
```

字段：

```text
variant_id
chrom
refseq_chrom
pos
plink_variant_id
allele1
allele2
variant_type
source_file
notes
```

注意：

```text
PLINK BIM 的 allele1 / allele2 不一定等于 reference / alt。
不要伪装成 ref_allele / alt_allele。
notes 中写明 allele orientation requires later validation.
```

报告字段：

```text
chrom
refseq_chrom
n_variants
min_pos
max_pos
n_missing_pos
n_duplicate_variant_id
notes
```

---

## 8. chr1 window table 和 variant-window mapping

创建：

```text
scripts/build_v0_1/build_chr1_window_tables.py
```

参数：

```text
chromosome = 1
refseq_chrom = NC_029256.1
window_size = 100000
stride = 50000
```

需要读取 chr1 reference length。优先从：

```text
reports/raw_data_inventory/reference_inventory.tsv
```

读取 `NC_029256.1` 的长度。
如果该文件缺失，则从 FASTA header 逐行计算长度。

输出：

```text
data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv
reports/v0_1_mini/window_table_chr1_summary.tsv
```

`window_table_chr1_v0_1.tsv` 字段：

```text
window_id
chrom
refseq_chrom
start
end
window_size
stride
n_snp
notes
```

`variant_window_mapping_chr1_v0_1.tsv` 字段：

```text
variant_id
window_id
chrom
refseq_chrom
pos
relative_position_in_window
variant_type
notes
```

窗口坐标使用 1-based inclusive start/end。
SNP 如果落入多个滑动窗口，可以产生多行 mapping。

---

## 9. chr1 weak evidence audit

创建：

```text
scripts/build_v0_1/build_chr1_weak_evidence_audit.py
```

读取：

```text
reports/weak_evidence_inventory/oryzabase_inventory.tsv
reports/weak_evidence_inventory/oryzabase_columns.tsv
reports/weak_evidence_inventory/qtaro_inventory.tsv
reports/weak_evidence_inventory/qtaro_columns.tsv
reports/trait_state_review/frozen_v0_1_traits.tsv
data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
data/interim/v0_1_mini/chromosome_map.tsv
```

输出：

```text
data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv
reports/v0_1_mini/weak_evidence_chr1_audit.tsv
reports/v0_1_mini/weak_evidence_mapping_summary.md
```

要求：

1. Q-TARO 如果有 Chr / Genome start / Genome end 字段，则筛选 chr1 interval。
2. Oryzabase 如果有 chromosome / RAP ID / MSU ID / trait class / trait terms，则筛选 chr1 candidate genes。
3. 对 frozen 9 个 trait 做关键词弱匹配。
4. 如果无法明确坐标，保留为 gene_or_trait_evidence_without_coordinate。
5. 不要把 gene 或 QTL 写成 causal ground truth。
6. 如果 coordinate build 不明确，必须标记 `coordinate_build_uncertain = true`。

`weak_evidence_chr1_candidates.tsv` 字段：

```text
evidence_candidate_id
source
evidence_tier
evidence_type
trait_id
trait_name
trait_or_category
chrom
refseq_chrom
start
end
gene_id
gene_symbol
coordinate_build_uncertain
overlaps_chr1_window
matched_window_ids
notes
```

`weak_evidence_chr1_audit.tsv` 字段：

```text
source
evidence_tier
evidence_type
n_raw_records
n_chr1_candidates
n_with_coordinates
n_without_coordinates
n_overlapping_windows
coordinate_build_uncertain_count
notes
```

---

## 10. run_build_v0_1_mini.sh

创建：

```text
scripts/build_v0_1/run_build_v0_1_mini.sh
```

内容：

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/interim/v0_1_mini reports/v0_1_mini

python scripts/build_v0_1/build_chromosome_map.py
python scripts/build_v0_1/build_chr1_snp_variant_tables.py
python scripts/build_v0_1/build_chr1_window_tables.py
python scripts/build_v0_1/build_chr1_weak_evidence_audit.py
```

---

## 11. 总报告

创建：

```text
reports/v0_1_mini/v0_1_mini_input_skeleton_report.md
```

主体中文，必须包含：

1. 本次任务目标。
2. 为什么要补这个前置步骤。
3. chromosome map 结果。
4. chr1 SNP variant table 结果。
5. chr1 window table 结果。
6. variant-window mapping 结果。
7. weak evidence chr1 audit 结果。
8. 哪些 weak evidence 有坐标。
9. 哪些 weak evidence 只有 gene/trait 语义，没有坐标。
10. 为什么不把 weak evidence 当作 causal ground truth。
11. 为什么 unknown 不是 negative。
12. 是否可以重新执行 05C。

结论必须明确：

```text
本任务只构建 05C 的前置输入表。
如果所有必需表都存在，则可以重新执行 05c_build_chr1_snp_task1_instances.md。
```

---

## 12. 运行命令

执行：

```bash
bash scripts/build_v0_1/run_build_v0_1_mini.sh
```

然后执行：

```bash
find reports/v0_1_mini -maxdepth 1 -type f | sort
find data/interim/v0_1_mini -maxdepth 1 -type f | sort
python -m py_compile scripts/build_v0_1/*.py
git status --short --ignored
```

---

## 13. Git 提交要求

注意：

```text
data/raw/ 不提交
data/interim/ 不提交
```

确认 data 仍 ignored。

提交：

```bash
git add reports/v0_1_mini scripts/build_v0_1 configs/v0_1_mini.yaml README.md docs .gitignore .codex/prompts/05c_build_chr1_snp_task1_instances.md
git commit -m "build v0.1 chr1 SNP input skeleton"
git push
```

如果 README/docs 未变化，可以不提交它们。

---

## 14. 最终回复要求

完成后用中文报告：

```text
1. 当前工作目录
2. 是否补齐 05C 所需输入表
3. chr1 SNP 数
4. chr1 window 数
5. variant-window mapping 行数
6. weak evidence chr1 candidates 数
7. weak evidence 有坐标 / 无坐标数量
8. 是否可以重新执行 05C
9. 主要风险
10. 生成的报告文件
11. Git commit / push 状态
12. raw/interim data 是否未进入 git
13. 下一步
```

下一步应该是：

```text
重新执行 05c_build_chr1_snp_task1_instances.md，构建 chr1 SNP-only minimal Task 1 instances。
```

现在开始构建 v0.1-mini chr1 SNP-only 前置输入骨架。
