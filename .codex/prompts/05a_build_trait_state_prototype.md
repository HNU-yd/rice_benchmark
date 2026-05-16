# 05a_build_trait_state_prototype.md

你现在执行 Phase 5A：基于高置信 accession 映射构建 trait_state prototype。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

当前 accession ID harmonization 已经完成，核心结果为：

- genotype union samples: 3024
- core SNP samples: 3024
- indel samples: 3023
- pruned SNP samples: 3024
- Qmatrix samples: 3023
- 3K_list_sra_ids coverage: 3024 / 3024
- NCBI RunInfo coverage: 3024 / 3024
- Genesys MCPD coverage: 2706 / 3024
- phenotype A/B 可用映射: 2269 / 3024
- phenotype C-level name-only candidates: 12
- phenotype D-level unmapped samples: 743

本任务目标：

1. 只使用 A/B 级 high-confidence accession mapping。
2. 冻结 high-confidence accession subset。
3. 从 `3kRG_PhenotypeData_v20170411.xlsx` 中抽取 trait 值。
4. 构建 trait_table prototype。
5. 构建 trait_value_table prototype。
6. 构建 trait_state_table prototype。
7. 统计每个 trait 的可用样本数、缺失率、类型和分布。
8. 给出 v0.1-mini 推荐 trait 子集。
9. 不做 phenotype prediction。
10. 不训练模型。
11. 不构建正式 benchmark schema。
12. 不把 C/D 级映射纳入主分析。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 主位数据：3K Rice accession-level SNP/indel genotype backbone
- 变异范围：SNP + indel
- 主任务：trait-conditioned SNP/indel localization
- 不做 phenotype prediction
- 不做 trait classification
- 不纳入 SV / PAV / CNV
- 不使用 pan-reference / multi-reference / 多物种 genotype benchmark
- weak evidence 只能作为 weak localization evidence
- unknown / unlabeled variants 不能默认作为 negative

本任务中的 trait_state 是模型条件输入，不是预测目标。

---

## 2. 输入文件

读取：

```text
data/interim/accession_mapping/accession_mapping_master.tsv
data/interim/accession_mapping/phenotype_accession_candidates.tsv
data/interim/accession_mapping/phenotype_to_genotype_candidate_matches.tsv
data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx
reports/accession_mapping/accession_mapping_summary.md
docs/accession_id_harmonization.md
````

如果路径不同，请在 `data/raw/`、`data/interim/` 和 `reports/` 中自动搜索相似文件。

---

## 3. 允许创建

创建：

```text
data/interim/trait_state/
reports/trait_state/
scripts/trait_state/
configs/trait_state_v0_1.yaml
```

注意：

```text
data/interim/ 不进入 git。
reports/trait_state/、scripts/trait_state/、configs/trait_state_v0_1.yaml 可以进入 git。
```

---

## 4. 禁止事项

禁止：

```text
不要做 phenotype prediction
不要把 trait 当预测目标
不要训练模型
不要跑 GWAS
不要构建 evaluator
不要构建 split
不要构建正式 benchmark schema
不要把 C 级 name match 纳入 trait_state prototype
不要把 D 级 unmapped samples 纳入 trait_state prototype
不要提交 data/raw 或 data/interim
```

---

## 5. high-confidence accession subset

构建：

```text
data/interim/trait_state/high_confidence_accessions.tsv
reports/trait_state/high_confidence_accession_summary.tsv
```

筛选条件：

```text
usable_for_trait_mapping = true
phenotype_mapping_confidence in A/B
snp_core_available = true
qmatrix_available = true
```

同时统计如果加入 indel 后还剩多少样本：

```text
indel_available = true
```

输出字段：

```text
internal_accession_id
genotype_sample_id
three_k_dna_iris_unique_id
genetic_stock_varname
sra_accession
best_phenotype_sheet
best_phenotype_row_id
best_phenotype_stock_id
best_phenotype_gs_accno
best_phenotype_name
best_phenotype_source_accno
phenotype_mapping_confidence
snp_core_available
indel_available
qmatrix_available
usable_for_snp_trait
usable_for_snp_indel_trait
notes
```

---

## 6. 创建 trait_state 构建脚本

创建：

```text
scripts/trait_state/build_trait_state_prototype.py
```

功能：

1. 读取 high-confidence accession subset。
2. 读取 phenotype XLSX 的所有 sheet。
3. 根据 `best_phenotype_sheet` 和 `best_phenotype_row_id` 抽取对应表型行。
4. 自动识别 ID / metadata 列，不把它们当 trait。
5. 自动识别 trait 候选列。
6. 对每个 trait 统计：

   * 非缺失样本数
   * 缺失率
   * 唯一值数量
   * 是否可转为数值
   * 均值
   * 标准差
   * 最小值
   * 5%、25%、50%、75%、95% 分位数
   * 最大值
   * trait 类型推断：continuous / categorical / binary / id_or_metadata
7. 输出 trait_table、trait_value_table 和 trait_state_table prototype。

---

## 7. trait_table_prototype.tsv

输出：

```text
data/interim/trait_state/trait_table_prototype.tsv
reports/trait_state/trait_table_summary.tsv
```

字段：

```text
trait_id
source_sheet
trait_name
trait_type_guess
n_total_accessions
n_non_missing
missing_rate
n_unique_values
numeric_convertible
mean
std
min
q05
q25
median
q75
q95
max
recommended_for_v0_1
recommendation_priority
recommendation_reason
notes
```

推荐规则：

```text
P0:
  n_non_missing >= 1000
  trait_type_guess = continuous
  不是 ID / metadata / comment 字段

P1:
  n_non_missing >= 500
  continuous 或清晰 categorical / binary

P2:
  样本少、解释困难、metadata-like 或暂不适合
```

---

## 8. trait_value_table_prototype.tsv

输出：

```text
data/interim/trait_state/trait_value_table_prototype.tsv
```

字段：

```text
trait_id
internal_accession_id
genotype_sample_id
source_sheet
phenotype_row_id
raw_value
numeric_value
normalized_value
missing_flag
trait_type_guess
notes
```

连续性状 normalized_value 使用 z-score：

```text
(value - mean) / std
```

如果 `std = 0` 或 trait 非数值，则 normalized_value 为空。

---

## 9. trait_state_table_prototype.tsv

输出：

```text
data/interim/trait_state/trait_state_table_prototype.tsv
```

字段：

```text
trait_id
internal_accession_id
genotype_sample_id
raw_value
numeric_value
normalized_value
trait_group
trait_state
trait_direction
state_rule
notes
```

连续性状规则：

```text
bottom 30% = low
middle 40% = mid
top 30% = high
```

分类性状规则：

```text
trait_state = normalized category string
trait_group = same as trait_state
```

二分类性状规则：

```text
trait_state = class_0 / class_1 或原始类别
```

必须在 notes 或报告中明确：

```text
trait_state 是模型条件扰动信号，不是 prediction label。
```

---

## 10. v0.1 trait 推荐子集

输出：

```text
reports/trait_state/v0_1_trait_recommendation.tsv
reports/trait_state/v0_1_trait_recommendation.md
```

`v0_1_trait_recommendation.tsv` 字段：

```text
trait_id
source_sheet
trait_name
trait_type_guess
n_non_missing
missing_rate
recommendation_priority
recommended_for_v0_1
reason
notes
```

报告中列出：

```text
推荐优先进入 v0.1 的 trait
暂缓 trait
不能作为 trait 的 metadata 字段
```

---

## 11. 配置文件

创建：

```text
configs/trait_state_v0_1.yaml
```

内容包括：

```yaml
version: v0.1-trait-state-prototype

accession_subset:
  use_confidence_levels: ["A", "B"]
  exclude_confidence_levels: ["C", "D"]
  require_snp_core: true
  require_qmatrix: true

trait_state_rules:
  continuous:
    normalization: "zscore"
    grouping:
      low: "bottom_30_percent"
      mid: "middle_40_percent"
      high: "top_30_percent"
  categorical:
    state: "normalized_category"
  binary:
    state: "class_value"

constraints:
  no_phenotype_prediction: true
  trait_state_is_condition_signal: true
  unknown_not_negative: true
```

---

## 12. 总报告

创建：

```text
reports/trait_state/trait_state_prototype_report.md
```

主体中文，必须包含：

1. 本次任务目标。
2. high-confidence accession subset 样本数。
3. 可用于 SNP-only trait prototype 的样本数。
4. 可用于 SNP+indel trait prototype 的样本数。
5. phenotype sheet 情况。
6. 识别到的 trait 总数。
7. 连续性状数量。
8. 分类性状数量。
9. 二分类性状数量。
10. 推荐 v0.1 trait 子集。
11. trait_state 构建规则。
12. 为什么这不是 phenotype prediction。
13. C/D 级样本为什么不进入 trait_state。
14. 主要风险。
15. 下一步建议。

结论必须明确：

```text
本阶段只生成 prototype，不是最终 benchmark 表。
只有 A/B accession mapping 样本进入 trait_state prototype。
trait_state 是条件输入，不是预测目标。
```

---

## 13. 运行命令

执行：

```bash
python scripts/trait_state/build_trait_state_prototype.py
```

然后执行：

```bash
find reports/trait_state -maxdepth 1 -type f | sort
find data/interim/trait_state -maxdepth 1 -type f | sort
python -m py_compile scripts/trait_state/*.py
git status --short --ignored
```

---

## 14. Git 提交

注意：

```text
data/raw/ 不提交
data/interim/ 不提交
```

确认 data 仍 ignored。

提交：

```bash
git add reports/trait_state scripts/trait_state configs/trait_state_v0_1.yaml README.md docs .gitignore
git commit -m "build trait state prototype from high-confidence accession mapping"
git push
```

如果 README/docs 没有变化，可以不提交它们。

---

## 15. 最终回复

完成后用中文报告：

```text
1. 当前工作目录
2. high-confidence accession subset 样本数
3. 可用于 SNP-only trait prototype 的样本数
4. 可用于 SNP+indel trait prototype 的样本数
5. 识别到的 trait 总数
6. 连续性状数量
7. 分类 / 二分类性状数量
8. 推荐进入 v0.1 的 trait 数和名称
9. trait_state 构建规则
10. 是否构建了正式 trait_value_table
11. 是否可以进入最小 Task 1 instance 构建
12. 主要风险
13. 生成的报告文件
14. Git commit / push 状态
15. raw/interim data 是否未进入 git
16. 下一步
```

下一步应该是：

```text
如果 v0.1 trait 子集足够，则构建 chr1 SNP-only minimal Task 1 instances；
否则先人工审查 trait 字段和 accession mapping。
```

现在开始构建 trait_state prototype。
