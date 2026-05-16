# 05c_build_chr1_snp_task1_instances.md

你现在执行 Phase 5C：构建 chr1 SNP-only minimal Task 1 instances。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

当前已经完成：

- high-confidence accession subset：2268
- frozen v0.1 traits：9 个
- frozen trait 配置：`configs/v0_1_frozen_traits.yaml`
- SNP genotype：`core_v0.7.{bed,bim,fam}.gz`
- 当前 v0.1-mini 只做 chr1 SNP-only prototype
- indel 暂不进入 v0.1-mini 主流程
- trait_state 是条件输入，不是预测目标
- Oryzabase / Q-TARO 只能作为 weak localization evidence，不是 causal ground truth

本任务目标：

1. 读取 frozen v0.1 trait 子集。
2. 读取 high-confidence accession subset。
3. 读取 chr1 SNP prototype variant table。
4. 读取 chr1 window table 和 SNP-window mapping。
5. 读取 trait_state prototype。
6. 读取 weak evidence chr1 audit。
7. 构建 chr1 SNP-only minimal Task 1 input instances。
8. 构建窗口级 weak signal prototype。
9. 构建 instance-level manifest 和统计报告。
10. 不训练模型，不构建 evaluator，不做 phenotype prediction。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 主位数据：3K Rice accession-level SNP/indel genotype backbone
- v0.1-mini：chr1 SNP-only prototype
- 主任务：trait-conditioned SNP/indel localization
- trait_state 是条件输入，不是预测目标
- weak evidence 只能作为 weak localization evidence
- Oryzabase / Q-TARO / GWAS 不能写成 causal ground truth
- unknown / unlabeled variants 不能默认作为 negative

本任务只构建 minimal Task 1 instances，不训练模型。

---

## 2. 输入文件

读取以下文件：

```text
configs/v0_1_frozen_traits.yaml

data/interim/trait_state/high_confidence_accessions.tsv
data/interim/trait_state/trait_state_table_prototype.tsv
data/interim/trait_state/trait_value_table_prototype.tsv

data/interim/v0_1_mini/chromosome_map.tsv
data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
data/interim/v0_1_mini/snp_table_chr1_v0_1.tsv
data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv
data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv

reports/trait_state_review/frozen_v0_1_traits.tsv
reports/v0_1_mini/weak_evidence_chr1_audit.tsv
````

如果 `data/interim/v0_1_mini/` 中相关文件不存在，请先运行：

```bash
bash scripts/build_v0_1/run_build_v0_1_mini.sh
```

如果仍缺失，请停止并报告缺失，不要凭空重建。

---

## 3. 允许创建

创建：

```text
data/interim/task1_chr1_snp/
reports/task1_chr1_snp/
configs/task1_chr1_snp_v0_1.yaml
scripts/task1/
```

允许创建脚本：

```text
scripts/task1/build_chr1_snp_task1_instances.py
scripts/task1/inspect_chr1_snp_task1_instances.py
scripts/task1/run_build_chr1_snp_task1.sh
```

注意：

```text
data/interim/ 不进入 git。
reports/task1_chr1_snp/、configs/、scripts/task1/ 可以进入 git。
```

---

## 4. 禁止事项

禁止：

```text
不要训练模型
不要构建 evaluator
不要构建 baseline
不要跑 GWAS
不要做 phenotype prediction
不要做 trait classification
不要把 trait_state 当 prediction label
不要把 unknown variants 当 negative
不要把 weak evidence 当 causal ground truth
不要生成 causal / non-causal 二分类标签
不要提交 data/raw 或 data/interim
```

---

## 5. 配置文件

创建：

```text
configs/task1_chr1_snp_v0_1.yaml
```

内容包括：

```yaml
version: v0.1-chr1-snp-task1

scope:
  chromosome: "1"
  variant_type: "SNP"
  reference_build: "IRGSP-1.0 / GCF_001433935.1"
  task: "trait-conditioned SNP/indel localization"
  prototype: true

inputs:
  frozen_traits: "configs/v0_1_frozen_traits.yaml"
  high_confidence_accessions: "data/interim/trait_state/high_confidence_accessions.tsv"
  trait_state_table: "data/interim/trait_state/trait_state_table_prototype.tsv"
  variant_table: "data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv"
  window_table: "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv"
  variant_window_mapping: "data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv"
  weak_evidence_candidates: "data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv"

rules:
  trait_state_is_condition_signal: true
  no_phenotype_prediction: true
  weak_evidence_not_causal_ground_truth: true
  unknown_not_negative: true
```

---

## 6. 构建 instance 表

创建脚本：

```text
scripts/task1/build_chr1_snp_task1_instances.py
```

输出：

```text
data/interim/task1_chr1_snp/task1_chr1_snp_instances.tsv
data/interim/task1_chr1_snp/task1_chr1_snp_instance_manifest.tsv
data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv
```

### 6.1 task1_chr1_snp_instances.tsv 字段

字段：

```text
instance_id
trait_id
trait_name
internal_accession_id
genotype_sample_id
window_id
chrom
refseq_chrom
start
end
trait_state
trait_group
trait_direction
n_snp_in_window
window_weak_signal
window_label_state
evidence_tier_summary
notes
```

说明：

```text
每一行表示一个 trait_state + accession + chr1 reference_window 实例。
```

必须保证：

```text
trait_state 来自 frozen v0.1 traits。
accession 只来自 high-confidence accession subset。
window 只来自 chr1。
```

### 6.2 instance_id 规则

```text
instance_id = trait_id + "__" + genotype_sample_id + "__" + window_id
```

---

## 7. window weak signal prototype

构建：

```text
data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
```

字段：

```text
trait_id
window_id
chrom
refseq_chrom
start
end
n_overlapping_evidence
overlap_evidence_sources
max_evidence_tier
window_weak_signal
window_label_state
coordinate_build_uncertain
notes
```

规则：

```text
如果窗口与 Oryzabase / Q-TARO chr1 candidate evidence overlap，则 window_weak_signal > 0。
否则 window_weak_signal = 0，但 label_state 必须是 unknown_unlabeled，不是 negative。
```

`window_label_state` 可选：

```text
positive_weak_evidence
regional_weak_evidence
unknown_unlabeled
```

注意：

```text
没有 evidence 的窗口不能标记为 negative。
```

---

## 8. variant weak label prototype

构建：

```text
data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv
```

字段：

```text
trait_id
variant_id
chrom
refseq_chrom
pos
overlap_evidence_id
evidence_source
evidence_tier
evidence_type
variant_label_state
distance_to_nearest_evidence
notes
```

规则：

```text
若 variant 位于 QTL interval 或 known gene window 附近，可标记为 regional_weak_evidence 或 positive_weak_evidence。
否则标记 unknown_unlabeled。
```

不能出现：

```text
negative
causal
non_causal
ground_truth
```

---

## 9. instance manifest

构建：

```text
data/interim/task1_chr1_snp/task1_chr1_snp_instance_manifest.tsv
```

字段：

```text
manifest_key
manifest_value
notes
```

必须记录：

```text
n_accessions
n_traits
n_windows
n_variants
n_instances
n_windows_with_weak_evidence
n_variants_with_weak_evidence
n_unknown_windows
n_unknown_variants
prototype_version
created_at
```

---

## 10. 统计报告

创建：

```text
reports/task1_chr1_snp/task1_chr1_snp_instance_summary.tsv
reports/task1_chr1_snp/task1_chr1_snp_trait_summary.tsv
reports/task1_chr1_snp/task1_chr1_snp_window_signal_summary.tsv
reports/task1_chr1_snp/task1_chr1_snp_report.md
```

### 10.1 trait summary 字段

```text
trait_id
trait_name
n_accessions_with_state
n_instances
n_windows
n_windows_with_weak_evidence
state_distribution
notes
```

### 10.2 window signal summary 字段

```text
trait_id
n_windows_total
n_windows_positive_weak_evidence
n_windows_regional_weak_evidence
n_windows_unknown_unlabeled
positive_or_regional_fraction
notes
```

---

## 11. 报告内容要求

`task1_chr1_snp_report.md` 主体中文，必须包含：

1. 本次任务目标。
2. 输入数据。
3. frozen trait 子集。
4. high-confidence accession 数。
5. chr1 SNP 数。
6. chr1 window 数。
7. Task 1 instance 数。
8. weak evidence 覆盖情况。
9. window weak signal 规则。
10. variant weak label 规则。
11. 为什么没有 evidence 不等于 negative。
12. 为什么这不是 phenotype prediction。
13. 当前 prototype 的限制。
14. 下一步建议。

结论必须明确：

```text
这是 chr1 SNP-only minimal Task 1 instance prototype。
它不是最终 benchmark。
weak evidence 只是 weak localization evidence。
unknown_unlabeled 不作为 negative。
```

---

## 12. 检查脚本

创建：

```text
scripts/task1/inspect_chr1_snp_task1_instances.py
```

功能：

1. 检查 instance_id 是否唯一。
2. 检查 trait 是否只来自 frozen v0.1 traits。
3. 检查 accession 是否只来自 high-confidence subset。
4. 检查 window 是否只来自 chr1。
5. 检查 label_state 中不存在 negative / causal / ground_truth。
6. 检查 unknown_unlabeled 是否保留。
7. 输出检查结果到：

```text
reports/task1_chr1_snp/task1_chr1_snp_validation.tsv
```

---

## 13. run 脚本

创建：

```text
scripts/task1/run_build_chr1_snp_task1.sh
```

内容：

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/interim/task1_chr1_snp reports/task1_chr1_snp

python scripts/task1/build_chr1_snp_task1_instances.py
python scripts/task1/inspect_chr1_snp_task1_instances.py
```

---

## 14. 运行命令

执行：

```bash
bash scripts/task1/run_build_chr1_snp_task1.sh
```

然后执行：

```bash
find reports/task1_chr1_snp -maxdepth 1 -type f | sort
find data/interim/task1_chr1_snp -maxdepth 1 -type f | sort
python -m py_compile scripts/task1/*.py
git status --short --ignored
```

---

## 15. Git 提交

注意：

```text
data/raw/ 不提交
data/interim/ 不提交
```

确认 data 仍 ignored。

提交：

```bash
git add reports/task1_chr1_snp scripts/task1 configs/task1_chr1_snp_v0_1.yaml README.md docs .gitignore
git commit -m "build chr1 SNP-only minimal Task 1 instances"
git push
```

如果 README/docs 未变化，可不提交它们。

---

## 16. 最终回复

完成后用中文报告：

```text
1. 当前工作目录
2. frozen trait 数
3. high-confidence accession 数
4. chr1 SNP 数
5. chr1 window 数
6. Task 1 instance 数
7. weak evidence 覆盖情况
8. unknown_unlabeled 是否保留
9. 是否出现 negative / causal / ground_truth 等禁止标签
10. 是否可以进入 baseline / evaluator prototype
11. 主要风险
12. 生成的报告文件
13. Git commit / push 状态
14. raw/interim data 是否未进入 git
15. 下一步
```

下一步应该是：

```text
如果 Task 1 instance prototype 合格，则构建 minimal evaluator 和 random / heuristic baseline prototype。
```

现在开始构建 chr1 SNP-only minimal Task 1 instances。
