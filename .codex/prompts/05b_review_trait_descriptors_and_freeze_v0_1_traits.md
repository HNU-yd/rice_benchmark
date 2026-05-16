# 05b_review_trait_descriptors_and_freeze_v0_1_traits.md

你现在执行 Phase 5B：审查 trait descriptor，并冻结 v0.1-mini trait 子集。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

上一阶段已经构建了 trait_state prototype，结果显示：

- high-confidence accession subset: 2268
- SNP-only trait prototype samples: 2268
- SNP+indel trait prototype samples: 2268
- 非 metadata trait: 122
- continuous trait: 0
- categorical trait: 99
- binary trait: 23
- v0.1 推荐 trait: 34
- 推荐 trait 均来自 `Data < 2007`

当前最大风险是：推荐 trait 全部是编码型 categorical / binary trait。下一步必须审查每个 trait 的 descriptor、编码含义、类别分布和生物学可解释性，不能直接把编码值当作连续表型。

本任务目标：

1. 读取上一阶段推荐的 34 个 trait。
2. 从 phenotype description / descriptor 中解析 trait 含义。
3. 检查每个 trait 的编码含义。
4. 检查类别分布和缺失率。
5. 判断 trait 是否适合进入 v0.1-mini。
6. 尝试与 Oryzabase / Q-TARO 的 trait 关键词做弱语义匹配。
7. 冻结一个小规模 v0.1 trait 子集。
8. 不构建 Task 1 instances。
9. 不训练模型。
10. 不做 phenotype prediction。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 主位数据：3K Rice accession-level SNP/indel genotype backbone
- 变异范围：SNP + indel
- 主任务：trait-conditioned SNP/indel localization
- 不做 phenotype prediction
- 不做 trait classification
- weak evidence 只能作为 weak localization evidence
- unknown / unlabeled variants 不能默认作为 negative

本任务只是审查 trait_state 的语义和可用性。

---

## 2. 输入文件

读取：

```text
reports/trait_state/v0_1_trait_recommendation.tsv
reports/trait_state/trait_table_summary.tsv
reports/trait_state/trait_state_prototype_report.md
data/interim/trait_state/trait_table_prototype.tsv
data/interim/trait_state/trait_state_table_prototype.tsv
data/interim/trait_state/trait_value_table_prototype.tsv
data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx
reports/weak_evidence_inventory/oryzabase_trait_gene_summary.tsv
reports/weak_evidence_inventory/qtaro_trait_summary.tsv
````

如果某些 weak evidence summary 不存在，请只报告缺失，不要重建整个 weak evidence 流程。

---

## 3. 允许创建

创建：

```text
reports/trait_state_review/
data/interim/trait_state_review/
configs/v0_1_frozen_traits.yaml
scripts/trait_state/review_and_freeze_v0_1_traits.py
```

注意：

```text
data/interim/ 不进入 git。
reports/trait_state_review/、configs/、scripts/ 可以进入 git。
```

---

## 4. 禁止事项

禁止：

```text
不要构建 Task 1 instances
不要训练模型
不要做 phenotype prediction
不要做 trait classification
不要跑 GWAS
不要构建 evaluator
不要构建 split
不要把编码型 trait 当作连续生物量
不要把 weak evidence 写成 causal ground truth
不要把 C/D accession mapping 纳入分析
不要提交 data/raw 或 data/interim
```

---

## 5. 检查 AGENTS.md 未提交改动

先执行：

```bash
git diff AGENTS.md || true
```

如果 `AGENTS.md` 有改动：

1. 不要覆盖。
2. 在报告中说明改动摘要。
3. 如果改动是项目约束或工作流规则，可以随本次一起提交。
4. 如果改动看不懂，不提交该文件，只报告。

---

## 6. 创建审查脚本

创建：

```text
scripts/trait_state/review_and_freeze_v0_1_traits.py
```

功能：

1. 读取 `v0_1_trait_recommendation.tsv` 中推荐的 34 个 trait。
2. 读取 phenotype XLSX 的所有 sheet，尤其是 descriptor / description 相关 sheet。
3. 对每个 trait 查找：

   * trait name
   * source sheet
   * descriptor text
   * definition
   * method
   * scale
   * code meaning
   * category labels
4. 读取 `trait_state_table_prototype.tsv` 统计类别分布。
5. 判断是否适合进入 v0.1。
6. 尝试与 Oryzabase / Q-TARO trait 关键词做简单匹配。
7. 输出冻结 trait 子集。

---

## 7. trait descriptor 审查表

输出：

```text
reports/trait_state_review/trait_descriptor_review.tsv
```

字段：

```text
trait_id
source_sheet
trait_name
trait_type_guess
n_non_missing
missing_rate
n_unique_values
category_distribution
descriptor_found
descriptor_source
trait_definition
measurement_method
scale_or_code_meaning
biological_interpretability
coding_risk
recommended_action
manual_review_required
notes
```

`biological_interpretability` 可选：

```text
high
medium
low
unknown
```

`coding_risk` 可选：

```text
low
medium
high
```

`recommended_action` 可选：

```text
keep_for_v0_1
keep_for_sensitivity_only
defer_until_manual_review
exclude_metadata_or_unclear
```

---

## 8. 类别分布审查

输出：

```text
reports/trait_state_review/trait_category_distribution.tsv
```

字段：

```text
trait_id
trait_name
trait_state
n_samples
fraction
notes
```

如果某个 trait 的最大类别比例 > 0.9，标记：

```text
class_imbalance_high
```

如果某个 trait 有太多类别，标记：

```text
too_many_categories
```

建议规则：

```text
binary 或少数类别 trait 更适合 v0.1；
类别过多、极度不平衡、编码含义不清楚的 trait 暂缓。
```

---

## 9. weak evidence 语义匹配

输出：

```text
reports/trait_state_review/trait_to_weak_evidence_keyword_match.tsv
```

字段：

```text
trait_id
trait_name
matched_source
matched_keyword
matched_trait_or_category
match_strength
notes
```

匹配来源：

```text
Oryzabase known / cloned gene trait terms
Q-TARO QTL trait terms
```

只做关键词级弱匹配，不要写成强证据。

`match_strength` 可选：

```text
strong_keyword
weak_keyword
none
```

---

## 10. 冻结 v0.1 trait 子集

输出：

```text
reports/trait_state_review/frozen_v0_1_traits.tsv
configs/v0_1_frozen_traits.yaml
data/interim/trait_state_review/frozen_v0_1_trait_ids.txt
```

冻结规则建议：

```text
keep_for_v0_1 条件：
  n_non_missing >= 1000
  biological_interpretability = high 或 medium
  coding_risk != high
  类别分布不过度极端
  不是 metadata
  最好能和 Oryzabase / Q-TARO 有关键词联系
```

数量建议：

```text
优先冻结 5-10 个 trait。
不要为了数量强行纳入含义不清楚的 trait。
```

`frozen_v0_1_traits.tsv` 字段：

```text
trait_id
source_sheet
trait_name
trait_type_guess
n_non_missing
category_summary
biological_interpretability
weak_evidence_match
freeze_decision
freeze_reason
notes
```

---

## 11. 总报告

创建：

```text
reports/trait_state_review/trait_descriptor_review_report.md
```

主体中文，必须包含：

1. 本次任务目标。
2. 为什么不能直接使用 34 个推荐 trait。
3. phenotype 字段为什么主要是 categorical / binary。
4. descriptor 审查结果。
5. 类别分布审查结果。
6. weak evidence 关键词匹配结果。
7. 冻结的 v0.1 trait 子集。
8. 暂缓或排除的 trait。
9. 对后续 Task 1 instances 的影响。
10. 为什么这不是 phenotype prediction。
11. 主要风险。
12. 下一步建议。

结论必须明确：

```text
v0.1-mini 只使用冻结的 trait 子集。
trait_state 是条件输入，不是预测目标。
编码含义不清楚的 trait 不进入主流程。
```

---

## 12. 运行命令

执行：

```bash
python scripts/trait_state/review_and_freeze_v0_1_traits.py
```

然后执行：

```bash
find reports/trait_state_review -maxdepth 1 -type f | sort
find data/interim/trait_state_review -maxdepth 1 -type f | sort
python -m py_compile scripts/trait_state/*.py
git status --short --ignored
```

---

## 13. Git 提交

注意：

```text
data/raw/ 不提交
data/interim/ 不提交
```

确认 data 仍 ignored。

提交：

```bash
git add reports/trait_state_review scripts/trait_state configs/v0_1_frozen_traits.yaml README.md docs AGENTS.md .gitignore
git commit -m "review trait descriptors and freeze v0.1 traits"
git push
```

如果 `AGENTS.md` 不应提交，就不要加它。

---

## 14. 最终回复

完成后用中文报告：

```text
1. 当前工作目录
2. AGENTS.md 是否有未提交改动及处理方式
3. 审查的 trait 数量
4. descriptor 找到多少
5. 类别分布是否合理
6. weak evidence 关键词匹配结果
7. 冻结进入 v0.1 的 trait 数和名称
8. 暂缓或排除的 trait 数
9. 是否可以进入 chr1 SNP-only minimal Task 1 instances
10. 主要风险
11. 生成的报告文件
12. Git commit / push 状态
13. raw/interim data 是否未进入 git
14. 下一步
```

下一步应该是：

```text
如果 frozen v0.1 trait 子集质量可以接受，则构建 chr1 SNP-only minimal Task 1 instances。
```

现在开始审查 trait descriptor 并冻结 v0.1 trait 子集。
